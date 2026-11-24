# -*- coding: utf-8 -*-
"""W8·F6 探针：真实视口坐标 / 当前可见世界矩形（纯静态，零真机，零注入）。

只读 gamemd.exe（ra2tool.Engine，磁盘镜像）；唯一写域 = 本目录的 _w8_f6_out.txt。
运行：python -I -X utf8 _w8_f6.py
覆盖：
  [A] 自证：SHA256 / 字节数 / ImageBase / 全 .text 重同步解码覆盖率
  [B] F6-1: 0x432A35 所在函数边界 + 调用者 + IAT 判名（Bink 电影播放器，非战术绘制链）
  [C] F6-2: DSurface+0x1C 类型定谳（RTTI + 构造器 CreateSurface 出参 + BinkDDSurfaceType 消费）
  [D] F6-3: 可见世界矩形：TacticalClass(0x887324) +0xB0/0xB4 像素原点与 +0xD80/D84/D88/D8C 格矩形
            （写者 0x6D8B30、逐帧驱动 MainLogicFrame 0x55D847、读方 IsVisible 0x6D2140 / 0x6D8AE0）
"""
import sys, time, bisect

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine  # noqa: E402

OUT = r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W8_STATIC_LOCATE\_w8_f6_out.txt"
_buf = []
def P(*a):
    line = " ".join(str(x) for x in a)
    _buf.append(line)
    print(line)

