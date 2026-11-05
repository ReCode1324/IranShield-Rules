import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build import (  # noqa: E402
    build, collapse_ips, make_geoip, make_geosite, normalize_domain,
    parse_domains, pb_varint, suffix_overlaps,
)


def decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        n = data[pos]
        pos += 1
        result |= (n & 127) << shift
        if n < 128:
            return result, pos
        shift += 7


def fields(data: bytes) -> list[tuple[int, bytes | int]]:
    result = []
    pos = 0
    while pos < len(data):
        key, pos = decode_varint(data, pos)
        num = key >> 3
        wire = key & 7
        if wire == 0:
            value, pos = decode_varint(data, pos)
        elif wire == 2:
            size, pos = decode_varint(data, pos)
            value = data[pos:pos + size]
            pos += size
        else:
            raise AssertionError(f"Unknown wire type {wire}")
        result.append((num, value))
    return result


class IranShieldTests(unittest.TestCase):
    def test_abp_parser_rejects_non_dns_rules(self):
        text = "\n".join(["||ads.example.com^", "@@||news.example.com^", "||foo.example.org^$third-party", "example.com##.ad", "||x.example.org/path"])
        block, except_, _ = parse_domains(text, "adblock")
        self.assertEqual(block, {"ads.example.com"})
        self.assertEqual(except_, {"news.example.com"})

    def test_hosts_only_sinkhole_addresses(self):
        domains, _, _ = parse_domains("0.0.0.0 ads.example.com\n8.8.8.8 safe.example.org", "hosts")
        self.assertEqual(domains, {"ads.example.com"})

    def test_domain_normalization(self):
        self.assertEqual(normalize_domain(" Example.IR. "), "example.ir")
        self.assertIsNone(normalize_domain("x.com/evil"))
        self.assertIsNone(normalize_domain("*.test.invalid"))
        self.assertTrue(suffix_overlaps("ads.example.com", "example.com"))
        self.assertFalse(suffix_overlaps("badexample.com", "example.com"))

    def test_ip_collapse(self):
        self.assertEqual(collapse_ips({"5.22.0.0/16", "5.22.0.0/17", "2a01:5e0::/32"}), ["5.22.0.0/16", "2a01:5e0::/32"])

    def test_protocol_geosite(self):
        blob = make_geosite({"ADS": ["ads.example.com"]})
        outer = fields(blob)
        self.assertEqual(outer[0][0], 1)
        site = fields(outer[0][1])
        self.assertEqual(site[0], (1, b"ADS"))
        domain = fields(site[1][1])
        self.assertEqual(domain, [(1, 2), (2, b"ads.example.com")])

    def test_protocol_geoip(self):
        blob = make_geoip({"IR": ["5.22.0.0/16", "2a01:5e0::/32"]})
        outer = fields(blob)
        record = fields(outer[0][1])
        self.assertEqual(record[0], (1, b"IR"))
        cidr1 = fields(record[1][1])
        self.assertEqual(cidr1, [(1, b"\x05\x16\x00\x00"), (2, 16)])
        self.assertEqual(len(fields(record[2][1])[0][1]), 16)

    def test_build_offline(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "dist"
            manifest = build(output, ROOT / "tests/fixtures", "example/IranShield-Rules", False)
            self.assertGreater(manifest["counts"]["ads"], 2)
            self.assertEqual(manifest["counts"]["iran_ip_cidrs"], 2)
            self.assertTrue((output / "xray/iranshield-geosite.dat").stat().st_size > 50)
            ads = json.loads((output / "sing-box/block-ads.json").read_text())
            elements = set(sum((x["domain_suffix"] for x in ads["rules"]), []))
            self.assertNotIn("critical.mock", elements)
            self.assertIn("ads.persian.mock", elements)
            self.assertIn("ads.ir", elements)
            self.assertIn("ir", json.loads((output / "sing-box/direct-iran-domains.json").read_text())["rules"][0]["domain_suffix"])
            self.assertTrue(json.loads((output / "srslist.json").read_text())["geosite-ir"].endswith("direct-iran-domains.srs"))
            self.assertEqual(len(json.loads((output / "examples/v2rayN-custom-routing.json").read_text())), 4)

    def test_fail_closed_preserves_last_good(self):
        import shutil
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            fixture = base / "fixtures"
            shutil.copytree(ROOT / "tests/fixtures", fixture)
            (fixture / "iran_hosted_domains.txt").unlink()
            out = base / "dist"
            out.mkdir()
            (out / "last-good.txt").write_text("previous stable release")
            with self.assertRaises(RuntimeError):
                build(out, fixture, "example/IranShield-Rules", False)
            self.assertEqual((out / "last-good.txt").read_text(), "previous stable release")

    def test_clash_plus_dot_format(self):
        domains, _, _ = parse_domains("+.cdn.ads.ir\nDOMAIN-SUFFIX,ads.example.com,REJECT\n", "clash")
        self.assertEqual(domains, {"cdn.ads.ir", "ads.example.com"})


if __name__ == "__main__":
    unittest.main()
