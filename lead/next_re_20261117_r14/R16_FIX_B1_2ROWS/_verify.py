# -*- coding: utf-8 -*-
"""Final verification of R16_FIX_B1_2ROWS deliverables. Read-only on all inputs."""
import io, os, sys, hashlib
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
OLD = os.path.join(R14, "R16_D1_WIDE_B1", "delta.tsv")

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

OK = True
def chk(cond, msg):
    global OK
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond: OK = False

# hashes unchanged
chk(sha(COV) == "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1", "coverage.tsv sha unchanged")
chk(sha(EXE) == "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476", "gamemd.exe sha unchanged")

# coverage rows (byte exact)
cov = {}
for bl in open(COV, "rb").read().split(b"\n"):
    c = bl.rstrip(b"\r").split(b"\t")
    if len(c) >= 8:
        cov[c[0].decode("ascii", "replace").strip().upper()] = c

# delta.tsv
dlines = open(os.path.join(HERE, "delta.tsv"), "rb").read().split(b"\n")
chk(dlines[0] == open(OLD, "rb").read().split(b"\n")[0], "delta header byte-identical to old delta")
rows = [l for l in dlines[1:] if l.strip()]
chk(len(rows) == 2, "delta has exactly 2 rows")
for l in rows:
    c = l.split(b"\t")
    chk(len(c) == 8, "delta row %s has 8 columns" % c[0].decode("ascii"))
    e = c[0].decode("ascii").strip().upper()
    covc = cov[e]
    for idx in (1, 2, 4, 5, 6, 7):
        chk(c[idx] == covc[idx], "delta %s col%d byte-identical to coverage" % (e, idx + 1))
    chk(c[3].startswith(covc[3]), "delta %s col4 strict prefix = coverage col4" % e)
    chk(b"\xe2\x91\xa3" in c[3], "delta %s col4 contains ④" % e)
    s = c[3].decode("utf-8")
    for token in ("vt=007E1668",
                  "槽 9 值=004322A0" if e == "004322A0" else "槽 10 值=004324B0",
                  "COL=007FA4D8 offset=0", "RTTI=00815E38→.?AVCDFileClass@@",
                  "装表点 0047AA3C 位于 0047AA30 体内", "装配方式=ctor_body",
                  "实测指令 mov dword ptr [esi], 0x7e1668", "entry 体外",
                  "D-47(A)", "§12.6"):
        chk(token in s, "delta %s ④ contains %s" % (e, token))
    chk("[esp + 0x20]" not in s, "delta %s ④ no longer has stack target" % e)

# vt1668_sites.tsv
vt = io.open(os.path.join(HERE, "vt1668_sites.tsv"), encoding="utf-8").read().splitlines()
chk(len(vt) == 10, "vt1668_sites header+9")
isct = [l.split("\t") for l in vt[1:]]
chk(sum(1 for c in isct if c[4] == "是") == 3, "vt1668_sites has 3 is_ctor=是")
chk(sum(1 for c in isct if c[4] == "否") == 6, "vt1668_sites has 6 is_ctor=否")
chk(any(c[0] == "00401953" for c in isct), "vt1668_sites has dtor 401953")
chk(any(c[0] == "535A60" or c[0] == "00535A60" for c in isct), "vt1668_sites has thunk 535A60")

# selfcheck18.tsv
sc = io.open(os.path.join(HERE, "selfcheck18.tsv"), encoding="utf-8").read().splitlines()
chk(len(sc) == 19, "selfcheck18 header+18")
srows = [l.split("\t") for l in sc[1:]]
sus = [c[0] for c in srows if c[5] == "SUSPECT"]
chk(sus == ["004322A0", "004324B0"], "selfcheck18 suspects exactly the 2 rows: %s" % sus)
for c in srows:
    if c[0] in ("004322A0", "004324B0"):
        chk(c[2] == "否" and c[3] == "是" and c[4] == "是", "selfcheck %s flags stack+dtor+notctor" % c[0])
    else:
        chk(c[5] == "OK", "selfcheck %s OK" % c[0])

# fields.tsv
fl = io.open(os.path.join(HERE, "fields.tsv"), encoding="utf-8").read().splitlines()
chk(len(fl) == 3, "fields header+2")
for l in fl[1:]:
    c = l.split("\t")
    chk(len(c) == 12, "fields row %s has 12 cols" % c[0])
    chk(c[6] == "0047AA3C" and c[8] == "0047AA30" and c[7] == "ctor_body", "fields %s new site/host/form correct" % c[0])
    chk(c[10] == "OK", "fields %s status OK" % c[0])
    chk("G1非栈=是" in c[9], "fields %s G1 reads 是" % c[0])

# REPORT
rpt = io.open(os.path.join(HERE, "REPORT.md"), encoding="utf-8").read()
for token in ("未写 `COVERAGE\\coverage.tsv`", "只重写这 2 行 ④、未改 grade/判定、未并表",
              "412ED7E36BC1AD4907763FEBB3A68D5FDABB3F0D2C999800444B57098B1AB2E1",
              "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476",
              "004322A0", "004324B0", "SUSPECT"):
    chk(token in rpt, "REPORT contains %s" % token)

print("\nALL_OK =", OK)
sys.exit(0 if OK else 1)
