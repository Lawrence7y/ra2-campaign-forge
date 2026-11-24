# -*- coding: utf-8 -*-
"""R16-MERGE-F1 / B1 — re-runnable verification (card §4, 9 items).
Reads current disk files + merge_state.json + raw backups; runs strict_panel.py
with OUT redirected to this product dir. Writes VERIFY.txt.
"""
import os, sys, json, hashlib, re, subprocess, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
STRICT_SRC = os.path.join(ROOT, "RULING_R15_20261119", "work", "strict_panel.py")
MY   = os.path.join(ROOT, "R16_MERGE_F1_B1")

FOUR = "④"
FOUR_SOLOT = "④ 活表槽位见证"
state = json.load(open(os.path.join(MY, "merge_state.json"), encoding="utf-8"))
orig_col4  = state["original_col4"]      # entry -> disk-original col4 (str)
delta_col4 = state["delta_col4"]         # entry -> delta col4 (str)
entries    = state["entries"]
disc_lines = state["disclosure_lines"]

results = []
def check(ok, name, detail=""):
    results.append((bool(ok), name, detail))
    print(("PASS" if ok else "FAIL"), name, ("| " + detail) if detail else "")

def sha(b):
    return hashlib.sha256(b).hexdigest()

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"):
        e = e[2:]
    try:
        return "%08X" % int(e, 16)
    except ValueError:
        return e

cov_after = open(COV, "rb").read()
panel_after = open(PANEL, "rb").read()
cov_before = open(os.path.join(MY, "coverage.before.bak"), "rb").read()
panel_before = open(os.path.join(MY, "PANEL.before.bak"), "rb").read()

# sanity: before backups match recorded before sha
check(sha(cov_before) == state["before"]["coverage"]["sha256"],
      "0a backup coverage sha == recorded before", state["before"]["coverage"]["sha256"][:16])
check(sha(panel_before) == state["before"]["panel"]["sha256"],
      "0b backup panel sha == recorded before", state["before"]["panel"]["sha256"][:16])
check(sha(cov_after) == state["after"]["coverage"]["sha256"],
      "0c current coverage sha == recorded after", state["after"]["coverage"]["sha256"][:16])
check(sha(panel_after) == state["after"]["panel"]["sha256"],
      "0d current panel sha == recorded after", state["after"]["panel"]["sha256"][:16])

# ---------- split helpers ----------
def split_cov(b):
    lines = b.split(b"\n")
    tn = lines[-1] == b""
    if tn:
        lines = lines[:-1]
    return lines, tn

covA_lines, covA_tn = split_cov(cov_after)
covB_lines, covB_tn = split_cov(cov_before)
hdrA, hdrB = covA_lines[0], covB_lines[0]
dataA, dataB = covA_lines[1:], covB_lines[1:]

# ======================================================================
# 1. 逐字节还原性 (coverage): swap 18 col4 back -> before sha
# ======================================================================
entry_idx_after = {}
for i, ln in enumerate(dataA, start=0):
    e = ln.split(b"\t")[0].decode("utf-8")
    entry_idx_after.setdefault(e, []).append(i)
restored = list(dataA)
for e in entries:
    i = entry_idx_after[e][0]
    f = list(restored[i].split(b"\t"))
    f[3] = orig_col4[e].encode("utf-8")
    restored[i] = b"\t".join(f)
restored_bytes = b"\n".join([hdrA] + restored) + (b"\n" if covA_tn else b"")
check(sha(restored_bytes) == state["before"]["coverage"]["sha256"],
      "1 coverage 逐字节还原性 (18 col4 换回 => before sha)",
      f"restored={sha(restored_bytes)[:16]} before={state['before']['coverage']['sha256'][:16]}")

# ======================================================================
# 2. 不变量
# ======================================================================
colcount = collections.Counter(len(ln.split(b"\t")) for ln in dataA)
atlas = set()
for i, line in enumerate(open(ATLAS, encoding="utf-8-sig")):
    if i == 0:
        continue
    p = line.rstrip("\r\n").split("\t")
    if p and p[0].strip():
        atlas.add(ne(p[0]))
proved = proved_in = proved_out = 0
for ln in dataA:
    f = ln.split(b"\t")
    if len(f) < 8:
        continue
    if f[4].decode("utf-8").strip() == "[已证]":
        proved += 1
        if ne(f[0].decode("utf-8")) in atlas:
            proved_in += 1
        else:
            proved_out += 1
inv_ok = (len(dataA) == 18498 and colcount == {8: 18498}
          and proved == 1654 and proved_in == 1648 and proved_out == 6)
check(inv_ok, "2 不变量 18498/{8:18498}/1654/1648/6",
      f"rows={len(dataA)} cols={dict(colcount)} proved={proved} in={proved_in} out={proved_out}")
