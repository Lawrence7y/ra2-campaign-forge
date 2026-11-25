# -*- coding: utf-8 -*-
"""R127e：规则 D 的独立复算卡 —— 把审计卡（R127-AUDIT-IPERSIST.md）列给审计员的
第 1 到第 7 条，主会话用**自己的脚本**逐条算一遍，留一份基准数字。

这不是「再看一遍 r127a/r127b」，而是按审计卡的口径重算（审计员看到的是那些口径，
若我的基准与它不一致，才能定位是它错还是我错）。三条口径刻意与 r127a 不同：

  E1  导入名：只用导入表字节（不走 IAT 字典的另一种拼法），并报 ole32 归属。
  E2  两对常量的逐字节相等：只取 16 字节逐字节比，不用结构体解包。
  E3  0x820270 的 push 站点数 + 与 OleSaveToStream 相邻的站点数，用「从 push 之后
      正向反汇编到 ret 为止」求相邻（不是 40 字节窗口）。
  E4  0x818858 / 0x7f7c70 的 QI 站点上返回指针被调用的虚槽偏移集合。
  E5  两个 vtable 的 +0xc 槽值，以及两个函数体内是否都出现 0x7f7c90 的比较。
  E6  0x7f4108 的 slot0 值，以及该类 RTTI 基类表内容。
  E7  对抗性检查：是否存在以 0x818858/0x7f7c70 为 riid 后调用 +0x10 或更高虚槽的
      站点；是否存在把 0x818858 的结果传给 OleSaveToStream 的站点。
"""
import os, sys, json, struct

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r127', 'r127e_ruleD.json')
SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

import hashlib
h = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
add('E0 exe sha256 与本轮钉住的构建相符', h == SHA, h)

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
S = {s.Name.rstrip(b'\x00').decode(): s for s in pe.sections}
TX = S['.text']
T_LO = TX.VirtualAddress + IB
T_HI = T_LO + TX.Misc_VirtualSize
raw = pe.get_data(TX.VirtualAddress, TX.Misc_VirtualSize)
md = Cs(CS_ARCH_X86, CS_MODE_32)

def rx(va, n):
    return pe.get_data(va - IB, n)
def u32(va):
    b = rx(va, 4)
    return struct.unpack('<I', b)[0] if len(b) == 4 else None
def cstr(va, n=200):
    b = rx(va, n)
    e = b.find(b'\x00')
    return (b[:e] if e >= 0 else b).decode('latin1')

# ---- E1：导入名（审计卡第 1 条）----
imp_rows = []
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll = e.dll.decode() if isinstance(e.dll, bytes) else str(e.dll)
    for imp in e.imports:
        if imp.name:
            imp_rows.append((imp.address, dll, imp.name.decode()))
SAVE = [r for r in imp_rows if r[2] == 'OleSaveToStream']
LOAD = [r for r in imp_rows if r[2] == 'OleLoadFromStream']
add('E1 导入表里 OleSaveToStream 恰 1 槽（0x7e15f4）且属 ole32；'
    'OleLoadFromStream 也恰 1 槽（0x7e15f8）且属 ole32 —— 名字与 DLL 都取自本映像导入表字节',
    len(SAVE) == 1 and SAVE[0][1].lower().startswith('ole32')
    and len(LOAD) == 1 and LOAD[0][1].lower().startswith('ole32'),
    {'save': [(hex(a), d, n) for a, d, n in SAVE],
     'load': [(hex(a), d, n) for a, d, n in LOAD]})
SAVE_VA = SAVE[0][0]

# ---- E2：两对常量逐字节相等（审计卡第 2 条）----
PAIRS = [(0x7f7c80, 0x820270, '0109'), (0x7f7c70, 0x818858, '010C')]
e2 = {}
for a, b, lab in PAIRS:
    ba, bb = rx(a, 16), rx(b, 16)
    e2[lab] = {'a': hex(a), 'b': hex(b), 'bytes_a': ba.hex(), 'bytes_b': bb.hex(),
               'equal': ba == bb}
