# -*- coding: utf-8 -*-
"""R219 m6：m4+m5 合并修正版（修两处自错）。

自错 E1（m5）：sweep 忘了 md.skipdata=True，disasm_lite 遇非法字节即停，
              只解出 155215 条 / 7 chunks（末 0x46f59d），与 R218 的 1394120 相差 10 倍。
自错 E2（m4）：trace() 在 from_zero/from_pop 分支返回字符串而非二元组，导致解包崩溃。

本脚本口径 = R218/R219-m3 定稿口径：
  - md.skipdata = True
  - 逐字节 resync：解码失败 pos += 1
  - 跨 chunk 无特殊处理（逐字节推进天然跨边界）
产出：
  [A] sweep 规模与末指令（正控 1394120 / 0x7e0ffd）
  [B] 接受集 [reg+disp] call/jmp（无索引、排除 esp）计数 + esp 计数 + 负 disp 计数
  [C] s>=256 计数 / distinct；UnitClass 域 256<=s<344 计数
  [D] domain 位点按调用方函数归并（CC 规则 256B），报函数数 / unresolved / top10
  [E] 11 处残余 C_neither 位点的 base 溯源（窗口 200，修好的 trace）
  [F] 反控 1：固定 64KB 重启 sweep（坏口径）计数必须 << 正确口径
  [G] 反控 2：含 esp 计数必须 > 排除 esp 计数
正控：0x414471 在接受集；0x7bea07 在 s>=256 集；0x414471 的 base 溯源必须是 from_vtable_load。
"""
import sys, struct, collections, json, re
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
md.skipdata = True                      # <<< E1 修复
T = P.B['.text']; LO, RAWOFF, RAWSZ = T['lo'], T['rawptr'], T['rawsize']
BASE_OFF = LO - RAWOFF
raw = P.RAW[RAWOFF:RAWOFF + RAWSZ]

insns = []
pos = 0
while pos < len(raw):
    got = False
    for a, sz, mn, ops in md.disasm_lite(raw[pos:pos + 16], LO + pos):
        insns.append((a, mn, ops)); pos += sz; got = True; break
    if not got:
        pos += 1
print('[A] sweep insns=%d  last=%#x   (R218/R219 target 1394120 / 0x7e0ffd)'
      % (len(insns), insns[-1][0]))
IDX = {a: i for i, (a, _, _) in enumerate(insns)}

# ---------- B ----------
MEM_RE = re.compile(r'\bptr\s*\[([^\]]+)\]', re.I)
POS = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?$', re.I)
NEGD = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp|esp)\s*-\s*(0x[0-9a-f]+|\d+)$', re.I)
def parse(inner):
    s = inner.strip()
    m = POS.match(s)
    if m: return m.group(1).lower(), (int(m.group(2), 0) if m.group(2) else 0)
    m = NEGD.match(s)
    if m: return m.group(1).lower(), -int(m.group(2), 0)
    return None, None

acc, esp_acc, neg_acc, indexed = [], [], [], 0
for i, (a, mn, ops) in enumerate(insns):
    if mn not in ('call', 'jmp'): continue
    mm = MEM_RE.search(ops)
    if not mm: continue
    inner = mm.group(1)
    if '*' in inner:
        indexed += 1; continue
    b, d = parse(inner)
    if b is None: continue
    if d < 0: neg_acc.append((a, ops)); continue
    if b == 'esp': esp_acc.append(a); continue
    acc.append((i, a, b, d))
print('\n[B] accepted (no-index, esp excluded) = %d   esp = %d   incl-esp = %d   neg-disp = %d   indexed(excluded) = %d'
      % (len(acc), len(esp_acc), len(acc) + len(esp_acc), len(neg_acc), indexed))
print('    (R218 报 18930 / 18935；m2 口径 18933；card B 报 15472 —— 三方须对齐口径)')
print('    POSITIVE CONTROL 0x414471 accepted: %s' % any(x[1] == 0x414471 for x in acc))
print('    neg-disp sites:', [(hex(a), o) for a, o in neg_acc])

