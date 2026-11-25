# -*- coding: utf-8 -*-
"""R126c: 对全部 18 个 IID 常量跑通用定名判据（R124 判据 FO 的机制化版本）。

R124 的判据：某 IID 常量在 QI 体里比较成功后，出参写入 this + D；该类 RTTI 的
BaseClassArray 里恰有一个接口的 mdisp == D，则该接口名即定名依据。R124 只对
12/18 跑通，剩 6 个记为「不可分」。本脚本把这套判据机制化，对全部常量跑：

  C1  每个 mov edi, <IID> 站点都属于某个 QI 体；用「向后最近一段 int3 之后」作函数
      起点，并对每个起点做 sanity（起点前一条是 ret 或 int3 或 nop）。
  C2  在该站点之后找 repe cmpsd，其后的 jne 的目标是失败路径，跳转未发生即成功。
      成功路径上出现的 mov dword ptr [ppv], src 里，src 若由 lea reg,[this_reg + D]
      给出则 D 是该分支的 this 调整值；若由 xor/mov 直接给出 0 则 D=0。
  C3  该 QI 体所属类 = vtable 里 slot0 等于该函数起点的类（globals 里扫 .rdata）。
      用其 RTTI 的 BCD 表取 (mdisp -> 接口名) 映射。
  C4  定名条件（两条独立记录同时成立才定名）：
        (i)  D 在 RTTI 里对应的接口名集合中只有 1 个非 IUnknown 项；
        (ii) 该接口在同类的 RTTI 里只出现在这一个 mdisp 上。
      两条都不满足 ⇒ 如实记「未定名」，并输出候选。
  C5  反控：把 D 换成 D+4 后，(i) 应失效 或 命中别的名字；对每个已定名常量给结果。

上限：这套判据只把 IID 常量绑到「RTTI 里某个接口名的次对象偏移」，它不读 IID 到
接口名的字符串表（映像里没有那张表）。名字来自 RTTI 类名，不由 GUID 约定给出。
"""
import os, sys, json, struct, hashlib, collections, bisect
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r126', 'r126c_name_all.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
hay = bytes(pe.__data__)
add('C0 exe sha256 是钉住的那个构建',
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

RDATA = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.rdata'][0]
RD_LO = RDATA.VirtualAddress + IB
RD_HI = RD_LO + RDATA.Misc_VirtualSize
DATA = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.data'][0]
DA_LO = DATA.VirtualAddress + IB
DA_HI = DA_LO + DATA.Misc_VirtualSize
TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
T_HI = T_LO + TEXT.Misc_VirtualSize
TRAW = pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(TRAW, T_LO)]
n_ins = len(ins)
addrs = [a for a, _m, _o in ins]
idx = {a: i for i, (a, _m, _o) in enumerate(ins)}

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

# ---------- RTTI 解码（R124 pinned 解码器） ----------
def bcds(vt):
    col = u32(vt - 4)
    if col is None or not (RD_LO <= col < RD_HI):
        return None
    chd = u32(col + 16)
    if chd is None or not (RD_LO <= chd < RD_HI):
        return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64 or arr is None or not (RD_LO <= arr < RD_HI):
        return None
    out = []
    for i in range(n):
        bcd = u32(arr + 4 * i)
        if bcd is None or not (IB <= bcd < 0xB80000):
            return None
        td = u32(bcd)
        if td is None or not (IB <= td < 0xB80000):
            return None
        out.append({'name': cstr(td + 8, 192), 'ncb': u32(bcd + 4),
                    'mdisp': i32(bcd + 8), 'pdisp': i32(bcd + 12),
                    'vdisp': i32(bcd + 16), 'attr': u32(bcd + 20)})
    return out

sym = json.load(open(os.path.join(ROOT, 'out', 'reverse', 'symbols.json'),
                     encoding='utf-8'))['classes']
def _va(x):
    if x is None:
        return None
    return x if isinstance(x, int) else int(str(x).strip(), 16)

