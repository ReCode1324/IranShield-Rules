# IranShield Rules

Monthly-updated, self-hosted ad-blocking and Iranian DIRECT routing data for sing-box and Xray clients.

1. Create a GitHub repository with a `main` default branch and upload these files.
2. Run **Actions → Monthly IranShield Rules Update → Run workflow** once.
3. The workflow fetches verified upstream blocklists and RIPEstat Iranian IP allocations, builds JSON/SRS for sing-box and custom `.dat` for Xray, publishes them under `dist/`, and schedules future builds monthly (day 5, 03:17 UTC).
4. Use `dist/srslist.json` to discover the SRS links; use the `dist/examples/` routing fragments in clients that support those formats.

**Important:** You must integrate routing fragments into a working client configuration; these files are not VPN server subscriptions. The custom `.dat` assets use names distinct from the core's built-in `geoip.dat` and `geosite.dat` so other categories are preserved. GitHub private repositories cannot serve unauthenticated remote SRS URLs. This pipeline is DNS/domain-level only and cannot eliminate all ads (notably first-party and cosmetic ads). Unreviewed repositories discovered by GitHub search are never automatically ingested.

Full Persian instructions: [README.md](README.md). Repository code: GPL-3.0; upstream data retain their respective licenses.
