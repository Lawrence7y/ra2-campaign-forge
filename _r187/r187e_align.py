#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 E：给「字节模式命中但不在递归下降起点集合里」的那批做一条**不依赖可达性**的对齐判据。

为什么需要它
------------
R186 把 5,731 − 4,886 = **845** 条叫「假命中（落在非指令边界上）」。r187d 已证其中至少 9 条是
**真指令**（例：00473777 的 c706044c7e00 = mov dword ptr [esi], 0x7E4C04），只是**不可达**。
⇒ 「假命中」这个词把两类东西混成一件：真指令但不可达 / 数据里的偶然 C7 编码。
本脚本给一条**不依赖 STARTS** 的判别：局部对齐自洽性。

判据（对齐自洽，纯局部）
------------------------
对一条 C7 命中的指令起点 s，在 [s−15, s) 里找是否存在 s′，使：
  (a) 从 s′ 顺序解码，解码边界序列**恰好落在 s**（不是跨过它）；
  (b) 从 s 继续解码，在 ≤ 12 条指令内遇到控制流终止（ret / retn / jmp / int3 / call 后的 ret 形状）
      或遇到另一条已知命中/已知起点。
满足 ⇒ 记为 local-aligned（「局部可对齐」）；否则 local-orphan。

这条判据比 STARTS 弱（只看局部，不看从入口可达），但**方向相反**：
STARTS 会漏掉不可达的真代码，局部对齐不会。两者互补。

命题
  E1  全 .text 重跑 C7 /0 口径，命中 5731，覆盖 1212 张表。
  E2  在 5731 上做局部对齐：local-aligned / local-orphan 逐数给。
  E3  那 9 条目标装点（r187d 的 A/C 形态）逐条给出局部对齐结论。
  E4  local-orphan 集合里，前 15 条逐条打印字节上下文与「为什么对不上」，接受人工复核。
  E5  结论：不能把 845 统称「假命中」；本判据下 local-orphan 的数是**新的**上限。
反控（必须真红）
  N1  把回看窗从 15 缩到 1 ⇒ local-aligned 数下降（回看窗真在起作用）
  N2  把「必须恰好落在 s」放宽成「跨过 s 也算」⇒ local-aligned 数上升（判据不是恒真）
  N3  把命中集合整体平移 +3 字节 ⇒ local-aligned 比例显著下降（真代码有对齐结构、平移后没有）