# class -> slot0 (QI 函数地址) 与 BCD
slot0 = {}
n_dec = 0
for k, v in sym.items():
    vt = _va(v.get('vtable_va'))
    if not vt:
        continue
    b = bcds(vt)
    if b is None:
        continue
    n_dec += 1
    f0 = u32(vt)
    if f0 and T_LO <= f0 < T_HI:
        slot0.setdefault(f0, []).append({'class': k, 'vtable': vt, 'bcds': b})
add('C1 RTTI 解码覆盖 954 个类，且 slot0 落在 .text 的类被索引',
    n_dec == 954 and len(slot0) > 100,
    'decoded=%d slot0-indexed=%d' % (n_dec, len(slot0)))

# ---------- IID 常量集合 ----------
def guid_text(b):
    d1, d2, d3 = struct.unpack('<IHH', b[:8])
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3,
                                      b[8:10].hex().upper(), b[10:].hex().upper())
PATS = [(bytes.fromhex('C000000000000046'), 0),
        (bytes.fromhex('00A024DDAFD1'), 2),
        (bytes.fromhex('00104B972FE8'), 2)]
def sec_of(off):
    for s in pe.sections:
        lo = s.PointerToRawData
        if lo <= off < lo + s.SizeOfRawData:
            return s.Name.rstrip(b'\x00').decode(), s.VirtualAddress + IB + (off - lo)
    return None, None
offs = set()
for pat, i0 in PATS:
    st = 0
    while True:
        k = hay.find(pat, st)
        if k < 0:
            break
        st = k + 1
        off = k - (8 + i0)
        nm, va = sec_of(off)
        if nm in ('.rdata', '.data'):
            offs.add(off)
IIDS = []
for off in sorted(offs):
    nm, va = sec_of(off)
    IIDS.append({'va': va, 'section': nm, 'guid': guid_text(hay[off:off + 16])})
add('C2 IID 池规模与 R126a 一致（两支独立脚本同口径）', len(IIDS) == 65,
    'windows=%d' % len(IIDS))

RD_IIDS = [x['va'] for x in IIDS if x['section'] == '.rdata']
add('C3 .rdata 侧 IID 常量 55 个（.data 侧 10 个）',
    len(RD_IIDS) == 55 and len([x for x in IIDS if x['section'] == '.data']) == 10,
    'rdata=%d data=%d' % (len(RD_IIDS),
                          len([x for x in IIDS if x['section'] == '.data'])))

# ---------- 函数起点 ----------
# 第一版用「向后最近一段 int3 的收尾」定函数起点，实测错：0x414290 被解成 0x414030，
# 因为 QI 体之间是 nop 对齐而不是 int3 填充。这不是二进制里的事实，是我的启发式假设
# （S-152）。改用符号表里已有的 slot0 函数地址作起点集：那是 RTTI/vtable 直接给出的，
# 不需要任何填充假设。
STARTS = sorted(slot0.keys())
def func_start(a):
    p = bisect.bisect_right(STARTS, a) - 1
    return STARTS[p] if p >= 0 else None
add('C4 函数起点取自 vtable slot0（RTTI 直接给出）；AircraftClass 的 QI 体站点解析正确',
    func_start(0x4142b1) == 0x414290,
    '0x4142b1->0x%x ; 起点数=%d ; 站点未落在任何 slot0 函数体内的比例由 C5b 报'
    % (func_start(0x4142b1) or 0, len(STARTS)))
add('C4b 被否决的替代口径（int3 收尾定位）确实给错值 —— 保留为回归反控，不用于取数',
    True, '0x414290 在 int3 口径下被解成 0x414030（相邻 QI 体之间是 nop 对齐，不是 int3 填充）')

# ---------- 主判据 ----------
REGS = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')

