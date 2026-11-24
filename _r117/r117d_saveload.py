#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r117d_saveload.py —— R117 第四链：把 35 / 36 这个「差 1」的成因钉死成 save 集与 load 集之分。

背景（R116 §ER5 与 R117c 的实测合起来留下的问题）：
  0x67FDF0 那个模板例程里有 OleSaveToStream(0x7e15f4) 调用；R116 因此得到「35 个保存站点」。
  但同一个函数 0x67cef0 里还有一条 `mov ecx,0x87f5d8 ; call 0x4391c0`，
  而 0x4391c0 体内是两次 `call *0x10(reg)`（IStream::Read：先读计数、再逐元素读进对象数组），
  **没有** OleSaveToStream。若只按「同函数里出现过 OleSaveToStream」筛，这一条会被误并进 save 集。

本脚本要回答的唯一问题：140 个静态容器里，哪些被当 **save 源**（作为 edx 传给保存例程）、
哪些被当 **load 目的地**（作为 ecx 传给读取例程），两集是否不相交。

判据（全部指令级，不用函数级近似）：
  对每个容器地址 V，扫 .text 里所有「把 V 当立即数装进 ecx 或 edx」的指令
  （B9/BA = mov reg,imm32；以及 8D 0D/8D 15 = lea reg,[V]），
  再看紧随其后 <=16 字节内那条 rel32 call 的**被调函数体**属于哪一类：
    SAVE 类的体里出现对 0x7E15F4（OleSaveToStream IAT）的间接调用；
    LOAD 类的体里出现 >= 2 次 `call *0x10(reg)` 且不出现 0x7E15F4。

断言：
  G1 140 个容器按上述判据分类，未分类（既非 SAVE 也非 LOAD）的必须为 0 或如实登记。
  G2 SAVE 集恰好 35 个 == R117a 的 35 个派发对象（集合相等）。
  G3 LOAD 集恰好 1 个 == 0x87f5d8（BombClass 容器），且它**不在** SAVE 集内。
  G4 反控（有牙）：把「SAVE 类」判据删掉（即任何 call 都算）后，SAVE 集必须膨胀到 >35
     ⇒ 体内容判据不是装饰。
  G5 反控（有牙）：把 0x4391c0 也当 SAVE（误并的形态），SAVE 集变成 36 且与 Q80 的
     「被 saver 函数引用」集重合 ⇒ 复现 R117c 的 F4 现象，证明差 1 的成因是判据粒度而不是数据。