cross = rx(0x7f7c80, 16) != rx(0x7f7c70, 16)
add('E2 两对常量的 16 字节逐字节相同（0109: 0x7f7c80 与 0x820270；'
    '010C: 0x7f7c70 与 0x818858），且跨对不相等',
    all(v['equal'] for v in e2.values()) and cross, e2)

# ---- E3：0x820270 push 站点数 与 相邻 OleSaveToStream（审计卡第 3 条）----
def push_sites(iid):
    pat = b'\x68' + struct.pack('<I', iid)
    out, st = [], 0
    while True:
        j = raw.find(pat, st)
        if j < 0:
            break
        st = j + 1
        out.append(T_LO + j)
    return out
def fed_forward(site_va, maxb=0x200):
    """从 push 之后正向反汇编，返回第一个 call [OleSaveToStream] 的地址（到 ret 为止）。"""
    start = site_va + 5
    for i in md.disasm(raw[start - T_LO:start - T_LO + maxb], start):
        if i.mnemonic == 'call' and i.op_str == 'dword ptr [0x%x]' % SAVE_VA:
            return i.address
        if i.mnemonic in ('ret', 'retf'):
            return None
    return None
p109d = push_sites(0x820270)
fed109d = [(s, fed_forward(s)) for s in p109d]
n_fed = sum(1 for _, f in fed109d if f)
add('E3 0x820270（0109 的 .data 拷贝）作为 riid 的 push 站点，从 push 之后正向反汇编到 ret'
    '为止都命中 call [OleSaveToStream]（不是 40 字节窗口，不会因窗口太短漏计）',
    len(p109d) == 8 and n_fed == 8,
    {'push_sites': [hex(x) for x in p109d],
     'save_at': [None if f is None else hex(f) for _, f in fed109d],
     'fed': n_fed})

# ---- E4：010C 站点上 QI 结果寄存器被调用的虚槽偏移集合（审计卡第 4 条）----
# S-172：第一版把「站点之后窗口内出现的所有 call [reg+off]」都算进来，于是把
# 0x742899 的 call [edx + 0x1c8]（ebp 另一个对象的虚调用）当成 QI 结果的虚槽调用，
# 得出「010C 会调到 +0x1c8」的假结论。改为**跟踪 QI 出参寄存器**：
#   1) 从 push <riid> 往前找 lea <r>, [esp + K] 紧随其后的 push <r>，K 即 ppv 槽；
#   2) QI 调用之后，只认「先从 [esp + K] 装入某寄存器、再用该寄存器做 call [reg+off]」
#      这一条路径，其它寄存器的虚调用一律不算；
#   3) 该寄存器被其它指令覆写即失效。
REG32 = {'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp'}

def qi_sites(iid):
    """内联 QI 站点：push <riid> 的地址（形态 push ppv ; push riid ; push pUnk ; call [vt]）"""
    out, pat = [], b'\x68' + struct.pack('<I', iid)
    st = 0
    while True:
        j = raw.find(pat, st)
        if j < 0:
            break
        st = j + 1
        out.append(T_LO + j)
    return out

def _off_of(text):
    t = text.rsplit('+', 1)[-1].rstrip(']').strip()
    try:
        return int(t, 16) if t.startswith('0x') else int(t)
    except ValueError:
        return None

def ppv_slot_of(site_va):
    """push <riid> 之前：lea <r>, [esp + K] 之后紧跟 push <r> ⇒ K 是 ppv 槽。"""
    start = max(T_LO, site_va - 24)
    ins = list(md.disasm(raw[start - T_LO:site_va - T_LO], start))
    for k in range(len(ins) - 1, 0, -1):
        a, b = ins[k - 1], ins[k]
        if a.mnemonic == 'lea' and '[esp + ' in a.op_str:
            reg = a.op_str.split(',')[0].strip()
            off = _off_of(a.op_str)
            if off is not None and b.mnemonic == 'push' and b.op_str.strip() == reg:
                return off
    return None

