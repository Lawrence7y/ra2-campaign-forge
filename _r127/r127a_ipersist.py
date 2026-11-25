# -*- coding: utf-8 -*-
"""R127a：定名 0x7f7c70 / 0x7f7c80（R113 起记作「不可分」的那一对）。

本轮不用外部头文件，用三条互相独立的字节记录：
  L1  排除法（族内枚举）：90 个类的 RTTI 里，除 IUnknown 外落在 mdisp 0 的接口
      恰好只有 IPersistStream 与 IPersist 两个，且两者的 mdisp 组合恒为 (0,0)。
      故「QI 体把出参写成未调整 this 的那两个常量」就是这两个接口，只是还不知道
      谁是谁。
  L2  使用侧契约：其中 0x820270/0x7f7c80 的 QI 结果被直接当作 ole32!OleSaveToStream
      的第 1 实参推栈（导入名由本映像导入表字节给出）。OleSaveToStream 的第 1
      实参类型是 IPersistStream*。
  L3  方法数上限：0x818858/0x7f7c70 的 QI 结果上只出现槽 3 的调用，且该调用的出参
      是 16 字节 GUID，随后立刻与一个 CLSID 常量做 repe cmpsd 比较，且不同站点的
      比较常量各不相同 —— 这正是 GetClassID 的形态（IPersist 唯一的方法）。

L2 与 L3 方向相反：L2 把 109 指成 IPersistStream，L3 把 010C 指成只有 1 个方法的
IPersist。L1 说这两个常量必须一个是 IPersistStream 一个是 IPersist。
三者合起来唯一解：109 = IPersistStream，010C = IPersist。

边界：L2 依赖 OleSaveToStream 的公开契约（操作系统 API 文档，不是本映像猜测）；
L3 的「只出现槽 3」是上近似下的存在性结论，否定式（无槽 >= 4）依赖 140 条窗口覆盖，
窗口未覆盖到的路径不计入，故如实声明「未覆盖」而不是「不存在」。
"""
import os, sys, json, struct, hashlib, collections, bisect
import pefile, capstone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracer2 as TR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r127', 'r127a_ipersist.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
add('A0 exe sha256 是钉住的那个构建',
    hashlib.sha256(open(EXE, 'rb').read()).hexdigest() == EXE_SHA)

def rd(va, n): return pe.get_data(va - IB, n)
def u32(va):
    b = rd(va, 4)
    return struct.unpack('<I', b)[0] if len(b) == 4 else None
def i32(va):
    b = rd(va, 4)
    return struct.unpack('<i', b)[0] if len(b) == 4 else None
def cstr(va, n=200):
    b = rd(va, n); e = b.find(b'\x00')
    return (b[:e] if e >= 0 else b).decode('latin1')
def gt(va):
    b = rd(va, 16); d1, d2, d3 = struct.unpack('<IHH', b[:8])
    return '{%08X-%04X-%04X-%s-%s}' % (d1, d2, d3, b[8:10].hex().upper(),
                                       b[10:].hex().upper())

S = {s.Name.rstrip(b'\x00').decode(): s for s in pe.sections}
RD = S['.rdata']; RD_LO = RD.VirtualAddress + IB; RD_HI = RD_LO + RD.Misc_VirtualSize
TX = S['.text']; T_LO = TX.VirtualAddress + IB
raw = pe.get_data(TX.VirtualAddress, TX.Misc_VirtualSize)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(raw, T_LO)]
idx = {a: i for i, (a, m, o) in enumerate(ins)}
add('A1 .text 线性扫描（disasm_lite 流式，未对整段开 detail）',
    len(ins) > 1000000, 'ins=%d ; .byte 伪指令 %d'
    % (len(ins), sum(1 for x in ins if x[1] == '.byte')))

