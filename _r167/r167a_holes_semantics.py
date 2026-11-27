#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r167a_holes_semantics.py —— F24 bounds 里那 65 个「1 字节重对齐点」到底是什么东西

R166 已证：这 65 条 = plain（无 skipdata）线性解码的单字节重对齐点集合（对称差 0），
不是「某条指令内部地址」。R166 待办第 1 条留下的问题是**语义**：它们是数据、跳转表、
还是对齐填充？本脚本把它拆成三条可失败命题 + 三条反控，全部只读。

判据（全部只用 .text 的 VirtualSize blob，不碰 detail=True 全段）：
  T1 严格对齐的「代码指针表」归属：以节内 4 字节网格（(a-LO)%4==0）为准，取包含该字节的
     那个 4 字节槽，向两侧数**连续**的、值为镜像内 .text 地址的 4 字节槽，得到 run 长度。
     run>=3 判为「落在代码指针表内」。
  T2 反向引用普查：该 VA 是否作为 4 字节值出现在镜像任何节的**对齐**槽里（指针），
     以及是否作为 4 字节值出现在任何**字节偏移**上（含非对齐，宽松）。
  T3 与 a2_sites 的 calls 目标集求交（0 则说明它们不是调用目标）。
反控：
  K1 2000 个随机 .text VA 的 T1 命中率（基线）
  K2 2000 个 bounds 起点（非洞）VA 的 T1 命中率
  K3 把 65 个洞各 +1/+2/+3 平移后仍落在同一张表内吗（说明「表内」不是洞的专属性质，
     所以只能断言「洞 ⇒ 表内」不能断言「表内 ⇒ 洞」）
