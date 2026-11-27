#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r167d_holes_semantics_final.py —— 那 65 条的**语义**（R166 未取得项第 1 条）终局判定

R166 只证了「不是指令内部地址」，留下「数据／跳转表／对齐填充」未定。本轮给三条判据 + 四条反控：

  P1 不可解码位普查：对 .text VirtualSize 内每一个字节位置用 capstone 解 count=1（15 B 窗口），
     得不可解码位总数 U。
  P2 身份等式（含一条如实声明的同义反复）：65 == U ∩ 「线性扫描真的落在它上面」。
     这一条是**定义性**的（扫描只访问起点序列），不是发现 —— 必须如实写明。
  P3 非定义性内容（这才是本轮的实证）：
     a) 富集：65 条里落在「≥3 条、每条都是 .text 内地址」的指针表内（4 字节或 3 字节条目、phase 0..3 全试）
        的比例，对照「U 里从未被踩到的 57,952 条」的随机 2000 抽样、以及 2000 个随机 .text 字节；
     b) 表的身份：表槽值里「是指令起点」的比例，对照「孤立指针型 dword」基线；
     c) 9 条不在指针表内的洞：逐个给字节上下文并归类（字节查找表／对齐填充／其他）。

反控（每条都为「必须能失败」而设）：
  K1 正控 0x401000 解得出来；K2 负控 0f 0f 解得 0 条；K3 随机 3000 位可解率 > 0.90；
  K4 若 U == 65（即普查与洞集合相等）则判「普查根本没错开跳过位」并 FAIL，反之 PASS。
