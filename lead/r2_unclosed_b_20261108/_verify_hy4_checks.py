# -*- coding: utf-8 -*-
"""独立复核员 hy4：① 全树摘要猎尾；② data.json 独立解析（+e>50 列）；
③ probe_expect 字面值 vs 主探针落盘记录独立比对；④ 两个尾串字面出现的分类统计。
只读（仅本脚本输出件写本任务写域）。"""
import hashlib, json, re, os, time
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
LEAD = ROOT / "lead"
WD = LEAD / "r2_unclosed_b_20261108"
TAILS = ["26f3fb61829756dfeecf", "b6f95763794"]

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

print("=== ① 全树摘要猎尾（hy4 独立实现，scope=lead/ 全树 + 根一级散件） ===")
paths = [p for p in LEAD.rglob("*") if p.is_file()
         and ".git" not in p.parts and ".mimosa" not in p.parts
         and "__pycache__" not in p.parts]
paths += [p for p in ROOT.iterdir() if p.is_file()]
t0 = time.time()
hits = {t: [] for t in TAILS}
n = 0
skipped = 0
for p in paths:
    try:
        if p.stat().st_size > 200_000_000:
            skipped += 1
            continue
        d = sha256_file(p)
        n += 1
        for t in TAILS:
            pos = d.find(t)
            if pos >= 0:
                hits[t].append((str(p.relative_to(ROOT)), d, pos, d.endswith(t)))
    except OSError:
        skipped += 1
print(f"hashed_files={n} skipped={skipped} elapsed={time.time()-t0:.1f}s")
for t in TAILS:
    print(f"  digest contains {t}: count={len(hits[t])}")
    for rel, d, pos, ew in hits[t][:5]:
        print(f"    HIT {rel} sha={d} pos={pos} endswith={ew}")

print()
print("=== ② data.json 独立解析（cells / trigger_details） ===")
P = LEAD / "dtrigger_round2_20261107" / "_dB_anchor_recompute_data.json"
with open(P, "rb") as f:
    data = json.loads(f.read().decode("utf-8-sig"))
cells = data["cells"]
details = data["trigger_details"]
print(f"cells ids = {list(cells.keys())}")
all_int = True
none_any = False
miss_any = False
eq_all = True
for cid in sorted(cells):
    c = cells[cid]
    v = c.get("nGt50PlusE", "MISSING")
    if v == "MISSING":
        miss_any = True
    if v is None:
        none_any = True
    if not isinstance(v, int) or isinstance(v, bool):
        all_int = False
    waits = []
    for r in details.get(cid, []):
        if isinstance(r, dict) and isinstance(r.get("wait"), (int, float)):
            waits.append(float(r["wait"]))
    ge100 = sum(1 for w in waits if w >= 100.0)
    e50_0 = sum(1 for w in waits if w > 50.0)
    e50_e = sum(1 for w in waits if w + 2.510999999 > 50.0)
    eq = (v == c["nTrig"] == c.get("nGt50") == e50_e == e50_0)
    ge100_eq = (ge100 == c["nGe100"])
    eq_all = eq_all and eq and ge100_eq
    print(f"  {cid}: nTrig={c['nTrig']} nGe100={c['nGe100']} nGt50={c.get('nGt50')} "
          f"nGt50PlusE={v!r} | waits n={len(waits)} min={min(waits):.3f} "
          f"re >=100={ge100} re +e>50(e=0)={e50_0} re +e>50(e=2.511)={e50_e} "
          f"| min>50={min(waits)>50} | 全等(列/重算)={eq} ge100同={ge100_eq}")
print(f"  判定: 全为整数={all_int} 任一None={none_any} 任一缺失={miss_any} 6/6恒等+重算全等={eq_all}")

print()
print("=== ③ probe_expect 字面值 vs _dtrigger_probe_out.txt 独立比对 ===")
SRC = LEAD / "dtrigger_round2_20261107" / "_dB_anchor_recompute.py"
src_lines = SRC.read_text(encoding="utf-8-sig").splitlines()
# 独立提取 :401-406 的字面元组
lit_pat = re.compile(r'^\s*"(C[^"]+)":\s*\(([^)]*)\),?\s*$')
lits = {}
for ln in src_lines[400:406]:
    m = lit_pat.match(ln)
    if m:
        vals = tuple(float(x) if "." in x else int(x) for x in m.group(2).split(",") if x.strip())
        lits[m.group(1)] = vals
print(f"  hard-coded probe_expect (_dB_anchor_recompute.py:401-406) = {lits}")
PROBE = LEAD / "dtrigger_compare_20261107" / "_dtrigger_probe_out.txt"
plines = PROBE.read_text(encoding="utf-8-sig", errors="replace").splitlines()
found = {}
cur = None
for i, ln in enumerate(plines, 1):
    m = re.match(r"\s{2}(C2-abs-P95x2|C3-r4|C3-r8|C3-r12)\s+\[", ln)
    if m:
        cur = m.group(1)
        found.setdefault(cur, {"def_line": i})
        continue
    if cur:
        mt = re.search(r"nTrig=(\d+)", ln)
        if mt and "nTrig" not in found[cur]:
            found[cur]["nTrig"] = int(mt.group(1)); found[cur]["nTrig_line"] = i
        mw = re.search(r"waitAfterS_hat\(ms\): min=([\d.]+) med=([\d.]+) .*max=([\d.]+)", ln)
        if mw and "min" not in found[cur]:
            found[cur].update(min=float(mw.group(1)), med=float(mw.group(2)),
                              max=float(mw.group(3)), wait_line=i)
ok_all = True
for cid, lit in lits.items():
    f = found.get(cid, {})
    pv = (f.get("nTrig"), f.get("min"), f.get("med"), f.get("max"))
    ok = (pv == lit)
    ok_all = ok_all and ok
    print(f"  {cid}: literal={lit} probe(:{f.get('nTrig_line')}/:{f.get('wait_line')})={pv} equal={ok}")
print(f"  四组逐值相等 = {ok_all}")

print()
print("=== ④ 两尾串字面出现（按目录分类，独立于 _b_textgrep 实现） ===")
suf = {".md", ".txt", ".py", ".json"}
for t in TAILS:
    rows = []
    for p in LEAD.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in suf:
            continue
        if any(x in p.parts for x in (".git", ".mimosa", "__pycache__")):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, ln in enumerate(txt.splitlines(), 1):
            if t in ln:
                rows.append((str(p.relative_to(ROOT)), i))
    pre = [r for r in rows if not r[0].startswith("lead\\r2_unclosed_b_20261108")]
    inwd = [r for r in rows if r[0].startswith("lead\\r2_unclosed_b_20261108")]
    print(f"  {t}: 总出现行={len(rows)}  写域外(既有件)={len(pre)}  写域内={len(inwd)}")
    for r in pre[:15]:
        print(f"    PRE {r[0]}:{r[1]}")