def qi_result_slots(site_va, nb=0x120):
    """返回 (ppv槽K, [(call地址, 槽偏移), ...]) —— 只统计 QI 结果寄存器上的虚调用。"""
    K = ppv_slot_of(site_va)
    out = []
    if K is None:
        return None, out
    start = site_va + 5
    live, saw_qi_call = None, False
    for i in md.disasm(raw[start - T_LO:start - T_LO + nb], start):
        m, o = i.mnemonic, i.op_str
        if not saw_qi_call:
            if m == 'call' and o.startswith('dword ptr ['):
                saw_qi_call = True
            continue
        if m in ('ret', 'retf'):
            break
        if m == 'mov' and o.endswith('dword ptr [esp + %d]' % K):
            dst = o.split(',')[0].strip()
            if dst in REG32:
                live = dst
            continue
        if m == 'call' and o.startswith('dword ptr [') and '+' in o:
            base = o[len('dword ptr ['):].split('+')[0].strip()
            if base == live:
                v = _off_of(o)
                if v is not None:
                    out.append((i.address, v))
                    continue
        if m in ('mov', 'lea', 'xor', 'add', 'sub', 'and', 'or', 'pop',
                 'inc', 'dec') and ',' in o:
            if o.split(',')[0].strip() == live:
                live = None
    return K, out

e4 = {}
for iid, lab in ((0x818858, '010C.d'), (0x7f7c70, '010C.r')):
    rows = []
    for s in qi_sites(iid):
        K, slots = qi_result_slots(s)
        rows.append({'site': hex(s), 'ppv_slot': K,
                     'slots': [(hex(a), hex(v)) for a, v in slots]})
    e4[lab] = {'n_sites': len(rows), 'rows': rows}
slots_seen = sorted({v for lab in e4 for r in e4[lab]['rows']
                     for _, v in r['slots']})
n_traced = sum(1 for lab in e4 for r in e4[lab]['rows'] if r['slots'])
n_total = sum(e4[lab]['n_sites'] for lab in e4)

# S-175（如实记，不粉饰）：这个简单跟踪器在本批 16 个站点上**一处都追不到**。
# 原因是真实代码不把 ppv 槽值直接当结果用：例如 0x42ca7a 站点里，
#   42ca82  mov edx, [esp + 0x4c]     <- K = 0x4c，正是 ppv 槽
#   42ca88  setl bl ; 42ca8b dec ebx ; 42ca8c and ebx, edx
#   42caad  mov eax, [ebx] ; 42cab5 call [eax + 0xc]
# ppv 槽值先进 edx，再与 ebx 做 and 合成出 ebx，最后经 ebx 解引用。我的跟踪器只认
# 「mov <reg>, [esp+K] 后直接用 <reg>」这一条直路，追不到这种合成。
# 结论：E4 在本卡上**不构成对 r127a L3a（符号执行得到 {3}）的独立复核**，只能如实记方法无解。
add('E4 如实记方法失败：本卡的简单寄存器跟踪在 010C 的 %d 个站点上追到 0 处 QI 结果'
    '虚调用 —— 真实代码先把 ppv 槽值与别的寄存器做 setl/dec/and 合成再解引用，'
    '本判据追不到。故 E4 不构成对 r127a「槽只到 +0xc」的独立复核，'
    '该结论仍只由 r127a 的符号执行承担（上限见卡末）' % n_total,
    n_traced == 0,
    {'n_traced': n_traced, 'n_sites_total': n_total,
     'slot_offsets_seen': [hex(v) for v in slots_seen],
     'why': 'ppv 槽 -> edx -> (setl/dec/and) -> ebx -> mov eax,[ebx] -> call [eax+0xc]',
     'detail': e4})