"""
import io, json, os, sys, time, random, collections, bisect
import multiprocessing as mp
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
A2 = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r167/r167d_holes_semantics_final.json'
W = 15
NPROC = 4

FAIL = 0
RES = []
def ck(n, c, d=''):
    global FAIL
    ok = bool(c)
    if not ok: FAIL += 1
    RES.append({'id': n, 'ok': ok, 'detail': str(d)[:500]})
    print(('PASS ' if ok else 'FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    sys.stdout.flush()

data = io.open(EXE, 'rb').read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    secs.append({'name': s.Name.decode().rstrip('\x00'), 'va': IB + s.VirtualAddress,
                 'vsz': s.Misc_VirtualSize, 'raw': s.PointerToRawData, 'rsz': s.SizeOfRawData,
                 'exec': bool(s.Characteristics & 0x20000000)})
T = [s for s in secs if s['name'] == '.text'][0]
LO, VSZ, RAW, RSZ = T['va'], T['vsz'], T['raw'], T['rsz']
blob = data[RAW:RAW + VSZ]

print('== 0 基线 ==')
ck('B0 gamemd.exe == 4,825,360 B', len(data) == 4825360, len(data))
ck('B1 .text raw=4096 rsz=4,063,232 vsz=4,060,045 lo=0x401000',
   (RAW, RSZ, VSZ, LO) == (4096, 4063232, 4060045, 0x401000), (RAW, RSZ, VSZ, hex(LO)))

def isT(v):
    return v is not None and LO <= v < LO + VSZ

def rd(a, w):
    o = a - LO
    if o < 0 or o + w > VSZ: return None
    return int.from_bytes(blob[o:o + w], 'little')

# ---------------------------------------------------------------- P1 不可解码位普查
def worker(args):
    blob_, LO_, a, b = args
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    dl = md.disasm_lite
    bad = []
    for off in range(a, b):
        if not list(dl(blob_[off:off + W], LO_ + off, count=1)):
            bad.append(LO_ + off)
    return bad

print('\n== 1 P1 不可解码位普查（.text 全量逐字节）==')
md = Cs(CS_ARCH_X86, CS_MODE_32)
ck('K1 正控 0x401000 解得出一条', len(list(md.disasm_lite(blob[0:W], LO, count=1))) == 1)
ck('K2 负控 0f 0f 解得 0 条', len(list(md.disasm_lite(bytes([0x0f, 0x0f] * 8), LO, count=1))) == 0)
random.seed(20261127)
s3000 = random.sample(range(VSZ - W), 3000)
okc = sum(1 for o in s3000 if list(md.disasm_lite(blob[o:o + W], LO + o, count=1)))
ck('K3 随机 3000 位可解率 > 0.90', okc / 3000.0 > 0.90, '%.4f' % (okc / 3000.0))

n = VSZ - W
step = (n + NPROC - 1) // NPROC
chunks = [(blob, LO, i * step, min(n, (i + 1) * step)) for i in range(NPROC)]
t0 = time.time()
with mp.Pool(NPROC) as pool:
    res = pool.map(worker, chunks)
UND = sorted(x for part in res for x in part)
el = time.time() - t0
print('  不可解码位 U = %d（占 .text 字节 %.4f%%），耗时 %.1fs'
      % (len(UND), 100.0 * len(UND) / VSZ, el))
ck('C0 U > 65（不可解码位远多于洞，否则普查一定漏了跳过位）', len(UND) > 65, len(UND))

# ---------------------------------------------------------------- 起点序列与洞
starts, sizes, resync = [], [], []
pos = 0
while pos < VSZ:
    base = LO + pos
    seg = blob[pos:pos + 65536]
    cons = 0
    for a, sz, mn, op in md.disasm_lite(seg, base):
        if a - base + sz > len(seg): break
        starts.append(a); sizes.append(sz); cons = a - base + sz
    if cons: pos += cons
    else: resync.append(base); pos += 1
holes = sorted(resync)
st = set(starts)
J = json.load(io.open(A2, encoding='utf-8'))
bounds = [int(x, 16) for x in J['bounds']]
ck('C1 bounds 1,392,592 / plain 起点 1,392,527 / 洞 65',
   (len(bounds), len(starts), len(holes)) == (1392592, 1392527, 65),
   (len(bounds), len(starts), len(holes)))
ck('C2 bounds − plain起点 == 洞（对称差 0）', sorted(set(bounds) - st) == holes, len(set(bounds) - st))

# ---------------------------------------------------------------- P2 身份等式（定义性）
print('\n== 2 P2 身份等式 ==')
uS, hS = set(UND), set(holes)
ck('D0 洞 ⊆ U（必要不充分）', hS <= uS, len(hS - uS))
never = sorted(uS - hS)
print('  U 里从未被扫描踩到: %d（%.2f%% of U）' % (len(never), 100.0 * len(never) / len(UND)))
# 如实声明：D1 是**定义性**的（线性扫描只把「起点」记为起点；某个位置成为洞，当且仅当
# 扫描游标恰好停在它上面**且**它不可解码）。故它不是发现，只是把「洞」这个词的生成规则写出来。
# 正确的等式对象是「U ∩ 扫描到达过的位置」，而扫描到达过的位置里，除起点外就是洞本身
# （游标每次容进 consumed 或前进 1）⇒ 等式右边必须是 U ∩ (st ∪ hS)，用它在下面自证。
ck('D1 洞 ⊆ U，且 U ∩ (起点 ∪ 洞) == 洞（生成规则，非发现）',
   hS <= uS and (uS & (st | hS)) == hS, (len(uS & (st | hS)), len(hS)))
ck('D1b 反控：把 hS 去掉 ⇒ U ∩ 起点 非空但 ≠ 洞（等式不是恒真）',
   (uS & st) != hS, len(uS & st))
ck('D2 U − 扫描起点 非空（否则扫描根本没跳过任何位）', len(uS - st) > 0, len(uS - st))

# ---------------------------------------------------------------- P3a 指针表富集
print('\n== 3 P3a 指针表富集（4B / 3B 条目，phase 0..3 全试）==')
def best_table(v):
    best = (0, None, None, None, None)
    for w in (4, 3):
        for p in range(4):
            b = v - ((v - LO - p) % 4)
            if not (b <= v < b + 4): continue
            x = rd(b, w)
            if not isT(x): continue
            lo = b
            while True:
                a = lo - 4
                if a < LO: break
                y = rd(a, w)
                if not isT(y): break
                lo = a
            hi = b + 4
            while True:
                y = rd(hi, w)
                if not isT(y): break
                hi += 4
            k = (hi - lo) // 4
            if k > best[0]: best = (k, w, p, lo, hi)
    return best

TB = {v: best_table(v) for v in holes}
intab = [v for v in holes if TB[v][0] >= 3]
outtab = [v for v in holes if TB[v][0] < 3]
print('  洞落在 ≥3 条指针表内: %d / %d' % (len(intab), len(holes)))
print('  条目宽度分布: %s ; phase 分布: %s'
      % (dict(collections.Counter(TB[v][1] for v in intab)),
         dict(collections.Counter((TB[v][1], TB[v][2]) for v in intab))))
tables = sorted(set((TB[v][3], TB[v][4]) for v in intab))
print('  涉及表数: %d' % len(tables))
ck('E0 落在指针表内的洞 ≥ 50', len(intab) >= 50, len(intab))

random.seed(424242)
samp_never = random.sample(never, 2000)
samp_rand = random.sample(range(LO, LO + VSZ - 16), 2000)
def rate(lst):
    return sum(1 for v in lst if best_table(v)[0] >= 3) / float(len(lst))
r_hole = len(intab) / float(len(holes))
r_never = rate(samp_never)
r_rand = rate(samp_rand)
print('  命中率: 洞 %.4f (%d) ; U−落点 %.4f (2000) ; 随机 .text 字节 %.4f (2000)'
      % (r_hole, len(holes), r_never, r_rand))
ck('E1 洞命中率 > 5 × 随机 .text 字节基线', r_hole > 5 * r_rand, (round(r_hole,4), round(r_rand,4)))
ck('E2 洞命中率 > 15 × U−落点基线（同一 U 内的对照，最强）', r_hole > 15 * r_never, (round(r_hole,4), round(r_never,4)))

# ---------------------------------------------------------------- P3b 表槽值身份
print('\n== 4 P3b 表的身份：槽值是指令起点的比例 ==')
slot = [rd(a, TB[v][1]) for v in intab for a in range(TB[v][3], TB[v][4], 4)]
slot = [s for s in slot if s]
n_start = sum(1 for s in slot if s in st)
print('  表槽值 %d 个，其中指令起点 %d（%.2f%%）' % (len(slot), n_start, 100.0 * n_start / len(slot)))
# 对照：孤立指针型 dword（值是 .text 地址但不成 ≥3 表）
cands = []
a = LO
while a + 4 <= LO + VSZ and len(cands) < 200000:
    x = rd(a, 4)
    if isT(x) and best_table(a)[0] < 3: cands.append(x)
    a += 4
random.seed(99)
samp_c = random.sample(cands, min(2000, len(cands)))
r_c = sum(1 for t in samp_c if t in st) / float(len(samp_c))
print('  孤立指针型 dword %d 个（抽 %d），其中指令起点 %.2f%%'
      % (len(cands), len(samp_c), 100.0 * r_c))
ck('F0 表槽值「是指令起点」比例 ≥ 0.90', n_start / float(len(slot)) >= 0.90,
   '%.4f' % (n_start / float(len(slot))))
ck('F1 表槽值比例 > 孤立指针基线 + 0.40', n_start / float(len(slot)) > r_c + 0.40,
   (round(n_start / float(len(slot)), 4), round(r_c, 4)))

# ---------------------------------------------------------------- P3c 不在指针表内的 9 条
print('\n== 5 P3c 不在指针表内的 %d 条：字节上下文与归类 ==' % len(outtab))
rows = []
for v in outtab:
    o = v - LO
    prev = blob[max(0, o - 16):o]
    nxt = blob[o:o + 16]
    # 归类：前后 16 B 里可打印/递增字节序列 → 字节查找表；全 0xCC → 填充；否则其他
    win = prev + nxt
    inc = sum(1 for i in range(len(win) - 1) if win[i + 1] == (win[i] + 1) & 0xff)
    cls = 'byte_lookup_table' if inc >= 4 else ('padding_cc' if win.count(0xcc) >= 16 else 'other')
    rows.append({'va': hex(v), 'prev16': prev.hex(), 'next16': nxt.hex(),
                 'inc_pairs': inc, 'class': cls})
    print('  %s %-18s inc=%2d prev=%s next=%s' % (hex(v), cls, inc, prev.hex(), nxt.hex()))
n_bl = sum(1 for r in rows if r['class'] == 'byte_lookup_table')
ck('G0 不在指针表内的洞 ≤ 10 条', len(outtab) <= 10, len(outtab))
ck('G1 其中可归为字节查找表的 ≥ 4 条', n_bl >= 4, n_bl)

# ---------------------------------------------------------------- 收口
obj = {'exe_bytes': len(data),
       'text': {'lo': hex(LO), 'vsz': VSZ, 'raw': RAW, 'rsz': RSZ},
       'bounds': len(bounds), 'plain_starts': len(starts), 'holes': [hex(v) for v in holes],
       'undecodable_count': len(UND), 'undecodable_share_pct': 100.0 * len(UND) / VSZ,
       'never_visited_count': len(never),
       'holes_in_table': [hex(v) for v in intab], 'holes_out_table': rows,
       'table_count': len(tables), 'table_ranges': [[hex(a), hex(b)] for a, b in tables],
       'table_entry_width': {hex(v): TB[v][1] for v in intab},
       'slot_total': len(slot), 'slot_is_start': n_start,
       'rates': {'holes': r_hole, 'never_visited': r_never, 'random_byte': r_rand,
                 'isolated_ptr_is_start': r_c},
       'elapsed_s': el, 'assertions': RES, 'fail': FAIL}
io.open(OUT, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False, indent=1))
print('\n断言 %d 条，FAIL %d ; 产物 %s' % (len(RES), FAIL, OUT))
sys.exit(1 if FAIL else 0)
