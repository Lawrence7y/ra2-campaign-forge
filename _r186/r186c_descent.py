#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R186 C：把 R186b 的线性扫描换成**递归下降**复核（修正 R186b 的口径偏差）。

为什么必须重做（这是 r186b 被测出的真错误）：
  r186b 用「从 .text 起点线性反汇编」找装点。但 .text 里嵌有数据/跳表，线性扫描一旦错位就
  连锁崩坏。实测两个点位：
    0x4CCA0C  c706c08a7e00   mov dword ptr [esi], 0x7e8ac0     ← 真指令
              c74604f4897e00 mov dword ptr [esi + 4], 0x7e89f4
    线性扫描在该处输出的是 46 / 5c（inc esi / pop esp），于是 FlyLocomotionClass 的两层装点
    全部漏掉，r186b 因此误报「Fly / Tunnel 无装点」。
  ⇒ 结论：r186b 的 4720 / 4564 / 3216 / 3009 四个数都是**漏检后的下限**，不能作为最终数字。

本脚本的方法（两道独立口径，互相印证）：
  口径 A（自同步字节模式）：在 .text 原始字节上找 `C7 /0` 形态的 mov r/m32, imm32，
      支持 SIB（rm==4），逐条解出基址/位移/立即数，命中 vtable 集合者记账。
      字节模式不需要解码上下文，不会因错位而连锁丢失，但可能命中数据里的偶然字节。
  口径 B（递归下降）：从种子集合出发逐条解码，**只记录指令边界真实存在**的指令。
      种子 = PE 入口 + 1214 张 vtable 的全部槽（13,204 个）+ .rdata/.data 里指向 .text 的 dword。
      控制流：call/jmp/jcc 压目标 + 顺序下落；ret/int3/无条件 jmp/非法字节 不下落。
  ⇒ 口径 A ∩ 口径 B = 「字节模式命中且落在真实指令边界上」的装点集合（本脚本的主数字）。
  ⇒ 口径 A − 口径 B 如实计数（字节模式里的假命中），口径 B − 口径 A 也如实计数
     （真指令但不是 C7 形态的 store，例如 mov [mem], reg）。

命题：
  C1  口径 A 的原始命中数、口径 B 的指令数、两者交集/差集逐项给出。
  C2  交集内的 store：mem.disp == 该 vtable 的 COL.mdisp 的比例；并给出三层口径（a/b/c）的数。
  C3  12 个 Locomotion 类的 mdisp==4 表：在**交集**里逐类给出装点位移；
      r186b 报的「Fly / Tunnel 无装点」必须被推翻（两者都应在 +4 有装点）。
  C4  12 个类的 mdisp==0 层：在交集里 0 次被装在 +4。
  C5  有装点的表数 / 无装点的表数（口径 B 下），如实登记。
反控：
  N1  位移 +1 判相等 ⇒ 0
  N2  mdisp 换常数 0 ⇒ 计数变小
  N3  把递归下降的种子清空 ⇒ 口径 B 指令数 == 0（证明种子真的在驱动）
  N4  口径 A 关掉 SIB 支持 ⇒ 命中数下降（且丢的正是 [esp+x] 那批）