# 18 rows grade still [已证]
grade_ok = True
for e in entries:
    i = entry_idx_after[e][0]
    f = dataA[i].split(b"\t")
    if f[4].decode("utf-8").strip() != "[已证]":
        grade_ok = False
check(grade_ok, "2b 18 行 grade 仍 [已证]", f"checked {len(entries)} rows")

# ======================================================================
# 3. 只有 18 行第 4 列变了
# ======================================================================
check(len(dataA) == len(dataB), "3a 行数未变", f"{len(dataB)} -> {len(dataA)}")
diff_entries = []
bad_diff = []
for i, (la, lb) in enumerate(zip(dataA, dataB)):
    if la == lb:
        continue
    fa, fb = la.split(b"\t"), lb.split(b"\t")
    e = fb[0].decode("utf-8")
    diff_entries.append(e)
    if len(fa) != 8 or len(fb) != 8:
        bad_diff.append((e, "colcount"))
        continue
    for k in range(8):
        if k != 3 and fa[k] != fb[k]:
            bad_diff.append((e, f"col{k+1}"))
check(set(diff_entries) == set(entries) and len(diff_entries) == 18 and not bad_diff,
      "3 只有 18 行第 4 列变了",
      f"diff_count={len(diff_entries)} match={set(diff_entries)==set(entries)} bad={bad_diff}")

# ======================================================================
# 4. 严格前缀 18/18
# ======================================================================
sp_fail = [e for e in entries if not delta_col4[e].startswith(orig_col4[e])]
check(len(sp_fail) == 0, "4 严格前缀 18/18", f"fail={sp_fail}")

# ======================================================================
# 5. 六个实测数 (recompute from current after + before backups)
# ======================================================================
def four_counts(lines):
    a = b = 0
    for ln in lines:
        f = ln.split(b"\t")
        if len(f) < 8:
            continue
        g = f[4].decode("utf-8").strip()
        s = f[3].decode("utf-8")
        if g == "[已证]":
            if FOUR in s:
                a += 1
            if FOUR_SOLOT in s:
                b += 1
    return a, b

NA_pre, NB_pre = four_counts(dataB)
NA_post, NB_post = four_counts(dataA)
N_pre_A = sum(1 for e in entries if FOUR in orig_col4[e])
N_pre_B = sum(1 for e in entries if FOUR_SOLOT in orig_col4[e])
six = dict(N_pre_A=N_pre_A, N_pre_B=N_pre_B,
           N_A_pre=NA_pre, N_A_post=NA_post,
           N_B_pre=NB_pre, N_B_post=NB_post,
           netA=NA_post-NA_pre, netB=NB_post-NB_pre)
exp = state.get("six_numbers_expected")
check(True, "5 六个实测数", json.dumps(six, ensure_ascii=False))
# consistency with analysis.json values
a = json.load(open(os.path.join(MY, "analysis.json"), encoding="utf-8"))["six_numbers"]
check(all(six[k] == a[k] for k in ["N_pre_A","N_pre_B","N_A_pre","N_A_post","N_B_pre","N_B_post"]),
      "5b 六个数与 analyze.py 一致", json.dumps(a, ensure_ascii=False))

# ======================================================================
# 6. §12.6 / §12.4 命中计数
# ======================================================================
seg126 = seg124 = 0
for e in entries:
    seg = delta_col4[e][len(orig_col4[e]):]
    seg126 += seg.count("§12.6")
    seg124 += seg.count("§12.4")
txtA = cov_after.decode("utf-8")
txtB = cov_before.decode("utf-8")
check(seg126 == 18 and seg124 == 0,
      "6a 18 行追加段 §12.6=18 §12.4=0", f"§12.6={seg126} §12.4={seg124}")
check(txtB.count("§12.4") == 0 and txtA.count("§12.4") == 0,
      "6b 全表 §12.4 = 0 (before&after)", f"before={txtB.count('§12.4')} after={txtA.count('§12.4')}")
check(txtA.count("§12.6") == txtB.count("§12.6") + 18,
      "6c 全表 §12.6 净增 18",
      f"before={txtB.count('§12.6')} after={txtA.count('§12.6')}")

# ======================================================================
# 7. PANEL.md 还原性
# ======================================================================
# remove the 7 inserted lines at recorded position from current panel
p_lines = panel_after.split(b"\n")
ins_1based = state["insert_line_after_m88"]  # line number in BEFORE panel, after which inserted
cnt = state["insert_line_count"]
# in after panel, inserted lines occupy indices ins_1based .. ins_1based+cnt-1 (0-based)
start = ins_1based  # 0-based index of first inserted line (since before line ins_1based is index ins_1based-1)
removed = p_lines[:start] + p_lines[start+cnt:]
panel_restored = b"\n".join(removed)
check(sha(panel_restored) == state["before"]["panel"]["sha256"],
      "7 PANEL.md 还原性 (删插入块 => before sha)",
      f"restored={sha(panel_restored)[:16]} before={state['before']['panel']['sha256'][:16]}")
