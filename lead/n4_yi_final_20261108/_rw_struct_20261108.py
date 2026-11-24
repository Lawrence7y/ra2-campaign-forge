# _rw_struct_20261108.py — 重签结论撰写员独立结构取证（唯一写域内，只读）
# 矩阵解析 / V2 关键行 / diff 回放 / difflib 块 / AST 提取 / n-a 扫描 / 关键词计数
import ast
import difflib
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
MOTHER = ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc151_u0400_trip/qc151_trip.py"
CAND = ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
DIFF = ROOT / "lead/b2b_candidate_lf_20261107/CANDIDATE_LF.diff"
MATRIX = ROOT / "lead/b2b_design_20261106/STATE_MATRIX.json"
V2 = ROOT / "lead/n4_yi_final_20261108/_n4v2_B_EXECUTION_SPEC_V2.md"
B2B = ROOT / "lead/b2b_design_20261106/B2B_DESIGN.md"
RULING = ROOT / "lead/direction_ruling_20261108/RULING_DIRECTION.md"
R3 = ROOT / "lead/b2b_candidate_review3_20261107/CANDIDATE_SEMANTIC_REVIEW_R3.md"


def read_lines(p: Path):
    b = p.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return b.decode(enc).splitlines(), enc
        except UnicodeDecodeError:
            continue
    raise RuntimeError("decode failed: %s" % p)


def show(label, ls, a, b):
    for i in range(a, b + 1):
        print(f"{label}:{i}| {ls[i - 1]}")


m_lines, m_enc = read_lines(MOTHER)
c_lines, c_enc = read_lines(CAND)
print(f"== line counts: mother={len(m_lines)} ({m_enc}) candidate={len(c_lines)} ({c_enc})")

# ---------- 1. matrix ----------
print("\n== STATE_MATRIX.json raw ==")
mtx_text = MATRIX.read_text(encoding="utf-8")
for i, ln in enumerate(mtx_text.splitlines(), 1):
    print(f"MTX:{i}| {ln}")
mtx = json.loads(mtx_text)
entries = mtx if isinstance(mtx, list) else mtx.get("rows", mtx.get("entries", []))
print("matrix entries:", len(entries))
if entries:
    print("first-row keys:", sorted(entries[0].keys()))

# ---------- 2. V2 / B2B / RULING / R3 key lines ----------
print("\n== V2 key lines ==")
v2l = V2.read_text(encoding="utf-8").splitlines()
show("V2", v2l, 78, 104)
show("V2", v2l, 110, 135)
show("V2", v2l, 158, 168)
print("\n== B2B_DESIGN.md:655-672 ==")
b2bl = B2B.read_text(encoding="utf-8").splitlines()
show("B2B", b2bl, 655, 672)
print("\n== RULING_DIRECTION.md:15-30 ==")
rul = RULING.read_text(encoding="utf-8").splitlines()
show("RULING", rul, 15, 30)
print("\n== R3:38-50 ==")
r3l = R3.read_text(encoding="utf-8").splitlines()
show("R3", r3l, 38, 50)

# ---------- 3. diff headers + replay ----------
print("\n== CANDIDATE_LF.diff hunk headers ==")
dtxt = DIFF.read_text(encoding="utf-8").splitlines()
pat = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
hunk_headers = []
for i, ln in enumerate(dtxt, 1):
    if pat.match(ln):
        hunk_headers.append((i, ln))
        print(f"DIFF:{i}| {ln}")