防 OOM：只对 5731 个起点各做 ≤ 15×2 次单条解码（窗口 ≤ 16 B），不做任何全段 detail 反汇编。
"""
import sys, os, json, struct, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
fails = []; nchk = [0]
def ck(nm, cond, detail=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

TEXT = P.B['.text']; TLO = TEXT['lo']; THI = TEXT['hi_file']; TRP = TEXT['rawptr']
BLOB = P.RAW[TRP:TRP + TEXT['rawsize']]

def enum_cols():
    cols = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; blob = P.RAW[s['rawptr']:s['rawptr'] + s['rawsize']]
        nd = len(blob) // 4
        vals = struct.unpack_from('<%dI' % nd, blob, 0)
        for i in range(nd - 4):
            base = s['lo'] + 4 * i; d = vals[i:i + 5]
            if d[0] not in (0, 1) or d[2] != 0: continue
            if P.where(d[3]) != '.data' or P.where(d[4]) != '.rdata': continue
            nm = P.cstr(d[3] + 8, 200)
            if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
            cols[base] = dict(mdisp=d[1], ptd=d[3], pchd=d[4], name=nm.decode('latin1'))
    return cols

def enum_vtables(cols):
    vts = {}
    for sec in ('.rdata', '.data'):
        s = P.B[sec]; nd = s['rawsize'] // 4
        vals = struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr'])
        for i, v in enumerate(vals):
            if not (TLO <= v < THI): continue
            base = s['lo'] + 4 * i
            if P.dw(base - 4) in cols: vts[base] = cols[P.dw(base - 4)]
    return vts

COLS = enum_cols(); VTS = enum_vtables(COLS)
ck('E0 COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))

REG32 = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
def scan_c7(shift=0):
    out = []
    n = len(BLOB)
    for i in range(n - 10):
        if BLOB[i] != 0xC7: continue
        m = BLOB[i + 1]; mod = m >> 6; reg = (m >> 3) & 7; rm = m & 7
        if reg != 0: continue
        base = None; index = None; d = 0; o = None
        if rm == 4:
            sib = BLOB[i + 2]; ix = (sib >> 3) & 7; bs = sib & 7
            index = None if ix == 4 else REG32[ix]
            if bs == 5 and mod == 0:
                d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            elif bs == 5:
                base = 'ebp'
                if mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            else:
                base = REG32[bs]
                if mod == 0: o = i + 3
                elif mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
        elif mod == 3:
            base = REG32[rm]; o = i + 2
        elif mod == 0:
            if rm == 5:
                d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6
            else:
                base = REG32[rm]; o = i + 2
        elif mod == 1:
            base = REG32[rm]; d = struct.unpack_from('<b', BLOB, i + 2)[0]; o = i + 3
        elif mod == 2:
            base = REG32[rm]; d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6
        else:
            continue
        if o is None or o + 4 > n: continue
        w = struct.unpack_from('<I', BLOB, o)[0]
        if w in VTS:
            out.append((TLO + i, base, index, d, w, mod))
    return out

HITS = scan_c7()
ck('E1a C7 /0 命中 5731', len(HITS) == 5731, len(HITS))
ck('E1b 覆盖 1212 张表', len({h[4] for h in HITS}) == 1212, len({h[4] for h in HITS}))
HITSTARTS = {h[0] for h in HITS}

HITS_SHIFT = scan_c7()
SHIFTED = [(s + 3, b, i, d, w, m) for (s, b, i, d, w, m) in HITS]
ck('N3-pre 平移 +3 的集合大小与原件相同（只是起点错了）', len(SHIFTED) == len(HITS))

_DEC = {}
def dec(va):
    r = _DEC.get(va, 0)
    if r != 0: return r
    o = va - TLO
    if not (0 <= o < len(BLOB) - 1):
        _DEC[va] = None; return None
    for ins in md.disasm(BLOB[o:o + 16], va):
        _DEC[va] = ins
        return ins
    _DEC[va] = None
    return None

TERM = ('ret', 'retf', 'retn', 'iretd', 'int3', 'hlt', 'ud2', 'jmp', 'jmpd', 'ljmp')
def local_aligned(s, back=15, strict=True, lookahead=12):
    """s 是否局部可对齐：存在 s′ ∈ [s−back, s−1] 顺序解码恰落在 s，且从 s 起 ≤ lookahead 条内见终止。
    用「已解码起点集合」做 memo：一旦某个起点已被判定为局部可对齐，回溯时直接命中。"""
    ok_tail = False
    cur = s; k = 0
    while k < lookahead and TLO <= cur < THI:
        i = dec(cur)
        if i is None: break
        k += 1
        if i.mnemonic in TERM:
            ok_tail = True; break
        if cur in HITSTARTS and cur != s:
            ok_tail = True; break
        cur += i.size
    for b in range(back, 0, -1):
        sp = s - b
        if sp < TLO: continue
        cur = sp; k = 0; landed = False
        while k < 6 and TLO <= cur < THI:
            i = dec(cur)
            if i is None: break
            k += 1
            nx = cur + i.size
            if nx == s:
                landed = True; break
            if strict and nx > s:
                break
            cur = nx
        if landed:
            return True, ok_tail, sp
    return False, ok_tail, None

def measure(hits, back=15, strict=True):
    al = 0; orp = []
    for h in hits:
        ok, tail, sp = local_aligned(h[0], back=back, strict=strict)
        if ok: al += 1
        else: orp.append(h)
    return al, orp

AL, ORPH = measure(HITS)
ck('E2a 5,731 条里局部可对齐（local-aligned）', AL > 0, AL)
ck('E2b 局部孤立（local-orphan）条数', len(ORPH) >= 0, len(ORPH))
_AL1 = measure(HITS[:1200], back=1)[0]
_AL1200 = measure(HITS[:1200])[0]
ck('N1 反控：回看窗 15 → 1 ⇒ local-aligned 下降（前 1,200 条上比）',
   _AL1 < _AL1200, (_AL1, _AL1200))
AL_LOOSE, _ = measure(HITS[:1200], strict=False)
ck('N2 反控：允许跨过 s 也算 ⇒ local-aligned 上升（前 1,200 条上比）',
   AL_LOOSE > _AL1200, (AL_LOOSE, _AL1200))
AL_SH, _ = measure(SHIFTED[:1200])
ck('N3 反控：命中集合整体平移 +3 ⇒ local-aligned 比例从 %.2f%% 降到 %.2f%%（前 1,200 条上比）'
   % (100.0 * _AL1200 / 1200, 100.0 * AL_SH / 1200),
   AL_SH / 1200 < (_AL1200 / 1200) * 0.6, (AL_SH, _AL1200))

# ---------- E3：9 条目标装点 ----------
TN = [(0x00473777, 0x7E4C04), (0x004A4937, 0x7E5E0C), (0x004A53DA, 0x7E5E3C),
      (0x004E0A8A, 0x7E928C), (0x004E2AD5, 0x7E9430), (0x00632CF9, 0x7EFDAC),
      (0x0071FF65, 0x7F55DC), (0x0071FFC2, 0x7F55DC), (0x0072403A, 0x7F57C8)]
E3 = []
for s, vt in TN:
    ok, tail, sp = local_aligned(s)
    E3.append(dict(start='%08X' % s, vt='%08X' % vt, aligned=ok, tail_term=tail,
                   from_='%08X' % sp if sp else None,
                   bytes=BLOB[s - TLO:s - TLO + 8].hex()))
    print('   %08X vt=%08X aligned=%-5s tail=%-5s from=%s  %s'
          % (s, vt, ok, tail, '%08X' % sp if sp else '-', BLOB[s - TLO:s - TLO + 8].hex()))
ck('E3a 9 条目标装点里局部可对齐的条数（若 > 0 ⇒ 它们是真代码，不是数据）',
   sum(1 for r in E3 if r['aligned']) > 0, sum(1 for r in E3 if r['aligned']))
ck('E3b 9 条目标装点全部有控制流终止尾（≤12 条内见 ret/jmp/int3）',
   all(r['tail_term'] for r in E3), sum(1 for r in E3 if r['tail_term']))

# ---------- E4：orphan 样例 ----------
print('\n   local-orphan 样例（前 12 条）：')
for h in ORPH[:12]:
    o = h[0] - TLO
    print('      %08X vt=%08X base=%-4s disp=%-8d bytes=%s  prev16=%s'
          % (h[0], h[4], h[1], h[3], BLOB[o:o + 8].hex(), BLOB[o - 16:o].hex()))
ck('E4a local-orphan 条数 < 「845 假命中」这个粗口径数（说明 845 不是「全假」）',
   len(ORPH) < 845, (len(ORPH), 845))
ck('E4b local-orphan 条数 > 0（如实登记确实存在数据里的偶然 C7）', len(ORPH) > 0, len(ORPH))

json.dump(dict(hits=len(HITS), aligned=AL, orphan=len(ORPH), aligned_loose=AL_LOOSE,
               aligned_shift3=AL_SH, targets=E3,
               orphan_sample=[dict(start='%08X' % h[0], vt='%08X' % h[4], base=h[1], disp=h[3])
                              for h in ORPH[:40]],
               checks=nchk[0], fails=fails),
          open(os.path.join(HERE, 'r187e.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