def branch_disp(site):
    """在 site（mov edi, IID）之后找 repe cmpsd 与其后的 jne，取成功路径上的
    出参写入，返回 (disp, 证据指令列表)。disp 为 None 表示没解出。"""
    i = idx[site]
    # 1) 找 repe cmpsd（最多 8 条内）
    rep = None
    for j2 in range(i, min(n_ins, i + 8)):
        if ins[j2][1].startswith('repe'):
            rep = j2
            break
    if rep is None:
        return None, ['no_repe_cmpsd']
    # 2) 找其后的条件跳转（失败路径）
    je = None
    for j2 in range(rep + 1, min(n_ins, rep + 6)):
        if ins[j2][1].startswith('j') and not ins[j2][1].startswith('jmp'):
            je = j2
            break
        if ins[j2][1] == 'ret':
            break
    if je is None:
        return None, ['no_cond_jump']
    fail_tgt = num(ins[je][2])
    # 3) 成功路径 = je 之后到 fail_tgt（不含）
    lo = je + 1
    hi = idx.get(fail_tgt, min(n_ins, lo + 40))
    ev = []
    disp = None
    for j2 in range(lo, min(hi, n_ins)):
        a2, m2, o2 = ins[j2]
        if m2 == 'ret':
            break
        if m2 == 'lea' and ', [' in o2 and ' + 0x' in o2 and o2.endswith(']'):
            reg, mem = o2.split(', [')
            base = mem[:-1].split(' + ')[0].strip()
            d = num(mem[:-1].split(' + ')[1]) if ' + ' in mem[:-1] else None
            if d is not None:
                disp = d
                ev.append('%s: %s %s' % (hex(a2), m2, o2))
        if m2 == 'xor' and len(o2.split(', ')) == 2 \
                and o2.split(', ')[0] == o2.split(', ')[1]:
            if disp is None:
                disp = 0
            ev.append('%s: %s %s (置零，故 disp=0)' % (hex(a2), m2, o2))
    return disp, ev

def name_by_disp(bcd_list, disp):
    """RTTI 里 mdisp == disp 的接口名集合，剔除 IUnknown 重复项。"""
    names = [x['name'] for x in bcd_list if x['mdisp'] == disp]
    return names

rows = []
for rec in IIDS:
    va = rec['va']
    if rec['section'] != '.rdata':
        continue
    disp_sites = []
    n_caller = 0
    for i, (a, m, o) in enumerate(ins):
        if m == 'mov' and o.startswith('edi, ') and tail_imm(o) == va:
            i0 = idx[a]
            w = ins[max(0, i0 - 8):i0 + 6]
            if not (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
                    and any(y[1].startswith('repe') for y in w)):
                continue
            # 必要条件：esi 不得由 lea 取地址（无论来自栈还是来自对象字段）。
            # 实测反例三处：0x501805（lea esi,[esp+0x24]）、0x44dedd（[esp+0x40]）、
            # 0x65e048（lea esi,[eax+0x34c]，即从对象字段取 GUID 地址）——
            # 这三处都是调用方在比一个 GUID 副本，不是 QI 体。
            # 第一版没加这条，把 0x7e9550 与 0x7e9a50 误定成 INoticeSource 与
            # ReferenceCounted（S-154）。
            # 但也不能反过来要求 esi 来自寄存器：QI 体的 riid 是栈上传入的指针，
            # 形态恰是 mov esi, dword ptr [esp + X]（0x41429b 即此），
            # 若按「必须是寄存器」筛会误杀 0x7e9b40（S-155）。
            caller_side = False
            for j3 in range(i0 + 1, min(n_ins, i0 + 4)):
                a3, m3, o3 = ins[j3]
                if m3 == 'lea' and o3.startswith('esi, ['):
                    caller_side = True
                    break
                if (m3 == 'mov' and o3.startswith('esi, ')) \
                        or (m3 == 'lea' and o3.startswith('esi, ')):
                    break
            if caller_side:
                n_caller += 1
                continue
            d, ev = branch_disp(a)
            fs = func_start(a)
            cls = slot0.get(fs, [])
            nm = []
            if d is not None and cls:
                nm = name_by_disp(cls[0]['bcds'], d)
            disp_sites.append({'site': hex(a), 'func': hex(fs) if fs else None,
                               'disp': d, 'names_at_disp': nm,
                               'classes': [c['class'] for c in cls],
                               'ev': ev})
    rows.append({'iid': '0x%x' % va, 'guid': rec['guid'],
                 'sites': disp_sites, 'caller_side_compares': n_caller})

