# -*- coding: utf-8 -*-
"""COMMON-FIX 自算复核脚本（只读盘面；输出文本供 RECOMPUTE.txt 摘录）。
运行：python -I recompute_commonfix.py
"""
import hashlib
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Project\ra2-campaign-forge")
ATLAS = ROOT / r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
COV = ROOT / r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
PANEL = ROOT / r"lead\next_re_20261117_r14\COVERAGE\PANEL.md"
COMMON = ROOT / r"lead\next_re_20261117_r14\R14_COMMON.md"
ORIG = ROOT / r"ra2youli\gamemd.exe"
R2 = ROOT / r"lead\next_re_20261117_r14\PATCH_D35R\work\gamemd_r2.exe"
SITES = ROOT / r"lead\next_re_20261117_r14\PATCH_D35R\EVIDENCE\sites_wired.tsv"
HASHES = ROOT / r"lead\next_re_20261117_r14\PATCH_D35R\EVIDENCE\hashes.txt"
DIAG = ROOT / r"lead\next_re_20261117_r14\PATCH_D35R\EVIDENCE\smoke_r2_diag_sites.json"
F3A = ROOT / r"lead\next_re_20261117_r14\MEASURE_F3A\F3A_CLASS.tsv"
PENDING = ROOT / r"lead\PENDING_DECISIONS.md"
OUT = []

def p(*a):
    OUT.append(" ".join(str(x) for x in a))

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()

# ============ 0. R14_COMMON 改前状态 ============
common_bytes = COMMON.read_bytes()
p("== [0] R14_COMMON.md BEFORE ==")
p("bytes_before =", len(common_bytes))
p("sha256_before =", hashlib.sha256(common_bytes).hexdigest().upper())
p("ends_with_newline =", common_bytes.endswith(b"\n"))
p("has_utf8_bom =", common_bytes.startswith(b"\xef\xbb\xbf"))

# ============ A. function_atlas.tsv 键格式 ============
p("== [A] function_atlas.tsv entry 列键格式 ==")
atlas_lines = ATLAS.read_text(encoding="utf-8-sig").splitlines()
atlas_header, atlas_rows = atlas_lines[0], [r for r in atlas_lines[1:] if r.strip()]
p("atlas_header =", atlas_header)
p("atlas data rows =", len(atlas_rows))
atlas_ent = [r.split("\t")[0] for r in atlas_rows]
p("atlas entry 含小写 a-f 的行数 =", sum(1 for e in atlas_ent if re.search(r"[a-f]", e)))
p("atlas entry 含大写 A-F 的行数 =", sum(1 for e in atlas_ent if re.search(r"[A-F]", e)))
p("atlas entry 全部匹配 ^[0-9a-f]{8}$ =",
  all(re.fullmatch(r"[0-9a-f]{8}", e) for e in atlas_ent))
atlas_set = set(atlas_ent)
atlas_set_lower = {e.lower() for e in atlas_ent}

# ============ B. coverage.tsv 键格式 ============
p("== [B] coverage.tsv entry 列键格式 ==")
cov_lines = COV.read_text(encoding="utf-8-sig").splitlines()
cov_header, cov_rows = cov_lines[0], [r for r in cov_lines[1:] if r.strip()]
p("cov_header =", cov_header)
p("cov data rows =", len(cov_rows))
cols = [r.split("\t") for r in cov_rows]
p("col count distribution =", dict(Counter(len(c) for c in cols)))
ent = [c[0] for c in cols]
sub = [c[1] for c in cols]
name = [c[2] for c in cols]
sem = [c[3] for c in cols]
grade = [c[4] for c in cols]
evp = [c[5] for c in cols]
p("cov entry 含小写 a-f 的行数 =", sum(1 for e in ent if re.search(r"[a-f]", e)))
p("cov entry 含大写 A-F 的行数 =", sum(1 for e in ent if re.search(r"[A-F]", e)))
p("cov entry 全部匹配 ^[0-9A-F]{8}$ =",
  all(re.fullmatch(r"[0-9A-F]{8}", e) for e in ent))

# ============ C. S09 交集：未归一 vs 归一 ============
p("== [C] S09 交集（未归一大小写 vs 归一） ==")
s09_idx = [i for i in range(len(cols)) if sub[i] == "S09"]
s09_ent = [ent[i] for i in s09_idx]
p("S09 rows in coverage =", len(s09_idx))
naive = sum(1 for e in s09_ent if e in atlas_set)
norm = sum(1 for e in s09_ent if e.lower() in atlas_set_lower)
p("S09 naive intersection (未归一, 大写∩小写) =", naive)
p("S09 normalized intersection (归一后) =", norm)
p("S09 naive 命中行中纯数字(不含字母)的 entry 数 =",
  sum(1 for e in s09_ent if e in atlas_set and not re.search(r"[A-Fa-f]", e)))