patched = []
mi = 0
hunks = []
cur = None
for ln in dtxt:
    m = pat.match(ln)
    if m:
        if cur:
            hunks.append(cur)
        a0 = int(m.group(1)); ac = int(m.group(2)) if m.group(2) else 1
        b0 = int(m.group(3)); bc = int(m.group(4)) if m.group(4) else 1
        cur = {"hdr": ln, "a0": a0, "ac": ac, "b0": b0, "bc": bc,
               "minus": [], "plus": [], "ctx": 0}
        while mi < a0 - 1:
            patched.append(m_lines[mi]); mi += 1
        continue
    if cur is None:
        continue
    if ln.startswith("\\") or ln.startswith("index ") or ln.startswith("diff ") \
       or ln.startswith("--- ") or ln.startswith("+++ "):
        continue
    if ln.startswith("-"):
        cur["minus"].append(ln[1:]); mi += 1
    elif ln.startswith("+"):
        cur["plus"].append(ln[1:]); patched.append(ln[1:])
    elif ln.startswith(" "):
        cur["ctx"] += 1; patched.append(ln[1:]); mi += 1
    elif ln == "":
        cur["ctx"] += 1; patched.append(""); mi += 1
    else:
        hunks.append(cur); cur = None
if cur:
    hunks.append(cur)
while mi < len(m_lines):
    patched.append(m_lines[mi]); mi += 1

print("\n== replay validation ==")
ok_h = 0
for h in hunks:
    good = (h["ctx"] + len(h["minus"]) == h["ac"]) and (h["ctx"] + len(h["plus"]) == h["bc"])
    ok_h += 1 if good else 0
    print(f"  hdr='{h['hdr']}' ctx={h['ctx']} minus={len(h['minus'])} plus={len(h['plus'])} counts_ok={good}")
print("hunk count-consistency:", f"{ok_h}/{len(hunks)}")
print("REPLAY patched==candidate:", patched == c_lines, f"(patched={len(patched)} lines)")
if patched != c_lines:
    for k, (x, y) in enumerate(zip(patched, c_lines)):
        if x != y:
            print("  first diff at line", k + 1, "| patched:", repr(x[:80]), "| cand:", repr(y[:80]))
            break
added = sum(len(h["plus"]) for h in hunks)
deleted = sum(len(h["minus"]) for h in hunks)
print("diff totals: added=%d deleted=%d net=%+d" % (added, deleted, added - deleted))

# ---------- 4. difflib change blocks vs hunk minus-ranges ----------
sm = difflib.SequenceMatcher(None, m_lines, c_lines, autojunk=False)
blocks = [op for op in sm.get_opcodes() if op[0] != "equal"]
print("\n== difflib change blocks:", len(blocks), "==")
for tag, a1, a2, b1, b2 in blocks:
    print(f"  {tag:7s} mother[{a1 + 1}-{a2}] cand[{b1 + 1}-{b2}] del={a2 - a1} add={b2 - b1}")
hunk_ranges = [(h["a0"], h["a0"] + h["ac"] - 1) for h in hunks]
outside = [b for b in blocks if not any(b[1] + 1 >= r[0] and b[2] <= r[1] for r in hunk_ranges)]
print("blocks outside nine hunk minus-ranges:", len(outside))
print("E-block 5984-5990 inside any hunk minus-range:",
      any(r[0] <= 5984 and r[1] >= 5990 for r in hunk_ranges))

# ---------- 5. AST extraction on candidate ----------
print("\n== AST (candidate only, never imported/executed) ==")
c_src = CAND.read_text(encoding="utf-8")
tree = ast.parse(c_src)
consts = {}
for node in ast.walk(tree):
    tgt_names = []
    val = None
    if isinstance(node, ast.Assign):
        tgt_names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        val = node.value
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        tgt_names = [node.target.id]
        val = node.value
    for nm in tgt_names:
        if nm in ("FRESHNESS_VERDICTS", "CONFIDENCES", "SNAPSHOT_STATES") and val is not None:
            try:
                consts[nm] = (ast.literal_eval(val), node.lineno)
            except Exception:
                consts[nm] = ("<nonliteral>", node.lineno)
for nm in ("FRESHNESS_VERDICTS", "CONFIDENCES", "SNAPSHOT_STATES"):
    v, ln = consts.get(nm, ("<absent>", -1))
    print(f"{nm} @cand:{ln} = {v}")