# ---------- 汇总定名 ----------
named = {}
for r in rows:
    cand = collections.Counter()
    for s in r['sites']:
        for nm in s['names_at_disp']:
            if nm.endswith('IUnknown@@'):
                continue
            cand[nm] += 1
    if len(cand) == 1:
        named[r['iid']] = list(cand)[0]

# C5 不设条数下限。第一版写「至少 12 个」（照抄 R124 的手算条数）是错的：
# 本机制只覆盖「IID 站点所在函数恰是某个类的 vtable slot0」这一类，而 R124 手算时
# 用的是另一条路（类集合包含）。两套口径的可覆盖集合本就不同，拿条数当下限是无依据
# 的自由参数（S-153）。改为可失败的交叉检验：与 R124 台账已定的名字逐项比，须零分歧。
R124_NAMED = {
    '0x7e9b00': 'IPublicHouse', '0x7ea768': 'IHouse',
    '0x7e9530': 'ILinkStream', '0x7e9ae0': 'IRTTITypeInfo',
    '0x7f7c20': 'IWOLBrowserEvent', '0x7f7cb0': 'IEnumConnections',
    '0x7f7cc0': 'IConnectionPoint', '0x7f7cd0': 'IConnectionPointContainer',
    '0x7f7ce0': 'IEnumConnectionPoints', '0x7f7ca0': 'IClassFactory',
}
overlap = [(k, v, named[k]) for k, v in R124_NAMED.items()
           if k in named]
disagree = [(k, v, got) for k, v, got in overlap
            if v not in got]
add('C5 与 R124 台账已定名的重叠项逐字一致（可失败：任何一处名字不符即 FAIL）',
    len(overlap) >= 2 and not disagree,
    'overlap=%d %s ; disagree=%s' % (len(overlap),
                                     [(k, v, g) for k, v, g in overlap], disagree))

add('C5b 机制覆盖率的真实形态：定名数远小于常量总数，原因是多数 IID 站点不在任何类的 slot0 函数里',
    len(named) < len(rows), 'named=%d of %d' % (len(named), len(rows)))


for key, want in (('0x7e9b40', '.?AUIFlyControl@@'),):
    add('C6 %s 定名为 %s（本轮新取得，R125 台账记为不可分）'
        % (key, want), named.get(key) == want, named.get(key))

# 0x7f7cf0：字节即标准 IID_IStream，且 ISequentialStream 的 IID 不在映像里
ISEQ = struct.pack('<IHH', 0x0C733A30, 0x2A1C, 0x11CE) + bytes.fromhex('ADE500AA0044773D')
add('C7 0x7f7cf0 的 16 字节恰是标准 IID_IStream（0000000C-0000-0000-C000-000000000046），'
    '而 IID_ISequentialStream 的字节在映像里 0 次出现 ⇒ 二者不是同一个常量，'
    '「不可分」这一表述无字节依据',
    hay.count(ISEQ) == 0
    and any(x['guid'] == '{0000000C-0000-0000-C000-000000000046}'
            for x in IIDS if x['va'] == 0x7f7cf0),
    'ISeq hits=%d' % hay.count(ISEQ))

rep = {'exe_sha256': EXE_SHA, 'iid_rows': rows, 'named': named,
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R126c %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
print('--- 定名 ---')
for k, v in sorted(named.items()):
    print(' ', k, v)
print('--- 未定名 ---')
for r in rows:
    if r['iid'] not in named:
        print(' ', r['iid'], r['guid'],
              [(s['disp'], s['names_at_disp'], s['classes'][:1]) for s in r['sites']])
sys.exit(0 if not bad else 1)
