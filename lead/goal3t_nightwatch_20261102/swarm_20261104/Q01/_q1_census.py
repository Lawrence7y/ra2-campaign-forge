# -*- coding: utf-8 -*-
"""Q01 步2+3：四旗标全镜像 disp 普查 + 写者上下文 + MLF 尾部 + 调度器 + 辅助全局 + 死块引用核查。"""
import sys, struct, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage %.6f%% / %d insns / %d resync" % eng.coverage)
stream = eng.stream

FLAGS = [("F1", 0xA83D49), ("F2", 0xA8ECD0), ("F3", 0x8B41C0), ("F4", 0xA83D48)]

# ---------- 1. 四旗标全镜像 disp_hits ----------
print("\n===== 四旗标全镜像 disp_hits =====")
allhits = {}
for nm, va in FLAGS:
    hits = eng.disp_hits(va)
    allhits[va] = hits
    print("\n[%s] 0x%08X : %d hits" % (nm, va, len(hits)))
    for a, rw, m, o in hits:
        print("   %08X %s  %s %s" % (a, rw, m, o))

# ---------- 2. 宿主函数归属（最大 E8 头 <= 命中） ----------
heads = sorted({i.operands[0].imm for i in stream
                if i.mnemonic == "call"
                for _ in [0]
                if i.operands and i.operands[0].type == 2})
def host(va):
    k = bisect.bisect_right(heads, va) - 1
    return heads[k] if k >= 0 else None

print("\n===== 命中点宿主归属 =====")
for nm, va in FLAGS:
    for a, rw, m, o in allhits[va]:
        print("[%s] hit 0x%08X %s -> host 0x%08X" % (nm, a, rw, host(a) or 0))

# ---------- 3. MLF 尾部精确字节 ----------
print("\n===== MLF 尾部 0x55DE60..0x55DEE0 =====")
for a, b, m, o in eng.disasm(0x55DE60, 0x80):
    print("  %08X  %-22s %s %s" % (a, b, m, o))

# ---------- 4. 调度器 0x48CCC0 头 + 帧循环 ----------
print("\n===== 调度器 0x48CCC0..0x48CEB8 =====")
for a, b, m, o in eng.disasm(0x48CCC0, 0x1F8):
    print("  %08X  %-22s %s %s" % (a, b, m, o))

# ---------- 5. 辅助全局普查：0xABCD58 / 0xA8DAB4 / 0xA83D4C / 0xA802C8-D0 / 0xA8F900 / 0xB779C4 ----------
print("\n===== 辅助全局 disp 普查 =====")
for nm, va in [("0xABCD58", 0xABCD58), ("0xA8DAB4", 0xA8DAB4),
               ("0xA83D4C", 0xA83D4C), ("0xA8F900", 0xA8F900),
               ("0xB779C4", 0xB779C4), ("0xA8B8C1", 0xA8B8C1)]:
    hits = eng.disp_hits(va)
    ws = [h for h in hits if h[1] == "W"]
    print("[%s] total=%d W=%d" % (nm, len(hits), len(ws)))
    for a, rw, m, o in ws:
        print("   W %08X  %s %s   host=0x%08X" % (a, m, o, host(a) or 0))

# ---------- 6. 死块 [0x55CFE1,0x55D059) 全镜像静态引用核查 ----------
print("\n===== 死块 0x55CFE1..0x55D058 静态引用核查 =====")
# 6a. 流内跳转/调用目标落入死块
targets = set()
for i in stream:
    if i.mnemonic in ("jmp",) or i.mnemonic.startswith("j") or i.mnemonic == "call":
        try:
            if i.operands and i.operands[0].type == 2:
                t = i.operands[0].imm
                if 0x55CFE1 <= t < 0x55D059:
                    targets.add((i.address, t, i.mnemonic))
        except Exception:
            pass
print("stream jmp/call targets into dead block:", [(hex(a), hex(t), m) for a, t, m in targets])
# 6b. 全文件 4 字节 LE 立即数/指针搜索
raw = eng.raw
LO, HI = 0x0055CFE1, 0x0055D058
hits2 = []
off = 0
blob = raw
while True:
    k = blob.find(struct.pack("<I", LO), off)
    if k < 0:
        break
    hits2.append(("first-of-range", k))
    break
cnt = 0
for v in range(LO, HI + 1):
    pat = struct.pack("<I", v)
    k = raw.find(pat)
    while k >= 0:
        cnt += 1
        if cnt <= 12:
            hits2.append((hex(v), hex(k)))
        k = raw.find(pat, k + 1)
print("raw 4-byte LE words in [0x55CFE1,0x55D058] anywhere in file: %d occurrences" % cnt)
for h in hits2[:12]:
    print("   ", h)

# ---------- 7. 四转换处理器 + 0x684240/0x7241A0/0x48C8B0 的 push 字符串清单 ----------
def push_strings(flo, fhi, tag):
    print("\n--- push-immediates in %s [0x%08X,0x%08X) ---" % (tag, flo, fhi))
    for i in stream:
        if not (flo <= i.address < fhi):
            continue
        if i.mnemonic != "push":
            continue
        try:
            if i.operands and i.operands[0].type == 2:
                v = i.operands[0].imm
        except Exception:
            continue
        if 0x401000 <= v < 0x8E0000:
            s = eng.rd(v, 64).split(b"\0")[0]
            try:
                txt = s.decode("gbk")
            except Exception:
                txt = repr(s[:32])
            if s and all(32 <= c < 127 or c >= 0x80 for c in s[:48]):
                print("   %08X push 0x%08X -> %r" % (i.address, v, txt))

for va in (0x685670, 0x685DC0, 0x6863E0, 0x686570, 0x684240, 0x48C8B0, 0x72DFB0, 0x6C8820, 0x6C6F50):
    # 宿主窗口：用相邻 E8 头定界
    k = heads.index(va) if va in heads else None
    if k is None or k + 1 >= len(heads):
        print("\n--- 0x%08X not a call-target head, skip window ---" % va)
        continue
    push_strings(va, heads[k + 1], hex(va))

print("\n--- string @0x82A044 ---")
print("  ", eng.rd(0x82A044, 96).split(b"\0")[0])
print("--- string @0x82A034 ---")
print("  ", eng.rd(0x82A034, 16).split(b"\0")[0])
