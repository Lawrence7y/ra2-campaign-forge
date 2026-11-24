# -*- coding: utf-8 -*-
"""W4 只读探针（一次性）：0x00A8ED50 字段规格卡独立二进制复验。
零真机、零活进程内存、零采样实现；只从磁盘读 ra2youli/gamemd.exe 原始字节并反汇编。
用法：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_line_20261105/W4_FIELD_SPEC/_probe_00A8ED50.py
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("SHA256", eng.sha)
print("IB", hex(eng.IB))
print("COVERAGE", eng.coverage)
print("SECTIONS", [(n, hex(a), hex(v), hex(rp), hex(rs)) for n, a, v, rp, rs in eng.SEC])

T = 0x00A8ED50
BASE = 0x00A8ED40
ITEMS = 0x00A8ED44
CAP = 0x00A8ED48
GS = 0x00A8ED54

print("\n=== 1) 目标 VA 及邻槽字节 / BSS 判定 ===")
for va in (BASE, ITEMS, CAP, T, GS):
    print("SLOT", hex(va), "rd4", eng.rd(va, 4).hex(), "fo", eng.fo(va), "u32", hex(eng.u32(va)))
o = eng.fo(T)
print("fo(T)", o, "rawLE_in_text", eng.raw.find(bytes.fromhex("50eda800")))

print("\n=== 2) disp_hits 全量普查 ===")
for name, va in [("T=Count", T), ("BASE", BASE), ("ITEMS", ITEMS), ("CAP", CAP), ("GS", GS)]:
    h = eng.disp_hits(va)
    ws = [x for x in h if x[1] == "W"]
    rs = [x for x in h if x[1] == "R"]
    print("\nHITS", name, hex(va), "total", len(h), "W", len(ws), "R", len(rs))
    print("  W:", [(hex(a), m, o) for a, _, m, o in ws])
    print("  R:", [(hex(a), m, o) for a, _, m, o in rs])

print("\n=== 3) 原始 LE 字节全镜像计数（含 .data 中的指针/常量） ===")
needle = bytes.fromhex("50eda800")
pos, locs = 0, []
while True:
    j = eng.raw.find(needle, pos)
    if j < 0:
        break
    locs.append(j)
    pos = j + 1
print("RAW_BYTES_50EDA800 count", len(locs), "offsets", [hex(x) for x in locs])
# 换算为 VA（若在节内）
for j in locs:
    hit = None
    for n, a, v, rp, rs in eng.SEC:
        if rp <= j < rp + rs:
            hit = (n, a + (j - rp))
    print("  off", hex(j), "->", (hit[0], hex(hit[1])) if hit else "outside_raw")

print("\n=== 4) Bullet 容器对象基址绝对引用（找构造/初始化） ===")
n2 = bytes.fromhex("40eda800")
pos, l2 = 0, []
while True:
    j = eng.raw.find(n2, pos)
    if j < 0:
        break
    l2.append(j)
    pos = j + 1
print("RAW_BYTES_40EDA800 count", len(l2), "offsets", [hex(x) for x in l2])
for j in l2:
    hit = None
    for n, a, v, rp, rs in eng.SEC:
        if rp <= j < rp + rs:
            hit = (n, a + (j - rp))
    print("  off", hex(j), "->", (hit[0], hex(hit[1])) if hit else "outside_raw")

print("\n=== 5) 关键区间反汇编 ===")
RANGES = [
    ("UpdateLoop_Anim+Bullet", 0x55B8E0, 0x160),
    ("BulletClass::Update_head", 0x4666E0, 0x60),
    ("Bullet_Add", 0x466400, 0xC0),
    ("Bullet_Del", 0x466600, 0x70),
    ("BulletClass_vtablesetup", 0x466410, 0xA0),
    ("Bullet_ctor_align", 0x466468, 0x60),
]
for nm, a, n in RANGES:
    print("\n---", nm, hex(a), "+", hex(n), "---")
    for va, b, m, op in eng.disasm(a, n):
        print(" ", hex(va), b, m, op)

print("\n=== 6) RTTI / vtable 链核实（Bullet 身份） ===")
def u(v):
    return eng.u32(v)
col = u(0x7E46E0)
td = u(col + 12)
print("COL", hex(col), "TD", hex(td), "name", eng.rd(td + 8, 48).split(b"\0")[0])
print("VFT_0x7E4740_slot_0x5C", hex(u(0x7E4740)))
print("vtable+0x5C raw", eng.rd(0x7E4740, 4).hex())

print("\n=== 7) 对象 +0x98 活跃标志：全 .text [reg+0x98] 普查计数 ===")
f = eng.disp_hits_field(0x98)
print("FIELD_0x98 total", len(f), "W", len([x for x in f if x[1] == "W"]), "R", len([x for x in f if x[1] == "R"]))
# 仅列 mov al/byte ptr [reg+0x98] 的读点样本（前 40）
samp = [(hex(a), w, m, o) for a, w, m, o in f if w == "R" and "0x98" in o][:40]
print("sample_R_0x98", samp)

print("\n=== 8) rel32 直接调用者枚举（进 B 函数体纪律） ===")
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
text_lo = eng.TLO
text_hi = eng.THI
def rel32_callers(target):
    out = []
    for j in range(len(tb) - 4):
        if tb[j] == 0xE8:
            d = int.from_bytes(tb[j + 1:j + 5], "little", signed=True)
            if text_lo + j + 5 + d == target:
                out.append(text_lo + j)
    return out
for t in (0x4666E0, 0x466400, 0x466600, 0x55B8F0, 0x55B93F, 0x7C978A):
    c = rel32_callers(t)
    print("CALLERS", hex(t), "n", len(c), "list", [hex(x) for x in c[:30]])

print("\n=== 9) 帧号 VA 邻域（生命周期/开局） ===")
for a, n in [(0x684660, 0x60), (0x55DE60, 0x30)]:
    print("--- disasm", hex(a), "+", hex(n), "---")
    for va, b, m, op in eng.disasm(a, n):
        print(" ", hex(va), b, m, op)

print("\nDONE")
