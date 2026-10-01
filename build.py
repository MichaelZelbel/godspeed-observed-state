#!/usr/bin/env python3
"""Build one line about the world from Observed State, for Godspeed Mission Control's morning brief.

Observed State (https://observedstate.com/en/, by Angel Cabrera) compares air traffic and the
internet each day against their own 90-day history and lists the magnitude 6+ earthquakes of
the last 24 hours. Its author agreed on 2026-10-01 that Godspeed Mission Control may offer that
as an optional line, on these terms, which this program keeps:

- Only three of the site's eleven files, chosen by him: adsb (air corridors past 3.5 sigma),
  ioda (countries' internet past 5 sigma) and usgs (magnitude 6+ in 24 hours). The other eight
  report over 7 to 15 day windows, so they cannot say what happened today.
- COUNT AND NAME, NEVER WEIGH. The line sums the three and names each item. No score, no index,
  no severity ranking, no "worst first". Items keep a fixed order: air, internet, earthquakes,
  and inside each group alphabetical names or the time the quake happened. Changing that is
  breaking the agreement, not a style choice.
- His site carries the cost, so this runs once an hour for every reader together and asks
  "has this changed?" first (If-None-Match), which costs him an empty reply when it has not.

Writes latest.json (the line plus what it was built from) and latest.txt (the line alone).
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

SITE = "https://observedstate.com"
LINK = "https://observedstate.com/en/"
SOURCES = ("adsb", "ioda", "usgs")
PREFIX = "The observed state of the world:"
USER_AGENT = "godspeed-observed-state/1 (+https://github.com/MichaelZelbel/godspeed-observed-state)"

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")

# The site's own English names (its page, var NODOS and var PAISES, read 2026-10-02). A code
# missing here is shown as it arrives: inventing a name would hide that the site added something.
CORRIDORS = {
    "ams_amsterdam": "Amsterdam", "atl_atlanta": "Atlanta", "bkk_bangkok": "Bangkok",
    "cai_cairo": "Cairo", "cdg_paris": "Paris", "del_delhi": "Delhi", "den_denver": "Denver",
    "dfw_dallas": "Dallas", "doh_doha": "Doha", "dubai_dubai": "Dubai",
    "fra_frankfurt": "Frankfurt", "gru_sao_paulo": "São Paulo", "mad_madrid": "Madrid",
    "icn_seoul": "Seoul", "ist_istanbul": "Istanbul", "jfk_new_york": "New York",
    "jnb_johannesburg": "Johannesburg", "lax_los_angeles": "Los Angeles", "lhr_london": "London",
    "maa_chennai": "Chennai", "mex_mexico_city": "Mexico City", "tyo_tokyo": "Tokyo",
    "ord_chicago": "Chicago", "pek_beijing": "Beijing", "pvg_shanghai": "Shanghai",
    "saw_istanbul_sabiha": "Istanbul Sabiha", "sin_singapore": "Singapore",
    "syd_sydney": "Sydney", "tlv_tel_aviv": "Tel Aviv", "yvr_vancouver": "Vancouver",
}
COUNTRIES = {
    "AE": "the United Arab Emirates", "AR": "Argentina", "AT": "Austria", "AU": "Australia",
    "BD": "Bangladesh", "BE": "Belgium", "BR": "Brazil", "CA": "Canada", "CH": "Switzerland",
    "CL": "Chile", "CN": "China", "CO": "Colombia", "CZ": "Czechia", "DE": "Germany",
    "DK": "Denmark", "EG": "Egypt", "ES": "Spain", "FR": "France", "GB": "the United Kingdom",
    "GR": "Greece", "HK": "Hong Kong", "ID": "Indonesia", "IE": "Ireland", "IL": "Israel",
    "IN": "India", "IQ": "Iraq", "IR": "Iran", "IT": "Italy", "JO": "Jordan", "JP": "Japan",
    "KE": "Kenya", "KR": "South Korea", "MX": "Mexico", "MY": "Malaysia", "NG": "Nigeria",
    "NL": "the Netherlands", "NO": "Norway", "PE": "Peru", "PH": "the Philippines",
    "PK": "Pakistan", "PL": "Poland", "PT": "Portugal", "QA": "Qatar", "RO": "Romania",
    "RU": "Russia", "SA": "Saudi Arabia", "SE": "Sweden", "SG": "Singapore", "SY": "Syria",
    "TH": "Thailand", "TR": "Türkiye", "TW": "Taiwan", "UA": "Ukraine",
    "US": "the United States", "VN": "Vietnam", "ZA": "South Africa",
}


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


def fetch(name):
    """Return (data, how) for one source, from the site or, when unchanged, from our last copy."""
    os.makedirs(os.path.join(STATE, "source"), exist_ok=True)
    cached = os.path.join(STATE, "source", name + ".json")
    etag_file = os.path.join(STATE, "source", name + ".etag")
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if os.path.exists(cached) and os.path.exists(etag_file):
        with open(etag_file, encoding="utf-8") as f:
            etag = f.read().strip()
        if etag:
            headers["If-None-Match"] = etag
    req = urllib.request.Request("%s/%s/latest.json" % (SITE, name), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            data = json.loads(body.decode("utf-8"))
            with open(cached, "wb") as f:
                f.write(body)
            with open(etag_file, "w", encoding="utf-8") as f:
                f.write(r.headers.get("ETag", "") or "")
            return data, "changed"
    except urllib.error.HTTPError as e:
        if e.code == 304 and os.path.exists(cached):
            with open(cached, encoding="utf-8") as f:
                return json.load(f), "unchanged"
        raise


def join_names(names):
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def magnitude(q):
    m = q.get("magnitud")
    if isinstance(m, (int, float)):
        return "a magnitude %.1f earthquake" % m
    return "an earthquake of magnitude 6 or more"


def compose(adsb, ioda, usgs):
    """The line and the items it names. Raises ValueError when a file lacks a field the line needs."""
    for d, field in ((adsb, "fuera_de_rango"), (ioda, "fuera_de_rango"), (usgs, "sismos")):
        if field not in d:
            raise ValueError("missing field %s in %s" % (field, d.get("fuente", "?")))
    air_n = int(adsb["fuera_de_rango"])
    net_n = int(ioda["fuera_de_rango"])
    quakes = list(usgs["sismos"] or [])
    count = air_n + net_n + len(quakes)

    items = []
    parts = []
    air = sorted(CORRIDORS.get(c, c) for c in (adsb.get("nodos_fuera_de_rango") or []))
    if air_n:
        if len(air) != air_n:
            air = air or ["%d air corridors" % air_n]
        parts.append("air traffic, at " + join_names(air))
        items += [{"kind": "air", "name": n} for n in air]
    net = sorted((COUNTRIES.get(c, c) for c in (ioda.get("paises_fuera_de_rango") or [])),
                 key=lambda n: n[4:] if n.startswith("the ") else n)
    if net_n:
        if len(net) != net_n:
            net = net or ["%d countries" % net_n]
        parts.append("internet, in " + join_names(net))
        items += [{"kind": "internet", "name": n} for n in net]
    for q in sorted(quakes, key=lambda q: str(q.get("momento", ""))):
        text = magnitude(q)
        if q.get("lugar"):
            text += " (%s)" % q["lugar"]
        parts.append(text)
        items.append({"kind": "earthquake", "name": text})

    if count == 0:
        sentence = "%s nothing to flag today." % PREFIX
    else:
        body = "; ".join(parts)
        body = body[0].upper() + body[1:]
        sentence = "%s %d %s to flag today. %s." % (
            PREFIX, count, "thing" if count == 1 else "things", body)
    return sentence, count, items


def main():
    built = now_utc()
    out = {"status": "ok", "link": LINK, "checked_utc": iso(built),
           "source": "Observed State, by Angel Cabrera", "sources": {}}
    try:
        data = {}
        for name in SOURCES:
            data[name], how = fetch(name)
            out["sources"][name] = {"calculado_utc": data[name].get("calculado_utc"), "fetch": how}
        sentence, count, items = compose(data["adsb"], data["ioda"], data["usgs"])
        out.update(line=sentence, count=count, items=items)
    except Exception as e:  # a broken hour is written down, never passed off as a quiet one
        out.update(status="unavailable", error=str(e)[:300],
                   line="%s not available right now." % PREFIX, count=None, items=[])
    out["text"] = "%s %s" % (out["line"], LINK)
    with open(os.path.join(HERE, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(os.path.join(HERE, "latest.txt"), "w", encoding="utf-8") as f:
        f.write(out["text"] + "\n")
    print(out["text"])
    return 0 if out["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