check(panel_after.count("M89".encode("utf-8")) == 1,
      "7b PANEL 恰 1 条 M89", f"count={panel_after.count('M89'.encode('utf-8'))}")
check(b"\r" not in panel_after, "7c PANEL 无 CR", "")
# verify inserted block bytes match
ins_block = b"\n".join([ln.encode("utf-8") for ln in disc_lines]) + b"\n"
check(sha(ins_block) == state["insert_bytes_sha256"],
      "7d 插入块字节 sha 与 state 一致", state["insert_bytes_sha256"][:16])

# ======================================================================
# 8. 达标未翻转 (strict_panel.py with OUT -> my dir)
# ======================================================================
strict_src = open(STRICT_SRC, encoding="utf-8").read()
strict_local = strict_src.replace(
    'OUT  = os.path.join(ROOT, "RULING_R15_20261119", "work")',
    'OUT  = r"%s"' % MY.replace("\\", "\\\\"))
assert strict_local != strict_src, "OUT replace failed"
local_path = os.path.join(MY, "strict_panel_local.py")
open(local_path, "w", encoding="utf-8").write(strict_local)
proc = subprocess.run([sys.executable, local_path], capture_output=True, text=True, encoding="utf-8")
sp_out = proc.stdout
with open(os.path.join(MY, "strict_panel_rerun.log"), "w", encoding="utf-8") as f:
    f.write(sp_out)
    if proc.stderr:
        f.write("\n[stderr]\n" + proc.stderr)
sp_json = json.load(open(os.path.join(MY, "strict_panel.json"), encoding="utf-8"))
nominal = sorted(r["S"] for r in sp_json["rows"] if r["dod_nominal"])
strict_set = sorted(r["S"] for r in sp_json["rows"] if r["dod_strict"])
check(nominal == ["S15", "S16", "S17"], "8a 名义达标仍 S15,S16,S17", ",".join(nominal))
check(strict_set == ["S17"], "8b 严格达标仍 S17", ",".join(strict_set))
check("名义达标: S15,S16,S17" in sp_out and "严格达标: S17" in sp_out,
      "8c strict_panel stdout 汇总一致", "")

# ======================================================================
# 9. 行尾
# ======================================================================
check(cov_before.count(b"\r") == 0 and cov_after.count(b"\r") == 0,
      "9a coverage 行尾 LF-only (无 CR)", f"before CR={cov_before.count(bytes([13]))} after CR={cov_after.count(bytes([13]))}")
check(panel_before.count(b"\r") == 0 and panel_after.count(b"\r") == 0,
      "9b PANEL 行尾 LF-only (无 CR)", f"before CR={panel_before.count(bytes([13]))} after CR={panel_after.count(bytes([13]))}")

# ======================================================================
# write VERIFY.txt
# ======================================================================
npass = sum(1 for ok, _, _ in results if ok)
nfail = sum(1 for ok, _, _ in results if not ok)
with open(os.path.join(MY, "VERIFY.txt"), "w", encoding="utf-8") as f:
    f.write("R16-MERGE-F1 / B1 — verification (card §4)\n")
    f.write("generated by verify.py (re-runnable)\n")
    f.write("=" * 70 + "\n")
    for ok, name, detail in results:
        f.write(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" | {detail}" if detail else "") + "\n")
    f.write("=" * 70 + "\n")
    f.write(f"TOTAL PASS={npass} FAIL={nfail}\n")
    f.write("\nSIX NUMBERS (measured):\n" + json.dumps(six, ensure_ascii=False, indent=2) + "\n")
    f.write("\nSTRICT PANEL nominal=%s strict=%s\n" % (",".join(nominal), ",".join(strict_set)))
    f.write("\nBYTES/SHA:\n")
    f.write("  coverage before %d %s\n" % (state["before"]["coverage"]["size"], state["before"]["coverage"]["sha256"]))
    f.write("  coverage after  %d %s\n" % (state["after"]["coverage"]["size"], state["after"]["coverage"]["sha256"]))
    f.write("  panel    before %d %s\n" % (state["before"]["panel"]["size"], state["before"]["panel"]["sha256"]))
    f.write("  panel    after  %d %s\n" % (state["after"]["panel"]["size"], state["after"]["panel"]["sha256"]))

print("=" * 70)
print(f"TOTAL PASS={npass} FAIL={nfail}")
print("SIX:", json.dumps(six, ensure_ascii=False))
print("nominal=", nominal, "strict=", strict_set)
