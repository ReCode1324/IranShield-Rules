# IranShield Rules

Twice-monthly updated, self-hosted ad-blocking and Iranian DIRECT routing data for sing-box and Xray clients.

1. Create a GitHub repository with a `main` default branch and upload these files.
2. Run **Actions → Twice-Monthly IranShield Rules Update → Run workflow** once.
3. The workflow fetches verified upstream blocklists and RIPEstat Iranian IP allocations, builds JSON/SRS for sing-box and custom `.dat` for Xray, publishes them under `dist/`, and schedules future builds twice monthly (days 1 and 15, 03:17 UTC).
4. Use `srslist.json` (or `nekobox/srslist.json`) to discover the NekoBox SRS links; use the `dist/examples/` routing fragments in clients that support those formats.

**Important:** You must integrate routing fragments into a working client configuration; these files are not VPN server subscriptions. The custom `.dat` assets use names distinct from the core's built-in `geoip.dat` and `geosite.dat` so other categories are preserved. GitHub private repositories cannot serve unauthenticated remote SRS URLs. This pipeline is DNS/domain-level only and cannot eliminate all ads (notably first-party and cosmetic ads). Unreviewed repositories discovered by GitHub search are never automatically ingested.

Full Persian instructions: [README.md](README.md). Repository code: GPL-3.0; upstream data retain their respective licenses.

## NekoBox SRS index

The files `srslist.json`, `nekobox/srslist.json`, and `dist/nekobox/srslist.json` are a flat mapping of rule-set names to the generated SRS URLs. The workflow refreshes them on days 1 and 15, at 03:17 UTC, and supports manual dispatch. Initial placeholder `YOUR_USERNAME` URLs are replaced after the first successful workflow run.

After publishing your repo, use `https://raw.githubusercontent.com/OWNER/REPO/main/srslist.json`. This JSON **is not a proxy subscription** or a complete route configuration. NekoBox must load/refresh the mapping or use its remote SRS handling; merely entering the index URL in a proxy-subscription field does not enable blocking. Connect ad rules to reject and Iranian domain/IP rules to direct.
