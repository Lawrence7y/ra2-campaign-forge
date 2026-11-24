#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R92-T1-REJUDGE / Q5② : 盲区修复的正控。

拿 §2.46 点名的两类样本各一例，证明
  旧法 判不出「地址」/「占比」，新法判得出。

旧法 = R44 judge_q4_v2.py 的两条具体门槛：
  (i)  地址正则 0x[0-9A-Fa-f]{6,8}            （judge_q4_v2.py:13）
  (ii) 占比分母 = 行，且只读前 8 KiB          （judge_q4_v2.py:33-45）

样本 A（盲区A）：含 entry=00524D70 的 ROW_*.txt
    next_re_20261117_r14/NAMED_PUSH_S05_B2/EVIDENCE/ROW_00524D70.txt
样本 B（盲区B）：§2.46 二节(2.2) 点名的 q3_cfg.json（846 KB 压一行）
    next_re_20261117_r14/S05_KPROVED3/_audit/EVIDENCE/q3_cfg.json

说明（重要，防夸大）：ROW_00524D70.txt 里 *确实有* 少量带 0x 的地址
（正文引用了 0x00524DAA / 0x00524DAD 等），所以「旧法命中 0」的说法不成立。
盲区A 的真实形态是：**文件标题行与环①的 entry= 行这类「标识本行对象」的写法不带 0x**，
且大量「入口相对偏移 + 指令字节」的行整行没有任何 0x 地址。
下面按「行级可见性」和「件级占比」两个层级分别量化。
"""
import csv, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
OUT = os.path.dirname(os.path.abspath(__file__))
LEAD = r"D:\Project\ra2-campaign-forge\lead"

OLD_ADDR = re.compile(r"0x[0-9A-Fa-f]{6,8}")            # R44 原样
NEW_ADDR_LINE = re.compile(r"(?<![0-9A-Za-z_])[0-9A-F]{6,8}(?![0-9A-Za-z_])")   # 行级粗口径（含裸大写）
OLD_CAP = 8192

import importlib.util
spec = importlib.util.spec_from_file_location("q2", os.path.join(OUT, "q2_rejudge.py"))
q2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q2)


def read(rel):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    with open(p, "rb") as f:
        b = f.read()
    return b.decode("utf-8", errors="replace"), os.path.getsize(p)


A = "next_re_20261117_r14/NAMED_PUSH_S05_B2/EVIDENCE/ROW_00524D70.txt"
B = "next_re_20261117_r14/S05_KPROVED3/_audit/EVIDENCE/q3_cfg.json"

L = ["=== Q5② · 盲区修复正控 ===", ""]

# ================= 样本 A =================
L.append("---- 样本 A（盲区A：地址不带 0x） ----")
L.append(f"file : {A}")
ta, sz = read(A)
lines = [x for x in ta.splitlines() if x.strip()]
old_hit_lines = [x for x in lines if OLD_ADDR.search(x)]
new_hit_lines = [x for x in lines if OLD_ADDR.search(x) or NEW_ADDR_LINE.search(x)]
L.append(f"size : {sz} B，非空行 {len(lines)}")
L.append("")
L.append(f"[A-1 行级] 旧法地址正则命中行：{len(old_hit_lines)} 行 / {len(lines)} 行"
         f" = {len(old_hit_lines)/len(lines):.1%}")
L.append(f"[A-1 行级] 新法（0x + 裸十六进制）命中行：{len(new_hit_lines)} 行 / {len(lines)} 行"
         f" = {len(new_hit_lines)/len(lines):.1%}")
L.append("      旧法完全看不见、新法看得见的行（前 8 条）：")
seen = 0
for x in lines:
    if not OLD_ADDR.search(x) and NEW_ADDR_LINE.search(x):
        L.append("        " + x.strip()[:96])
        seen += 1
        if seen >= 8:
            break
L.append("")
L.append("[A-2 件级] 两条判据下的「行首 VA 占比」门槛（>=60%）是否过闸：")
old_ratio = len(old_hit_lines) / len(lines)
new_ratio = len(new_hit_lines) / len(lines)
L.append(f"      旧法占比 {old_ratio:.1%} -> {'过闸' if old_ratio>=0.6 else '不过闸（判据看不见这个文件的内容）'}")
L.append(f"      新法占比 {new_ratio:.1%} -> {'过闸' if new_ratio>=0.6 else '不过闸'}")
L.append("")
L.append("[A-3 防误判] 同文件里形状像十六进制、但不应算地址的串（若被收就是假阳性）：")
fp = []
for m in NEW_ADDR_LINE.finditer(ta):
    tok = m.group(0)
    if not q2.bare_is_addr(tok, ta[:m.start()]):
        fp.append(tok)
L.append(f"      被新法闸门拒掉的裸串：{len(fp)} 个 -> {sorted(set(fp))[:12]}")
L.append("      拒收理由（三道闸）：纯数字不在 .text VA 区间 0x00400000..0x00B00000 / "
         "混合大小写且非 hex 语境 / 无可识别的地址锚（entry= / call / @ / 偏移…）")
L.append("")

# ================= 样本 B =================
L.append("---- 样本 B（盲区B：单行大 JSON） ----")
L.append(f"file : {B}")
tb, szb = read(B)
L.append(f"size : {szb} B，整文件换行数 {tb.count(chr(10))}")
L.append("")
old_line_n = 1
L.append(f"[B-1 分母] 旧法按「行」切：分母 = {old_line_n}（§2.46 二节(2.2) 的原话：分母是 1）")
L.append(f"          旧法只读前 {OLD_CAP} B —— 占本件 {OLD_CAP/szb:.1%}，"
         f"即 {szb-OLD_CAP} B（{(szb-OLD_CAP)/szb:.1%}）从未被读过")
segs = q2.segments(tb)
addr_segs = sum(1 for s in segs if q2.find_addrs(s) or q2.find_dec_pairs(s))
L.append(f"[B-1 分母] 新法按内容分隔符（}} {{  / \\n / ; / \",\"）切：分母 = {len(segs)} 段")
L.append("")
L.append(f"[B-2 占比] 旧法：行内地址占比 = {1.0 if OLD_ADDR.search(tb[:OLD_CAP]) else 0.0:.1%}"
         f"（分母 1，门槛恒失效）")
L.append(f"          新法：含地址的段 {addr_segs} / {len(segs)} = {addr_segs/len(segs):.1%}；"
         f"地址命中总数 {sum(len(q2.find_addrs(s))+q2.find_dec_pairs(s) for s in segs)}")
L.append("")
L.append("[B-3 内容性质] 该件是 8 个函数的完整 CFG（entry/lo/hi/nins + 逐指令 a/hex/m/o/tgt），")
L.append("      每条指令都带「地址 + 指令字节 + 助记符」⇒ §2.49 问1「地址↔值同段并存、可回原址复核」成立。")
L.append("")

# ================= A 类全集的量化 =================
L.append("---- 盲区A 在 1,242 件全集的规模（同一条行级口径） ----")
rows = list(csv.DictReader(open(os.path.join(OUT, "rejudge1242.tsv"), encoding="utf-8"), delimiter="\t"))
tot = fail_old = pass_new = 0
for r in rows:
    p = os.path.join(LEAD, r["rel"].replace("/", os.sep))
    try:
        t = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    ls = [x for x in t.splitlines() if x.strip()]
    if not ls:
        continue
    tot += 1
    o = sum(1 for x in ls if OLD_ADDR.search(x)) / len(ls)
    n = sum(1 for x in ls if OLD_ADDR.search(x) or NEW_ADDR_LINE.search(x)) / len(ls)
    if o < 0.6:
        fail_old += 1
        if n >= 0.6:
            pass_new += 1
L.append(f"可读件数 {tot}；按旧法行级地址占比 <60%（=被旧判据判为「看不见地址」）的 {fail_old} 件；")
L.append(f"其中补上裸十六进制后占比 >=60% 的 {pass_new} 件 ⇒ 这 {pass_new} 件是旧法「地址识别」盲区直接误测的。")
L.append("")

# ================= 裁决落点 =================
rowsd = {r["rel"]: r for r in rows}
L.append("---- 两例在新旧两套判据下的裁决 ----")
for rel, tag in ((A, "ROW 样本"), (B, "单行JSON样本")):
    r = rowsd[rel]
    L.append(f"  {tag}：旧 = {r['old_verdict']}（R44 basis={r['old_basis']}）"
             f"  ->  新 = {r['new_verdict']}（changed={r['changed']}）")
L.append("")
L.append("结论：")
L.append(f"  A：旧法只看见 {len(old_hit_lines)}/{len(lines)} 行的地址（{old_ratio:.1%}），"
         f"看不到 entry=00524D70 与全部「相对偏移+字节」行；新法 {len(new_hit_lines)}/{len(lines)} 行"
         f"（{new_ratio:.1%}）。")
L.append(f"  B：旧法分母 1、只读 {OLD_CAP/1024:.0f} KiB/{szb/1024:.0f} KiB；"
         f"新法分母 {len(segs)} 段、读全件，含地址段占比 {addr_segs/len(segs):.1%}。")

with open(os.path.join(OUT, "q5_posctrl2.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")
print("\n".join(L))