hi = [x for x in acc if x[3] >= 0x400]
print('\n[C] s>=256 = %d  distinct_s = %d   (R218 931/91 ; card B 744/82)'
      % (len(hi), len(set(x[3] // 4 for x in hi))))
dom = [x for x in hi if 256 <= x[3] // 4 < 344]
print('    UnitClass domain 256<=s<344 = %d   (R218 925 ; card B 739)' % len(dom))
print('    POSITIVE CONTROL 0x7bea07 in hi: %s' % any(x[1] == 0x7bea07 for x in hi))
print('    top s:', collections.Counter(x[3] // 4 for x in dom).most_common(6))

# ---------- D ----------
def func_start(va, window=256):
    o = P.r2o(va); lo = max(RAWOFF, o - window); i = o - 1
    while i > lo:
        if P.RAW[i - 1] == 0xCC and P.RAW[i] == 0xCC:
            j = i
            while j < o and P.RAW[j] == 0xCC: j += 1
            return j + BASE_OFF, 'cc'
        i -= 1
    i = o - 1
    while i > lo:
        if P.RAW[i] == 0xC3 and P.RAW[i + 1] != 0xCC:
            return i + 1 + BASE_OFF, 'ret'
        i -= 1
    return None, 'unresolved'

grp = collections.Counter(); kinds = collections.Counter()
pers = collections.defaultdict(set)
for i, a, b, d in dom:
    f, k = func_start(a); kinds[k] += 1
    if f: grp[f] += 1; pers[f].add(d // 4)
print('\n[D] domain grouping: funcs=%d unresolved=%d kinds=%s  (card B 234 / 436 / {unresolved:436,ret:303})'
      % (len(grp), kinds['unresolved'], dict(kinds)))
print('    top10 funcs:', [(hex(f), c) for f, c in grp.most_common(10)])
print('    max distinct s per func:', sorted(((len(v), hex(k)) for k, v in pers.items()), reverse=True)[:5])

# ---------- E ----------
GRP = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')
BRE = re.compile(r'^(eax|ebx|ecx|edx|esi|edi|ebp)(?:\s*\+\s*(0x[0-9a-f]+|\d+))?$', re.I)
def base_of(ops):
    mm = MEM_RE.search(ops)
    if not mm: return None, None
    m = BRE.match(mm.group(1).strip())
    if not m: return None, None
    return m.group(1).lower(), (int(m.group(2), 0) if m.group(2) else 0)

def trace(idx, base, win=200):
    lo = max(0, idx - win)
    for a2, m2, o2 in reversed(insns[lo:idx]):
        dst = o2.split(',')[0].strip() if ',' in o2 else o2.strip()
        if m2 == 'pop':
            if o2.strip() == base: return 'from_pop', '%#x pop %s' % (a2, o2)
            continue
        if m2 in ('inc', 'dec'):
            if dst == base: return 'from_%s' % m2, '%#x %s %s' % (a2, m2, o2)
            continue
        if m2 not in ('mov', 'lea', 'xor', 'and', 'or', 'add', 'sub', 'movzx', 'movsx'): continue
        if dst != base: continue
        src = o2.split(',', 1)[1].strip() if ',' in o2 else ''
        if m2 == 'mov' and 'dword ptr [' in src:
            bb, dd = base_of(src)
            if bb in GRP:
                return ('from_vtable_load' if dd == 0 else 'from_indirect_ld'), '%#x %s %s' % (a2, m2, o2)
            return 'from_mem_other', '%#x %s %s' % (a2, m2, o2)
        if m2 == 'mov' and re.match(r'^0x[0-9a-f]+$', src, re.I):
            return 'from_imm', '%#x %s %s' % (a2, m2, o2)
        if m2 == 'lea':
            return 'from_lea', '%#x %s %s' % (a2, m2, o2)
        if m2 == 'xor' and src == base:
            return 'from_zero', '%#x %s %s' % (a2, m2, o2)
        return 'from_%s' % m2, '%#x %s %s' % (a2, m2, o2)
    return 'not_found', None

RESID = [0x43e2ff, 0x43e36f, 0x43e40a, 0x43e5c6, 0x43e759,
         0x50d97e, 0x519286, 0x759f90, 0x759fa0, 0x75a3c9, 0x75a3d1]
print('\n[E] residual C_neither (%d) base provenance:' % len(RESID))
rows = []; kcnt = collections.Counter()
for a in RESID:
    i = IDX[a]; _, mn, ops = insns[i]
    b, d = base_of(ops)
    kind, ev = trace(i, b)
    kcnt[kind] += 1
    print('   %#x %-26s base=%s disp=0x%03x -> %-16s %s' % (a, mn + ' ' + ops, b, d, kind, ev))
    rows.append(dict(addr=hex(a), insn=mn + ' ' + ops, base=b, disp=hex(d), kind=kind, ev=ev))
print('    kind summary:', dict(kcnt))

# ---------- F / G ----------
CHUNK = 0x10000
bad = 0
for off in range(RAWOFF, RAWOFF + RAWSZ, CHUNK):
    buf = P.RAW[off:off + CHUNK]
    for a, sz, mn, ops in md.disasm_lite(buf, LO + (off - RAWOFF)):
        bad += 1
print('\n[F] NEG CONTROL bad fixed-64KB restart sweep = %d  (must be << %d)' % (bad, len(insns)))
print('[G] NEG CONTROL incl-esp %d > excl-esp %d : %s'
      % (len(acc) + len(esp_acc), len(acc), len(acc) + len(esp_acc) > len(acc)))

json.dump(dict(sweep=len(insns), last=hex(insns[-1][0]), acc=len(acc), esp=len(esp_acc),
               neg=len(neg_acc), indexed=indexed, hi=len(hi),
               hi_s=len(set(x[3] // 4 for x in hi)), dom=len(dom),
               funcs=len(grp), unresolved=kinds['unresolved'], kinds=dict(kinds),
               resid=rows, resid_kinds=dict(kcnt), bad_sweep=bad),
          open('/home/t628/projects/ra2-campaign-forge/_r219/m6.json', 'w'), indent=1)
print('\n[done] -> _r219/m6.json')
