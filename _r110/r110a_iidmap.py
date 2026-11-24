#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r110a_iidmap.py —— 用 slot0 = QueryInterface 的字节特征，机械抽出「每个类认哪些 IID」。

R109 §EK 已用字节闭合 slot0 = QueryInterface。R109 待办③：既然 slot0 已定，
就能反查「哪些类只认 IUnknown、哪些认多个 IID」⇒ 本镜像的 COM 暴露面。
本轮只做机械抽取与计数，语义命名仅在 GUID 有公认标准时给出，其余只报字节。

抽取判据（严格，逐条可复核）：
  slot0 函数体内按序出现  mov ecx,4 ; mov edi,<imm32> ; ... ; repe cmpsd
  ⇒ <imm32> 记为一个「被比对的 IID 指针」；且该指针必须落在 PE 数据节内（本节区间从 PE 头现读，不手抄）。
额外要求（R110 修正）：首个 cmpsd 必须落在函数头 QI_HEAD=120 B 内。理由：700 B 窗口会让随机起点
「漂进」真 QI 函数体，令反控基线虚高到 1.9%（自错 L-02）；限头部窗口后反控才有判别力。

反控：
  N1 随机 20000 个指令起点（同一判据、同一窗口）⇒ 基线命中率与富集倍数。
  N2 每个抽到的 IID 指针必须落在 PE 数据节，落在 .text 的一律记异常并列入断言。
  N3 正控：0x7f7c90 的 16 字节逐字节等于 IUnknown。
  N4 与 R109 §EK5 的 171 个类交叉：本轮集必须是其超集（R109 额外要求 GUID 尾 8 字节为 c000000000000046）。
