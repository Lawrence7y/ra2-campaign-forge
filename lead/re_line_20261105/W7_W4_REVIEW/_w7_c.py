# -*- coding: utf-8 -*-
"""W7 复核员 C · 跨文件一致性独立探针（只读、零真机、零注入）。

用 ra2tool.Engine 真反汇编核字节；不采信七份正文的自述输出。
唯一写域：W7_W4_REVIEW/。运行：python -I -X utf8 _w7_c.py > _w7_c_out.txt 2>&1
"""
import sys, os, hashlib, re, struct, datetime

ROOT = r"D:\Project\ra2-campaign-forge"
SEC = os.path.join(ROOT, r"lead\re_line_20261105\W4_FIELD_SPEC\sections")
sys.path.insert(0, os.path.join(ROOT, r"lead\goal3t_nightwatch_20261102\swarm_20261104"))
from ra2tool import Engine

FILES = [
    "card_0087E8E0.md",
    "card_00A8EC34.md",
    "card_00B0CE88.md",
    "card_00A8ED50.md",
    "Q2_ALPHA.md",
    "Q3_FRAME_EDGE_SPEC.md",
    "Q4_REDLINE.md",
]

def line(s=""):
    print(s, flush=True)

def sep(tag):
    line("")
    line("=" * 78)
    line(tag)
    line("=" * 78)

line("W7_C_PROBE_START " + datetime.datetime.now().isoformat(timespec="seconds"))
line("PYTHON " + sys.version.replace("\n", " "))

# ---------------------------------------------------------------- 0. 被核对象绑定
sep("0. 被核对象 SHA256 / 字节数（本次实算，二进制读流）")
total = 0
concat = b""
for f in FILES:
    p = os.path.join(SEC, f)
    b = open(p, "rb").read()
    total += len(b)
    concat += b
    line("%-26s size=%6d sha256=%s" % (f, len(b), hashlib.sha256(b).hexdigest()))
line("TOTAL_BYTES_7 %d" % total)
line("COMPOSITE_SHA256_of_concat_in_table_order %s" % hashlib.sha256(concat).hexdigest())

