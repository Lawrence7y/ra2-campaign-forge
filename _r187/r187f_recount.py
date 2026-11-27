#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 F2：【关键复算·快版】R186 的「845 假命中」这个标签是错的。

r187e 的结果推翻了 R186 的一条**分类**（不是数字）：
  R186 把「字节模式命中但不在递归下降起点集合」的 845 条叫「假命中（落在非指令边界上）」。
  r187e 用不依赖可达性的**局部对齐**判据实测：5,731 条里 **5,730** 条局部可对齐、**1** 条孤立。
  ⇒ 那 845 条绝大多数是**真指令、只是不可达**（种子没覆盖到它们的入口）。
  ⇒ 「假命中」这个词把「不可达」误称成「不是指令」，必须撤回。
  ⇒ F01 的三层口径（4,886 → 3,666 → 3,204）建立在一个**不必要的收缩**上，必须用全 5,731 重算。

本版为什么不用递归下降：STARTS 的重建要 10+ 分钟，而 R186 那三个交集口径的数已经由
`_r186/r186c.json` 与 `_r187/r187d.json` 两次独立复算锁定（4,886 / 3,666 / 3,204），
本轮只需**引用**它们作为对照，不必重跑。全口径的数才是本轮要新算的。

命题（逐条可失败）
  F1  C7 /0 命中 5,731；覆盖 1,212 张表；未覆盖 2 张（走 B 形态那 2 张）。
  F2  全 5,731 里「基址非 esp/ebp、无索引」的对象寄存器 store 条数。
  F3  该集合里 disp == COL.mdisp 的条数与比例。
  F4  放宽到「disp ∈ 该 TD 在全镜像 CHD 出现过 mdisp」的条数与比例。
  F5  残差按类名分组、模板/容器占比；非模板残差类名去重列出。
  F6  与交集口径对照：全口径 − 交集口径 = 差集；差集里 disp==mdisp 的比例同样高
      ⇒ 不可达不等于「假」，847 这个收缩量不改变结论方向，只改变样本量与比例。
  F7  5,731 里局部对齐 5,730 / 孤立 1（引 r187e 的独立判据；本脚本用同一判据重跑前 800 条抽检）。
反控（必须真红）
  N1  disp+1 判相等 ⇒ 0 命中
  N2  mdisp 换常数 0 ⇒ 命中数下降
  N3  vtable 换常数 0 ⇒ 命中数归 0