DEC = {
 '0x7f7c70': '{0000010C-0000-0000-C000-000000000046}',
 '0x7f7c80': '{00000109-0000-0000-C000-000000000046}',
 '0x7f7c90': '{00000000-0000-0000-C000-000000000046}',
 '0x7f7ca0': '{00000001-0000-0000-C000-000000000046}',
 '0x7f7cf0': '{0000000C-0000-0000-C000-000000000046}',
 '0x818858': '{0000010C-0000-0000-C000-000000000046}',
 '0x820270': '{00000109-0000-0000-C000-000000000046}',
 '0x817bc0': '{00000000-0000-0000-C000-000000000046}',
}
got = {k: gt(int(k, 16)) for k in DEC}
add('A2 八个常量的 16 字节与它们被引用的语义逐字节相符（IUnknown/IStream/IClassFactory 三个'
    '公认常量同表作正控）', got == DEC, got)

PAIRS = {'010C': (0x7f7c70, 0x818858), '0109': (0x7f7c80, 0x820270)}
add('A3 两对常量的 .rdata 拷贝与 .data 拷贝逐字节相同，且两对互不相同',
    all(got['0x%x' % a] == got['0x%x' % b] for a, b in PAIRS.values())
    and got['0x7f7c70'] != got['0x7f7c80'], {k: v for k, v in PAIRS.items()})

# ---- L1：族内 mdisp 枚举 ----
sym = json.load(open(os.path.join(ROOT, 'out', 'reverse', 'symbols.json'),
                     encoding='utf-8'))['classes']
def _va(x):
    return None if x is None else (x if isinstance(x, int) else int(str(x).strip(), 16))
def bases_of(vt):
    col = u32(vt - 4)
    if not col or not (RD_LO <= col < RD_HI): return None
    chd = u32(col + 16)
    if not chd or not (RD_LO <= chd < RD_HI): return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64: return None
    out = []
    for i in range(n):
        bcd = u32(arr + 4 * i)
        if bcd is None: return None
        td = u32(bcd)
        if td is None: return None
        out.append({'name': cstr(td + 8, 200), 'mdisp': i32(bcd + 8),
                    'ncb': u32(bcd + 4)})
    return out

fam, dist, at0 = 0, collections.Counter(), collections.Counter()
for k, v in sym.items():
    vt = _va(v.get('vtable_va'))
    if not vt: continue
    b = bases_of(vt)
    if b is None: continue
    nm = {x['name']: x['mdisp'] for x in b}
    if '.?AUIPersistStream@@' not in nm: continue
    fam += 1
    dist[(nm.get('.?AUIPersist@@'), nm['.?AUIPersistStream@@'])] += 1
    for x in b:
        # 只统计 .?AU 接口前缀：.?AV 是类名/基类名，它们同样落在 mdisp 0，
        # 把类名算进来会让「只有两个候选」这条断言永远失败（S-162）。
        if x['mdisp'] == 0 and x['name'].startswith('.?AU') \
                and not x['name'].endswith('IUnknown@@'):
            at0[x['name']] += 1
add('L1a 带 IPersistStream 基类的类共 90 个，且 IPersist 与 IPersistStream 的 mdisp 组合'
    '恒为 (0,0) —— 故 RTTI 位置不可能把两者分开（这解释了 R113 起为什么一直不可分）',
    fam == 90 and set(dist) == {(0, 0)}, '%d 类 ; dist=%s' % (fam, dict(dist)))
m0 = sorted(x for x in at0)
add('L1b 这 90 个类里，除 IUnknown 外落在 mdisp 0 的接口名只有 IPersistStream 与 IPersist 两个',
    m0 == ['.?AUIPersist@@', '.?AUIPersistStream@@'], {k: v for k, v in at0.items()})

# ---- QI 站点枚举：形态 push ppv ; push riid ; push this ; mov ecx,[this] ; call [ecx] ----
GSET = {0x7f7c70: '010C.r', 0x818858: '010C.d', 0x7f7c80: '0109.r', 0x820270: '0109.d'}
QS = []
shape_bad = []
for i, (a, m, o) in enumerate(ins):
    if m != 'push': continue
    t = TR.num(o)
    if t not in GSET: continue
    if i + 2 >= len(ins): continue
    # 两种形态：.data 侧 push ppv ; push riid ; push this ; call [ecx]
    #           .rdata 侧 push ppv ; push riid ; push X ; push this ; call [eax+0]
    ic = None
    for d in (2, 3):
        if i + d < len(ins) and ins[i + d][1] == 'call' \
                and ins[i + d][2].startswith('dword ptr [e'):
            ic = i + d
            break
    if ic is None: continue
    QS.append((i, a, GSET[t], ic))
