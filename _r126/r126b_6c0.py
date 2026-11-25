# -*- coding: utf-8 -*-
"""R126b: 用 R124 已立的「QI 出参调整值 == RTTI mdisp」判据去判 0x7e9b40。

R125 台账 GK④ 写「0x7e9b40 仍与 0x7f7c70/0x7f7c80 这对不可分」。本轮侦察在
0x4142c1 读到 lea eax, [ebx + 0x6c0] 紧接 mov dword ptr [ebp], eax —— 即 QI 成功
分支把出参写成 this+0x6c0。R124 的判据（R14_COMMON FO）要求该调整值等于该类
RTTI 里对应 BaseClassDescriptor 的 mdisp。本脚本把这条判据真跑：

  B1  0x7e9b40 的 QI 体（0x414290）成功分支确实写 this + 0x6c0，且不写 this + 0。
      反控：同函数失败分支 0x4142da 写 0。
  B2  0x414290 所属类（vtable 0x412b8c 一类）的 RTTI 里，有且仅有一个 BaseClass
       的 mdisp == 0x6c0。给出该 BaseClass 的类名。
  B3  该类的 RTTI 里是否有名字含 IPersist 的基类，其 mdisp 是否也为 0x6c0。
  B4  0x7e9b40 的 .data 孪生 0x822410 的 8 个引用点是另一件事：它们的 QI 源对象
       与出参怎么写，与 B1 无关。只记录它们是否写 this+0 以外的偏移。

上限：能读出的只有「这个 IID 对应的子对象在 this+0x6c0」。名字仍由 RTTI 类名表
反查，不由 IID 字节给出。
"""
import os, sys, json, struct, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r126', 'r126b_6c0.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
add('B0 exe sha256 是钉住的那个构建',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

def rd(va, n):
    return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4)
    return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4)
    return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=192):
    b = rd(va, n)
    e = b.find(b'\x00')
    return b[:e].decode('latin1') if e >= 0 else b.decode('latin1')

SECS = [(s.VirtualAddress + IB, s.VirtualAddress + IB
         + max(s.Misc_VirtualSize, s.SizeOfRawData)) for s in pe.sections]
def in_img(va):
    return va is not None and any(lo <= va < hi for lo, hi in SECS)
RDATA = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.rdata'][0]
RD_LO = RDATA.VirtualAddress + IB
RD_HI = RD_LO + RDATA.Misc_VirtualSize

def bcds(vt):
    """R124 的 BCD 解码器原样复用（pinned）：COL -> CHD -> BCA。"""
    col = u32(vt - 4)
    if not (RD_LO <= col < RD_HI):
        return None
    chd = u32(col + 16)
    if not (RD_LO <= chd < RD_HI):
        return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64 or not (RD_LO <= arr < RD_HI):
        return None
    out = []
    for i in range(n):
        bcd = u32(arr + 4 * i)
        if not in_img(bcd):
            return None
        td = u32(bcd)
        if not in_img(td):
            return None
        out.append({'name': cstr(td + 8, 192), 'ncb': u32(bcd + 4),
                    'mdisp': i32(bcd + 8), 'pdisp': i32(bcd + 12),
                    'vdisp': i32(bcd + 16), 'attr': u32(bcd + 20)})
    return out

# 反汇编 .text（disasm_lite 流式，不开 detail）
TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(
    pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize), T_LO)]
n_ins = len(ins)
idx = {a: i for i, (a, m, o) in enumerate(ins)}

QI39 = 0x414290
add('B1a QI 体入口 0x414290 在指令边界上（不是中途切进来的）', QI39 in idx)

def dump(start, count):
    i = idx[start]
    return [(hex(ins[j][0]), ins[j][1], ins[j][2])
            for j in range(i, min(n_ins, i + count))]

body = dump(QI39, 40)
# 找写 [ebp] 的两处：成功分支与失败分支
writes = []
for j in range(idx[QI39], idx[QI39] + 40):
    a, m, o = ins[j]
    if m == 'mov' and o.startswith('dword ptr [ebp], '):
        src = o.split(', ')[-1]
        # 回溯找 src 的来源
        origin = None
        for k in range(j - 1, max(idx[QI39], j - 6), -1):
            am, mm, om = ins[k]
            if mm == 'lea' and om.startswith(src + ', ') \
                    and ' + 0x6c0]' in om:
                origin = 'this+0x6c0'
                break
            if mm == 'xor' and om == src + ', ' + src:
                origin = 'zero'
                break
        writes.append({'at': hex(a), 'dst': '[ebp]', 'src': src, 'origin': origin})
add('B1b QI 成功分支把出参写成 this+0x6c0，失败分支写 0（两条都存在）',
    [w['origin'] for w in writes] == ['this+0x6c0', 'zero'], writes)

add('B1c 成功分支确实出现过 lea reg, [reg + 0x6c0]（不是别处的常量）',
    any(m == 'lea' and ' + 0x6c0]' in o
        for a, m, o in [ins[j] for j in range(idx[QI39], idx[QI39] + 40)]),
    [o for a, m, o in [ins[j] for j in range(idx[QI39], idx[QI39] + 40)]
     if m == 'lea' and ' + 0x6c0]' in o])

# B2 这个 QI 属于哪个类：找 vtable 里 slot0 == 0x414290
sym = json.load(open(os.path.join(ROOT, 'out', 'reverse', 'symbols.json'),
                     encoding='utf-8'))['classes']