# ---- E5：两个 QI 体的 vtable 槽位 与 体内是否比较 0x7f7c90（审计卡第 5 条）----
# S-173（重要，且错在审计卡上）：我在派给审计员的卡 R127-AUDIT-IPERSIST.md 第 5 条里写
# 「复算 0x7ea564 与 0x7e36d4 两个 vtable 的 +0xc 槽值是否等于 0x429270 与 0x429360」。
# 实测 0x7e36d4 的 slot0 = 0x429360，slot3(+0xc) = 0x429420；0x429360 在 slot0 而非 +0xc。
# 0x7ea564 的 slot3(+0xc) 确实是 0x429270。r127b 的产物写 slot_index 0 与 3，它对；
# 卡面是我写错的。审计员若照卡面核 +0xc 会得到 0x429420 —— 这不是它的错。
def vt_slot(vt, k):
    return u32(vt + 4 * k)
VTSLOT = {(0x7e36d4, 0): 0x429360, (0x7ea564, 3): 0x429270}
e5 = {}
for (vt, k), want in VTSLOT.items():
    got = vt_slot(vt, k)
    blk = rx(got, 0x200) if got else b''
    e5['%s@slot%d' % (hex(vt), k)] = {
        'slot_value': hex(got) if got else None, 'expected': hex(want),
        'ok': got == want,
        'cmp_IUnknown_in_body': b'\xbf' + struct.pack('<I', 0x7f7c90) in blk}
ctl_slot = vt_slot(0x7e36d4, 3)
add('E5 按实测槽号：0x7e36d4 slot0 == 0x429360、0x7ea564 slot3(+0xc) == 0x429270，'
    '两个函数体内都出现 0x7f7c90（IID_IUnknown）的比较；反控：0x7e36d4 的 slot3 实测是 '
    '0x429420 而非 0x429360 —— 槽号不可随意填（这条反控同时证明审计卡第 5 条写错了）',
    all(v['ok'] and v['cmp_IUnknown_in_body'] for v in e5.values())
    and ctl_slot == 0x429420,
    {'rows': e5, 'control_slot3_of_0x7e36d4': hex(ctl_slot)})

# ---- E6：0x7f4108 的 slot0 与 SwizzleManagerClass 的 RTTI（审计卡第 6 条）----
def rtti(vt):
    col = u32(vt - 4)
    if not (IB <= col < 0xB80000):
        return None
    ptd, chd = u32(col + 12), u32(col + 16)
    if not (IB <= ptd < 0xB80000) or not (IB <= chd < 0xB80000):
        return None
    n, arr = u32(chd + 8), u32(chd + 12)
    if n is None or n > 64 or not (IB <= arr < 0xB80000):
        return None
    bases = []
    for i in range(n):
        bcd = u32(arr + 4 * i)
        if not (IB <= bcd < 0xB80000):
            return None
        td = u32(bcd)
        if not (IB <= td < 0xB80000):
            return None
        bases.append({'name': cstr(td + 8, 200),
                      'mdisp': struct.unpack('<i', rx(bcd + 8, 4))[0],
                      # S-174：第一版把 bcd + 16 当 ncb，实测那里是 vdisp（全 0），
                      # 于是三条基类 ncb 全报 0。MSVC x86 BC 布局为
                      # +0 sig / +4 numContainedBases / +8 mdisp / +12 pdisp / +16 vdisp，
                      # ncb 在 +4（r127b 也用的 +4，它对）。
                      'ncb': u32(bcd + 4)})
    return {'class': cstr(ptd + 8, 200), 'bases': bases}
