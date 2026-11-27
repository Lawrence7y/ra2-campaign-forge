#!/usr/bin/env python3
"""R146 E：大位移组的宿主对象是**静态容器**还是堆对象 —— 顺着基址寄存器回溯到根。

r146d 的一手证据（0x665650 内 73 个 large 站点）已显示：
  TypeList<H> 的 vptr 写在 0x358/0x374/0x390…（步长恰 28 = 0x1c），共 54 次；
  每次写完紧接一条 thiscall 构造调用（ecx = 位移 + 0x1c）。
  ⇒ 同一个宿主对象里有一串 28 字节的内嵌子对象。

本脚本回答「宿主是什么」：对每个 large 站点，沿 base 寄存器做**有界符号回溯**
（最多回退 60 条指令，处理 mov reg,reg / mov reg,imm / lea reg,[…] / call 清寄存器），
直到落到 IMM / LEA_GLB（静态地址）或 LOAD_STK / LOAD（堆或参数）或无法定。
判据：
  M1 large 站点里落到 IMM/LEA_GLB 的比例 > 20%（宿主是静态全局对象）。
  M2 反控：把同一回溯套到 small 组，比例应显著更低（small 是就地 this）。
  M3 若 IMM 命中，打印这些静态地址所属节与是否与已知 35 个静态容器的地址相符。
纪律：disasm_lite 64KB 流式；回溯在内存索引上做，不重复反汇编。
"""
import sys, re, json, collections, hashlib, time, bisect
sys.path.insert(0, '_r143')
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import r143lib as L

T0 = time.time()
B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
TDs, COL, VTS = B.vtset()
GEN = L.GEN
COLof = {}
for vt in VTS:
    c = B.dw(vt - 4)
    if c in COL: COLof[vt] = c
coloff = {c: B.dw(c + 4) for c in COL}
def off_of(vt): return coloff.get(COLof.get(vt))
def immv(t): return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

TOL = re.compile(r'^dword ptr \[(.+?)\](?:,(.+))?$')
def parse_mem(s):
    s = s.replace(' ', '')
    m = re.fullmatch(r'([a-z0-9]+)(?:([+-])(0x[0-9a-f]+|\d+))?', s)
    if not m: return None
    if m.group(3) is None: return m.group(1), 0
    v = int(m.group(3), 16) if m.group(3).startswith('0x') else int(m.group(3))
    return m.group(1), (-v if m.group(2) == '-' else v)

# 一次性把整段 .text 的 (va, mn, op) 存成数组（1.39M 条，内存约 1.39M*~60B ≈ 85MB，
# 在 3.3GB 机器上可接受；不保留 CsInsn 对象，只留字符串，且扫完即释放 capstone 迭代器）
ins = []
calltgt = set()
for a, sz, mn, op in B.sweep(md):
    ins.append((a, mn, op or ''))
    if mn == 'call':
        m2 = re.match(r'^(0x[0-9a-f]+)$', op or '')
        if m2: calltgt.add(int(m2.group(1), 16))
VAS = [x[0] for x in ins]
def idx(va):
    i = bisect.bisect_left(VAS, va)
    return i if i < len(VAS) and VAS[i] == va else None

sites = []
for a, mn, op in ins:
    if mn != 'mov': continue
    mt = TOL.match(op)
    if not mt: continue
    pm = parse_mem(mt.group(1))
    if not pm: continue
    base, disp = pm
    tgt = (mt.group(2) or '').strip()
    if L.RE_IMM.match(tgt) and immv(tgt) in VTS and base in GEN:
        sites.append({'va': a, 'base': base, 'disp': disp, 'vt': immv(tgt),
                      'strict': L.RE_STORE.match(op) is not None})

CLOBBER = ('eax', 'ecx', 'edx')
# 会写目的寄存器的助记符（除此之外 met 到该寄存器即视为「只读」，继续回溯）
WRITERS = {'mov', 'lea', 'pop', 'xor', 'and', 'or', 'add', 'sub', 'imul', 'mul', 'idiv', 'div',
           'shl', 'shr', 'sar', 'sal', 'rol', 'ror', 'inc', 'dec', 'neg', 'not',
           'movzx', 'movsx', 'xchg', 'setz', 'setnz', 'adc', 'sbb', 'bswap'}
