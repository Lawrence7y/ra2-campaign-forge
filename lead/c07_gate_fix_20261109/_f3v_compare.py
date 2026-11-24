# _f3v_compare.py -- independent H-series drift check between orig/enh transcripts
# parses "  [PASS|FAIL] <name>" lines, compares H* checks per target; also N-hit summary for newly blocked
import re, os, json
HERE = r"D:\Project\ra2-campaign-forge\lead\c07_gate_fix_20261109"
LINE = re.compile(r"^  \[(PASS|FAIL)\] (H[^\s].*?)(?:  — .*)?$")

def parse(path):
    out = {}
    cur = None
    with open(path, encoding="utf-8") as f:
        for ln in f:
            m = re.match(r"^===== (.+?) exit=(-?\d+) =====$", ln.strip("\n"))
            if m:
                cur = m.group(1)
                out[cur] = {"exit": int(m.group(2)), "checks": {}}
                continue
            m = LINE.match(ln.rstrip("\n"))
            if m and cur:
                out[cur]["checks"][m.group(2)] = m.group(1)
    return out

orig = parse(os.path.join(HERE, "_f3v_orig_transcript.txt"))
enh = parse(os.path.join(HERE, "_f3v_enh_transcript.txt"))
assert set(orig) == set(enh), "target sets differ"
drift = []
for t in sorted(orig):
    o, e = orig[t]["checks"], enh[t]["checks"]
    hs_o = {k: v for k, v in o.items()}
    hs_e = {k: v for k, v in e.items() if k in o}  # only original check names
    if hs_o != hs_e:
        diff = {k: (hs_o.get(k), hs_e.get(k)) for k in set(hs_o) | set(hs_e)
                if hs_o.get(k) != hs_e.get(k)}
        drift.append((t, diff))
print("targets compared:", len(orig))
print("H-series drift:", len(drift))
for t, d in drift:
    print("DRIFT", t, json.dumps(d, ensure_ascii=False))
# exit-level table
flips = []
for t in sorted(orig):
    oe, ee = orig[t]["exit"], enh[t]["exit"]
    tag = "SAME" if oe == ee else ("ORIG_PASS->ENH_BLOCK" if oe == 0 and ee == 1 else "ORIG_BLOCK->ENH_PASS")
    if oe != ee:
        flips.append((t, oe, ee, tag))
print("exit flips:", len(flips))
for t, oe, ee, tag in flips:
    print("FLIP", t, "orig_exit=%d enh_exit=%d %s" % (oe, ee, tag))
# any orig-block -> enh-pass would be degradation
deg = [f for f in flips if f[1] == 1 and f[2] == 0]
print("degradation (orig blocked, enh passed):", len(deg), deg)
# first H-line count sanity per target (15 H items each in orig)
bad_hcount = [t for t in orig if len(orig[t]["checks"]) != 15]
print("targets with orig H-item count != 15:", bad_hcount)
