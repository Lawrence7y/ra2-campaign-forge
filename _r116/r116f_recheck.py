#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r116f_recheck.py —— 主会话独立复算（规则 D）：用一个**完全独立重写**的最小实现，
复核本轮全部关键数字，不复用 r116a..r116e 的任何函数，也不复用 r113_lib 的 census。

复算目标（每条都与落盘 json 逐一比对）：
  V1 GUID 形状常量数 = 6，地址集合精确相等
  V2 0x7f7c80 的 push-imm32 站点数 = 60；0x7f7c70 = 0
  V3 0x7f7c80 请求函数数 = 36；0x7f7c70 = 0
  V4 与 OleSaveToStream 耦合（两种调用形态）的函数数 = 36
  V5 dispatcher：35 个 call 锚形态、35 份模板体全等、35 个 edx 两两不同
  V6 0x7f7c90 的 push 站点 = 56，耦合 0
"""
import collections, json, os, struct, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
import pefile
pe = pefile.PE(os.path.join(ROOT, 'ra2bench/gamemd.exe'), fast_load=True)
BASE = pe.OPTIONAL_HEADER.ImageBase
SEC = []
for s in pe.sections:
    SEC.append((s.Name.rstrip(b'\0').decode(), BASE + s.VirtualAddress,
                s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
F = open(os.path.join(ROOT, 'ra2bench/gamemd.exe'), 'rb')
IMG = F.read()
F.close()


def raw_at(va):
    for nm, v0, vs, pr, rs in SEC:
        if v0 <= va < v0 + vs:
            d = va - v0
            if d < rs:
                return pr + d
            return None
    return None


def rd32(va):
    o = raw_at(va)
    if o is None or o + 4 > len(IMG):
        return None
    return struct.unpack_from('<I', IMG, o)[0]


TX = [x for x in SEC if x[0] == '.text'][0]
T0, T1 = TX[1], TX[1] + TX[2]
RD = [x for x in SEC if x[0] == '.rdata'][0]
R0, R1 = RD[1], RD[1] + RD[2]
DT = [x for x in SEC if x[0] == '.data'][0]
D0, D1 = DT[1], DT[1] + DT[2]

# ---- 独立的函数入口集合：不用 r113 的 HB，改用「call/jmp rel32 目标 ∪ 有填充前缀」----
targets = set()
for a in range(T0, T1 - 5):
    o = raw_at(a)
    if o is None:
        continue
    b = IMG[o]
    if b in (0xe8, 0xe9):
        rel = struct.unpack_from('<i', IMG, o + 1)[0]
        t = a + 5 + rel
        if T0 <= t < T1:
            targets.add(t)


def fn_before(va):
    """va 之前最近的 call/jmp 目标（独立于 HB 的实现）"""
    cands = [t for t in targets if t <= va]
    return max(cands) if cands else None


checks = []


def ck(n, c, d=''):
    checks.append({'n': n, 'ok': bool(c), 'd': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d else ''), flush=True)


# ---- V1 ----
g = []
for a in range(R0, R1 - 0x10, 4):
    if rd32(a + 4) == 0 and rd32(a + 8) == 0xC0 and rd32(a + 12) == 0x46000000:
        g.append(a)
ck('V1 GUID 形状常量 = %d 个：%s' % (len(g), [hex(x) for x in g]),
   len(g) == 6 and sorted(g) == sorted([0x7f7c70, 0x7f7c80, 0x7f7c90, 0x7f7ca0, 0x7f7cf0, 0x7f7d00]),
   [hex(x) for x in g])


def push_sites(iid):
    """独立实现：扫 .text 里该 imm32 的出现，用「前 1 字节 == 0x68」判定 push imm32"""
    pat = struct.pack('<I', iid)
    o0 = raw_at(T0)
    buf = IMG[o0:raw_at(T1)]
    out = []
    i = buf.find(pat)
    while i != -1:
        if i >= 1 and buf[i - 1] == 0x68:
            out.append(T0 + i - 1)
        i = buf.find(pat, i + 1)
    return out


p80 = push_sites(0x7f7c80)
p70 = push_sites(0x7f7c70)
p90 = push_sites(0x7f7c90)
ck('V2 push-imm32 站点：0x7f7c80=%d、0x7f7c70=%d、0x7f7c90=%d'
   % (len(p80), len(p70), len(p90)),
   len(p80) == 60 and len(p70) == 0 and len(p90) == 56,
   {'80': len(p80), '70': len(p70), '90': len(p90)})

# ---- V3 函数去重（用独立 targets 集合）----
f80 = set(fn_before(x) for x in p80)
f70 = set(fn_before(x) for x in p70)
ck('V3 请求函数数（独立 fn_before 实现）：0x7f7c80=%d、0x7f7c70=%d'
   % (len(f80), len(f70)),
   len(f80) == 36 and len(f70) == 0,
   {'80': len(f80), '70': len(f70), 'fns': sorted(hex(x) for x in f80)[:5]})

# ---- V4 耦合（两种调用形态，独立实现：在函数体窗口内找 IAT 槽出现 + call）----
IAT_SAVE = 0x7e15f4


# S-27（自错，本轮在跨实现复算里被抓到，两版都错，记录完整过程）：
#   实测字节（0x67d351）：8b 2d f4 15 7e 00  =  mov ebp, dword ptr [0x7e15f4]
#     0x67d351: 8b   <- opcode MOV r32, r/m32
#     0x67d352: 2d   <- ModRM，reg 字段 = (0x2d>>3)&7 = 5 = ebp，rm 字段 = 5 = [disp32]
#     0x67d353: f4 15 7e 00  <- imm32 (IAT 槽)
#   第一版错在 `modrm = seg[i+4]`（越过立即数去读）；第二版错在 `seg[i-1]==0x8b`
#   且 `reg = seg[i]&7`（拿 rm 字段当寄存器）。本镜像里 reg 与 rm 恰好都是 5，
#   所以第二版对这一个站点**碰巧**也对，但对 `mov eax,[IAT]`（8b 05）会错。
#   正确：opcode 在 i-2，ModRM 在 i-1，target reg = (seg[i-1] >> 3) & 7。
def ole_save_in(f, lo, hi):
    """在 [lo,hi) 区间内找：直接 call [IAT] 或 mov reg,[IAT] 后 call reg"""
    o = raw_at(f)
    if o is None:
        return False
    pat = struct.pack('<I', IAT_SAVE)
    end = raw_at(hi) or (o + 2000)
    seg = IMG[o:end]
    direct = False
    regs = set()
    i = seg.find(pat)
    while i != -1:
        # 前 2 字节 ff 15 => call [IAT]
        if i >= 2 and seg[i - 2:i] == b'\xff\x15':
            direct = True
        # i-2 == 8b => mov r32, [disp32]；i-1 是 ModRM，目标寄存器在 reg 字段
        if i >= 2 and seg[i - 2] == 0x8b and seg[i - 1] < 0x40:   # mod==00 且 rm==101
            regs.add((seg[i - 1] >> 3) & 7)
        i = seg.find(pat, i + 1)
    if direct:
        return True
    # 找 call modrm 指向这些 reg 的 ff /2（call r/m32）
    for j in range(len(seg) - 2):
        if seg[j] == 0xff and ((seg[j + 1] >> 3) & 7) == 2 and (seg[j + 1] & 0xc0) == 0xc0:
            if (seg[j + 1] & 7) in regs:
                return True
    return False


coup = 0
for f in sorted(f80):
    sites = [x for x in p80 if fn_before(x) == f]
    hi = min([x for x in range(min(sites), T1) if x in targets and x > min(sites)] or [T1])
    if ole_save_in(f, min(sites), hi):
        coup += 1
ck('V4 与 OleSaveToStream 耦合的请求函数 = %d / %d（两种调用形态都算）' % (coup, len(f80)),
   coup == 36, {'coupled': coup, 'total': len(f80)})

# ---- V5 dispatcher ----
LO, HI = 0x67fdf0, 0x681000
disp = []
a = 0x67df00
while a < 0x67e400:
    o = raw_at(a)
    if IMG[o] == 0xe8:
        rel = struct.unpack_from('<i', IMG, o + 1)[0]
        t = a + 5 + rel
        if LO <= t < HI and IMG[o - 2:o] == b'\x8b\xce' and IMG[o - 7] == 0xba:
            disp.append((a, t, struct.unpack_from('<I', IMG, o - 6)[0]))
    a += 1
bodies = set()
for _, t, _ in disp:
    o = raw_at(t)
    bodies.add(IMG[o:o + 0x70])
ck('V5 dispatcher：锚形态命中 %d 个；模板体种类 %d；edx 两两不同 %d'
   % (len(disp), len(bodies), len(set(e for _, _, e in disp))),
   len(disp) == 35 and len(bodies) == 1 and len(set(e for _, _, e in disp)) == 35,
   {'calls': len(disp), 'bodies': len(bodies), 'distinct_edx': len(set(e for _, _, e in disp))})

# ---- V6 ----
c90 = 0
for f in set(fn_before(x) for x in p90):
    sites = [x for x in p90 if fn_before(x) == f]
    hi = min([x for x in range(min(sites), T1) if x in targets and x > min(sites)] or [T1])
    if ole_save_in(f, min(sites), hi):
        c90 += 1
ck('V6 0x7f7c90 的请求函数中与 OleSaveToStream 耦合的 = %d（必须 0）' % c90, c90 == 0, {'c90': c90})

json.dump({'checks': checks}, open(os.path.join(ROOT, '_r116/r116f_recheck.json'), 'w'), indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
sys.exit(0 if np_ == len(checks) else 1)