t0 = time.time()
eng = Engine()
s = eng.stream
by = eng.by()
addrs = sorted(by.keys())
def idx(a): return bisect.bisect_left(addrs, a)
def dump(lo, hi):
    for ins in s:
        if lo <= ins.address < hi:
            P("%08X  %-22s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
def callers(f):
    return [ins.address for ins in s if ins.mnemonic == "call"
            and ins.operands and ins.operands[0].type == 2 and ins.operands[0].imm == f]
def cstr(va, n=64):
    b = eng.rd(va, n)
    return b.split(b"\0")[0].decode("latin1", "replace")

# ---------- [A] 自证 ----------
P("=" * 78)
P("[A] 自证")
P("SHA256", eng.sha)
P("SIZE_BYTES", len(eng.raw))
P("IMAGEBASE 0x%X" % eng.IB)
cov, nins, res = eng.coverage
P("COVERAGE pct=%s insns=%d resync=%d .text_size=%d" % (cov, nins, res, eng.TSZ))

# ---------- [B] F6-1 ----------
P("=" * 78)
P("[B] F6-1: 函数边界 0x432750..0x432A50（含 0x432A35），IAT 判名，调用者")
P("-- head/tail")
dump(0x432750, 0x432768)
dump(0x432A35, 0x432A62)
P("-- 0x432A16..0x432A35（矩形写入现场：4 个 dword，非 8 个）")
dump(0x432A16, 0x432A35)
for slot in (0x7E14C4, 0x7E11BC, 0x7E11C0, 0x7E11E0, 0x7E1590, 0x7E1594,
             0x7E1598, 0x7E159C, 0x7E15A0, 0x7E15A4, 0x7E15A8):
    P("IAT 0x%X -> %s" % (slot, eng.resolve_iat(slot)))
P("str 0x818B2C:", repr(cstr(0x818B2C)))
P("str 0x818B40:", repr(cstr(0x818B40, 32)))
P("DIRECT CALLERS of 0x432750:", [hex(c) for c in callers(0x432750)])
P("-- wrapper ctor 0x4326C0")
dump(0x4326C0, 0x4326F4)
P("callers of 0x4326C0:", [hex(c) for c in callers(0x4326C0)])
P("callers of 0x432700:", [hex(c) for c in callers(0x432700)])

# ---------- [C] F6-2 ----------
P("=" * 78)
P("[C] F6-2: DSurface+0x1C 类型")
col = eng.u32(0x7E85D4 - 4)
td = eng.u32(col + 0x0C) if col else 0
P("vtable 0x7E85D4 COL=0x%X  TD name=%r" % (col, cstr(td + 8) if td else "?"))
vt = [ (hex(ins.address), ins.mnemonic, ins.op_str) for ins in s if "0x7e85d4" in ins.op_str ]
P("DSurface vtable write sites: %d -> %s" % (len(vt), [v[0] for v in vt]))
P("-- DSurface ctor 0x4BA5A0 关键行")
for lo, hi in ((0x4BA5A0, 0x4BA5D8), (0x4BA645, 0x4BA69E)):
    dump(lo, hi)
P("-- Bink 消费方 0x432A35..0x432A44")
dump(0x432A35, 0x432A48)
P("IAT 0x7E15A8 ->", eng.resolve_iat(0x7E15A8))

# ---------- [D] F6-3 ----------
P("=" * 78)
P("[D] F6-3: 可见世界矩形")
P("-- TacticalClass vtable 0x7F4348 槽位")
for i, off in ((23, 0x5C), (5, 0x14), (8, 0x20)):
    P("vtable[%d] (+0x%X) = 0x%08X" % (i, off, eng.u32(0x7F4348 + 4 * i)))
P("-- ctor 0x6D1C20 关键行（零初始化 +0xB0/0xB4/0xD64..0xD7C，vtable，[A8]=-1）")
dump(0x6D1C20, 0x6D1C6A)
dump(0x6D1CAA, 0x6D1D00)
dump(0x6D1D54, 0x6D1D60)
dump(0x6D1E1E, 0x6D1E2A)
P("-- 实例创建/销毁点（new 0xE18 + ctor 调用者 + 写 0x887324 的 W 点）")
P("callers of ctor 0x6D1C20:", [hex(c) for c in callers(0x6D1C20)])
ih = eng.disp_hits(0x887324)
P("REFS 0x887324 total=%d W=%d" % (len(hs) if False else len(ih), len([h for h in ih if h[1] == 'W'])))
for va, rw, mn, ops in ih:
    if rw == "W":
        P("  %08X %s %s %s" % (va, rw, mn, ops))
P("-- 逐帧驱动：MainLogicFrame 0x55D847")
dump(0x55D83F, 0x55D84C)
P("-- 视口像素原点写者 0x6D8B30 关键行")
dump(0x6D8B30, 0x6D8B98)
dump(0x6D8BF0, 0x6D8C50)
P("-- 读方1：TacticalClass::IsVisible 0x6D2140 关键行")
dump(0x6D2140, 0x6D2146)
dump(0x6D2202, 0x6D2272)
P("direct callers of IsVisible 0x6D2140:", len(callers(0x6D2140)))
P("-- 读方2：格矩形判定 0x6D8AE0（CellInViewport 形态）")
dump(0x6D8AE0, 0x6D8B26)
P("-- 滚动当前/目标 [T+0xD64/0xD68]/[T+0xD74/0xD78] 的 Tactical 族写点")
for off, nm in ((0xD64, "+0xD64 curX"), (0xD68, "+0xD68 curY"),
                (0xD74, "+0xD74 tgtX"), (0xD78, "+0xD78 tgtY"),
                (0xB0, "+0xB0 viewX"), (0xB4, "+0xB4 viewY")):
    hs2 = [h for h in eng.disp_hits_field(off) if h[1] == "W"]
    tac = [h for h in hs2 if 0x6D1C00 <= h[0] < 0x6DC500]
    P("W sites %s: total=%d  Tactical族(0x6D1C00..0x6DC500)=%d -> %s"
      % (nm, len(hs2), len(tac), [hex(h[0]) for h in tac]))
P("-- 屏幕宽高全局 0xB0CE30/0xB0CE34 写点")
for g in (0xB0CE30, 0xB0CE34):
    for va, rw, mn, ops in eng.disp_hits(g):
        if rw == "W":
            P("  0x%08X %s %s %s" % (va, rw, mn, ops))
P("-- 屏幕矩形源 0x886FA0（W 点）")
for va, rw, mn, ops in eng.disp_hits(0x886FA0):
    if rw == "W":
        P("  0x%08X %s %s %s" % (va, rw, mn, ops))
P("-- 0x6D5F60（Rect→0xB0CE28..34 + 视口同步）关键行")
dump(0x6D5F60, 0x6D5FFA)
P("callers of 0x6D5F60:", [hex(c) for c in callers(0x6D5F60)])
P("-- 跳视口 0x6D6070 尾部（[D64]=[D74] 立即同步）")
dump(0x6D613F, 0x6D616C)
P("callers of 0x6D6070 count:", len(callers(0x6D6070)))
P("-- AI 内同步+重算（0x6D2540 体, vtable[23]）")
dump(0x6D2540, 0x6D256B)
dump(0x6D2752, 0x6D2784)
P("-- AI 体外的第二重算路径 0x6DBD20（vtable[5]）尾部")
dump(0x6DBDBB, 0x6DBDF0)

P("=" * 78)
P("ELAPSED %.1fs" % (time.time() - t0))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(_buf) + "\n")
print("WROTE", OUT)
