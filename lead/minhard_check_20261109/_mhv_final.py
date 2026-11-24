# -*- coding: utf-8 -*-
# 独立复核 ⑦ 收尾：被引输出行抽查 / 写域件数 / 只读域 mtime / 绑定行格式
import os, re, hashlib, time, datetime
BASE = os.path.normpath(os.path.abspath("D:/Project/ra2-campaign-forge"))
W = os.path.join(BASE, "lead", "minhard_check_20261109")

def P(rel):
    return os.path.normpath(os.path.join(BASE, *rel.split("/")))
def L(rel):
    with open(P(rel), "r", encoding="utf-8", newline="") as f:
        return f.read().split("\n")

print("== A. 撰写人关键引证抽查（逐字取输出文件的指定行） ==")
CHECKS = [
 ("lead/minhard_check_20261109/_mh_blocks_out.txt", 47, 58, "全仓逐字同文计数 9 命中"),
 ("lead/minhard_check_20261109/_mh_intersect_out.txt", 16, 21, "13 件 IN_BLOCK 判定"),
 ("lead/minhard_check_20261109/_mh_intersect_out.txt", 35, 35, "SLOW_WINDOW:127"),
 ("lead/minhard_check_20261109/_mh_verify2_out.txt", 1, 12, "§607 身份"),
 ("lead/minhard_check_20261109/_mh_verify3_out.txt", 67, 90, "合订本 §607 wrapper"),
 ("lead/minhard_check_20261109/_mh_verify4_out.txt", 131, 134, "ATTRIBUTION:136 ≡ _sa:90"),
 ("lead/minhard_check_20261109/_mh_fp_verify_out.txt", 1, 13, "11 件指纹 MATCH"),
]
for rel, a, b, label in CHECKS:
    ls = L(rel)
    print(f"-- {label}: {rel}:{a}-{b}")
    for i in range(a, min(b, len(ls)) + 1):
        print(f"   [{i}] {ls[i-1][:200]}")

print("\n== B. 写域 _mh_ 件数（核实「21 件」申报）==")
allf = sorted(os.listdir(W))
mh = [f for f in allf if f.startswith("_mh_")]
mhv = [f for f in allf if f.startswith("_mhv_")]
print("  _mh_* 件数 =", len(mh))
print("  _mhv_* 件数 =", len(mhv))
print("  _mh_* 清单 =", mh)
print("  写域总件数 =", len(allf))

print("\n== C. 只读域关键件 mtime（本会话无写入应早于本会话）==")
RO = [
 "lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md",
 "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
 "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
 "lead/ledger_appendix_20261108/_lad_tpl.md",
 "lead/s604_attribution_20261108/S604_ATTRIBUTION.md",
 "lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",
 "lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md",
 "lead/ledger_bound_20261109/_lb2_TEMPLATE.md",
 "lead/GOAL_THREE_TARGETS_20261018.md",
 "lead/PENDING_DECISIONS.md",
]
for rel in RO:
    st = os.stat(P(rel))
    print(f"  {rel}  mtime={datetime.datetime.fromtimestamp(st.st_mtime).isoformat()}  bytes={st.st_size}")

print("\n== D. 被核回件绑定行格式（必须无路径/括号/星号/反引号/空格插入）==")
rep = L("lead/minhard_check_20261109/_mh_MINHARD_CHECK.md")
pat = re.compile(r"^被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)$")
for i, s in enumerate(rep, 1):
    if "被核对象 SHA256" in s:
        m = pat.match(s)
        print(f"  :{i} {s!r}")
        print(f"  strict_format_match = {bool(m)}")
        if m:
            print(f"  sha = {m.group(1)}  bytes = {m.group(2)}")
print("  被核对象实测：", end="")
b = open(P("lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md"), "rb").read()
print(f"sha = {hashlib.sha256(b).hexdigest()}  bytes = {len(b)}")

print("\n== E. 撰写人是否把建议写成已执行（扫『已改/已入账/已执行』措辞）==")
for i, s in enumerate(rep, 1):
    if re.search(r"已改|已入账|已执行|已追加|本会话.*改了", s) and ("未改" not in s and "未入账" not in s and "未执行" not in s and "未追加" not in s):
        print(f"  :{i} {s[:180]}")
print("DONE")
