#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R188 审计第二遍（低内存）：4 个争点的定向复算 + 2 条新反控。

内存纪律：全量指令只存 array('I') 地址 + array('B') 尺寸 + array('B') 助记码，
操作数字符串只留 call / mov 两类。

运行： timeout 900 python3 _r188/audit_deepseek/audit2_r188_deepseek.py
"""
import os, re, json, struct, collections, array

ROOT = '/home/t628/projects/ra2-campaign-forge'
RAW = open(os.path.join(ROOT, 'ra2bench', 'gamemd.exe'), 'rb').read()
pe = struct.unpack_from('<I', RAW, 0x3c)[0]
NSEC = struct.unpack_from('<H', RAW, pe + 6)[0]
OPTSZ = struct.unpack_from('<H', RAW, pe + 20)[0]
IB = struct.unpack_from('<I', RAW, pe + 24 + 28)[0]
ORDER, SEC = [], {}
for i in range(NSEC):
    o = pe + 24 + OPTSZ + 40 * i
    nm = RAW[o:o + 8].rstrip(b'\0').decode('latin1')
    vs, va, rs, ra = struct.unpack_from('<IIII', RAW, o + 8)
    SEC[nm] = dict(lo=IB + va, raw=ra, rawsize=rs, hifile=IB + va + rs)
    ORDER.append(nm)
def r2o(va):
    for nm in ORDER:
        s = SEC[nm]
        if s['lo'] <= va < s['hifile']:
            return s['raw'] + (va - s['lo'])
def dw(va):
    o = r2o(va)
    return None if o is None or o + 4 > len(RAW) else struct.unpack_from('<I', RAW, o)[0]
def secname(va):
    for nm in ORDER:
        s = SEC[nm]
        if s['lo'] <= va < s['hifile']:
            return nm
def cstr(va, mx=200):
    o = r2o(va)
    if o is None:
        return None
    e = RAW.find(b'\0', o, o + mx)
    return None if e < 0 else RAW[o:e]
T = SEC['.text']
LO, HI, BLOB = T['lo'], T['hifile'], RAW[T['raw']:T['raw'] + T['rawsize']]
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import capstone
MD = Cs(CS_ARCH_X86, CS_MODE_32)
CH = 65536
print('capstone %s' % capstone.__version__)

# ======== 流式扫描（只存轻量数组）========
MN = {'mov': 1, 'call': 2, 'jmp': 3, 'ret': 4, 'jcc': 5}
def mcode(mn):
    if mn == 'mov':
        return 1
    if mn == 'call':
        return 2
    if mn == 'jmp':
        return 3
    if mn == 'ret':
        return 4
    if mn.startswith('j'):
        return 5
    return 0
def stream(overlap=0, want_ops=True):
    pos = 0
    ad = array.array('I')
    sz_a = array.array('B')
    mc = array.array('B')
    ops = {}
    while pos < len(BLOB):
        end = min(pos + CH, len(BLOB))
        lim = min(end + overlap, len(BLOB))
        last = None
        for a, s, mn, op in MD.disasm_lite(BLOB[pos:lim], LO + pos):
            last = pos + (a - LO - pos) + s
            c = mcode(mn)
            ad.append(a)
            sz_a.append(s)
            mc.append(c)
            if want_ops and c in (1, 2):
                ops[a] = op
        if last is None:
            pos += 1
        elif last >= end:
            pos = last if overlap else end
        else:
            pos = last + 1
    return ad, sz_a, mc, ops

AD, SZ, MC, OPS = stream(0)
print('重同步流：指令 %d（主会话 1394134）' % len(AD))
IDX = {a: i for i, a in enumerate(AD)}
EOF_MARK = None

# ======== 解析器 ========
REG = r'(eax|ecx|edx|ebx|esp|ebp|esi|edi)'
def parse_mem(op):
    if not op.startswith('dword ptr ['):
        return None
    i = op.index('[')
    j = op.rindex(']')
    if op[j + 1:].strip():
        return None
    inner = op[i + 1:j]
    parts = []
    for t in inner.split('+'):
        if ' - ' in t:
            a, b = t.split(' - ')
            parts += [a.strip(), '-' + b.strip()]
        else:
            parts.append(t.strip())
    base = idx = None
    scale = 1
    disp = 0
    for t in parts:
        neg = t.startswith('-')
        tt = t[1:].strip() if neg else t
        if re.fullmatch(REG, tt):
            base = tt
        elif re.fullmatch(r'%s ?\* ?[1248]' % REG, tt):
            m = re.fullmatch(r'(%s) ?\* ?([1248])' % REG, tt)
            idx = m.group(1)
            scale = int(m.group(3))
        elif re.fullmatch(r'0x[0-9a-f]+|[0-9]+', tt):
            disp = int(tt, 0) * (-1 if neg else 1)
        else:
            return None
    return (base, idx, scale, disp)

MOV_RE = re.compile(r'^(eax|ecx|edx|ebx|esp|ebp|esi|edi), dword ptr \[esi\]$')
WM = set('mov movzx movsx lea xor add sub and or adc sbb pop inc dec mul imul div idiv '
         'neg not shl shr sar rol ror xchg bswap'.split())
# 写入检测需要知道任意指令的首操作数，我们只存了 call/mov 的 op；为此另建一张
# "写 r32 的指令" 索引（只存 (addr, reg, mnemonic)），内存很小。
WR = collections.defaultdict(set)
pos = 0
blob = BLOB
while pos < len(blob):
    end = min(pos + CH, len(blob))
    last = None
    for a, s, mn, op in MD.disasm_lite(blob[pos:end], LO + pos):
        last = pos + (a - LO - pos) + s
        if mn in WM:
            head = op.split(',')[0].strip()
            if head in ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi'):
                WR[head].add(a)
    if last is None:
        pos += 1
    elif last >= end:
        pos = end
    else:
        pos = last + 1
print('写寄存器指令索引：%s' % {k: len(v) for k, v in sorted(WR.items())})

def pair_main(window=32):
    """原样复刻 r188d_resync.py 的 prop()：一个 mov 只配一个 call（命中即 break）。"""
    pairs = []
    n = len(AD)
    for i in range(n):
        if MC[i] != 1:
            continue
        op = OPS.get(AD[i], '')
        m = MOV_RE.match(op)
        if not m:
            continue
        r = m.group(1)
        for j in range(i + 1, min(i + 1 + window, n)):
            a2 = AD[j]
            if MC[j] == 2:
                pm = parse_mem(OPS.get(a2, ''))
                if pm and pm[0] == r and pm[1] is None:
                    pairs.append((AD[i], r, a2, pm[3]))
                    break
            w = WR.get(r)
            if w and a2 in w:
                break
    return pairs

def pair_all(window=32):
    """审计版：一个 mov 可配其后的所有 call，直到该寄存器被改写。"""
    pairs = []
    n = len(AD)
    for i in range(n):
        if MC[i] != 1:
            continue
        op = OPS.get(AD[i], '')
        m = MOV_RE.match(op)
        if not m:
            continue
        r = m.group(1)
        w = WR.get(r, ())
        for j in range(i + 1, min(i + 1 + window, n)):
            a2 = AD[j]
            if MC[j] == 2:
                pm = parse_mem(OPS.get(a2, ''))
                if pm and pm[0] == r and pm[1] is None:
                    pairs.append((AD[i], r, a2, pm[3]))
                    continue
            if a2 in w:
                break
    return pairs

PM = pair_main()
PA = pair_all()
print('\n配对：主会话算法 %d（自报 6965）；审计版（一 mov 多 call）%d' % (len(PM), len(PA)))
reuse = collections.Counter(p[0] for p in PA)
print('  同一 mov 被复用 >=2 次的 %d 个 mov，共贡献 %d 对；差 = %d' %
      (sum(1 for v in reuse.values() if v >= 2),
       sum(v for v in reuse.values() if v >= 2),
       len(PA) - len({p[2] for p in PM})))
d = collections.Counter()
for p in PM:
    d[IDX[p[2]] - IDX[p[0]]] += 1
print('  主会话算法配对的距离分布：最大 %d，>=28 的 %s' %
      (max(d), {k: v for k, v in sorted(d.items()) if k >= 28}))
for p in PA:
    if reuse[p[0]] >= 2:
        k = IDX[p[0]]
        print('  复用样例 mov %#010x %-28s 后续 call:' %
              (AD[k], OPS.get(AD[k], '')))
        for c2 in [x for x in PA if x[0] == p[0]]:
            print('      +%2d 条 %#010x %s' % (IDX[c2[2]] - k, c2[2], OPS.get(c2[2], '')))
        break
PDm = collections.Counter(p[3] for p in PM)
PDa = collections.Counter(p[3] for p in PA)
print('  位移去重：主会话算法 %d / 审计版 %d（主会话自报 267）' % (len(PDm), len(PDa)))
print('  top6 位移：主会话算法 %s' % [(hex(k), v) for k, v in PDm.most_common(6)])
print('  top6 位移：审计版     %s' % [(hex(k), v) for k, v in PDa.most_common(6)])

# ======== 枚举 ========
COLS, VTS = {}, {}
for nm in ('.rdata', '.data'):
    s = SEC[nm]
    n = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % n, RAW, s['raw'])
    for i in range(n - 4):
        d3, d4 = v[i + 3], v[i + 4]
        if v[i] not in (0, 1) or v[i + 2] != 0:
            continue
        if secname(d3) != '.data' or secname(d4) != '.rdata':
            continue
        cn = cstr(d3 + 8)
        if cn and cn.startswith(b'.?A') and cn.endswith(b'@@'):
            COLS[s['lo'] + 4 * i] = dict(mdisp=v[i + 1], name=cn.decode('latin1'))
for nm in ('.rdata', '.data'):
    s = SEC[nm]
    n = s['rawsize'] // 4
    v = struct.unpack_from('<%dI' % n, RAW, s['raw'])
    for i, x in enumerate(v):
        if not (LO <= x < HI):
            continue
        va = s['lo'] + 4 * i
        if dw(va - 4) in COLS:
            VTS[va] = COLS[dw(va - 4)]
def nslots(vt):
    k = 0
    while k < 4000:
        x = dw(vt + 4 * k)
        if x is None or not (LO <= x < HI):
            return k
        k += 1
    return k
SN = {vt: nslots(vt) for vt in VTS}
IMP = collections.defaultdict(list)
for vt in VTS:
    for k in range(SN[vt]):
        IMP[dw(vt + 4 * k)].append((vt, k))
print('\n枚举 COL %d / vtable %d / 槽位实例 %d / 实现 %d' %
      (len(COLS), len(VTS), sum(SN.values()), len(IMP)))

# ======== 争点：槽3 宿主表的"槽11"读的是不是槽位 ========
TH = 0x410210
owners = [vt for vt, kk in IMP[TH] if kk == 3]
print('\n【C5/C6】槽3 thunk %#010x 宿主表 %d 张' % (TH, len(owners)))
print('  槽数分布 %s（主会话未报此量）' % dict(collections.Counter(SN[vt] for vt in owners)))
print('  有第 11 号槽（槽数 > 11）的宿主表：%d 张' % sum(1 for vt in owners if SN[vt] > 11))
print('  ⇒ 主会话 A6g 的 P.dw(vt+44) 在这 %d 张表上全部越界读出' % sum(1 for vt in owners if SN[vt] <= 11))
raw44 = collections.Counter(dw(vt + 44) for vt in owners)
print('  越界读 vt+44 的取值 top6 %s' % [(hex(k), v) for k, v in raw44.most_common(6)])
print('  这些值是什么：')
for k, v in raw44.most_common(4):
    o = r2o(k) if k else None
    print('    %s x%d → 落 %s；是某 COL 的 VA=%s；是某 vtable 的 VA=%s；是某表槽位值=%s' %
          (hex(k) if k else None, v, secname(k) if k else None,
           k in COLS, k in VTS, k in IMP))
print('  vt+44 处字节与"该表之后紧邻的内容"对齐情况：')
for vt in owners[:4]:
    o = r2o(vt)
    print('    表 %#010x 槽数 %2d 该表字节 %s | vt+44 处 %s 落 %s' %
          (vt, SN[vt], RAW[o:o + 4 * SN[vt]].hex(), RAW[r2o(vt + 44):r2o(vt + 44) + 4].hex(),
           secname(vt + 44)))
print('  槽3 宿主表 COL.offset 分布 %s（主会话未报）' %
      dict(collections.Counter(VTS[vt]['mdisp'] for vt in owners)))
print('  槽3 宿主表名样例 %s' % [VTS[vt]['name'] for vt in owners[:5]])
print('  0x410450 是否作为任何槽位值出现：%s（出现 %d 次）' %
      (0x410450 in IMP, len(IMP.get(0x410450, []))))
for t in (0x410450, 0x410310, 0x410260, 0x512280):
    o = r2o(t)
    if o is None:
        print('  %#010x 不在文件' % t)
        continue
    seq = list(MD.disasm(RAW[o:o + 16], t))
    occ = IMP.get(t, [])
    print('  %#010x %s | %s' % (t, RAW[o:o + 8].hex(),
                                ' ; '.join('%s %s' % (i.mnemonic, i.op_str) for i in seq[:3])))
    print('            出现槽位 %d 次，槽号分布 %s' %
          (len(occ), dict(collections.Counter(k for _, k in occ).most_common(6))))

# ======== 争点：槽2 top 实现的并列 ========
print('\n【C8】槽2（disp 0x8）实现计数：')
t2 = collections.Counter(dw(vt + 8) for vt in VTS if SN[vt] > 2)
for v2, c2 in t2.most_common(4):
    print('  %#010x -> %d 张表' % (v2, c2))
print('  ⇒ 主会话取 0x410310(74)，本审计第一遍取 0x410600(74)：两者并列，'
      'most_common 的 tie-break 决定 C8 第 6 组三元组，C8 的"六组"不唯一')

# ======== symbols.json 独立交叉 ========
print('\n【独立交叉】out/reverse/symbols.json（RTTI 派生，非本库枚举）：')
sj = json.load(open(os.path.join(ROOT, 'out/reverse/symbols.json')))
cls = sj['classes']
print('  类数 %d' % len(cls))
for impl, slot in ((0x410210, 3), (0x410220, 4), (0x410310, 2), (0x410600, 2),
                   (0x410450, 11), (0x4e1570, 11), (0x5f6bc0, 33), (0x4104c0, 18)):
    hitn = sum(1 for c in cls.values()
               if len(c.get('vfuncs', [])) > slot and c['vfuncs'][slot].lower() == '%08x' % impl)
    print('  实现 %#010x 在 symbols.json 里作为"第 %d 槽"出现 %d 次' % (impl, slot, hitn))
mis = [c['name'] for c in cls.values()
       if c.get('vtable_va') and dw(int(c['vtable_va'], 16)) is not None]
print('  symbols.json 的 vtable_va 直接读首 dword 落 .text 的 %d / %d' % (len(mis), len(cls)))

# ======== 新反控 R1：重同步多出的站点有多少"对齐可达" ========
print('\n【反控 R1】重同步多出的间接 call 站点，有多少能由函数起点线性解码对齐到？')
call_naive = set()
for a in OPS:
    if parse_mem(OPS[a]) is not None:
        call_naive.add(a)
# 朴素流（无重叠、坏字节跳块尾）的站点集
NA_AD, NA_SZ, NA_MC, NA_OPS = None, None, None, None
pos = 0
naive_calls = set()
while pos < len(BLOB):
    end = min(pos + CH, len(BLOB))
    last = None
    for a, s, mn, op in MD.disasm_lite(BLOB[pos:end], LO + pos):
        last = pos + (a - LO - pos) + s
        if mn == 'call' and parse_mem(op) is not None:
            naive_calls.add(a)
    if last is None:
        pos += 1
    elif last >= end:
        pos = end
    else:
        pos = end
resync_calls = call_naive
extra = resync_calls - naive_calls
print('  重同步站点 %d，朴素站点 %d，增量 %d' % (len(resync_calls), len(naive_calls), len(extra)))
# 函数起点近似：0xCC 填充之后的第一个字节
PAD = []
i = 0
n = len(BLOB)
while i < n - 1:
    if BLOB[i] == 0xCC and BLOB[i + 1] == 0xCC:
        j = i
        while j < n and BLOB[j] == 0xCC:
            j += 1
        if j < n:
            PAD.append(j)
        i = j
    else:
        i += 1
print('  0xCC 填充后的候选函数起点 %d 个' % len(PAD))
reach = set()
for p in PAD:
    end = min(p + 400, n)
    cur = p
    while cur < end:
        d = list(MD.disasm_lite(BLOB[cur:end], LO + cur))
        if not d:
            break
        a, s, mn, op = d[0]
        reach.add(a)
        if mn in ('ret', 'jmp') or mn == 'int3':
            break
        if mn == 'call' and op == '':
            break
        cur = cur + s
print('  由候选起点线性解码可达的地址 %d 个' % len(reach))
print('  增量站点中"对齐可达"的 %d / %d = %.2f%%' %
      (len(extra & reach), len(extra), 100.0 * len(extra & reach) / max(1, len(extra))))
print('  朴素站点中"对齐可达"的 %d / %d = %.2f%%' %
      (len(naive_calls & reach), len(naive_calls), 100.0 * len(naive_calls & reach) / max(1, len(naive_calls))))
garb = sorted(extra - reach)[:5]
for a in garb:
    o = r2o(a) - 8
    print('     对齐不可达样例 %#010x %-34s 上下文 %s' % (a, OPS[a], RAW[o:o + 20].hex()))

# ======== 新反控 R2：分块尺寸敏感度 ========
print('\n【反控 R2】重同步结果对分块尺寸的敏感度（4 组块大小）：')
for chunk in (4096, 16384, 65536, 262144):
    pos = 0
    ni = 0
    nc = 0
    nh = 0
    while pos < len(BLOB):
        end = min(pos + chunk, len(BLOB))
        last = None
        for a, s, mn, op in MD.disasm_lite(BLOB[pos:end], LO + pos):
            last = pos + (a - LO - pos) + s
            ni += 1
            if mn == 'call' and parse_mem(op) is not None:
                nc += 1
        if last is None:
            pos += 1
            nh += 1
        elif last >= end:
            pos = end
        else:
            pos = last + 1
            nh += 1
    print('  块 %6d 字节：指令 %7d  间接call %6d  洞 %3d' % (chunk, ni, nc, nh))
print('  ⇒ 若这三个量随块尺寸变化，则"1394134 / 22731 / 97"不是唯一真值，只是块=65536 的读数')
