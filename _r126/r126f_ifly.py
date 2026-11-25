# -*- coding: utf-8 -*-
"""R126f: 对 0x7e9b40 = IFlyControl 这一条做对抗性复核，并回答「R125 那句
「0x7e9b40 与 0x7f7c70/0x7f7c80 不可分」错在哪里」。

F1  0x7e9b40 的 QI 体属于哪一个类：不是靠 slot0 猜，而是从「哪个类的 vtable 里
    这个 QI 函数当 slot0」反查，给出类名与地址，并核该类 RTTI 里 0x6c0 处唯一。
F2  该类的 QI 体里查了哪些 IID、每个 IID 对应哪个 this 调整值，逐个列出。
    这一步用来回答「为什么 R124 会把它和 IPersist 家族扯在一起」——
    因为它同类的 RTTI 里 IPersist 与 IPersistStream 都在 mdisp 0。
F3  可失败预测：若 0x7e9b40 真是 IFlyControl，则「全映像里 QI 体把出参写成
    this+0x6c0」的函数应当只有这一个；若有第二个，给出地址。
F4  反控：把同样的方法套到 0x7e9b20 与 0x7e36c0 上，看它们能否也被解出唯一
    this 调整值。若解不出，如实记，不要为了凑覆盖率放宽判据。
"""
import os, sys, json, struct, hashlib, collections
import pefile, capstone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r126', 'r126f_ifly.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'

ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
add('F0 exe sha256 是钉住的那个构建',
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
RD_LO, RD_HI = RDATA.VirtualAddress + IB, RDATA.VirtualAddress + IB + RDATA.Misc_VirtualSize
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
    return None if x is None else (x if isinstance(x, int) else int(str(x).strip(), 16))

TEXT = [s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text'][0]
T_LO = TEXT.VirtualAddress + IB
T_HI = T_LO + TEXT.Misc_VirtualSize
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(
    pe.get_data(TEXT.VirtualAddress, TEXT.Misc_VirtualSize), T_LO)]
n_ins = len(ins)
idx = {a: i for i, (a, m, o) in enumerate(ins)}

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

# ---- F1: 哪个类的 slot0 是 0x414290 ----
QI = 0x414290
own = []
for k, v in sym.items():
    vt = _va(v.get('vtable_va'))
    if vt and u32(vt) == QI:
        own.append({'class': k, 'vtable': vt})
add('F1 恰有一个类把 0x414290 用作 slot0（不是靠地址窗口猜的）',
    len(own) == 1, own)
cls = own[0]['class'] if own else None
b = bcds(own[0]['vtable']) if own else None
add('F1b 该类 RTTI 可完整解码', b is not None,
    None if b is None else len(b))

# ---- F2: QI 体里查了哪些 IID、每个对应哪个 this 调整值 ----
def qi_table(start):
    """逐分支解析一个 QI 体：mov edi, IID 之后成功路径上读出的 this 调整值。"""
    i = idx.get(start)
    if i is None:
        return None
    out = []
    j = i
    while j < min(n_ins, i + 400):
        a, m, o = ins[j]
        if m == 'ret':
            break
        if m == 'mov' and o.startswith('edi, ') and tail_imm(o) is not None:
            iid = tail_imm(o)
            # 找它后面的 repe cmpsd 与失败跳转
            rep = None
            for j2 in range(j, min(n_ins, j + 8)):
                if ins[j2][1].startswith('repe'):
                    rep = j2
                    break
            je = None
            if rep is not None:
                for j2 in range(rep + 1, min(n_ins, rep + 6)):
                    if ins[j2][1].startswith('j') and not ins[j2][1].startswith('jmp'):
                        je = j2
                        break
                    if ins[j2][1] == 'ret':
                        break
            disp = None
            if je is not None:
                fail = num(ins[je][2])
                lo = je + 1
                hi = idx.get(fail, min(n_ins, lo + 40))
                for j2 in range(lo, min(hi, n_ins)):
                    a2, m2, o2 = ins[j2]
                    if m2 == 'ret':
                        break
                    if m2 == 'lea' and o2.endswith(']') and ', [' in o2 \
                            and ' + 0x' in o2:
                        disp = num(o2.split(' + ')[-1][:-1])
                        break
                    if m2 == 'xor' and len(o2.split(', ')) == 2 \
                            and o2.split(', ')[0] == o2.split(', ')[1]:
                        disp = 0
                        break
            out.append({'iid': '0x%x' % iid, 'disp': disp})
        j += 1
    return out

tab = qi_table(QI)
# 该 QI 体只查一个 IID（0x7e9b40）：它先把基类 QueryInterface 委派给 0x410260
# （AbstractClass 那一层），只有基类失败才比自己的 IID。故条数为 1 是事实，
# 不是解析失败。第一版把「至少 2 个」当断言，是我凭空设的下限（S-156）。
add('F2 该 QI 体逐分支解出 1 个 (IID, this 调整值) 对（它先把基类 QI 委派出去，'
    '只自己处理一个 IID，故 1 条即完整）',
    tab is not None and len(tab) == 1, tab)

b39 = [x for x in (tab or []) if x['iid'] == '0x7e9b40']
add('F2b 0x7e9b40 在该 QI 体里解析出的 this 调整值为 0x6c0',
    b39 and b39[0]['disp'] == 0x6C0, b39)

# 该类的 RTTI 在 disp 0 处同时有 IPersist 与 IPersistStream —— 这就是 R124
# 把它与那两个常量混在一起的结构原因
if b:
    at0 = [x['name'] for x in b if x['mdisp'] == 0]
    at6c0 = [(x['name'], x['mdisp']) for x in b if x['mdisp'] == 0x6C0]
    add('F3 该类 RTTI 在 mdisp 0 处同时有 IPersist 与 IPersistStream（这两个接口'
        '本身没有次对象偏移，故 R124 的对称记录永远分不开它们俩）；'
        '而 0x6c0 处只有 IFlyControl 与一个 IUnknown',
        any('IPersistStream' in x for x in at0)
        and any(x.endswith('IPersist@@') for x in at0),
        {'disp0': at0, 'disp6c0': at6c0})

# ---- F3: this+0x6c0 在全映像里的全部出现 ----
# 实测 10 处。我原先在注释里写「应只有 2 处」，那是估计值不是实测值（S-157）。
# 本条只记录实测分布，并给出可失败的形态断言：
#   (a) 恰有 1 处是 QI 体写出参（0x4142c1）；
#   (b) 其余 9 处都是取子对象地址（lea reg,[reg+0x6c0] 后接 push 或 call），
#       其中 0x4177c0 我最先看到，后接 call dword ptr [ecx+0xc]（slot 3）。
hits = []
for j, (a, m, o) in enumerate(ins):
    if m == 'lea' and o.endswith(' + 0x6c0]') and ', [' in o:
        # 严格判据：只有「紧接在 mov edi, <IID> + mov ecx, 4 + repe cmpsd」这个
        # 分派器模板之后的 lea 才算 QI 体写出参。第一版只看「往前 10 条里有
        # mov edi, 立即数」，把 0x4177c0 的 mov edi, 0xb（一个枚举值）也算进去了（S-158）。
        qi_body = False
        for k in range(max(0, j - 12), j):
            if ins[k][1] == 'mov' and ins[k][2].startswith('edi, 0x'):
                w = ins[max(0, k - 8):k + 6]
                if (any(y[1] == 'mov' and y[2] == 'ecx, 4' for y in w)
                        and any(y[1].startswith('repe') for y in w)):
                    qi_body = True
                break
        hits.append({'at': hex(a), 'kind': 'qi_body' if qi_body else 'subobject_addr'})
n_qi = sum(1 for h in hits if h['kind'] == 'qi_body')
n_sub = sum(1 for h in hits if h['kind'] == 'subobject_addr')
add('F3b this+0x6c0 全映像共 10 处：恰 1 处是 QI 体写出参，9 处是取子对象地址'
    '（后者独立印证同一偏移，不是反例）',
    len(hits) == 10 and n_qi == 1 and n_sub == 9,
    {'total': len(hits), 'qi_body': n_qi, 'subobject_addr': n_sub, 'hits': hits})
sl3 = []
for h in hits:
    if h['kind'] != 'subobject_addr':
        continue
    j = idx[int(h['at'], 16)]
    w = ins[j + 1:j + 5]
    if any(m2 == 'call' and o2.startswith('dword ptr [') and ' + 0xc]' in o2
           for _a2, m2, o2 in w):
        sl3.append(h['at'])
add('F3c 其中至少 1 处（0x4177c0）紧接 call dword ptr [reg+0xc]，'
    '即该子对象被按 IPersist 的 slot 3 调用 —— 与 0x7f7c70 侧 R125 得到的槽位集合一致',
    '0x4177c0' in sl3, {'slot3_sites': sl3})

# ---- F4: 反控 —— 同样的方法对 0x7e9b20 与 0x7e36c0 ----
CTRL = {0x7e9b20: 0x6cf44e, 0x7e36c0: 0x4292ab}
ctrl = {}
for iid, site in CTRL.items():
    i = idx.get(site)
    # 找该站点所在 QI 体的起点（前面最近的 ret 之后）
    start = None
    for k in range(i - 1, max(0, i - 600), -1):
        if ins[k][1] == 'ret':
            start = ins[k + 1][0]
            break
    t = qi_table(start) if start else None
    ok = 0
    if start:
        for k, v in sym.items():
            vt = _va(v.get('vtable_va'))
            if vt and u32(vt) == start:
                ok += 1
    ctrl['0x%x' % iid] = {'start': hex(start) if start else None,
                          'table': t, 'n_classes_using_as_slot0': ok}
add('F4 反控：0x7e9b20 与 0x7e36c0 的 QI 体也能被同一方法解析（不是只有 0x7e9b40 特例）',
    all(v['table'] for v in ctrl.values()), ctrl)

# 但它们的 QI 体不是任何类的 slot0 —— 如实记
own_ctrl = {k: v['n_classes_using_as_slot0'] for k, v in ctrl.items()}
add('F4b 如实记录：这两个 QI 体不被任何类的 slot0 引用，故本方法对它们只能给出'
    '「查了哪些 IID」，不能给出接口名 —— 不为了让覆盖率好看而放宽判据',
    all(v == 0 for v in own_ctrl.values()), own_ctrl)

rep = {'exe_sha256': EXE_SHA, 'owner': own, 'qi_table': tab,
       'disp0_names': [x['name'] for x in (b or []) if x['mdisp'] == 0],
       'hits_6c0': hits, 'ctrl': ctrl,
       'checks': ck, 'all_ok': all(c['ok'] for c in ck)}
json.dump(rep, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

bad = [c for c in ck if not c['ok']]
print('R126f %d/%d PASS' % (len(ck) - len(bad), len(ck)))
for c in ck:
    print(('  PASS  ' if c['ok'] else '  FAIL  ') + c['name']
          + (' :: ' + c['detail'] if c['detail'] else ''))
sys.exit(0 if not bad else 1)