# ============ D. 英文措辞族（第三措辞族） ============
p("== [D] 英文措辞族 (?i)unproven|unverified|not proven ==")

def in_atlas(i):
    """atlas 归属：两侧键统一小写后比对（㉚ 判据的正面实现）。"""
    return ent[i].lower() in atlas_set_lower

rx = re.compile(r"(?i)unproven|unverified|not proven")
eng = [i for i in range(len(cols)) if rx.search(sem[i])]
p("全表命中行数 =", len(eng))
p("subsystem 分布 =", dict(Counter(sub[i] for i in eng)))
p("grade 分布 =", dict(Counter(grade[i] for i in eng)))
p("在 atlas 内的行数（归一后比对） =", sum(1 for i in eng if in_atlas(i)))
p("全部含中文子串 [未证] 的行数 =", sum(1 for i in eng if "[未证]" in sem[i]))
fam_re = re.compile(r"^Save_VectorBlock_(\d{2})$")
fam = [name[i] for i in eng if fam_re.match(name[i])]
p("name 为 Save_VectorBlock_NN 形态的行数 =", len(fam))
nums = sorted(int(fam_re.match(n).group(1)) for n in fam)
p("族编号 =", nums)
p("编号集合 == {1..35}\\{17} =", nums == [n for n in range(1, 36) if n != 17])
p("语义尾缀 == 'class name unproven (arg .bss obj)' 全部成立 =",
  all(sem[i].endswith("class name unproven (arg .bss obj)") for i in eng))
p("evidence_path 分布 =", dict(Counter(evp[i] for i in eng)))
p("样例行（第 1 行）:")
i0 = eng[0]
p("  entry=%s sub=%s name=%s grade=%s" % (ent[i0], sub[i0], name[i0], grade[i0]))
p("  sem=%s" % sem[i0])
p("  evidence=%s" % evp[i0])

# ============ E. N / W / S（strict_panel 口径）与 S17 ============
p("== [E] N / W / S（atlas ∩ [已证] ∖ 含[未证]子串）与 S17 strict ==")
provd = [i for i in range(len(cols)) if grade[i] == "[已证]" and in_atlas(i)]
N = len(provd)
W_idx = [i for i in provd if "[未证]" in sem[i]]
W = len(W_idx)
S = N - W
p("N (atlas ∩ [已证], 归一比对) =", N)
p("W (N 中语义含子串 [未证]) =", W)
p("S = N - W =", S)
p("全表 grade=[已证] 总数（含 atlas 外）=",
  sum(1 for i in range(len(cols)) if grade[i] == "[已证]"))
p("atlas 外的 [已证] 行数 =",
  sum(1 for i in range(len(cols)) if grade[i] == "[已证]" and not in_atlas(i)))
p("全表 grade 三分级 =", dict(Counter(grade[i] for i in range(len(cols)))))
s17_all = [i for i in range(len(cols)) if sub[i] == "S17" and in_atlas(i)]
s17_prov = [i for i in s17_all if grade[i] == "[已证]"]
s17_strict = [i for i in s17_prov if "[未证]" not in sem[i]]
s17_noeng = [i for i in s17_strict if not rx.search(sem[i])]
p("S17 atlas_n（归一比对） =", len(s17_all))
p("S17 [已证]∩atlas =", len(s17_prov))
p("S17 strict 计入英文族 =", len(s17_strict))
p("S17 strict 剔除英文族 =", len(s17_noeng))
p("门槛 ceil(0.5*102) =", math.ceil(0.5 * 102))
# 措辞 A 复核（㉗ 的第一族；判据 8 口径 = grade [已证] 且语义含该字样）
famA = [i for i in range(len(cols)) if "（槽语义未证）" in sem[i]]
famA_prov = [i for i in famA if grade[i] == "[已证]"]
p("措辞 A「（槽语义未证）」全表行数 =", len(famA))
p("措辞 A ∩ grade=[已证] 行数 =", len(famA_prov),
  " subsystem 分布 =", dict(Counter(sub[i] for i in famA_prov)))

# ============ F. §8.6 界向更正的两个反例行 ============
p("== [F] 反例行 004AB9B0 / 00522340 ==")
for addr in ("004AB9B0", "00522340"):
    idx = [i for i in range(len(cols)) if ent[i].upper() == addr]
    p("---", addr, "---")
    for i in idx:
        p("  coverage 行号(1-based 含表头) =", i + 2,
          " sub=%s name=%s grade=%s atlas=%s" % (sub[i], name[i], grade[i], in_atlas(i)))
        p("  sem =", sem[i])
        p("  sem 含 [未证] 子串 =", "[未证]" in sem[i],
          "  sem 含英文族措辞 =", bool(rx.search(sem[i])))
        p("  evidence =", evp[i])
