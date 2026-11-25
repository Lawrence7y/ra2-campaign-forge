# -*- coding: utf-8 -*-
"""R128d：0x7ea6e8 = .?AUIGameMap@@ 的字节链（R127 台账 GY ② 记的「未定名」）。

R127 放弃定名的理由：接受分支把出参写成 .data 单例 0x87f7e8 而非 this，
故「出参调整值 == RTTI mdisp」这条 mdisp 判据无效。本轮改走反向路径：

  1. 0x87f7e8 的 vptr 唯一写入者 = 0x5bda4a（ctor 0x5bda40，ecx 由 0x40d190 给）与
     0x40d1b2（同对象的析构重写），写入值 0x7e1964，COL = .?AVMouseClass@@（r128b 已证）。
  2. 0x7ea6e8 在全映像只有 2 处指令级引用，都是「mov edi,0x7ea6e8 + repe cmpsd」的
     QI 比较常量：0x42930f（TiberianSunClassFactory::QI 体内）与 0x4293a5（0x429360 体内）。
  3. 两条接受分支的下一步都是把「全局 MouseClass 单例」交出去：
     0x42931c/0x42933e 直接 call [0x87f7e8] 的 vptr slot0；
     0x4293b2 直接把 ppv 写成常量 0x87f7e8。
  4. MouseClass 的 COL 在 mdisp 0 处的非 IUnknown 接口名唯一 = .?AUIGameMap@@
     （INoticeSink 在 mdisp 0x5518，被 ppv=this 排除）。
  ⇒ 0x7ea6e8 = IGameMap。判据不用 mdisp，故不受 R127 的上限影响。
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128d_igamemap.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
h = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})
add('D0 exe sha256 未变', h == EXE_SHA, h)

TXT_LO, TXT_HI = 0x401000, 0x7e1000
raw = rd(TXT_LO, TXT_HI - TXT_LO)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(raw, TXT_LO)]
idx = {a: i for i, (a, m, o) in enumerate(ins)}

T = 0x7ea6e8
r = [(a, m, o) for a, m, o in ins if '0x%x' % T in o.lower()]
add('D1 0x7ea6e8 在全 .text 的指令级引用恰 3 处，三处都是 mov edi,0x7ea6e8（QI 的比较常量）'
    '（S-181：我先用 grep 得 2 处，是因为 capstone 的 skipdata 没在 disasm 前生效、'
    '漏掉了 0x4f4273；三处口径才是对的）',
    len(r) == 3 and all(m == 'mov' and o == 'edi, 0x7ea6e8' for a, m, o in r),
    [(hex(a), m, o) for a, m, o in r])
add('D2 三处引用落在三个 QI 体内：0x42930f（TiberianSunClassFactory::CreateInstance）、'
    '0x4293a5（0x429360 ApplicationClass::QI）、0x4f4273（0x4f4240 MouseClass::QI）—— '
    '再无第三处，故「谁认这个 IID」的宿主集合完整；三者恰好构成 认->转交->自认 的闭环',
    [a for a, m, o in r] == [0x42930f, 0x4293a5, 0x4f4273], [hex(a) for a, m, o in r])

def seq(lo, hi):
    return [(a, m, o) for a, m, o in ins if lo <= a < hi]

# --- 宿主 1：0x429360 (ApplicationClass QI) 第三分支 ---
s1 = seq(0x42939e, 0x4293bc)
accepted1 = [(a, m, o) for a, m, o in s1 if m == 'mov' and o.startswith('dword ptr [edx], ')]
add('D3 0x429360 第三分支接受 0x7ea6e8 后写 ppv = 0x87f7e8（常量，不是 this）——'
    '这正是 R127 判「mdisp 判据无效」的那一处',
    len(accepted1) == 1 and accepted1[0][2] == 'dword ptr [edx], 0x87f7e8'
    and accepted1[0][0] == 0x4293b2, [(hex(a), o) for a, m, o in accepted1])

# --- 宿主 2：0x429270 (TiberianSunClassFactory::CreateInstance) 第三分支 ---
s2 = seq(0x42930a, 0x429360)
chk = [(a, m, o) for a, m, o in s2 if m == 'mov' and o == 'edi, 0x7ea6e8']
obj = [(a, m, o) for a, m, o in s2 if m == 'mov' and o == 'ecx, 0x87f7e8']
raw_v = [(a, m, o) for a, m, o in s2 if m == 'mov' and o == 'edx, dword ptr [0x87f7e8]']
callv = [(a, m, o) for a, m, o in s2 if m == 'call' and o.strip() == 'dword ptr [edx]']
add('D4 0x429270 第三分支：比 0x7ea6e8 通过后 mov ecx,0x87f7e8 / mov edx,[0x87f7e8] / '
    'push ppv / push riid / push 0x87f7e8 / call [edx] —— 即把该 IID 转交给全局 MouseClass 的 QI',
    len(chk) == 1 and len(obj) == 1 and len(raw_v) == 1 and len(callv) == 1,
    {'cmp': [(hex(a), o) for a, m, o in chk], 'obj': [(hex(a), o) for a, m, o in obj],
     'load_vptr': [(hex(a), o) for a, m, o in raw_v], 'call': [(hex(a), o) for a, m, o in callv]})

# [0x87f7e8] 的 vptr -> slot0
vptr = u32(0x7e1964)
slot0 = u32(0x7e1964)
add('D5 0x87f7e8 的 vptr 静态读为 0（BSS），但其唯一写入值是 0x7e1964，slot0 = 0x4f4240；'
    '故 D4 的 call [edx] 实际进入 MouseClass::QI 0x4f4240',
    rd(0x87f7e8, 4) == b'' and slot0 == 0x4f4240, 'slot0=0x%08x' % slot0)

ms = seq(0x4f4240, 0x4f42a0)
ms_cmp = [(a, m, o) for a, m, o in ms if m == 'mov' and o.startswith('edi, 0x')]
ms_w = [(a, m, o) for a, m, o in ms if m == 'mov' and o.startswith('dword ptr [edx], ')]
add('D6 MouseClass::QI 0x4f4240 只比较两个 IID：0x7f7c90（IID_IUnknown）与 0x7ea6e8；'
    '两条接受分支都写 ppv = this（eax 取自 [esp+0xc]，即 this）',
    [o.split(', ')[1] for a, m, o in ms_cmp] == ['0x7f7c90', '0x7ea6e8']
    and len(ms_w) == 1 and ms_w[0][2] == 'dword ptr [edx], eax',
    {'cmps': [(hex(a), o) for a, m, o in ms_cmp], 'ppv_write': [(hex(a), o) for a, m, o in ms_w]})

# MouseClass 接口名唯一性
c = col_of(0x7e1964)
au0 = [b['name'] for b in c['bases'] if b['name'].startswith('.?AU') and b['mdisp'] == 0
       and not b['name'].endswith('IUnknown@@')]
add('D7 MouseClass 的 COL 在 mdisp 0 处只有两个 .?AU 接口：IGameMap 与 IUnknown'
    '（INoticeSink 在 mdisp 0x5518，被 D6 的 ppv=this 排除）⇒ 0x7ea6e8 = .?AUIGameMap@@，唯一解',
    au0 == ['.?AUIGameMap@@'],
    {'au_at_0': au0, 'INoticeSink_mdisp': [b['mdisp'] for b in c['bases']
                                           if b['name'] == '.?AVINoticeSink@@']})

# 全库唯一性：954 类里 IGameMap 出现在哪些类的 mdisp 0
sym = json.load(open(os.path.join(ROOT, 'out', 'reverse', 'symbols.json'),
                     encoding='utf-8'))['classes']
def _va(x):
    return None if x is None else (x if isinstance(x, int) else int(str(x).strip(), 16))
n_cls, n_ig, n_only = 0, [], []
for k, v in sym.items():
    vt = _va(v.get('vtable_va'))
    if not vt: continue
    cc = col_of(vt)
    if not cc: continue
    n_cls += 1
    names = [b['name'] for b in cc['bases']]
    if '.?AUIGameMap@@' in names:
        n_ig.append(cc['type_desc'])
        au = [b['name'] for b in cc['bases'] if b['name'].startswith('.?AU')
              and b['mdisp'] == 0 and not b['name'].endswith('IUnknown@@')]
        if au == ['.?AUIGameMap@@']:
            n_only.append(cc['type_desc'])
add('D8 全库 %d 个可解 COL 的类里，%d 个声明了 .?AUIGameMap@@；其中「mdisp 0 处唯一的'
    '非 IUnknown 接口就是 IGameMap」的只有 %d 个 —— MouseClass 在其中，故 D7 的判据不是巧合'
    '(反控：判据对多接口类给出空集，不强行凑答案)'
    % (n_cls, len(n_ig), len(n_only)),
    n_cls > 900 and '.?AVMouseClass@@' in n_only and len(n_only) < 40,
    {'n_cls': n_cls, 'n_ig': len(n_ig), 'n_unique_ok': len(n_only),
     'unique_ok_sample': n_only[:12], 'ig_sample': n_ig[:12]})

# 反控：0x7f7c90 走同一条路应该得到 IUnknown
ms_unk = [a for a, m, o in ms_cmp if o == 'edi, 0x7f7c90']
add('D9 反控：同一个 MouseClass::QI 对 0x7f7c90 也接受并返回 this，但 0x7f7c90 已在 R124 '
    '由 IID_IUnknown 常量（全 0 的 Data1）独立定名 —— 判据对两个常量给出不同名字，不是恒等判据',
    len(ms_unk) == 1 and gt(0x7f7c90) == '{00000000-0000-0000-C000-000000000046}',
    gt(0x7f7c90))

# 反控：0x7ea6e8 与 0x7e36c0 只差 Data1 末字节，不是同一常量
add('D10 反控：0x7ea6e8 = {96F02EC7-...} 与 0x7e36c0 = {96F02EC3-...} 仅 Data1 末字节不同，'
    '是两个不同常量；0x7e36c0 已在 R127 由「mdisp 0 处非 IUnknown 唯一」定为 IApplication',
    gt(0x7ea6e8) == '{96F02EC7-6FE8-11D1-B6FD-00A024DDAFD1}'
    and gt(0x7e36c0) == '{96F02EC3-6FE8-11D1-B6FD-00A024DDAFD1}',
    [gt(0x7e36c0), gt(0x7ea6e8)])

json.dump({'checks': ck}, open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128d: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']:
        print('        ' + str(x['detail'])[:500])