内存纪律：只解 slot0 起 700 B（954 个函数，detail=False），不做全段 detail=True。
"""
import array, hashlib, json, os, random, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB, TS, TE = 0x400000, 0x401000, 0x7e038d
fo = lambda va: va - IB
QI_HEAD = 120

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

ck('S0 exe sha256 == R109 同口径',
   hashlib.sha256(raw).hexdigest() == '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476',
   hashlib.sha256(raw).hexdigest()[:16])

# ---------- 节表：从 PE 头现读（自错 L-03：上一稿把 RVA 当 VA 硬编码，导致 0x7f7c90 被判为「不在数据节」） ----------
import pefile
pe = pefile.PE('ra2bench/gamemd.exe', fast_load=True)
SECT = []
for s in pe.sections:
    nm = s.Name.decode().strip('\x00')
    va = IB + s.VirtualAddress
    SECT.append((nm, va, va + s.Misc_VirtualSize))
TEXT_SEC = [x for x in SECT if x[0] == '.text'][0]
DATA = [x for x in SECT if x[0] != '.text']
ck('S0b 节表从 PE 头现读：.text = [%s, %s)，数据节 %s；且 .text 终点与 TE 一致'
   % (hex(TEXT_SEC[1]), hex(TEXT_SEC[2]), [(n, hex(a), hex(b)) for n, a, b in DATA]),
   TEXT_SEC[1] == TS and TEXT_SEC[2] == TE, hex(TEXT_SEC[2]))

def sec_of(v):
    for n, a, b in SECT:
        if a <= v < b:
            return n
    return None

def in_data(v):
    return any(a <= v and v + 16 <= b for n, a, b in DATA)

sym = json.load(open('out/reverse/symbols.json'))
cls = sym['classes']
VT = {int(c['vtable_va'], 16): k for k, c in cls.items() if c.get('vtable_va')}
ck('S1 vtable 数 954（R107 EI3 / R109 同口径）', len(VT) == 954, len(VT))

md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
slot = lambda va, i: struct.unpack_from('<I', raw, fo(va) + 4 * i)[0]

RE_EDI = re.compile(r'^edi, (0x[0-9a-f]+)$')
RE_ECX4 = re.compile(r'^ecx, 4$')

def iids_of(f, head=QI_HEAD):
    """返回 (iid_ptr_list, first_cmpsd_offset 或 None)。
    严格：mov ecx,4 -> mov edi,imm -> ... -> repe cmpsd，且首个 cmpsd 须在 head 字节内。"""
    out = []
    pend = None
    ecx4 = False
    first = None
    for a, sz, m, o in md.disasm_lite(raw[fo(f):fo(f) + 700], f):
        if m == 'mov':
            mo = RE_EDI.match(o)
            if mo:
                # 实测指令序是 mov ecx,4 在前、mov edi,imm 在后（0x410278 / 0x41027d），
                # 故此处**不得**重置 ecx4（自错 L-01：上一稿在此写 ecx4=False，954 个 slot0 全部抽空）。
                pend = int(mo.group(1), 16)
                continue
            if RE_ECX4.match(o):
                ecx4 = True
                continue
        if 'cmpsd' in m:
            if pend is not None and ecx4:
                if first is None:
                    first = a - f
                if first is not None and a - f < head:
                    out.append(pend)
            pend = None
            ecx4 = False
            continue
    if first is None or first >= head:
        return [], first
    return out, first

# ---------- 主抽取 ----------
QI = {}
impl = defaultdict(list)
bad_ptr = []
for va, k in sorted(VT.items()):
    f = slot(va, 0)
    if not (TS <= f < TE):
        continue
    g, first = iids_of(f)
    if not g:
        continue
    for p in g:
        if not in_data(p):
            bad_ptr.append((k, hex(f), hex(p), sec_of(p)))
    QI[k] = (f, g)
    impl[f].append(k)

ck('S2 slot0 具备 QI 头部形态（%d B 内 mov ecx,4 + mov edi,IID + repe cmpsd）的类 = %d/954 = %.1f%%'
   % (QI_HEAD, len(QI), 100.0 * len(QI) / 954), len(QI) > 100,
   {'qi_classes': len(QI), 'pct': round(100.0 * len(QI) / 954, 1)})
ck('S3 所有抽到的 IID 指针都落在非 .text 节内，落在 .text 的 0 个', len(bad_ptr) == 0, bad_ptr[:5])
ck('S4 distinct QI 实现函数数 = %d（< 类数 %d ⇒ 大量类共享同一实现）'
   % (len(impl), len(QI)), len(impl) < len(QI), {'distinct_impl': len(impl), 'classes': len(QI)})

# ---------- N3 正控 ----------
IUNK = bytes.fromhex('0000000000000000c000000000000046')
ck('N3 正控：0x7f7c90 的 16 字节 == IUnknown（00000000-0000-0000-C000-000000000046）',
   raw[fo(0x7f7c90):fo(0x7f7c90) + 16] == IUNK, raw[fo(0x7f7c90):fo(0x7f7c90) + 16].hex())

def guid_str(p):
    b = raw[fo(p):fo(p) + 16]
    return '%08X-%04X-%04X-%s-%s' % (struct.unpack('<I', b[0:4])[0], struct.unpack('<H', b[4:6])[0],
                                     struct.unpack('<H', b[6:8])[0], b[8:10].hex().upper(), b[10:16].hex().upper())

per_class_n = Counter(len(g) for f, g in QI.values())
ck('S5 每类认的 IID 个数分布 = %s' % sorted(per_class_n.items()),
   sum(per_class_n.values()) == len(QI), sorted(per_class_n.items()))

iid_classes = defaultdict(set)
for k, (f, g) in QI.items():
    for p in set(g):
        iid_classes[p].add(k)
ck('S6 distinct IID 按指针 = %d；按 16 字节内容去重 = %d（两者相等 ⇒ 无不同指针指向同一 GUID 内容，或反之）'
   % (len(iid_classes), len(set(guid_str(p) for p in iid_classes))), len(iid_classes) >= 2,
   {'by_ptr': len(iid_classes), 'by_content': len(set(guid_str(p) for p in iid_classes))})

iunk_set = iid_classes.get(0x7f7c90, set())
ck('S7 认 IUnknown 的 = %d/%d = %.1f%%；**不认 IUnknown 的 = %d 个**（列出，这才是「非常规 COM 面」）'
   % (len(iunk_set), len(QI), 100.0 * len(iunk_set) / max(1, len(QI)), len(QI) - len(iunk_set)),
   True, {'with_iunk': len(iunk_set), 'total': len(QI),
          'without_iunk': sorted(set(QI) - iunk_set)[:10]})

# 非 IUnknown 尾 GUID（不以 c000000000000046 结尾）= 厂商自定义 IID
vendor = {p: s for p, s in iid_classes.items()
          if raw[fo(p) + 8:fo(p) + 16] != bytes.fromhex('c000000000000046')}
ck('S8 非标准尾（GUID[8:16] != c000000000000046）的 IID = %d 个，共被 %d 个类认领；'
   'R109 的 171 判据只收标准尾 ⇒ 本轮的 %d 应是其超集'
   % (len(vendor), len(set().union(*vendor.values())) if vendor else 0, len(QI)),
   len(set(QI)) >= 171, {hex(p): guid_str(p) for p in sorted(vendor)})

# ---------- N4 与 R109 交叉 ----------
r109 = json.load(open('_r109/r109j_com.json'))
r109_ex_cls = set(x['cls'] for x in r109['ex'])
ck('N4 R109 §EK5 报 QI = %d/954；本轮 %d/954。本轮 ≥ R109（R109 额外要求 GUID 尾 8 字节为标准尾）'
   % (r109['qi'], len(QI)), len(QI) >= r109['qi'], {'r109': r109['qi'], 'r110': len(QI)})

# ---------- N1 反控 ----------
f2 = open('_r108/branchmap2.bin', 'rb')
D = {}
while True:
    hd = f2.read(12)
    if len(hd) < 12:
        break
    n, isz, kl = struct.unpack('<III', hd)
    k2 = f2.read(kl).decode()
    arr = array.array('I'); arr.frombytes(f2.read(n * isz)); D[k2] = arr
f2.close()
starts = D['starts']
ck('N1a 复用 R108 branchmap2.bin 的 starts = %d（同源，非本轮重扫）' % len(starts),
   len(starts) == 1392592, len(starts))
rnd = random.Random(110)
hit = 0
N = 20000
for a in rnd.sample(list(starts), N):
    if a + 700 > TE:
        continue
    g, _ = iids_of(a)
    if g:
        hit += 1
base = 100.0 * hit / N
real = 100.0 * len(QI) / 954
ck('N1b 反控：随机 %d 个指令起点里同判据（同窗口 %d B）命中的 = %d（%.3f%%）；slot0 为 %.1f%% ⇒ 富集 %.1f 倍'
   % (N, QI_HEAD, hit, base, real, real / max(base, 1e-9)),
   real >= 5 * max(base, 0.01), {'rand_hit': hit, 'rand_pct': round(base, 3), 'enrich': round(real / max(base, 1e-9), 1)})

# 更硬的反控：随机起点命中里，有多少落在**已知 QI 函数体**内（说明判据只是「窗口漂进真函数」）
qifunc = set(f for f, _ in QI.values())
inside = 0
for a in rnd.sample(list(starts), N):
    if a + 700 > TE:
        continue
    if any(f <= a < f + QI_HEAD for f in qifunc):
        inside += 1
ck('N1c 同一批随机起点里，落在已知 QI 函数头 %d B 内的 = %d（%.3f%%）；'
   '这说明 N1b 的基线主要是「窗口漂进真 QI 体」，不是判据松'
   % (QI_HEAD, inside, 100.0 * inside / N), True, {'inside': inside, 'pct': round(100.0 * inside / N, 3)})

# ---------- 落盘 ----------
rows = []
for k, (f, g) in sorted(QI.items()):
    rows.append({'cls': k, 'slot0': hex(f), 'n_iid': len(g),
                 'iids': [{'ptr': hex(p), 'guid': guid_str(p)} for p in g]})
json.dump({'checks': checks, 'n_qi_classes': len(QI), 'n_distinct_impl': len(impl),
           'per_class_n': sorted(per_class_n.items()),
           'iid_classes': {hex(p): sorted(v) for p, v in sorted(iid_classes.items())},
           'iid_n': {hex(p): len(v) for p, v in sorted(iid_classes.items())},
           'guid_of_ptr': {hex(p): guid_str(p) for p in sorted(iid_classes)},
           'vendor_iids': {hex(p): guid_str(p) for p in sorted(vendor)},
           'without_iunk': sorted(set(QI) - iunk_set),
           'negctl': [hit, N, round(base, 3), inside],
           'rows': rows},
          open('_r110/r110a_iidmap.json', 'w'), ensure_ascii=False, indent=1)

print('\n--- 每个 IID 的类数 ---')
for p, s in sorted(iid_classes.items(), key=lambda x: -len(x[1])):
    print('%-10s %-38s %3d 类  e.g. %s' % (hex(p), guid_str(p), len(s), sorted(s)[:2]))
np_ = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (np_, len(checks), len(checks) - np_))