"""
import io, json, os, random, sys, collections
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r167/r167a_holes_semantics.json'

FAIL = 0
RES = []
def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok: FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:900]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:400]) if detail else ''))

data = io.open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    n = s.Name.decode().rstrip('\x00')
    secs.append({'name': n, 'va': IB + s.VirtualAddress, 'vsz': s.Misc_VirtualSize,
                 'raw': s.PointerToRawData, 'rsz': s.SizeOfRawData,
                 'exec': bool(s.Characteristics & 0x20000000)})
T = [s for s in secs if s['name'] == '.text'][0]
LO, VSZ, RAW, RSZ = T['va'], T['vsz'], T['raw'], T['rsz']
blob = data[RAW:RAW + VSZ]
print('== 0 段表 ==')
for s in secs:
    print('  %-9s va=%#010x vsz=%8d raw=%8d rsz=%8d exec=%s' % (s['name'], s['va'], s['vsz'], s['raw'], s['rsz'], s['exec']))
ck('B0 gamemd.exe == 4,825,360 B', len(data) == 4825360, len(data))
ck('B1 .text (raw 4096 / rsz 4,063,232 / vsz 4,060,045)',
   (RAW, RSZ, VSZ) == (4096, 4063232, 4060045), (RAW, RSZ, VSZ))

def sec_of(a):
    for s in secs:
        if s['va'] <= a < s['va'] + s['vsz']:
            return s
    return None

def rd4(a):
    """读 VA a 处的 4 字节（要求整 4 字节都落在该节 VirtualSize 内）。"""
    s = sec_of(a)
    if s is None: return None
    off = s['raw'] + (a - s['va'])
    if a - s['va'] + 4 > s['vsz'] or off + 4 > len(data): return None
    return int.from_bytes(data[off:off + 4], 'little')

def is_text_addr(v):
    return v is not None and LO <= v < LO + VSZ

# ---------------------------------------------------------------- 1 重导基线
print('\n== 1 重导基线（bounds / plain 起点 / 重对齐点）==')
J = json.load(io.open(A2, encoding='utf-8'))
bounds = [int(x, 16) for x in J['bounds']]
bS = set(bounds)
ck('B2 bounds 1,392,592 条 / 无重复 / 严格递增',
   len(bounds) == 1392592 and len(bS) == 1392592 and all(bounds[i] < bounds[i + 1] for i in range(len(bounds) - 1)),
   len(bounds))
md = Cs(CS_ARCH_X86, CS_MODE_32)
starts, resync = [], []
pos = 0
while pos < VSZ:
    base = LO + pos
    seg = blob[pos:pos + 65536]
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(seg, base):
        if a - base + sz > len(seg): break
        starts.append(a); consumed = a - base + sz
    if consumed: pos += consumed
    else: resync.append(base); pos += 1
pS = set(starts)
holes = sorted(resync)
ck('B3 plain 起点 == 1,392,527', len(starts) == 1392527, len(starts))
ck('B4 重对齐点 == 65', len(holes) == 65, len(holes))
ck('B5 bounds - plain起点 == 重对齐点集合（对称差 0）',
   sorted(bS - pS) == holes, (len(bS - pS), len(pS - bS)))

# ---------------------------------------------------------------- 2 T1 严格对齐代码指针表归属
print('\n== 2 T1 严格 4 字节网格上的「代码指针表」归属 ==')
def table_run(v):
    """以节内 4 字节网格为准，返回 (run, 槽基址, 槽内偏移)。槽基址 b 满足 (b-LO)%4==0 且 b<=v<b+4。"""
    b = LO + ((v - LO) // 4) * 4
    if not (b <= v < b + 4): return (0, None, None)
    tot = 0
    a = b
    while a >= LO and a + 4 <= LO + VSZ and is_text_addr(rd4(a)):
        tot += 1; a -= 4
    a = b + 4
    while a + 4 <= LO + VSZ and is_text_addr(rd4(a)):
        tot += 1; a += 4
    if not is_text_addr(rd4(b)): tot = 0
    return (tot, b, v - b)

T1 = {}
for v in holes:
    run, b, off = table_run(v)
    T1[v] = {'run': run, 'base': b, 'off': off}
intab = [v for v in holes if T1[v]['run'] >= 3]
print('  run>=3 的洞 %d / %d' % (len(intab), len(holes)))
print('  槽内偏移分布 :', dict(collections.Counter(T1[v]['off'] for v in holes)))
print('  run 长度分布 :', dict(sorted(collections.Counter(T1[v]['run'] for v in holes).items())))
ck('C0 run>=3 的洞 ≥ 50（「绝大多数落在代码指针表内」）', len(intab) >= 50, len(intab))
ck('C1 洞的槽内偏移只有 0..3 四种', set(T1[v]['off'] for v in holes) <= {0, 1, 2, 3},
   dict(collections.Counter(T1[v]['off'] for v in holes)))

# ---------------------------------------------------------------- 3 T2 反向引用
print('\n== 3 T2 反向引用（该 VA 作为 4 字节值出现在哪）==')
ALIGN = collections.defaultdict(list)   # 对齐槽
ANYOF = collections.defaultdict(list)   # 任意字节偏移（宽松）
for s in secs:
    buf = data[s['raw']:s['raw'] + s['rsz']]
    for off in range(0, len(buf) - 3):
        val = int.from_bytes(buf[off:off + 4], 'little')
        if val in bS or val in set(holes):
            ANYOF[val].append((s['name'], s['va'] + off))
        if off % 4 == 0:
            ALIGN[val].append((s['name'], s['va'] + off))
refA = {v: ALIGN.get(v, []) for v in holes}
refB = {v: ANYOF.get(v, []) for v in holes}
print('  作为对齐 4 字节值被引用 :', sum(1 for v in holes if refA[v]), '/', len(holes))
print('  作为任意偏移 4 字节值 :', sum(1 for v in holes if refB[v]), '/', len(holes))
ck('D0 洞被当作对齐指针引用的条数 <= 10（不是「被大量引用的表项」）',
   sum(1 for v in holes if refA[v]) <= 10, sum(1 for v in holes if refA[v]))

ct = set(int(k, 16) for k in J['calls'].keys())
holein = [v for v in holes if v in ct]
ck('D1 洞中作为 calls 目标的条数 == 0', len(holein) == 0, len(holein))

# ---------------------------------------------------------------- 4 反控
print('\n== 4 反控（基线率）==')
random.seed(20261127)
samp_rand = random.sample(range(LO, LO + VSZ), 2000)
base_rand = sum(1 for a in samp_rand if table_run(a)[0] >= 3) / 2000.0
nohole = [b for b in bounds if b not in set(holes)]
samp_bnd = random.sample(nohole, 2000)
base_bnd = sum(1 for a in samp_bnd if table_run(a)[0] >= 3) / 2000.0
rate_hole = len(intab) / float(len(holes))
print('  随机 .text VA 命中率 %.4f%%' % (base_rand * 100))
print('  bounds 起点（非洞）命中率 %.4f%%' % (base_bnd * 100))
print('  洞命中率 %.4f%%' % (rate_hole * 100))
ck('K1 洞命中率 > 随机基线 20 倍', rate_hole > 20 * base_rand, (rate_hole, base_rand))
ck('K2 洞命中率 > bounds 起点基线 20 倍', rate_hole > 20 * base_bnd, (rate_hole, base_bnd))
shift = {}
for k in (1, 2, 3):
    shift[k] = sum(1 for v in holes if table_run(v + k)[0] >= 3)
print('  洞平移 +1/+2/+3 后仍在表内 :', shift)
ck('K3 平移后仍在表内 ⇒ 「表内」不是洞的专属性质（只能断言 洞⇒表内）',
   all(shift[k] >= len(intab) - 3 for k in (1, 2, 3)), shift)

# ---------------------------------------------------------------- 5 逐个列出 10 个不在表内的洞
print('\n== 5 不在代码指针表内的洞（逐个给字节上下文）==')
out_tab = [v for v in holes if T1[v]['run'] < 3]
rows = []
for v in out_tab:
    off = RAW + (v - LO)
    ctx = {'va': hex(v), 'run': T1[v]['run'],
           'prev8': data[off - 8:off].hex(), 'next8': data[off:off + 8].hex(),
           'byte': data[off], 'dword_at_slot': hex(rd4(LO + ((v - LO) // 4) * 4) or 0)}
    rows.append(ctx)
    print('  %s run=%d prev=%s next=%s' % (ctx['va'], ctx['run'], ctx['prev8'], ctx['next8']))
ck('E0 不在表内的洞 10 条以内', len(out_tab) <= 10, len(out_tab))

# ---------------------------------------------------------------- 6 表内洞的分布（按表基址聚合）
print('\n== 6 洞按所属表聚合（前 12 张表）==')
byTable = collections.Counter(T1[v]['base'] for v in holes if T1[v]['run'] >= 3)
for b, n in byTable.most_common(12):
    print('  slot_base=%#010x  洞数=%2d  run=%d' % (b, n, T1[[v for v in holes if T1[v]['base'] == b][0]]['run']))
ck('F0 表数 <= 20（洞集中在少数几张表里）', len(byTable) <= 20, len(byTable))

obj = {'exe_bytes': len(data), 'text': {'lo': hex(LO), 'vsz': VSZ, 'raw': RAW, 'rsz': RSZ},
       'bounds': len(bounds), 'plain_starts': len(starts), 'holes': [hex(v) for v in holes],
       'holes_in_table': [hex(v) for v in intab], 'holes_out_table': rows,
       'table_run': {hex(v): T1[v]['run'] for v in holes},
       'slot_off_hist': dict(collections.Counter(T1[v]['off'] for v in holes)),
       'tables': {hex(b): n for b, n in byTable.items()},
       'align_ref_count': {hex(v): len(refA[v]) for v in holes if refA[v]},
       'anyof_ref_count': {hex(v): len(refB[v]) for v in holes if refB[v]},
       'calls_target_hits': [hex(v) for v in holein],
       'ctrl_random_tab_rate': base_rand, 'ctrl_bounds_tab_rate': base_bnd,
       'hole_tab_rate': rate_hole, 'shift_rates': shift,
       'assertions': RES, 'fail': FAIL}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1))
print('\n== 收口 ==')
print('断言 %d 条, FAIL %d' % (len(RES), FAIL))
print('saved ' + OUT)
sys.exit(1 if FAIL else 0)