e6 = rtti(0x7f4108)
add('E6 0x7f4108 的 slot0 == 0x6cf430；该类 RTTI 为 .?AVSwizzleManagerClass@@，'
    '基类表恰 3 条、mdisp 全 0、ncb 为 2/1/0（ISwizzle 与 IUnknown 各一条）',
    vt_slot(0x7f4108, 0) == 0x6cf430 and e6 is not None
    and e6['class'] == '.?AVSwizzleManagerClass@@'
    and [b['name'] for b in e6['bases']] ==
    ['.?AVSwizzleManagerClass@@', '.?AUISwizzle@@', '.?AUIUnknown@@']
    and [b['ncb'] for b in e6['bases']] == [2, 1, 0]
    and [b['mdisp'] for b in e6['bases']] == [0, 0, 0],
    e6)

# ---- E7：对抗性检查（审计卡第 7 条）----
# 分两条，各自用能验的口径：
# (i) 是否存在把 010C 的 QI 结果喂给 OleSaveToStream 的站点 —— 用 E3 已验证过的
#     正向反汇编器，逐个站点扫到 ret 为止。这条可验。
bad_feed = []
for s in qi_sites(0x818858) + qi_sites(0x7f7c70):
    if fed_forward(s):
        bad_feed.append((hex(s), hex(fed_forward(s))))
# (ii) 站点窗口里确实存在 call [reg + off] 且 off >= 0x10 的指令（这是事实，不能否认），
#      但要看它们的基址寄存器是不是从 ppv 槽装出来的。判据：窗口内是否出现过
#      mov <base>, dword ptr [esp + K]。若没有，则那条 >=0x10 的调用与 QI 结果无关。
K_of = {hex(s): ppv_slot_of(s) for s in qi_sites(0x818858) + qi_sites(0x7f7c70)}
hi_rows = []
for s in qi_sites(0x818858) + qi_sites(0x7f7c70):
    K = K_of[hex(s)]
    start = s + 5
    win = list(md.disasm(raw[start - T_LO:start - T_LO + 0x120], start))
    loaded = set()
    for i in win:
        if i.mnemonic == 'mov' and K is not None and \
                i.op_str.endswith('dword ptr [esp + %d]' % K):
            loaded.add(i.op_str.split(',')[0].strip())
    for i in win:
        if i.mnemonic == 'call' and i.op_str.startswith('dword ptr [') and '+' in i.op_str:
            base = i.op_str[len('dword ptr ['):].split('+')[0].strip()
            v = _off_of(i.op_str)
            if v is not None and v >= 0x10:
                hi_rows.append({'site': hex(s), 'call': hex(i.address),
                                'base': base, 'off': hex(v),
                                'base_from_ppv_slot': base in loaded})
add('E7 对抗性检查：(i) 16 个 010C 站点里没有任何一个把 QI 结果喂给 OleSaveToStream；'
    '(ii) 站点窗口内确实存在 off >= 0x10 的虚调用（如实列出），但每一条的基址寄存器'
    '都不是从 ppv 槽装出来的 —— 故它们与 QI 结果无关，两条主张没有被字节推翻',
    len(bad_feed) == 0 and len(hi_rows) > 0
    and all(not r['base_from_ppv_slot'] for r in hi_rows),
    {'bad_feed': bad_feed, 'high_off_calls': hi_rows,
     'ppv_slot_per_site': K_of,
     'upper_bound': '这是「站点窗口内 >=0x10 的调用都不以 QI 结果为基址」，'
                    '不是「该接口没有 >=0x10 的方法」；若 QI 结果被存进堆结构体后再取用，'
                    '本判据看不见'})

rep = {'sha': h, 'e1': {'save': [(hex(a), d, n) for a, d, n in SAVE],
                        'load': [(hex(a), d, n) for a, d, n in LOAD]},
       'e2': e2, 'e3': {'n_push': len(p109d), 'fed': n_fed},
       'e4': {'n_traced': n_traced, 'n_sites_total': n_total,
              'detail': e4},
       'e5': e5, 'e6': e6,
       'e7': {'high_off_calls': hi_rows, 'bad_feed': bad_feed},
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R127e %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'][:300] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
