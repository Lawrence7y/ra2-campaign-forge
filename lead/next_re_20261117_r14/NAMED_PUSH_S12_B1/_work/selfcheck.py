# -*- coding: utf-8 -*-
"""产物自校验：把 REPORT.md 的 ② 表与 delta.tsv / base_rate.tsv 里声称的每一项
都回到二进制复算一遍，任何不一致即报警。"""
import csv, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

D = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
MAIN_VT, COL, TD = 0x007E3EBC, 0x007FC360, 0x00818D60
err = []

rows = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows_b1.json"),
                      encoding="utf-8"))
hint = {r["entry"]: int(r["name"].split("::")[-1].replace("vslot", "").replace("slot", "")) for r in rows}

# --- 1) REPORT ② 表逐格复算 ---
rep = open(os.path.join(D, "REPORT.md"), encoding="utf-8").read()
pat = re.compile(r"^\|\s*(\d+)\s*\|\s*([0-9A-F]{8})\s*\|\s*(007E[0-9A-F]{4})\s*\|\s*`([0-9a-f ]{11})`\s*\|\s*(\d+)\s*\|", re.M)
n = 0
for m in pat.finditer(rep):
    idx, ent, slotva, byteclaim, slotclaim = m.group(1), m.group(2), int(m.group(3), 16), m.group(4), int(m.group(5))
    n += 1
    e = int(ent, 16)
    real = " ".join("%02x" % b for b in C.va_read(slotva, 4))
    if real != byteclaim:
        err.append("ROW %s 槽 %08X 字节：报告 %r vs 实测 %r" % (ent, slotva, byteclaim, real))
    if C.u32(slotva) != e:
        err.append("ROW %s 槽 %08X 的值 %08X != entry" % (ent, slotva, C.u32(slotva) or 0))
    if (slotva - MAIN_VT) % 4 != 0 or (slotva - MAIN_VT) // 4 != slotclaim:
        err.append("ROW %s 槽号：报告 %d vs 实测 %d" % (ent, slotclaim, (slotva - MAIN_VT) // 4))
    if slotclaim != hint[ent]:
        err.append("ROW %s 槽号 %d 与线索 vslot%d 不一致" % (ent, slotclaim, hint[ent]))
print("REPORT ② 表行数复算 = %d" % n)
if n != 18:
    err.append("② 表行数 %d != 18" % n)

# --- 2) 主表 / RTTI 锚 ---
if C.u32(MAIN_VT) != 0x410260:
    err.append("主表槽0 %08X != 00410260" % (C.u32(MAIN_VT) or 0))
if C.u32(MAIN_VT - 4) != COL:
    err.append("[vt-4] %08X != COL %08X" % (C.u32(MAIN_VT - 4) or 0, COL))
if C.u32(COL + 0xC) != TD:
    err.append("[COL+0xC] %08X != TD %08X" % (C.u32(COL + 0xC) or 0, TD))
if C.read_cstr(TD + 8, 60) != ".?AVBuildingClass@@":
    err.append("TD+8 名串 %r" % C.read_cstr(TD + 8, 60))

# --- 3) delta.tsv ---
d = list(csv.reader(open(os.path.join(D, "delta.tsv"), encoding="utf-8"), delimiter="\t"))
deliver = [r[0] for r in d[1:]]
print("delta 行 =", deliver)
for r in d[1:]:
    if len(r) != 6:
        err.append("delta 列数 %d" % len(r))
    if not re.fullmatch(r"[0-9A-F]{8}", r[0]):
        err.append("delta entry 格式 %r" % r[0])
    if r[1] != "S12" or r[4] != "[已证]":
        err.append("delta 字段 %r" % (r[1], r[4]))
    if not os.path.isfile(r[5]):
        err.append("delta evidence 缺 %r" % r[5])
    if r[2] != next(x["name"] for x in rows if x["entry"] == r[0]):
        err.append("delta name 与候选表不符 %r" % r[2])
if len({r[3] for r in d[1:]}) != len(d) - 1:
    err.append("delta reason 有重复（整批共用）")
# 只该放四环齐全行
for r in d[1:]:
    ev = open(r[5], encoding="utf-8").read()
    if "四环齐全=是" not in ev:
        err.append("delta 行 %s 的证据显示四环不齐" % r[0])
# 反之，四环齐全的 EVIDENCE 必须都在 delta 里
for fn in os.listdir(os.path.join(D, "EVIDENCE")):
    ev = open(os.path.join(D, "EVIDENCE", fn), encoding="utf-8").read()
    ent = fn[len("ROW_"):-len(".txt")]
    if "四环齐全=是" in ev and ent not in deliver:
        err.append("EVIDENCE %s 四环齐全但未进 delta" % fn)

# --- 4) base_rate.tsv ---
b = list(csv.reader(open(os.path.join(D, "base_rate.tsv"), encoding="utf-8"), delimiter="\t"))
print("base_rate:", b)
if b[0] != ["batch", "rows_checked", "ring2_ok", "ring3b_ok", "ring4_ok", "all_four", "rate"]:
    err.append("base_rate 表头不符")
if b[1][0] != "S12_B1" or b[1][1] != "18":
    err.append("base_rate 行不符")
if len(deliver) != int(b[1][5]):
    err.append("all_four %s != delta 行数 %d" % (b[1][5], len(deliver)))
if abs(float(b[1][6]) - len(deliver) / 18.0) > 5e-5:
    err.append("rate %s != %d/18" % (b[1][6], len(deliver)))

# --- 5) 三处安装点 ---
for va, func in ((0x43B71F, 0x43B680), (0x43B9FA, 0x43B740), (0x43BCFD, 0x43BCF0)):
    if C.u32(va + 2) != MAIN_VT:
        err.append("安装点 %08X 立即数 %08X != 主表" % (va, C.u32(va + 2) or 0))
    if C.is_atexit_registered(func):
        err.append("安装点所在函数 %08X 被 atexit 注册 ⇒ ㉓ 陷阱" % func)
    if not C.atlas_covering(va) or C.atlas_covering(va)[0] != func:
        err.append("安装点 %08X 不在函数 %08X 内" % (va, func))

print()
if err:
    print("!! 不一致 %d 项：" % len(err))
    for e in err:
        print("   -", e)
    sys.exit(1)
print("自校验全部通过：② 18/18 槽号与槽值复算一致、RTTI 锚一致、delta/base_rate 与证据互相对齐、3 安装点非 atexit。")
