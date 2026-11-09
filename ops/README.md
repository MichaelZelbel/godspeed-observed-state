# Backup for the shared hourly refresh

GitHub's scheduled workflow can run several hours late. On the Godspeed VPS,
this timer checks the published copy every 30 minutes. It dispatches the same
GitHub workflow only if the copy is more than 90 minutes old and no refresh is
already running. The workflow remains the one place that reads Observed State's
three files and publishes the line for every reader.

Install after cloning this repository to `/opt/godspeed-observed-state` on the
VPS, where the `gh` command is authenticated for the repository:

```sh
cp ops/godspeed-observed-state-refresh.* /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now godspeed-observed-state-refresh.timer
systemctl start godspeed-observed-state-refresh.service
```

The morning note independently refuses a published copy older than six hours.