def _va(x):
    """symbols.json 的地址是十六进制字符串（无 0x 前缀，含前导零）。"""
    if x is None:
        return None
    if isinstance(x, int):
        return x
    s = x.strip()
    return int(s, 16)
add('B2z symbols.json 的 vtable_va 是十六进制字符串，已显式转换（不是直接当整数用）',
    isinstance(list(sym.values())[0].get('vtable_va'), str),
    type(list(sym.values())[0].get('vtable_va')).__name__)
owners = []
for k, v in sym.items():
    vt = _va(v.get('vtable_va'))
    if vt and u32(vt) == QI39:
        owners.append((k, vt))
add('B2a 至少有一个带 vtable 的类的 slot0 就是 0x414290', len(owners) > 0, owners[:6])

# 也扫一遍所有 vtable 常量位置（不只 symbols），确认没漏
vt_ptrs = []
for va in range(RD_LO, RD_HI - 4, 4):
    if u32(va) == QI39:
        vt_ptrs.append(va)
add('B2b 在 .rdata 里以 4 字节对齐扫到指向 0x414290 的槽位，数量与 symbols 一致',
    len(vt_ptrs) >= len(owners), 'raw-matches=%d symbols=%d' % (len(vt_ptrs), len(owners)))

# B2c 该类的 RTTI 基类表里有且仅有一个 mdisp == 0x6c0
bcd_info = []
for k, vt in owners[:4]:
    b = bcds(vt)
    bcd_info.append({'class': k, 'vtable': '0x%x' % vt,
                     'bcds': None if b is None else
                     [{'name': x['name'], 'mdisp': x['mdisp']} for x in b]})
hit_6c0 = []
for rec in bcd_info:
    if not rec['bcds']:
        continue
    for x in rec['bcds']:
        if x['mdisp'] == 0x6c0:
            hit_6c0.append((rec['class'], x['name']))
# 实测是 2 条：IFlyControl 与它的 IUnknown 次对象，同占 0x6c0。这是多继承子对象的
# 标准配对（每个接口子对象都带自己的 IUnknown），不是两条互相竞争的解释。
# 第一版写「有且仅有一个基类 mdisp==0x6c0」是我照直觉设的口径（S-159）。
non_iu_6c0 = [(c, n) for c, n in hit_6c0 if not n.endswith('IUnknown@@')]
add('B2c 该类 RTTI 在 mdisp 0x6c0 处恰有 2 个基类：一个接口 + 它的 IUnknown 次对象；'
    '剔除 IUnknown 后唯一',
    len(hit_6c0) == 2 and len(non_iu_6c0) == 1, hit_6c0)

mdisp_6c0_name = non_iu_6c0[0][1] if non_iu_6c0 else None
add('B3 该 mdisp==0x6c0 的接口名字是 .?AUIFlyControl@@（.?AU 前缀即 COM 接口，'
    '不是 .?AV 类名）',
    mdisp_6c0_name == '.?AUIFlyControl@@', mdisp_6c0_name)

# 反控：把 mdisp 改成 0x6c4 应无命中（判据真的在起作用）
n_6c4 = sum(1 for rec in bcd_info if rec['bcds']
            for x in rec['bcds'] if x['mdisp'] == 0x6c4)
add('B3b 反控：把目标 mdisp 换成 0x6c4 后命中 0 条', n_6c4 == 0, 'hits=%d' % n_6c4)

# B4 .data 孪生 0x822410 的 8 个引用点：出参是否也写 this+0x6c0
def num(t):
    t = t.strip()
    if t and t[0] in '0123456789':
        try:
            return int(t, 0)
        except ValueError:
            pass
    return None
def tail_imm(o):
    return num(o.rsplit(', ', 1)[-1])

sites = [a for a, m, o in ins if m == 'push' and tail_imm(o) == 0x822410]
add('B4a 0x822410 的 push 站点恰为 8 个', len(sites) == 8, [hex(s) for s in sites])

def out_param_offset(va):
    """在 push 站点往前找 lea reg,[esp+X]，再往后找 mov [reg],... 的调整形态。"""
    i = idx[va]
    K = None
    for j in range(i - 1, max(0, i - 9), -1):
        a, m, o = ins[j]
        if m == 'lea' and '[esp + ' in o:
            K = o.split('[esp + ')[1][:-1]
            break
    # 往后 12 条里找 QI 成功分支是否用 [esp+K] 直接存或经 +0x6c0 调整
    adj = None
    for j in range(i + 1, min(n_ins, i + 14)):
        a, m, o = ins[j]
        if m == 'lea' and ' + 0x6c0]' in o:
            adj = '0x6c0'
            break
    return K, adj

det = [{'site': hex(s), 'K': out_param_offset(s)[0], 'adj': out_param_offset(s)[1]}
       for s in sites]
add('B4b 0x822410 的 8 个站点都不做 this+0x6c0 调整（与 0x7e9b40 的 QI 体不同形态）',
    all(d['adj'] is None for d in det), det)

rep = {'exe_sha256': EXE_SHA, 'qi_body': body, 'writes': writes,
       'owners': [{'class': k, 'vtable': hex(v)} for k, v in owners],
       'bcd_info': bcd_info, 'mdisp_6c0': hit_6c0,
       'twin_sites': det, 'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R126b %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