def trace(va_site, base, depth=60):
    """从 va_site 往前回溯 base 的定义链，返回 (kind, va, op, hops)。"""
    i = idx(va_site)
    if i is None: return ('NONE', None, None, 0)
    cur = base; hops = 0
    j = i - 1
    while j >= 0 and hops < depth:
        a, mn, op = ins[j]
        j -= 1
        if not op: continue
        head = op.partition(',')[0].strip()
        rest = op.partition(',')[2].strip()
        if mn == 'call':
            if cur in CLOBBER: return ('CALL_CLOBBER', a, op, hops)
            hops += 1; continue
        if head != cur: continue
        if mn == 'mov':
            if L.RE_IMM.match(rest):
                return ('IMM', a, op, hops)
            m = re.fullmatch(r'dword ptr \[(.+?)\]', rest)
            if m:
                pm = parse_mem(m.group(1))
                if pm and pm[0] in ('esp', 'ebp'): return ('LOAD_STK', a, op, hops)
                return ('LOAD', a, op, hops)
            if rest in GEN:
                cur = rest; hops += 1; continue
            return ('MOV_OTHER', a, op, hops)
        if mn == 'lea':
            m = re.fullmatch(r'\[(.+?)\]', rest)
            if m:
                e = m.group(1).replace(' ', '')
                if 'esp' in e or 'ebp' in e: return ('LEA_STK', a, op, hops)
                if re.fullmatch(r'0x[0-9a-f]+', e): return ('LEA_GLB', a, op, hops)
                # lea reg,[reg2+disp]：继续追 reg2
                mm = re.fullmatch(r'([a-z0-9]+)(?:[+-](?:0x[0-9a-f]+|\d+))?', e)
                if mm and mm.group(1) in GEN: cur = mm.group(1); hops += 1; continue
                return ('LEA_OTHER', a, op, hops)
            return ('LEA_OTHER', a, op, hops)
        if mn == 'pop': return ('POP', a, op, hops)
        # 只有真正**写**该寄存器的指令才算定义点；push/test/cmp/bt 等只读，必须继续往前找
        if mn in WRITERS:
            if mn in ('xor', 'sub') and rest == cur: return ('ZERO', a, op, hops)
            return (mn.upper(), a, op, hops)
        continue
    return ('UNRESOLVED', None, None, hops)

bucket = lambda d: 'small' if d in (4, 8, 12) else 'large'
large = [s for s in sites if s['disp'] != 0 and bucket(s['disp']) == 'large']
small = [s for s in sites if s['disp'] != 0 and bucket(s['disp']) == 'small']

for s in large + small:
    k, a, op, hp = trace(s['va'], s['base'])
    s['root'] = k; s['root_va'] = a; s['root_op'] = op; s['hops'] = hp

def prof(grp):
    c = collections.Counter(s['root'] for s in grp)
    return {'n': len(grp), 'roots': c.most_common(),
            'frac': {k: round(v / len(grp), 4) for k, v in c.items()} if grp else {}}
res = {'exe_sha256': hashlib.sha256(B.data).hexdigest(), 'exe_bytes': B.N,
       'ins_count': len(ins), 'large': len(large), 'small': len(small),
       'M1_large': prof(large), 'M1_small': prof(small)}
STATIC = ('IMM', 'LEA_GLB')
res['static_large_n'] = sum(1 for s in large if s['root'] in STATIC)
res['static_small_n'] = sum(1 for s in small if s['root'] in STATIC)
res['static_large_frac'] = round(res['static_large_n'] / len(large), 4)
res['static_small_frac'] = round(res['static_small_n'] / len(small), 4)
res['static_examples'] = [[hex(s['va']), s['base'], s['disp'], s['root'], hex(s['root_va']) if s['root_va'] else None,
                           (B.sec_of(immv(s['root_op'].partition(',')[2].strip())) if s['root'] == 'IMM' else None)]
                          for s in large if s['root'] in STATIC][:12]

# M3：静态根地址的分布
addrs = []
for s in large:
    if s['root'] == 'IMM':
        addrs.append(immv(s['root_op'].partition(',')[2].strip()))
res['static_root_addrs'] = [[hex(a), B.sec_of(a), n] for a, n in collections.Counter(addrs).most_common(12)]

POS = []
def chk(n, c, v): POS.append([n, bool(c), v])
chk('严格口径 large 站点 278', sum(1 for s in large if s['strict']) == 278, sum(1 for s in large if s['strict']))
chk('回溯命中率高（UNRESOLVED 占比 < 0.35）', res['M1_large']['frac'].get('UNRESOLVED', 0) < 0.35, res['M1_large']['frac'])
chk('large 静态根比例 > small 静态根比例（判据有判别力）', res['static_large_frac'] > res['static_small_frac'],
    [res['static_large_frac'], res['static_small_frac']])
res['POS'] = POS; res['pos_fail'] = sum(1 for x in POS if not x[1])
res['elapsed_s'] = round(time.time() - T0, 1)
json.dump(res, open('/home/t628/projects/ra2-campaign-forge/_r146/r146e_root.json', 'w'), indent=1)
for x in POS: print(('PASS ' if x[1] else 'FAIL ') + x[0], x[2])
print('pos_fail', res['pos_fail'], 'elapsed', res['elapsed_s'])