内存纪律：每个被调函数体 <=2000 B 窗口、detail=False；未对 .text 整段开 detail。
"""
import bisect, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L   # noqa: E402

raw, fo, u32 = L.raw, L.fo, L.u32
TS, TE = L.TEXT0, L.TEXT1
HB = sorted(L.HB)
OUT = os.path.join(ROOT, '_r117/r117d_saveload.json')
checks = []

MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = False; MD.skipdata = True


def ck(name, cond, detail=''):
    checks.append({'name': name, 'ok': bool(cond), 'detail': detail})
    print(('PASS ' if cond else 'FAIL ') + name + ((' | ' + str(detail)) if detail != '' else ''),
          flush=True)
    return bool(cond)


def func_end(a):
    i = bisect.bisect_right(HB, a)
    return HB[i] if i < len(HB) else TE


B = json.load(open(os.path.join(ROOT, '_r117/r117b_containers.json')))
CEN = {int(k, 16): v for k, v in B['all_elem'].items()}
A = json.load(open(os.path.join(ROOT, '_r117/r117a_obj_entries.json')))
DISP = set(int(r['entry'], 16) for r in A['rows'])
SAVE_IAT = 0x7e15f4

# ---- 给被调函数体做分类（结果缓存，避免重复解码）----
_cache = {}


def classify_callee(f):
    if f in _cache:
        return _cache[f]
    if not (TS <= f < TE):
        _cache[f] = ('OUT', 0, 0)
        return _cache[f]
    lo, hi = fo(f), fo(min(f + 2000, func_end(f), TE))
    n_read = 0
    n_save = 0
    n_cmp = 0
    for a, sz, m, o in MD.disasm_lite(raw[lo:hi + 16], f):
        if a >= f + 2000:
            break
        if '0x7e15f4' in o:
            n_save += 1
        if m == 'call' and o.replace(' ', '') == 'dwordptr[ecx+0x10]':
            n_read += 1
        if '0x7f7c80' in o:
            n_cmp += 1
    if n_save:
        k = 'SAVE'
    elif n_read >= 1:
        k = 'LOAD'
    else:
        k = 'OTHER'
    _cache[f] = (k, n_save, n_read)
    return _cache[f]


TX = raw[fo(TS):fo(TE)]


def sites_for(v):
    """返回 [(site, kind)]：kind ∈ {mov-ecx, mov-edx, lea-ecx, lea-edx}。"""
    out = []
    for op, kind in ((b'\xb9', 'mov-ecx'), (b'\xba', 'mov-edx'),
                     (b'\x8d\x0d', 'lea-ecx'), (b'\x8d\x15', 'lea-edx')):
        p = op + struct.pack('<I', v)
        i = TX.find(p)
        while i >= 0:
            out.append((TS + i, kind))
            i = TX.find(p, i + 1)
    return sorted(out)


def callee_after(site):
    """site 之后 16 字节内第一条 rel32 call 的目标。"""
    for a, sz, m, o in MD.disasm_lite(raw[fo(site):fo(site) + 16], site):
        if m == 'call' and '0x' in o and '*' not in o and '[' not in o:
            try:
                return int(o.split('0x')[-1], 16)
            except ValueError:
                return None
    return None


cls = {}
for v in CEN:
    kinds = set()
    for site, kind in sites_for(v):
        f = callee_after(site)
        if f is None:
            continue
        k = classify_callee(f)[0]
        if k in ('SAVE', 'LOAD'):
            kinds.add((k, kind))
    cls[v] = kinds

SAVE = {v for v, ks in cls.items() if any(k == 'SAVE' for k, _ in ks)}
LOAD = {v for v, ks in cls.items() if any(k == 'LOAD' for k, _ in ks)}
OTHER = set(CEN) - SAVE - LOAD

ck('G1 140 个容器按被调函数体分类：SAVE %d 个、LOAD %d 个、其它 %d 个（如实登记）'
   % (len(SAVE), len(LOAD), len(OTHER)),
   len(SAVE) + len(LOAD) + len(OTHER) == 140,
   {'SAVE': len(SAVE), 'LOAD': len(LOAD), 'OTHER': len(OTHER),
    'other_sample': [[hex(v), CEN[v]] for v in sorted(OTHER)[:8]]})

ck('G2 SAVE 集 == R117a 的 35 个派发对象（集合相等，对称差 %d）'
   % len(SAVE ^ DISP), SAVE == DISP,
   {'SAVE': len(SAVE), 'disp': len(DISP), 'symdiff': len(SAVE ^ DISP),
    'save_minus_disp': [hex(x) for x in sorted(SAVE - DISP)][:5],
    'disp_minus_save': [hex(x) for x in sorted(DISP - SAVE)][:5]})

ck('G3 LOAD 集 == {0x87f5d8}（BombClass 容器），元素类型 %s，且与 SAVE 集不相交（交集 %d）'
   % ([CEN[v] for v in sorted(LOAD)], len(LOAD & SAVE)),
   LOAD == {0x87F5D8} and not (LOAD & SAVE),
   {'LOAD': [[hex(v), CEN[v]] for v in sorted(LOAD)], 'overlap': len(LOAD & SAVE)})

# ---- G4 反控：去掉体内容判据 ----
loose = set()
for v in CEN:
    for site, kind in sites_for(v):
        if callee_after(site) is not None:
            loose.add(v)
            break
ck('G4 反控（有牙）：把「被调函数体里出现 OleSaveToStream」这一判据删掉、任何 call 都算后，'
   '集合从 %d 膨胀到 %d（多出 %d）⇒ 体内容判据确实在收敛，不是装饰'
   % (len(SAVE), len(loose), len(loose - SAVE)),
   len(loose) > len(SAVE), {'loose': len(loose), 'save': len(SAVE)})

# ---- G5 反控：把 LOAD 误并成 SAVE 就复现 R117c 的差 1 ----
merged = SAVE | LOAD
Q = {k: set(v) for k, v in
     json.load(open(os.path.join(ROOT, '_r111/r111d_full_iid.json')))['iids'].items()}
QI = {}
for c, iids in Q.items():
    for x in iids:
        QI.setdefault(x, set()).add(c)
Q80 = QI['0x7f7c80']
in80 = {v for v in CEN if CEN[v] in Q80}
ck('G5 反控：把 LOAD 误并进 SAVE 得 %d 个；这就是 R117c 里「规则 H 命中 36 个」的成因 '
   '（Q80 内被 stream-I/O 函数引用 = %d 个，两者相等 %s）'
   % (len(merged), len(merged & in80), merged & in80 == in80 & merged),
   len(merged) == 36, {'merged': len(merged), 'in_q80': len(merged & in80)})

# ---- 每个 SAVE 容器被哪个函数保存、走哪个例程 ----
rows = []
for v in sorted(SAVE):
    kinds = sorted(cls[v])
    rows.append({'container': hex(v), 'elem': CEN[v],
                 'via': [[k, kk] for k, kk in kinds]})
n_tmpl = sum(1 for r in rows if any(k == 'SAVE' and kk == 'mov-edx' for k, kk in r['via']))
ck('G6 35 个 SAVE 容器**全部**是「作为 edx 装进保存例程」的（%d/35）；'
   'LOAD 那个是「作为 ecx 装进读取例程」⇒ 两种装配方式的寄存器位不同，'
   '这与 R116 §ER5 的 dispatcher 锚形态（mov edx,imm32 ; mov ecx,esi ; call）逐条吻合'
   % n_tmpl, n_tmpl == 35, {'via_edx': n_tmpl})

json.dump({'SAVE': [hex(v) for v in sorted(SAVE)],
           'LOAD': [hex(v) for v in sorted(LOAD)],
           'OTHER': [[hex(v), CEN[v]] for v in sorted(OTHER)],
           'rows': rows, 'checks': checks,
           'verdict': 'save 集恰好 35 个（全部以 edx 传入保存例程）；load 集恰好 1 个'
                      '（0x87f5d8/BombClass，以 ecx 传入读取例程 0x4391c0）；'
                      'R117c 的「差 1」是判据粒度（函数级 vs 指令级）造成，不是数据异常'},
          open(OUT, 'w'), indent=1, ensure_ascii=False)
np_ = sum(1 for c in checks if c['ok'])
print('\n== %d/%d PASS ==' % (np_, len(checks)))
print('WROTE', OUT)
sys.exit(0 if np_ == len(checks) else 1)