# ---------------------------------------------------------------- 1. 目标镜像
sep("1. 目标镜像 Engine() 绑定与覆盖率")
e = Engine()
line("EXE_SHA256 " + e.sha)
line("EXPECT_SHA256 " + "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")
line("EXE_SHA_MATCH " + str(e.sha == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"))
line("IMAGE_BASE %s" % hex(e.IB))
line("COVERAGE(pct,insns,resync) " + str(e.coverage))
line("SECTIONS " + str([(n, hex(v), hex(vs), hex(rp), hex(rs)) for n, v, vs, rp, rs in e.SEC]))

def show(va, n, tag):
    line("-- %s : disasm(0x%X, 0x%X) --" % (tag, va, n))
    for a, b, m, o in e.disasm(va, n):
        line("  0x%08x %-24s %-8s %s" % (a, b, m, o))

# 一次遍历 stream，收集所有直接 call 目标计数
TARGETS = {0x42A5B0, 0x42C900, 0x42D170, 0x6D2790, 0x6F8DF0, 0x6D3D10}
line("-- building direct-call census over full stream (single pass) --")
calls = {t: [] for t in TARGETS}
s = e.stream
for ins in s:
    if ins.mnemonic != "call":
        continue
    try:
        if ins.operands and ins.operands[0].type == 2:
            t = ins.operands[0].imm
            if t in calls:
                calls[t].append(ins.address)
    except Exception:
        pass
for t in sorted(TARGETS):
    line("  CALLERS 0x%X count=%d %s" % (t, len(calls[t]), [hex(x) for x in calls[t][:25]]))

# ---------------------------------------------------------------- 2. 对①：card_0087E8E0 <-> Q4_REDLINE（C1 判定）
sep("2. 对① C1 判定：代际戳「尝试代理 / 不能说展开很多节点」的字节底座")
show(0x42A5F0, 0x20, "ResetWorkspace W1 自增/写回 + 回绕早退 jne")
show(0x42A67F, 0x10, "回绕全清分支尾部 W2 第二次自增（+2 跳 0）")
show(0x42A6D0, 0x38, "构造函数体：初值 -1 / W3 写 +0x28")
show(0x42CC70, 0x30, "同步重试层 0x42CC80 再次 call 0x42A5B0")
show(0x42D170, 0x14, "另一入口 0x42D170 prologue")
show(0x42D220, 0x14, "另一入口：递增早于可能失败的检查 0x42D229")
show(0x429AB0, 0x10, "SearchCore 栈局部 [esp+0x28]（节点轮数，非本 VA）")
# 单例立即数模式
needle = bytes.fromhex("b9b8e88700")
tb = e.raw[e.TB:e.TB + e.TSZ]
pos, occ = 0, []
while True:
    k = tb.find(needle, pos)
    if k < 0:
        break
    occ.append(e.TLO + k)
    pos = k + 1
line("IMM_mov_ecx_0x87E8B8 count=%d %s" % (len(occ), [hex(x) for x in occ[:30]]))
# 0x42A5B0 直接 E8 调用者（用原始 rel32 扫描复核 capstone 结果）
raw_e8 = []
pos = 0
while True:
    k = tb.find(b"\xe8", pos)
    if k < 0:
        break
    if k + 5 <= len(tb):
        rel = struct.unpack_from("<i", tb, k + 1)[0]
        va = e.TLO + k
        if (va + 5 + rel) & 0xFFFFFFFF == 0x42A5B0:
            raw_e8.append(va)
    pos = k + 1
line("RAW_E8_to_0x42A5B0 count=%d %s" % (len(raw_e8), [hex(x) for x in raw_e8]))
line("C1_NOTE 节点展开量在 SearchCore 的 [esp+0x28]（见 0x429AB6/0x42A3D4），不是 [this+0x28]")

# ---------------------------------------------------------------- 3. 对②：card_00B0CE88 <-> Q4_REDLINE（C2 判定）
sep("3. 对② C2 判定：脏矩形 Count 语义 + W3 抄录订正 + DrawIfVisible 零 call")
show(0x6D3DE8, 0x28, "Render 判脏段：0x6D3DF0 读 Count / 0x6D3DF5 / 0x6D3DFF / 0x6D3E01")
show(0x6D1A60, 0x40, "CRT 构造 0x6D1A60：Count 置 0、vptr 绝对地址")
show(0x6D2790, 0x10, "RegisterDirtyArea 序言：ecx 被绝对地址覆盖（证明非 TacticalClass 成员）")
show(0x6D2A90, 0x20, "追加新条目：读 Count / inc / 写回 W3")
show(0x6DA980, 0x18, "独立 Clear 例程 0x6DA980")
line("DISP_HITS_0xB0CE88 " + str([(hex(a), w, m, o) for a, w, m, o in e.disp_hits(0xB0CE88)]))
# DrawIfVisible 函数体内 call 0x6D2790 计数
lo, hi = 0x5F4B10, 0x5F4D30
in_range = [hex(a) for a in calls[0x6D2790] if lo <= a < hi]
line("RDA_callers_in_[0x5F4B10,0x5F4D30) count=%d %s" % (len(in_range), in_range))
line("RDA_callers_total count=%d" % len(calls[0x6D2790]))
# ret 位置（0x5F4B85 / 0x5F4D0C 是否都存在）
rets = []
for a, b, m, o in e.disasm(0x5F4B10, 0x230):
    if m.startswith("ret"):
        rets.append((hex(a), b, m, o))
line("RET_in_[0x5F4B10,0x5F4D40) " + str(rets))
# 0x6D3DF5 与 0x6D3DFF 的原始字节
line("RAW_0x6D3DF5_8B " + e.rd(0x6D3DF5, 8).hex())
line("RAW_0x6D3DFF_8B " + e.rd(0x6D3DFF, 8).hex())

# ---------------------------------------------------------------- 4. 对③：card_00A8EC34 <-> Q4_REDLINE（C4 判定）
sep("4. 对③ C4 判定：唯一写点 / 入口无条件自增 / 早退在写回之后")
show(0x6F8DF0, 0x60, "Greatest_Threat 序言：读 / inc / 写回 / 早退 ret")
line("DISP_HITS_0xA8EC34 " + str([(hex(a), w, m, o) for a, w, m, o in e.disp_hits(0xA8EC34)]))
line("CALLERS_0x6F8DF0 count=%d %s" % (len(calls[0x6F8DF0]), [hex(x) for x in calls[0x6F8DF0]]))
# 入口到写回之间是否存在 jcc/cmp/test/call
mid = [ (hex(a), m, o) for a, b, m, o in e.disasm(0x6F8DF0, 0x19)
        if m.startswith("j") or m in ("cmp", "test", "call") ]
line("JCC_CMP_TEST_CALL_between_0x6F8DF0_and_0x6F8E09 count=%d %s" % (len(mid), mid))
# 函数体内 ret 位置
rets2 = []
for a, b, m, o in e.disasm(0x6F8DF0, 0xFC0):
    if m.startswith("ret"):
        rets2.append(hex(a))
line("RET_in_[0x6F8DF0,0x6F9DB0) " + str(rets2))
# 全文件裸 dword 0xA8EC34 出现次数
nd = struct.pack("<I", 0x00A8EC34)
cnt = e.raw.count(nd)
line("RAW_LE_DWORD_0xA8EC34_whole_file_count %d" % cnt)
# 9 字节 Inline Hook 源码行号核对（A2/C2 诚实账相关）
line("-- hook source line existence --")
for rel, rng in [
    (r"ra2render\dllmain.cpp", (20, 35)),
    (r"ra2render\blitter_hooks.cpp", (1340, 1420)),
    (r"ra2render\blitter_hooks.cpp", (3775, 3790)),
    (r"ra2render\ra2render.ini", (18, 30)),
]:
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        line("  MISSING " + rel)
        continue
    L = open(p, encoding="utf-8", errors="replace").read().split("\n")
    line("  EXISTS %s lines=%d range=%s" % (rel, len(L), rng))
    for i in range(rng[0] - 1, min(rng[1], len(L))):
        if re.search(r"GreatestThreat|greatestThreat|0x6F8DF0|83 EC 5C|interval|InstallVTableHooks|DLL_PROCESS_ATTACH|ThrottleKey|throttledTargetScans|E9|trampoline", L[i], re.I):
            line("    L%d %s" % (i + 1, L[i].strip()[:150]))

# ---------------------------------------------------------------- 5. 对④：card_00A8ED50 <-> Q2_ALPHA（Bullet 量纲）
sep("5. 对④ Bullet 量纲：瞬时水位 / 注册对象 Count / +0x98 与 +0x90 二道门")
show(0x55B93F, 0x30, "主更新循环：Count 作倒序边界 + 对象 +0x98 一字节活跃标志门控")
show(0x4666E0, 0x30, "BulletClass::Update 体：+0x90 二道门 je 0x467FEE 早退")
show(0x467FEE, 0x10, "二道门早退落点 pop/ret")
show(0x5F3928, 0x10, "基类构造：+0x90 初值 1 / +0x98 初值 0")
line("DISP_HITS_0xA8ED50 " + str([(hex(a), w, m, o) for a, w, m, o in e.disp_hits(0xA8ED50)]))
# 复现 Q2_ALPHA §2.2 [3] 打印的字节（核对该文转述是否属实）
line("-- Q2_ALPHA §2.2 segment [3] reproduced --")
for a, b, m, o in e.disasm(0x55B93F, 0x26):
    line("  0x%08x %-24s %-8s %s" % (a, b, m, o))
# 卡内「不每帧归零 / 双向变化」的写点：W2 inc / W3 dec
show(0x4664A0, 0x10, "Add 路径 inc ecx / 写回 Count（+1）")
show(0x466623, 0x14, "Del 路径 dec ecx / 写回 Count（-1）")

# ---------------------------------------------------------------- 6. 对⑤：Q3 <-> Q2（5 读口径 / alpha 不可解 / 算术）
sep("6. 对⑤ 5 读口径与 alpha 不可解：算术与文本口径")
four = [0x0087E8E0, 0x00A8EC34, 0x00B0CE88, 0x00A8ED50]
allv = four + [0x00A8ED84]
line("FOUR_VA_ASC " + str([hex(x) for x in sorted(four)]))
line("SPAN_max_minus_min %d = 0x%X" % (max(four) - min(four), max(four) - min(four)))
line("PAYLOAD_4x4 %d B ; READS_incl_f_post %d B nominal" % (4 * 4, 5 * 4))
line("BASELINE 500 calls/s *4 = %d B/s ; +1Hz*8 = %d B/s ; total %d calls/s %d B/s"
     % (500 * 4, 8 * 4, 500 + 8, 500 * 4 + 8 * 4))
rows = [
    (5.9952, "Q2:52 1000/166.8"),
    (6.0, "W3:237"),
    (19.8112, "FB:165 1000/50.4764"),
    (30.2016, "FB:166 1000/33.1108"),
    (30.8426, "FB:167 1000/32.4227"),
    (31.25, "W3:237"),
    (500.0, "cap"),
]
for lam, src in rows:
    line("LAMBDA %-10.4f %-24s 20B/s=%9.2f 5calls/s=%8.2f 24B/s=%9.2f 6calls/s=%8.2f"
         % (lam, src, 20 * lam, 5 * lam, 24 * lam, 6 * lam))
# 复算 λ 由 stored p50
for p50 in (166.8, 50.47639999247622, 33.11079999548383, 32.422699994640425):
    line("P50 %-22.14f -> lambda %.6f" % (p50, 1000.0 / p50))
# 十六进制间隔
sv = sorted(allv)
for (a, b) in zip(sv, sv[1:]):
    line("GAP 0x%08X -> 0x%08X = %d B = 0x%X" % (a, b, b - a, b - a))
# D-21 / V6 文件存在性与关键口径
for rel, keys in [
    (r"lead\re_line_20261105\D21_RULING\RULING_D21.md", ["每沿新增 5 次", "20 B", "S0"]),
    (r"lead\re_line_20261105\V6_V3_REVIEW\V6_V3_REVIEW.md", ["CONFIRMED", "5 次"]),
    (r"lead\re_line_20261105\W4_FIELD_SPEC\TASK.md", ["每沿"]),
]:
    p = os.path.join(ROOT, rel)
    line("REF_EXISTS %s %s" % (rel, os.path.isfile(p)))
    if os.path.isfile(p):
        txt = open(p, encoding="utf-8", errors="replace").read()
        for k in keys:
            line("   contains %-18r -> %s" % (k, k in txt))

# ---------------------------------------------------------------- 7. C2 项：未验标记 / 诚实账 / 强断言
sep("7. C2 项：逐文件「未验/未核实」标记、诚实账落点、同句强断言扫描")
MARK = re.compile(r"未验|未核实|未独立复验|未复验|未穷尽|未闭合|未定位|未定名|未做|未重跑|未验证|未测|未量化|未证|未授|未获|未通过|未检查|采信|不宣称|不冒称|未运行|未启动|未读|未追|未采|未普查|未复算|未校准|未定谳|未逐|未重算|未独立重跑|未闭合|未解决|未实跑")
STRONG = re.compile(r"确证|已验|实测|已核实|穷尽\s*=|穷尽=|已定位|定谳|已通过|独立复验|已复验|已确认|严格成立|完全成立|已闭合|已穷尽|已定谳|已验证|已采信为亲验")
LEDGER = re.compile(r"^#{1,4} .*诚实账|^#{1,4} .*未验|本次未做|本次未验|本次未运行|本次未跑|本次未启动|未运行 / 未获证|\*\*本次未", re.I)
for f in FILES:
    p = os.path.join(SEC, f)
    txt = open(p, encoding="utf-8").read()
    L = txt.split("\n")
    mhits = [(i, l) for i, l in enumerate(L, 1) if MARK.search(l)]
    lhits = [(i, l) for i, l in enumerate(L, 1) if LEDGER.search(l)]
    co = [(i, l) for i, l in mhits if STRONG.search(l)]
    line("")
    line("### FILE %s  lines=%d  marker_lines=%d  ledger_heads=%d  marker+strong_cooccur=%d"
         % (f, len(L), len(mhits), len(lhits), len(co)))
    line("  LEDGER_HEADS " + str([i for i, _ in lhits]))
    line("  MARKER+LONG_LEDGER_LINES " + str([i for i, l in mhits if len(l) > 200][:40]))
    for i, l in co:
        line("  CO_L%d %s" % (i, l.strip()[:230]))
    # 输出全部 marker 行（去表格前缀压缩）
    for i, l in mhits:
        line("  M_L%d %s" % (i, l.strip()[:190]))

# ---------------------------------------------------------------- 8. 结论性交叉断言抽取（人工复核用）
sep("8. 五对关键断言原文抽取（供人工逐对比对）")
KEYS = {
    "Q4_REDLINE.md": [r"C2 渲染", r"C1 寻路", r"C4 索敌", r"部分能", r"不能", r"未验", r"未重跑"],
    "card_0087E8E0.md": [r"尝试代理", r"不能说", r"展开节点", r"未验", r"穷尽"],
    "card_00B0CE88.md": [r"可见单位数", r"不能", r"未验", r"穷尽"],
    "card_00A8EC34.md": [r"主犯", r"不能", r"未验", r"穷尽", r"Hook"],
    "card_00A8ED50.md": [r"水位", r"瞬时", r"不能", r"未验", r"门控"],
    "Q2_ALPHA.md": [r"水位", r"不可解", r"未验", r"未独立复验", r"平凡界"],
    "Q3_FRAME_EDGE_SPEC.md": [r"5 次", r"20 B", r"名义操作数", r"未验", r"alpha", r"未做"],
}
for f, pats in KEYS.items():
    L = open(os.path.join(SEC, f), encoding="utf-8").read().split("\n")
    line("")
    line("### " + f)
    for pat in pats:
        rx = re.compile(pat)
        hit = [(i, l.strip()[:170]) for i, l in enumerate(L, 1) if rx.search(l)]
        line("  PAT %-16r count=%d first=%s" % (pat, len(hit), hit[:3]))

line("")
line("W7_C_PROBE_END " + datetime.datetime.now().isoformat(timespec="seconds"))
