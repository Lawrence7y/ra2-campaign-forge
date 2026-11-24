# -*- coding: utf-8 -*-
"""Test the host-identity rule before generating products."""
import io, os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
STARTS = os.path.join(ROOT, "lead", "next_re_20261117_r14", "R16_AUDIT_D1_WIDE_B1", "starts.json")
sys.path.insert(0, HERE)
from host_rule import Image, HostRule

im = Image(EXE)
hr = HostRule(im, STARTS)
VT = 0x7E1668

print("=== A) 8 non-stack sites of 0x7E1668 (incl. 535A60 thunk) ===")
SITES = [(0x401953, 0x401950), (0x4019BA, 0x4019A0), (0x47A9E3, 0x47A9D0),
         (0x47AA10, 0x47AA00), (0x47AA3C, 0x47AA30), (0x535A60, 0x535A60),
         (0x535A8A, 0x535A70), (0x697A47, 0x697840), (0x759532, 0x759510)]
for site, host in SITES:
    r = hr.classify(site, VT, host)
    print(" site=%s host=%08X ins=%-34s stack=%s this=%s ctorcall=%s dtorafter=%s rets=%s core_ctor=%s canon=%s dtor=%s fail=%s" % (
        r["site"], host, r["ins"], r["target_is_stack"], r["this_from_ecx"],
        r["base_ctor_before"], r["dtor_call_after"], r["returns_this"],
        r["host_is_ctor"], r["host_is_canonical_ctor"], r["host_is_dtor"], r["failed_gates"]))

print("\n=== B) 18 rows of OLD delta.tsv ===")
OLD = os.path.join(ROOT, "lead", "next_re_20261117_r14", "R16_D1_WIDE_B1", "fields.tsv")
lines = io.open(OLD, encoding="utf-8-sig").read().splitlines()
hdr = lines[0].split("\t")
for ln in lines[1:]:
    c = ln.split("\t")
    d = dict(zip(hdr, c))
    site = int(d["install_site"], 16)
    host = int(d["install_host"], 16)
    vt = int(d["vt"], 16)
    form = d["install_form(ctor_body|mov_abs|reg|other)"]
    r = hr.classify(site, vt, host)
    expected = "OK" if d["entry"] not in ("004322A0", "004324B0") else "SUSPECT"
    print(" %s form=%-9s site=%s host=%s stack=%s this=%s dtor=%s core=%s verdict=%s expected=%s %s" % (
        d["entry"], form, r["site"], d["install_host"], r["target_is_stack"],
        r["this_from_ecx"], r["host_is_dtor"], r["host_is_ctor"], r["verdict"],
        expected, "OK" if r["verdict"] == expected else "MISMATCH"))

print("\n=== C) canonical selection for CDFileClass (strict rule) ===")
for site, host in [(0x47A9E3, 0x47A9D0), (0x47AA10, 0x47AA00), (0x47AA3C, 0x47AA30)]:
    r = hr.classify(site, VT, host)
    print(" site=%s host=%08X canonical=%s gates=%s" % (r["site"], host, r["host_is_canonical_ctor"], r["failed_gates"]))