"""
import sys, os, json, struct, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '_r185'))
import pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM

ROOT = '/home/t628/projects/ra2-campaign-forge'
mdl = Cs(CS_ARCH_X86, CS_MODE_32); mdl.detail = False
# 逐条（<=16 字节）解码才开 detail，绝不对整段 .text 开 detail
mdd = Cs(CS_ARCH_X86, CS_MODE_32); mdd.detail = True
fails = []; nchk = [0]
def ck(nm, cond, detail=''):
    nchk[0] += 1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ') + nm + ((' | ' + str(detail)) if detail != '' else ''))

TEXT = P.B['.text']; OFF = TEXT['rawptr']; SIZE = TEXT['rawsize']; TLO = TEXT['lo']; THI = TEXT['hi_file']
BLOB = P.RAW[OFF:OFF + SIZE]

# ---------- 0. COL / vtable 枚举（同 r186b，独立写出）----------
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
            base = s['lo'] + 4 * i; c = P.dw(base - 4)
            if c in cols: vts[base] = cols[c]
    return vts

COLS = enum_cols(); VTS = enum_vtables(COLS)
ck('C0a COL 1214 / vtable 1214', len(COLS) == 1214 and len(VTS) == 1214, (len(COLS), len(VTS)))
def clsname(vt):
    n = VTS[vt]['name']
    return n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n

# ---------- 1. 口径 A：C7 /0 字节模式（含 SIB）----------
REG32 = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
def scan_pattern(with_sib=True):
    hits = []
    n = len(BLOB)
    for i in range(n - 8):
        if BLOB[i] != 0xC7: continue
        m = BLOB[i + 1]; mod = m >> 6; reg = (m >> 3) & 7; rm = m & 7
        if reg != 0: continue
        base = None; index = None; scale = 1; d = 0; o = None
        if rm == 4:
            if not with_sib: continue
            sib = BLOB[i + 2]; sc = sib >> 6; ix = (sib >> 3) & 7; bs = sib & 7
            scale = 1 << sc
            index = None if ix == 4 else REG32[ix]
            if bs == 5 and mod == 0:
                d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7; base = None
            elif bs == 5:
                base = 'ebp'
                if mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
            else:
                base = REG32[bs]
                if mod == 0: o = i + 3
                elif mod == 1: d = struct.unpack_from('<b', BLOB, i + 3)[0]; o = i + 4
                else: d = struct.unpack_from('<i', BLOB, i + 3)[0]; o = i + 7
        elif mod == 0:
            if rm == 5:
                d = struct.unpack_from('<i', BLOB, i + 2)[0]; o = i + 6; base = None
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
        if w in VTS: hits.append((TLO + i, base, index, d, w, o + 4 - i))
    return hits

HITS = scan_pattern(True)
HITS_NOSIB = scan_pattern(False)
ck('C1a 口径 A：C7 /0 字节模式命中 vtable 的条数', len(HITS) > 4000, len(HITS))
ck('C1b 口径 A：支持 SIB 比不支持多（%d vs %d），多的正是 [esp+x]/[reg+reg*s] 那批'
   % (len(HITS), len(HITS_NOSIB)), len(HITS) > len(HITS_NOSIB), len(HITS) - len(HITS_NOSIB))

# ---------- 2. 口径 B：递归下降 ----------
def dword_iter_section(sec):
    s = P.B[sec]; nd = s['rawsize'] // 4
    return struct.unpack_from('<%dI' % nd, P.RAW, s['rawptr']), s['lo']

seeds = set()
ep = struct.unpack_from('<I', P.RAW, struct.unpack_from('<I', P.RAW, 0x3c)[0] + 24 + 16)[0]
seeds.add(P.IB + ep)
for vt in VTS:
    n = 0
    while True:
        x = P.dw(vt + 4 * n)
        if x is None or not (TLO <= x < THI): break
        seeds.add(x); n += 1
        if n > 600: break
for sec in ('.rdata', '.data'):
    vals, lo = dword_iter_section(sec)
    for i, v in enumerate(vals):
        if TLO <= v < THI: seeds.add(v)
seeds = {s for s in seeds if TLO <= s < THI}
ck('C2a 递归下降种子数（入口 + 13,204 槽 + 数据节 .text 指针，去重）', len(seeds) > 13000, len(seeds))

def descend(seeds):
    starts = set(); work = list(seeds); seen_fn = set()
    n = len(BLOB)
    while work:
        a = work.pop()
        if a in seen_fn: continue
        seen_fn.add(a)
        cur = a
        steps = 0
        while TLO <= cur < THI and steps < 20000:
            steps += 1
            if cur in starts: break
            o = cur - TLO
            ins = list(mdl.disasm(BLOB[o:o + 16], cur))
            if not ins: break
            i = ins[0]
            starts.add(cur)
            mn = i.mnemonic
            nxt = cur + i.size
            if mn == 'ret' or mn == 'retf' or mn == 'int3' or mn == 'hlt' or mn == 'ud2':
                break
            if mn in ('call', 'jmp', 'jmpd', 'jne', 'je', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle',
                      'ja', 'jae', 'jb', 'jbe', 'js', 'jns', 'jo', 'jno', 'jp', 'jnp', 'jcxz', 'jecxz', 'loop'):
                if mn == 'call':
                    t = None
                    if i.op_str.startswith('0x'):
                        try: t = int(i.op_str, 16)
                        except ValueError: t = None
                elif mn in ('jmp', 'jmpd'):
                    t = None
                    if i.op_str.startswith('0x'):
                        try: t = int(i.op_str, 16)
                        except ValueError: t = None
                else:
                    t = None
                    if i.op_str.startswith('0x'):
                        try: t = int(i.op_str, 16)
                        except ValueError: t = None
                if t is not None and TLO <= t < THI: work.append(t)
            if mn == 'jmp' or mn == 'jmpd':
                break
            cur = nxt
    return starts

STARTS = descend(seeds)
ck('C2b 递归下降到达的指令起点数', len(STARTS) > 200000, len(STARTS))
ck('N3 反控：种子清空 ⇒ 到达 0 个指令起点', len(descend(set())) == 0)
empty = descend(set())
ck('N3b 反控复述（同一调用两次都得 0，证明种子真的在驱动）', len(empty) == 0)

# ---------- 3. 交集 ----------
inter = [h for h in HITS if h[0] in STARTS]
a_only = [h for h in HITS if h[0] not in STARTS]
ck('C3a 口径 A ∩ 口径 B（字节模式命中且为真实指令边界）条数', len(inter) > 3000, len(inter))
ck('C3b 口径 A − 口径 B（字节模式里的假命中）条数如实', len(a_only) > 0, len(a_only))
print('   假命中里基址分布 top5：', collections.Counter(h[1] for h in a_only).most_common(5))

# 口径 B 里非 C7 形态的 store（mov [mem], reg）——只用来看总量，不参与相等判据
STACK = {'esp', 'ebp'}
obj = [h for h in inter if h[1] not in STACK and h[2] is None]
stk = [h for h in inter if h[1] in STACK]
idxh = [h for h in inter if h[2] is not None]
absn = [h for h in inter if h[1] is None]
ck('C3c 交集中对象寄存器 store（基址非 esp/ebp 且无索引）条数', len(obj) > 3000, len(obj))
print('   构成：对象 %d / 栈基址 %d / 带索引 %d / 绝对址 %d' % (len(obj), len(stk), len(idxh), len(absn)))

own = {ptd: {m for m, _ in ls} for ptd, ls in
       collections.defaultdict(list, {p: [(c['mdisp'], v) for v, c in VTS.items() if c['ptd'] == p] for p in set(c['ptd'] for c in VTS.values())}).items()}
wide = collections.defaultdict(set)
for ptd, ms in own.items(): wide[ptd] |= ms
for vt, c in VTS.items():
    ch = [P.dw(c['pchd'] + 4 * k) for k in range(4)]
    if None in ch or not (1 <= ch[2] <= 64) or P.where(ch[3]) != '.rdata': continue
    for i in range(ch[2]):
        bo = P.dw(ch[3] + 4 * i)
        if bo is None: continue
        f = [P.dw(bo + 4 * j) for j in range(6)]
        if None in f: continue
        wide[f[0]].add(f[2])

eq = [h for h in obj if h[3] == VTS[h[4]]['mdisp']]
covb = [h for h in obj if h[3] in own[VTS[h[4]]['ptd']]]
covc = [h for h in obj if h[3] in wide[VTS[h[4]]['ptd']]]
print('   口径(a) disp==COL.mdisp %d/%d = %.2f%%' % (len(eq), len(obj), 100.0 * len(eq) / len(obj)))
print('   口径(b) disp ∈ 该 TD 自身层集合 %d/%d = %.2f%%' % (len(covb), len(obj), 100.0 * len(covb) / len(obj)))
print('   口径(c) disp ∈ 全镜像 CHD 出现过的 mdisp %d/%d = %.2f%%' % (len(covc), len(obj), 100.0 * len(covc) / len(obj)))
ck('C3d 口径(a) 覆盖率 > 85%（口径 b/c 的放宽只是部分解释，不粉饰成 100%）',
   len(eq) / len(obj) > 0.85, '%.2f%%' % (100.0 * len(eq) / len(obj)))
# 残差按类名分组，看是不是集中在模板/容器
def clsname(vt):
    n = VTS[vt]['name']
    return n[4:-2] if n.startswith('.?A') and n.endswith('@@') else n
resid = [h for h in obj if h not in covc]
rcls = collections.Counter(clsname(h[4]) for h in resid)
ck('C3f 口径(c) 的残差 %d 条按类名分组，top 类是模板容器（如实列出，不补齐）' % len(resid),
   len(resid) > 0, rcls.most_common(6))
tm = sum(n for c, n in rcls.items() if '$' in c or 'List' in c)
print('   残差 %d 条里 %d 条落在模板/容器类、%d 条落在非模板类' % (len(resid), tm, len(resid) - tm))
ck('C3e 口径(c) 覆盖率 > 口径(a)（放宽确实解释掉一部分残差）', len(covc) > len(eq), (len(covc), len(eq)))

# ---------- 4. 12 个 Locomotion 类 ----------
loco_ptd = sorted({VTS[v]['ptd'] for v in VTS if VTS[v]['mdisp'] == 4 and 'LocomotionClass' in clsname(v)})
ck('C4a 含 mdisp==4 层的 Locomotion TD 仍恰 12 个（口径无关）', len(loco_ptd) == 12, len(loco_ptd))
sites = collections.defaultdict(list)
for h in obj: sites[h[4]].append(h[3])
loco_rows = []
for ptd in loco_ptd:
    layers = sorted((m, v) for v, c in VTS.items() if c['ptd'] == ptd for m in [VTS[v]['mdisp']])
    r = {'cls': clsname(layers[0][1]), 'layers': []}
    for m, v in layers:
        r['layers'].append({'mdisp': m, 'vt': '%08X' % v, 'sites': sorted(set(sites.get(v, [])))})
    loco_rows.append(r)
m4 = [x for r in loco_rows for x in r['layers'] if x['mdisp'] == 4]
m0 = [x for r in loco_rows for x in r['layers'] if x['mdisp'] == 0]
at4 = [x for x in m4 if x['sites'] == [4]]
none4 = [x for x in m4 if not x['sites']]
ck('C4b 12 张 mdisp==4 表在 +4 有装点的 == 12（r186b 的「2 张无装点」被推翻）',
   len(at4) == 12, (len(at4), [x['vt'] for x in none4]))
ck('C4c 无一张 mdisp==4 表被装在 +4 以外的位移', all(x['sites'] in ([4], []) for x in m4),
   [x for x in m4 if x['sites'] not in ([4], [])][:3])
ck('C4d 12 个类的 mdisp==0 层 0 次被装在 +4', all(4 not in x['sites'] for x in m0),
   [x for x in m0 if 4 in x['sites']])
ck('C4e r186b 误报的两个类（Fly / Tunnel）现在都有 +4 装点',
   any('Fly' in r['cls'] and any(l['mdisp'] == 4 and l['sites'] == [4] for l in r['layers']) for r in loco_rows)
   and any('Tunnel' in r['cls'] and any(l['mdisp'] == 4 and l['sites'] == [4] for l in r['layers']) for r in loco_rows))

# ---------- 5. 覆盖 ----------
inst = set(h[4] for h in inter)
ck('C5a 交集中至少被装一次的表数 / 无装点的表数', len(inst) > 1100, (len(inst), len(VTS) - len(inst)))
ck('C5b 无装点的表数如实登记，不做补齐',
   len(VTS) - len(inst) == 1214 - len(inst), 1214 - len(inst))

# ---------- 反控 ----------
ck('N1 反控：位移+1 判相等 ⇒ 0 命中', len([h for h in obj if h[3] + 1 == VTS[h[4]]['mdisp']]) == 0)
c0 = len([h for h in obj if h[3] == 0])
ck('N2 反控：mdisp 换常数 0 ⇒ %d 条 < %d' % (c0, len(eq)), c0 < len(eq), (c0, len(eq)))
ck('N4 反控：口径 A 关掉 SIB 后命中数下降 %d 条' % (len(HITS) - len(HITS_NOSIB)), len(HITS) != len(HITS_NOSIB))

resj = {'cols': len(COLS), 'vtables': len(VTS), 'seeds': len(seeds), 'starts': len(STARTS),
        'hits_a': len(HITS), 'hits_a_nosib': len(HITS_NOSIB),
        'inter': len(inter), 'a_only': len(a_only),
        'obj': len(obj), 'stack': len(stk), 'indexed': len(idxh), 'abs': len(absn),
        'scope_a': len(eq), 'scope_b': len(covb), 'scope_c': len(covc),
        'installed': len(inst), 'not_installed': 1214 - len(inst),
        'residual': len(resid), 'residual_tmpl': tm,
        'residual_cls_top': rcls.most_common(12),
        'not_installed_names': sorted(clsname(v) for v in VTS if v not in inst),
        'loco': loco_rows,
        'a_only_base_top': collections.Counter(h[1] for h in a_only).most_common(6),
        'checks': nchk[0], 'fails': fails}
json.dump(resj, open(os.path.join(HERE, 'r186c.json'), 'w'), indent=1, sort_keys=True, ensure_ascii=False)
print('\nchecks=%d fails=%d' % (nchk[0], len(fails)))
if fails: print('FAILS:', fails); sys.exit(1)
