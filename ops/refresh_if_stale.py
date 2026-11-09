#!/usr/bin/env python3
"""Dispatch the shared GitHub refresh when its scheduled run falls behind."""
import datetime as dt
import base64
import json
import subprocess
import urllib.request

REPO = 'MichaelZelbel/godspeed-observed-state'
LATEST = 'https://api.github.com/repos/' + REPO + '/contents/latest.json'
MAX_AGE = dt.timedelta(minutes=90)
ACTIVE_AGE = dt.timedelta(minutes=30)


def instant(value):
    return dt.datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(dt.timezone.utc)


def needs_refresh(record, now):
    try:
        return now - instant(record['checked_utc']) > MAX_AGE
    except (KeyError, TypeError, ValueError):
        return True


def run(argv):
    return subprocess.run(argv, check=True, capture_output=True, text=True, timeout=30).stdout


def active_refresh(runs, now):
    return any(row.get('status') in ('queued', 'in_progress', 'waiting', 'requested')
               and now - instant(row['createdAt']) < ACTIVE_AGE
               for row in runs if row.get('createdAt'))


def main():
    now = dt.datetime.now(dt.timezone.utc)
    req = urllib.request.Request(LATEST, headers={'User-Agent': 'godspeed-observed-state-refresh',
                                                  'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            record = json.loads(base64.b64decode(json.load(response)['content']))
    except (OSError, ValueError):
        record = {}
    if not needs_refresh(record, now):
        print('shared line is fresh')
        return
    rows = json.loads(run(['gh', 'run', 'list', '--repo', REPO, '--workflow', 'hourly.yml',
                           '--limit', '5', '--json', 'status,createdAt']))
    if active_refresh(rows, now):
        print('shared refresh already running')
        return
    run(['gh', 'workflow', 'run', 'hourly.yml', '--repo', REPO])
    print('dispatched shared refresh')


if __name__ == '__main__':
    main()