finish_defs = []
finish_calls = []
copy_calls = []
final_calls = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_finish":
        finish_defs.append(node.lineno)
    if isinstance(node, ast.Call):
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
        if name == "_finish":
            verdict = conf = None
            kws = {k.arg: k.value for k in node.keywords if k.arg}
            if "verdict" in kws and isinstance(kws["verdict"], ast.Constant):
                verdict = kws["verdict"].value
            if "confidence" in kws and isinstance(kws["confidence"], ast.Constant):
                conf = kws["confidence"].value
            if verdict is None and len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                verdict = node.args[0].value
            if conf is None and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                conf = node.args[1].value
            finish_calls.append((node.lineno, verdict, conf))
        if name == "copy_post_except_evidence":
            copy_calls.append((node.lineno, [k.arg for k in node.keywords]))
        if name == "finalize_trip":
            final_calls.append(node.lineno)
print("_finish def lines:", finish_defs)
print("_finish call count:", len(finish_calls))
for ln, v, cf in finish_calls:
    print(f"  _finish call @{ln} verdict={v!r} confidence={cf!r}")
print("copy_post_except_evidence calls:", copy_calls)
print("finalize_trip call lines:", final_calls)

mtx_pairs = set()
for e in entries:
    vd = e.get("verdict") or e.get("expectedVerdict") or e.get("expected_verdict")
    cf = e.get("confidence") or e.get("expectedConfidence") or e.get("expected_confidence")
    if vd is not None:
        mtx_pairs.add((vd, cf))
code_pairs = {(v, cf) for _, v, cf in finish_calls if v is not None}
print("matrix (verdict,confidence) pairs:", sorted(mtx_pairs))
print("code   (verdict,confidence) pairs:", sorted(code_pairs))
print("code-only pairs:", sorted(code_pairs - mtx_pairs))
print("matrix-only pairs:", sorted(mtx_pairs - code_pairs))

# ---------- 6. n/a scan + TERM line + keywords + imports ----------
print("\n== n/a scan ==")
for label, ls in (("MOTHER", m_lines), ("CAND", c_lines)):
    loose = [(i, ln.strip()[:110]) for i, ln in enumerate(ls, 1) if re.search(r"n/a", ln, re.IGNORECASE)]
    print(f"{label} n/a (case-insensitive) lines: {len(loose)}")
    for i, s in loose:
        print(f"  {label}:{i}| {s}")
print("CAND:7320 vs MOTHER:7079 identical:", c_lines[7319] == m_lines[7078])
print("CAND:7320|", c_lines[7319].strip()[:160])
print("MOTHER:7079|", m_lines[7078].strip()[:160])

print("\n== keyword substring counts (lowercased full text) ==")
low_m = MOTHER.read_bytes().decode("utf-8", "replace").lower()
low_c = c_src.lower()
for kw in ("gamemd", "ra2loader", "taskkill", "yuri", "os.system", "subprocess.popen",
           "ctypes", "b2_fix_design", "readprocessmemory", "minidump", "suspendthread"):
    print(f"  {kw}: mother={low_m.count(kw)} cand={low_c.count(kw)}")

def import_set(src):
    s = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            for a in node.names:
                s.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            s.add((node.module or "?").split(".")[0])
    return s

ims, imc = import_set(MOTHER.read_text(encoding="utf-8")), import_set(c_src)
print("import sets equal:", ims == imc)
print("  mother-only:", sorted(ims - imc), "cand-only:", sorted(imc - ims))

# ---------- 7. targeted source line evidence ----------
print("\n== targeted lines ==")
show("MOTHER", m_lines, 212, 217)
show("CAND", c_lines, 215, 229)
show("CAND", c_lines, 4473, 4481)
show("MOTHER", m_lines, 4558, 4565)
show("CAND", c_lines, 4580, 4585)
show("CAND", c_lines, 4628, 4631)
show("CAND", c_lines, 4643, 4650)
show("CAND", c_lines, 6164, 6169)
show("CAND", c_lines, 7363, 7368)
show("MOTHER", m_lines, 7122, 7128)