p("F3A_CLASS.tsv 中 00522340 行:")
if F3A.exists():
    f3a = F3A.read_text(encoding="utf-8-sig").splitlines()
    hit = [r for r in f3a if "00522340" in r]
    for r in hit:
        p("  ", r)
    p("  F3A_CLASS.tsv 总行数 =", len(f3a))
else:
    p("  (文件不存在:", str(F3A), ")")
p("PENDING_DECISIONS.md D-44 条:")
pend = PENDING.read_text(encoding="utf-8-sig")
m = re.search(r"^#+\s*D-44.*$", pend, re.M)
if m:
    seg = pend[m.start():m.start() + 900]
    for ln in seg.splitlines()[:12]:
        p("  ", ln)
else:
    i44 = pend.find("D-44")
    for ln in pend[max(0, i44 - 200):i44 + 700].splitlines()[:14]:
        p("  ", ln)

# PANEL L134 / L138 原文摘录
p("PANEL.md L134 / L138 / L139 原文:")
plines = PANEL.read_text(encoding="utf-8-sig").splitlines()
for ln_no in (134, 138, 139):
    p("  L%d: %s" % (ln_no, plines[ln_no - 1]))

# ============ G. PATCH-D35R 可核项 ============
p("== [G] PATCH-D35R 可核项 ==")
p("orig gamemd.exe SHA-256 =", sha256_file(ORIG))
p("orig 期望值              = 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476")
p("orig SHA 未变 =", sha256_file(ORIG) == "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476")
orig_b = ORIG.read_bytes()
r2_b = R2.read_bytes()
p("orig size =", len(orig_b), " r2 size =", len(r2_b), " 长度相同 =", len(orig_b) == len(r2_b))
diff = [i for i in range(min(len(orig_b), len(r2_b))) if orig_b[i] != r2_b[i]]
p("全文件差异字节数 =", len(diff))
site_rows = [r for r in SITES.read_text(encoding="utf-8-sig").splitlines()[1:] if r.strip()]
p("sites_wired.tsv 数据行数 =", len(site_rows))
site_offs = []
for r in site_rows:
    f = r.split("\t")
    off = int(f[1], 16)
    site_offs.append((off, off + 5))
p("站点文件偏移区间 =", ["0x%X..0x%X" % (a, b) for a, b in site_offs])
cave_lo, cave_hi = 0x3DF781, 0x3DF7C0
in_cave = [i for i in diff if cave_lo <= i < cave_hi]
in_site = [i for i in diff if any(a <= i < b for a, b in site_offs)]
outside = [i for i in diff if i not in set(in_cave) and not any(a <= i < b for a, b in site_offs)]
p("洞 [0x3DF781,0x3DF7C0) 内差异数 =", len(in_cave))
p("8 站点 5B 区间内差异数 =", len(in_site))
p("越界差异数 =", len(outside))
p("允许集合并集大小（洞 63B ∪ 8×站点 5B）=",
  len(set(range(cave_lo, cave_hi)) | {x for a, b in site_offs for x in range(a, b)}))
p("执行器自报 hashes.txt 关键行:")
for ln in HASHES.read_text(encoding="utf-8-sig").splitlines():
    if ln.split("=")[0] in ("total_diff_bytes", "cave_diff_bytes", "site_diff_bytes",
                            "outside_allowed_set_diff_count", "orig_gamemd_sha256",
                            "r2_copy_sha256"):
        p("  ", ln)
p("smoke_r2_diag_sites.json（桩执行只读采样证据）:")
p("  ", json.dumps(json.loads(DIAG.read_text(encoding="utf-8-sig")), ensure_ascii=False))

# ============ 汇总 ============
p("== [Z] 与卡面/BOUND_DIR 对照 ==")
p("卡面 12,916/11,160/0/198/1,051 → 上面 [A][C]")
p("卡面 34/全S17/全已证/全atlas/55/21/51 → 上面 [D][E]")
p("卡面 1,138(PANEL 行文)/1,159(盘上重算) → [E] S 值；PANEL L129-131 行文 1,455/317/1,138")
p("卡面 8 站点/73=49+24/越界0/1处桩证据/崩0/原SHA未变 → [G]")

out_path = Path(__file__).with_name("recompute_out.txt")
out_path.write_text("\n".join(OUT), encoding="utf-8")
print("\n".join(OUT))
print("\n[saved]", out_path)
