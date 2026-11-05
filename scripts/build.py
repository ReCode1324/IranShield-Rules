#!/usr/bin/env python3
"""IranShield Rules: fetch, parse, validate, export sing-box sources & Xray Geo*.dat.

Only a DNS/domain subset of ABP syntax is safely convertible. Unsupported cosmetic,
URL/path, regex, and modifier rules are skipped instead of broadening blocking.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = re.compile(r"^(?:[a-z0-9_-]+\.)+[a-z0-9_-]+$", re.I)
ADBLOCK = re.compile(r"^(\|\||@@\|\|)([a-z0-9._-]+)\^(?:$|\$([a-z,~_-]+))", re.I)
SAFE_HOST_IPS = {"0.0.0.0", "127.0.0.1", "::", "::1"}
MAX_BYTES = 20 * 1024 * 1024
SRS_TAGS = ["block-ads", "block-ads-ir", "block-ads-global", "direct-iran-domains", "direct-iran-ips", "direct-iran-all"]


def normalize_domain(token: str) -> str | None:
    token = token.strip().lower().strip(".")
    if token.startswith("*."):
        token = token[2:]
    if len(token) > 253 or not token or ":" in token or "/" in token or "*" in token:
        return None
    try:
        token = token.encode("idna").decode("ascii")
    except (UnicodeError, ValueError):
        return None
    if not DOMAIN.fullmatch(token) or any(len(p) > 63 for p in token.split(".")):
        return None
    if token.endswith((".local", ".localhost", ".invalid", ".test", ".example")):
        return None
    try:
        ipaddress.ip_address(token)
        return None
    except ValueError:
        return token


def suffix_overlaps(a: str, b: str) -> bool:
    return a == b or a.endswith("." + b) or b.endswith("." + a)


def parse_domains(content: str, kind: str) -> tuple[set[str], set[str], set[str]]:
    """Returns (blocks/domains, ABP exceptions, IP ranges)."""
    domains: set[str] = set()
    exceptions: set[str] = set()
    ips: set[str] = set()
    if kind == "ripe-json":
        payload = json.loads(content)
        if payload.get("status") not in ("ok", None):
            raise ValueError("RIPEstat returned non-ok status")
        resources = payload["data"]["resources"]
        for family in ("ipv4", "ipv6"):
            for item in resources.get(family, []):
                try:
                    ips.add(str(ipaddress.ip_network(item, strict=False)))
                except (ValueError, TypeError):
                    continue
        return domains, exceptions, ips
    for original in content.splitlines():
        line = original.strip().lstrip("\ufeff")
        if not line or line.startswith(("!", "#", "//", "[")):
            continue
        if kind == "hosts":
            parts = line.split("#", 1)[0].split()
            if len(parts) < 2 or parts[0] not in SAFE_HOST_IPS:
                continue
            for host in parts[1:]:
                domain = normalize_domain(host)
                if domain:
                    domains.add(domain)
        elif kind == "adblock":
            # DNS-level conversion only. Rules with options are rejected rather than
            # misinterpreted; the ABP syntax can be context/path-specific.
            if line.startswith("@@||") or line.startswith("||"):
                m = ADBLOCK.fullmatch(line)
                if not m or m.group(3):
                    continue
                domain = normalize_domain(m.group(2))
                if domain:
                    (exceptions if m.group(1).startswith("@@") else domains).add(domain)
            elif line.startswith("0.0.0.0 ") or line.startswith("127.0.0.1 "):
                domain = normalize_domain(line.split()[1])
                if domain:
                    domains.add(domain)
            else:
                # Plain domains appear in some mixed DNS lists.
                domain = normalize_domain(line)
                if domain:
                    domains.add(domain)
        elif kind == "clash":
            # Format DOMAIN-SUFFIX,domain,policy or DOMAIN,domain,policy.
            parts = [x.strip() for x in line.split(",")]
            if len(parts) >= 2 and parts[0].upper() in ("DOMAIN-SUFFIX", "DOMAIN", "+.DOMAIN-SUFFIX"):
                domain = normalize_domain(parts[1])
                if domain:
                    domains.add(domain)
            elif line.startswith("+.") or line.startswith("."):
                # bootmortis ruleset uses Clash domain-set notation +.example.ir
                domain = normalize_domain(line[2:] if line.startswith("+.") else line[1:])
                if domain:
                    domains.add(domain)
            elif (domain := normalize_domain(line)):
                domains.add(domain)
        elif kind == "domains":
            domain = normalize_domain(line.split("#", 1)[0])
            if domain:
                domains.add(domain)
        elif kind == "cidr":
            try:
                ips.add(str(ipaddress.ip_network(line.split("#", 1)[0].strip(), strict=False)))
            except ValueError:
                pass
        else:
            raise ValueError(f"Unknown parser: {kind}")
    return domains, exceptions, ips


def fetch_source(source: dict, fixture_dir: Path | None) -> str:
    if fixture_dir is not None:
        return (fixture_dir / (source["id"] + ".txt")).read_text(encoding="utf-8")
    url = source["url"]
    if not url.startswith("https://"):
        raise ValueError("Source URL must be HTTPS")
    request = urllib.request.Request(url, headers={"User-Agent": "IranShieldRules/1.0 (+github actions)", "Accept": "text/plain, application/json, */*"})
    with urllib.request.urlopen(request, timeout=50) as r:
        if r.status != 200:
            raise ValueError(f"Unexpected status: {r.status}")
        # Hard size limit even when Content-Length is absent or forged.
        data = r.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError(f"Source too large: {source['id']}")
    return data.decode("utf-8-sig", errors="replace")


def collapse_ips(values: set[str]) -> list[str]:
    networks = [ipaddress.ip_network(x, strict=False) for x in values]
    v4 = [x for x in networks if x.version == 4]
    v6 = [x for x in networks if x.version == 6]
    return [str(n) for n in list(ipaddress.collapse_addresses(v4)) + list(ipaddress.collapse_addresses(v6))]


def pb_varint(n: int) -> bytes:
    if n < 0:
        raise ValueError("varint must be nonnegative")
    out = bytearray()
    while n > 127:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def pb_bytes(field: int, value: bytes) -> bytes:
    return pb_varint((field << 3) | 2) + pb_varint(len(value)) + value


def pb_string(field: int, value: str) -> bytes:
    return pb_bytes(field, value.encode("utf-8"))


def pb_int(field: int, value: int) -> bytes:
    return pb_varint(field << 3) + pb_varint(value)


def make_geosite(entries: dict[str, list[str]]) -> bytes:
    """Wire-format GeoSiteList from v2fly/v2ray-core routercommon/common.proto.

    Domain.Type RootDomain=2; domain.type field=1, domain.value field=2;
    GeoSite.country_code field=1, repeated domain field=2;
    GeoSiteList.repeated entry field=1.
    """
    output = bytearray()
    for tag, domains in entries.items():
        site = bytearray(pb_string(1, tag.upper()))
        for domain in domains:
            entry = pb_int(1, 2) + pb_string(2, domain)
            site += pb_bytes(2, entry)
        output += pb_bytes(1, site)
    return bytes(output)


def make_geoip(entries: dict[str, list[str]]) -> bytes:
    """Wire-format GeoIPList from v2fly/v2ray-core routercommon/common.proto."""
    output = bytearray()
    for tag, ranges in entries.items():
        entry = bytearray(pb_string(1, tag.upper()))
        for range_ in ranges:
            net = ipaddress.ip_network(range_, strict=False)
            cidr = pb_bytes(1, net.network_address.packed) + pb_int(2, net.prefixlen)
            entry += pb_bytes(2, cidr)
        output += pb_bytes(1, entry)
    return bytes(output)


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")


def rules_for_domains(domains: list[str]) -> list[dict]:
    return [{"domain_suffix": domains[i : i + 1200]} for i in range(0, len(domains), 1200)]


def rules_for_ips(ips: list[str]) -> list[dict]:
    return [{"ip_cidr": ips[i : i + 1200]} for i in range(0, len(ips), 1200)]


def build(out: Path, fixture_dir: Path | None, repository: str, min_total: bool, branch: str = "main") -> dict:
    sources = json.loads((ROOT / "config/sources.json").read_text(encoding="utf-8"))["sources"]
    collected: dict[str, set[str]] = defaultdict(set)
    all_exceptions: set[str] = set()
    reports = []
    for source in sources:
        try:
            raw = fetch_source(source, fixture_dir)
            domains, exceptions, ips = parse_domains(raw, source["format"])
            num = len(domains) + len(ips)
            if num < (1 if fixture_dir is not None else source["min_entries"]):
                raise ValueError(f"too few entries: {num}")
            collected[source["group"]].update(domains | ips)
            all_exceptions.update(exceptions)
            reports.append({"id": source["id"], "status": "ok", "items": num, "url": source["url"], "license": source["license"], "sha256": hashlib.sha256(raw.encode()).hexdigest()})
        except (OSError, ValueError, KeyError, urllib.error.URLError, TimeoutError) as e:
            if source["required"]:
                raise RuntimeError(f"Required source {source['id']} failed; previous published outputs stay untouched: {e}") from e
            reports.append({"id": source["id"], "status": "skipped", "reason": str(e)[:240], "url": source["url"]})
    def local(name: str, fmt: str = "domains") -> set[str]:
        return parse_domains((ROOT / "config" / name).read_text(encoding="utf-8"), fmt)[0 if fmt == "domains" else 2]

    blocks_ir = collected["ads-ir"]
    blocks_global = collected["ads-global"]
    blocks_manual = local("blocklist.txt")
    allowlist = local("allowlist.txt") | all_exceptions
    # Safety: broad parent blocking must be dropped when it would also cover
    # an exception. This intentionally errs toward fewer false positives.
    def permitted(domain: str) -> bool:
        return not any(suffix_overlaps(domain, exception) for exception in allowlist)
    blocks_ir = {d for d in blocks_ir if permitted(d)}
    blocks_global = {d for d in blocks_global if permitted(d)}
    blocks_manual = {d for d in blocks_manual if permitted(d)}
    blocks_ir |= {d for d in blocks_manual if d.endswith(".ir")}
    blocks_global |= {d for d in blocks_manual if not d.endswith(".ir")}
    ads = sorted(blocks_ir | blocks_global)
    ir_domains = sorted(collected["iran-domains"] | local("direct-domains.txt") | {"ir"})
    ir_ips = collapse_ips(collected["iran-ips"] | local("direct-ip.txt", "cidr"))
    if min_total and fixture_dir is None and (len(ads) < 1000 or len(ir_domains) < 10000 or len(ir_ips) < 200):
        raise RuntimeError("Global safety threshold failed; refusing to publish truncated output")
    if not ads or not ir_domains or not ir_ips:
        raise RuntimeError("Empty required category")

    # Stage all changes before modifying output directory.
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="iranshield-", dir=out.parent) as temp:
        stage = Path(temp) / "dist"
        stage.mkdir()
        categories = {
            "block-ads": rules_for_domains(ads),
            "block-ads-ir": rules_for_domains(sorted(blocks_ir)),
            "block-ads-global": rules_for_domains(sorted(blocks_global)),
            "direct-iran-domains": rules_for_domains(ir_domains),
            "direct-iran-ips": rules_for_ips(ir_ips),
            "direct-iran-all": rules_for_domains(ir_domains) + rules_for_ips(ir_ips),
        }
        for filename, rules in categories.items():
            write_json(stage / "sing-box" / (filename + ".json"), {"version": 2, "rules": rules})
        (stage / "xray").mkdir()
        (stage / "xray/iranshield-geosite.dat").write_bytes(make_geosite({
            "ADS": ads, "ADS-IR": sorted(blocks_ir), "ADS-GLOBAL": sorted(blocks_global),
            "IR": ir_domains,
        }))
        (stage / "xray/iranshield-geoip.dat").write_bytes(make_geoip({"IR": ir_ips}))
        base = f"https://raw.githubusercontent.com/{repository}/{branch}/dist/sing-box/"
        aliases = {
            "geosite-category-ads-all": "block-ads", "geosite-ads": "block-ads",
            "geosite-ads-ir": "block-ads-ir", "geosite-ads-global": "block-ads-global",
            "geosite-ir": "direct-iran-domains", "geoip-ir": "direct-iran-ips",
            "block-ads": "block-ads", "block-ads-ir": "block-ads-ir",
            "block-ads-global": "block-ads-global", "direct-iran-domains": "direct-iran-domains",
            "direct-iran-ips": "direct-iran-ips", "direct-iran-all": "direct-iran-all",
        }
        # NekoBox (including this fork) uses a flat name -> remote SRS URL map.
        # Keep copies at dist/srslist.json, dist/nekobox/srslist.json and the
        # repository root (published by the workflow).
        neko_srslist = {alias: base + target + ".srs" for alias, target in aliases.items()}
        write_json(stage / "srslist.json", neko_srslist)
        write_json(stage / "nekobox/srslist.json", neko_srslist)
        plain = stage / "plain"
        plain.mkdir()
        for name, values in {
            "ads": ads, "ads-ir": sorted(blocks_ir), "ads-global": sorted(blocks_global),
            "iran-domains": ir_domains, "iran-ips": ir_ips,
        }.items():
            (plain / (name + ".txt")).write_text("\n".join(values) + "\n", encoding="utf-8")
        hosts = stage / "hosts"
        hosts.mkdir()
        (hosts / "ads-hosts.txt").write_text("# IranShield DNS hosts list; domain-level only\n" + "".join(f"0.0.0.0 {host}\n" for host in ads), encoding="utf-8")
        rawbase = f"https://raw.githubusercontent.com/{repository}/{branch}/dist/"
        write_json(stage / "assets.json", {
            "singbox_srslist": rawbase + "srslist.json",
            "nekobox_srslist": f"https://raw.githubusercontent.com/{repository}/{branch}/srslist.json",
            "xray": {"geosite": rawbase + "xray/iranshield-geosite.dat", "geoip": rawbase + "xray/iranshield-geoip.dat"},
            "plain": {"ads": rawbase + "plain/ads.txt", "iran_domains": rawbase + "plain/iran-domains.txt", "iran_ips": rawbase + "plain/iran-ips.txt"},
            "dns_hosts": rawbase + "hosts/ads-hosts.txt",
        })
        # No forced outbound for unmatched traffic; integrate into existing config.
        sing = {
            "route": {
                "rules": [
                    {"rule_set": ["block-ads"], "action": "reject"},
                    {"ip_is_private": True, "action": "route", "outbound": "direct"},
                    {"rule_set": ["direct-iran-all"], "action": "route", "outbound": "direct"},
                ],
                "rule_set": [{"tag": tag, "type": "remote", "format": "binary", "url": base + tag + ".srs", "update_interval": "24h"} for tag in ("block-ads", "direct-iran-all")],
            }
        }
        xray = {
            "domainStrategy": "IPIfNonMatch",
            "rules": [
                {"type": "field", "domain": ["ext:iranshield-geosite.dat:ADS"], "outboundTag": "block"},
                {"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"},
                {"type": "field", "domain": ["ext:iranshield-geosite.dat:IR"], "outboundTag": "direct"},
                {"type": "field", "ip": ["ext:iranshield-geoip.dat:IR"], "outboundTag": "direct"},
            ],
        }
        write_json(stage / "examples/singbox-route-fragment.json", sing)
        write_json(stage / "examples/xray-routing-fragment.json", xray)
        write_json(stage / "examples/v2rayN-custom-routing.json", [
            {"remarks": "IranShield BLOCK Ads", "enabled": True, "domain": ["ext:iranshield-geosite.dat:ADS"], "outboundTag": "block"},
            {"remarks": "IranShield DIRECT Private", "enabled": True, "ip": ["geoip:private"], "outboundTag": "direct"},
            {"remarks": "IranShield DIRECT Domains", "enabled": True, "domain": ["ext:iranshield-geosite.dat:IR"], "outboundTag": "direct"},
            {"remarks": "IranShield DIRECT IPs", "enabled": True, "ip": ["ext:iranshield-geoip.dat:IR"], "outboundTag": "direct"},
        ])
        files = {str(p.relative_to(stage)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob("*")) if p.is_file()}
        manifest = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "repository": repository,
            "counts": {"ads": len(ads), "ads_ir": len(blocks_ir), "ads_global": len(blocks_global), "iran_domains": len(ir_domains), "iran_ip_cidrs": len(ir_ips), "allowlist": len(allowlist)},
            "sources": reports, "sha256": files,
            "notice": "Only DNS/host-level block rules converted; cosmetic, URL-path and complex ABP rules intentionally omitted.",
        }
        write_json(stage / "manifest.json", manifest)
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(stage, out)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--fixtures", type=Path, help="Use local sample inputs; never access the network")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "YOUR_USERNAME/IranShield-Rules"))
    parser.add_argument("--branch", default=os.environ.get("GITHUB_REF_NAME", "main"))
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("repository must be GitHub OWNER/REPO")
    if not re.fullmatch(r"[A-Za-z0-9_.\/-]+", args.branch) or args.branch.startswith("/") or ".." in args.branch:
        parser.error("branch contains unsafe characters")
    report = build(args.out.resolve(), args.fixtures, args.repository, True, args.branch)
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    main()