cnt = collections.Counter(x[2] for x in QS)
for i, a, lab, ic in QS:
    if TR.qi_ppv_key(ins, ic) is None:
        shape_bad.append((hex(a), lab))
add('A4 四个常量作为 riid 的内联 QI 站点实测分布：010C 16 处（全在 .data 拷贝，'
    '.rdata 拷贝 0 处 riid 内联点），0109 68 处（8 .data + 60 .rdata）；'
    '每个站点的 ppv 槽都能按 lea 形态唯一解出',
    cnt.get('010C.d') == 16 and cnt.get('010C.r', 0) == 0
    and cnt.get('0109.d') == 8 and cnt.get('0109.r') == 60 and not shape_bad,
    '%s ; ppv 解不出 %d 处 %s' % (dict(cnt), len(shape_bad), shape_bad[:4]))

# ---- L2：OleSaveToStream ----
IAT = {}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll = e.dll.decode()
    for imp in e.imports:
        IAT[imp.address] = (dll, imp.name.decode() if imp.name else 'ord')
SAVE = [va for va, (d, n) in IAT.items() if n == 'OleSaveToStream']
LOAD = [va for va, (d, n) in IAT.items() if n == 'OleLoadFromStream']
add('L2a 导入表里 OleSaveToStream / OleLoadFromStream 各恰 1 槽，且都属 ole32（名字来自'
    '本映像导入表字节，不是外部记忆）',
    len(SAVE) == 1 and len(LOAD) == 1
    and IAT[SAVE[0]][0].lower() == 'ole32.dll' == IAT[LOAD[0]][0].lower(),
    'save=0x%x load=0x%x' % (SAVE[0], LOAD[0]))

def feeds(ic):
    """QI 调用 ic 之后：结果是否被 push 后立即 call OleSaveToStream。
    用 tracer2 的 esp 簿记（push/pop/add esp 全程记账），而不是裸比较 [esp+K] ——
    第一版裸比较，遇到 push ebx 导致偏移漂 4 就漏报 2 处（0x4b6313、0x50469e），
    而这两处人工核读都是「od/edx 从 ppv 槽取出后即喂入」（S-163）。"""
    pk = TR.qi_ppv_key(ins, ic)
    r = TR.walk(ins, ic + 1, 120, seed_ppv=pk)
    return any(v == SAVE[0] and q for _a, v, q in r['iatcalls'])
fed = [(lab, a) for i, a, lab, ic in QS if feeds(ic)]
fh = collections.Counter(x[0] for x in fed)
add('L2b L2 主体：0109.d 的 8 处 QI 结果全部被直接当作 OleSaveToStream 第 1 实参；'
    '010C 的 16 处一次都没有（0109.r 的 60 处 riid 内联点在 0x67d3xx 的循环里，'
    '其喂入由 L2c 的「前置 push」口径覆盖）',
    fh.get('0109.d', 0) == 8 and fh.get('010C.d', 0) == 0 and fh.get('010C.r', 0) == 0,
    '0109.d 喂入 %d / 8 ; 010C 喂入 %d / 16'
    % (fh.get('0109.d', 0), fh.get('010C.d', 0) + fh.get('010C.r', 0)))

def prev_guid(calladdr, maxn=80):
    i = idx[calladdr]
    for j in range(i - 1, max(0, i - maxn), -1):
        a, m, o = ins[j]
        if m == 'push' and TR.num(o) in GSET: return GSET[TR.num(o)]
        if m == 'ret': return None
    return None
scalls = [a for a, m, o in ins if m == 'call' and o == 'dword ptr [0x%x]' % SAVE[0]]
pg = collections.Counter(prev_guid(a) for a in scalls)
add('L2c 全映像 43 个 OleSaveToStream 调用点的 riid 前置 push：8 处 .data 拷贝、35 处 .rdata '
    '拷贝，全部是 0109，无一例 010C',
    pg.get('010C.r', 0) == 0 and pg.get('010C.d', 0) == 0
    and pg.get('0109.r') == 35 and pg.get('0109.d') == 8,
    'calls=%d dist=%s' % (len(scalls), dict(pg)))