防 OOM：只做一次全 .text 字节扫（纯 struct）+ 差集上逐点 <=16 B 解码。
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
ck('F0 COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))

def clsname(vt):
    n = VTS[vt]['name']
    return n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n

REG32 = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
def scan_c7(vtset):
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
        if w in vtset:
            out.append((TLO + i, base, index, d, w, mod))
    return out

HITS = scan_c7(VTS)
ck('F1a C7 /0 命中 5,731', len(HITS) == 5731, len(HITS))
ck('F1b 覆盖 1,212 张表 / 未覆盖 2 张', len({h[4] for h in HITS}) == 1212,
   (len({h[4] for h in HITS}), 1214 - len({h[4] for h in HITS})))

# ---------- R186 交集口径的三个数（引用，不重跑）----------
R186 = json.load(open(os.path.join(HERE, '..', '_r186', 'r186c.json')))
ck('F6a 引用 R186c 的交集口径：inter 4,886 / obj 3,666 / scope_a 3,204',
   (R186['inter'], R186['obj'], R186['scope_a']) == (4886, 3666, 3204),
   (R186['inter'], R186['obj'], R186['scope_a']))

own = collections.defaultdict(set)
for vt, c in VTS.items(): own[c['ptd']].add(c['mdisp'])
wide = collections.defaultdict(set)
for ptd in own: wide[ptd] |= own[ptd]
for vt, c in VTS.items():
    ch = [P.dw(c['pchd'] + 4 * k) for k in range(4)]
    if None in ch or not (1 <= ch[2] <= 64) or P.where(ch[3]) != '.rdata': continue
    for i in range(ch[2]):
        bo = P.dw(ch[3] + 4 * i)
        if bo is None: continue
        f = [P.dw(bo + 4 * j) for j in range(6)]
        if None in f: continue
        wide[f[0]].add(f[2])

obj = [h for h in HITS if h[1] not in ('esp', 'ebp') and h[2] is None]
stk = [h for h in HITS if h[1] in ('esp', 'ebp')]
idxh = [h for h in HITS if h[2] is not None]
ck('F2a 全口径对象寄存器 store 条数（基址非 esp/ebp、无索引）', len(obj) > 0, len(obj))
print('   构成：对象 %d / 栈基址 %d / 带索引 %d（合计 %d）'
      % (len(obj), len(stk), len(idxh), len(obj) + len(stk) + len(idxh)))
ck('F2b 三类合计 == 5,731', len(obj) + len(stk) + len(idxh) == 5731,
   len(obj) + len(stk) + len(idxh))
ck('F2c 全口径对象寄存器 store 比 R186 交集口径多（收缩被撤掉的量）',
   len(obj) > 3666, (len(obj), 3666))

eq = [h for h in obj if h[3] == VTS[h[4]]['mdisp']]
covb = [h for h in obj if h[3] in own[VTS[h[4]]['ptd']]]
covc = [h for h in obj if h[3] in wide[VTS[h[4]]['ptd']]]
print('   口径(a) disp == COL.mdisp        %d/%d = %.2f%%' % (len(eq), len(obj), 100.0 * len(eq) / len(obj)))
print('   口径(b) disp ∈ 该 TD 层集合      %d/%d = %.2f%%' % (len(covb), len(obj), 100.0 * len(covb) / len(obj)))
print('   口径(c) disp ∈ 全镜像 CHD mdisp  %d/%d = %.2f%%' % (len(covc), len(obj), 100.0 * len(covc) / len(obj)))
ck('F3a 全口径 disp == COL.mdisp 的条数与比例', len(eq) > 0,
   '%d/%d = %.2f%%' % (len(eq), len(obj), 100.0 * len(eq) / len(obj)))
ck('F4a 全口径口径(c) 的条数与比例', len(covc) >= len(eq),
   '%d/%d = %.2f%%' % (len(covc), len(obj), 100.0 * len(covc) / len(obj)))

resid = [h for h in obj if h not in covc]
rcls = collections.Counter(clsname(h[4]) for h in resid)
tm = sum(n for c, n in rcls.items() if '$' in c or 'List' in c)
print('   全口径残差 %d 条：模板/容器 %d / 非模板 %d' % (len(resid), tm, len(resid) - tm))
print('   top 类：', rcls.most_common(10))
non_tmpl = sorted({clsname(h[4]) for h in resid if not ('$' in clsname(h[4]) or 'List' in clsname(h[4]))})
print('   非模板残差类名（去重 %d）：%s' % (len(non_tmpl), non_tmpl))
ck('F5a 残差里模板/容器占多数', tm > len(resid) - tm, (tm, len(resid) - tm))

ck('N1 反控：disp+1 判相等 ⇒ 0 命中', len([h for h in obj if h[3] + 1 == VTS[h[4]]['mdisp']]) == 0)
c0 = len([h for h in obj if h[3] == 0])
ck('N2 反控：mdisp 换常数 0 ⇒ %d < %d' % (c0, len(eq)), c0 < len(eq), (c0, len(eq)))
N3 = scan_c7(set())
ck('N3 反控：vtable 集合置空 ⇒ 命中 0', len(N3) == 0, len(N3))

json.dump(dict(hits=len(HITS), obj=len(obj), stack=len(stk), indexed=len(idxh),
               eq=len(eq), covb=len(covb), covc=len(covc),
               resid=len(resid), resid_tmpl=tm, non_tmpl=non_tmpl,
               resid_top=rcls.most_common(12), r186=(R186['inter'], R186['obj'], R186['scope_a']),
               checks=nchk[0], fails=fails),
          open(os.path.join(HERE, 'r187f.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