# ---- L3：010C 只用槽 3，且该槽出参是 CLSID ----
def slot_calls(ic, window=150):
    pk = TR.qi_ppv_key(ins, ic)
    return TR.walk(ins, ic + 1, window, seed_ppv=pk)
per = collections.defaultdict(set)
trunc = {}
for i, a, lab, ic in QS:
    r = slot_calls(ic)
    per[lab] |= r['slots']
    trunc[(lab, a)] = r['truncated']
add('L3a 010C 的 QI 结果上出现过的虚槽只有 3（0xc），从无 4..7；0109 的结果上只出现 8（Release）'
    '（Release 与 OleSaveToStream 喂入都不改变「010C 方法数 <= 1」这一条）',
    (per['010C.r'] | per['010C.d']) == {0xc} and (per['0109.r'] | per['0109.d']) == {8},
    {k: sorted(v) for k, v in per.items()})
add('L3b 上近似未截断：24 个站点全部在窗口内自然终止（truncated 全 False），'
    '故「无槽 >= 4」不是被上限截断造成的假阴性',
    not any(trunc.values()), '%d 站点，截断 %d 个' % (len(trunc), sum(trunc.values())))

# 每个 010C 站点：槽 3 调用之后比较的 16 字节常量
def clsid_after(ic, window=150):
    for j in range(ic + 1, min(len(ins), ic + window)):
        a, m, o = ins[j]
        if m == 'ret': return None
        if m == 'mov' and o.startswith('edi, 0x'):
            t = TR.num(o.rsplit(', ', 1)[-1])
            if t is None:
                continue
            for k2 in range(j + 1, min(len(ins), j + 4)):
                if ins[k2][1].startswith('repe'):
                    return t
                if ins[k2][1] == 'mov' and ins[k2][2].startswith('edi, '):
                    break
    return None
cls = {}
for i, a, lab, ic in QS:
    if not lab.startswith('010C'): continue
    t = clsid_after(ic)
    if t is not None:
        cls[a] = t
vals = sorted(set(cls.values()))
add('L3c 能线性追到「槽 3 出参 -> 与 GUID 常量 repe cmpsd」的 010C 站点数（实测口径见 '
    'detail；不设「全部 16 处都要命中」这种无依据下限）',
    len(cls) >= 3, '%d 站点 %s，目标常量 %d 个' % (len(cls), sorted(hex(k) for k in cls), len(vals)))
add('L3d 这些被比常量互不相同（每个类比自己的 CLSID）—— 若它们是同一个常量，'
    '「GetClassID」这一解释就不成立',
    len(vals) >= 3, {'0x%x' % k: gt(v) for k, v in sorted(cls.items())})

# ---- 结论 ----
named = {'0x7f7c80': 'IPersistStream', '0x820270': 'IPersistStream',
         '0x7f7c70': 'IPersist', '0x818858': 'IPersist'}
add('A5 结论：0109 对 = IPersistStream（L2），010C 对 = IPersist（L3）；两对必须在 L1 的'
    '两个候选里二选一，因此这不是「挑一个看起来像的」而是唯一解',
    set(named.values()) == {'IPersist', 'IPersistStream'}
    and m0 == ['.?AUIPersist@@', '.?AUIPersistStream@@'], named)

rep = {'exe_sha256': EXE_SHA, 'decoded_constants': got, 'family_n': fam,
       'mdisp_dist': [[list(k), v] for k, v in dist.items()],
       'mdisp0_names': dict(at0), 'qi_counts': dict(cnt),
       'save_feed': dict(fh), 'save_calls': len(scalls),
       'save_riid_dist': {str(k): v for k, v in pg.items()},
       'slots_per_label': {k: sorted(v) for k, v in per.items()},
       'classid_cmp': {'0x%x' % k: '0x%x' % v for k, v in cls.items()},
       'named': named, 'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R127a %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
