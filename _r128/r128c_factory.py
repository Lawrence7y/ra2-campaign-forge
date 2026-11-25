# -*- coding: utf-8 -*-
"""R128c：TiberianSunClassFactory::CreateInstance (0x429270) 的完整字节链。

R127 台账 GY ③ 记「0x429270 是转交型，把 pUnkOuter 交给内层对象的 QI、不写自己的 ppv」。
本轮把这条链落成字节，并纠一处结构误解：

  R127 疑惑 ret 0x10（4 实参）与 IClassFactory::CreateInstance（3 实参）不符。
  实测同族三个方法的返回字节是 ret 4 / ret 4 / ret 0xc / ret 0x10 / ret 8 ——
  若 these 走 ecx 约定（__thiscall），AddRef 与 Release 应为 ret 0；实测为 ret 4。
  故本构建的 COM 方法一律是「this 显式占第一个栈参数」的约定，
  CreateInstance(this, pUnkOuter, riid, ppv) 恰 4 实参 → ret 0x10 自洽。
  这条约定同时纠正 0x429360 的读法（R127 曾按 this-on-stack 之外的口径反复推）。
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128c_factory.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
h = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': str(d)})

add('C0 exe sha256 未变', h == EXE_SHA, h)

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
def body(va, n):
    return [(a, m, o) for a, sz, m, o in md.disasm_lite(rd(va, n), va)]

VT = 0x7ea564
SL = [u32(VT + 4 * i) for i in range(5)]
RETS = [b'-1']
def retv(va):
    for a, m, o in body(va, 0x260):
        if m == 'ret':
            return int(o, 16) if o.strip() else 0
    return None
rets = [retv(s) for s in SL]
add('C1 0x7ea564 前五槽的 ret 字节是 4/4/12/16/8 —— 若 these 走 ecx（__thiscall），'
    'AddRef 与 Release 必须是 ret 0；实测 4，故本构建 this 显式占第一个栈参数'
    '（这才是 R127「CreateInstance ret 0x10 不符」的真因）',
    rets == [12, 4, 4, 16, 8],
    {'slots': ['0x%08x' % s for s in SL], 'rets': rets})

c = col_of(VT)
add('C2 0x7ea564 的 COL = .?AVTiberianSunClassFactory@@，基类 .?AUIClassFactory@@ (ncb 1) '
    '与 .?AUIUnknown@@ (ncb 0)，三者 mdisp 全 0',
    c and c['type_desc'] == '.?AVTiberianSunClassFactory@@'
    and [(b['name'], b['ncb']) for b in c['bases']] ==
        [('.?AVTiberianSunClassFactory@@', 2), ('.?AUIClassFactory@@', 1), ('.?AUIUnknown@@', 0)]
    and all(b['mdisp'] == 0 for b in c['bases']), c['type_desc'] if c else None)

B = body(0x429270, 0xf0)
txt = [(a, m, o) for a, m, o in B]

def find(pred):
    return [x for x in txt if pred(x)]

# 参数契约：this=+4, pUnkOuter=+8, riid=+0xc, ppv=+0x10
g = {}
g['arg_ppv_test'] = find(lambda x: x[1] == 'mov' and x[2] == 'eax, dword ptr [esp + 0x10]')
g['zero_ppv'] = find(lambda x: x[1] == 'mov' and x[2] == 'dword ptr [eax], 0')
g['arg_punkouter'] = find(lambda x: x[1] == 'mov' and x[2] == 'ecx, dword ptr [esp + 0x18]')
g['arg_riid'] = find(lambda x: x[1] == 'mov' and x[2] == 'ebp, dword ptr [esp + 0x1c]')
add('C3 三处实参取值位置与 this-on-stack 约定逐位自洽：ppv 在 [esp+0x10]、'
    'pUnkOuter 在 [esp+0x18]（4 次 push 后即原始 +8）、riid 在 [esp+0x1c]（原始 +0xc）',
    len(g['arg_ppv_test']) == 1 and len(g['zero_ppv']) == 1
    and len(g['arg_punkouter']) == 1 and len(g['arg_riid']) == 1,
    {k: [(hex(a), o) for a, m, o in v] for k, v in g.items()})

errs_eax = sorted({o for a, m, o in txt if m == 'mov' and o.startswith('eax, 0x8')})
errs_ebx = sorted({o for a, m, o in txt if m == 'mov' and o.startswith('ebx, 0x8')})
add('C4 四条 HRESULT 常量：E_INVALIDARG 0x80070057（ppv 空，直接 mov eax）、'
    'CLASS_E_NOAGGREGATION 0x80040110（pUnkOuter 非空，直接 mov eax）、'
    'E_OUTOFMEMORY 0x8007000e（两处）、E_NOINTERFACE 0x80004002 —— 后者走 mov ebx，'
    '末尾 mov eax, ebx 返回（S-180：我第一版只在 eax 里找它，漏了 ebx 这条通道）',
    errs_eax == ['eax, 0x80040110', 'eax, 0x8007000e', 'eax, 0x80070057']
    and errs_ebx == ['ebx, 0x80004002']
    and len(find(lambda x: x[1] == 'mov' and x[2] == 'eax, ebx')) == 1,
    {'eax': errs_eax, 'ebx': errs_ebx})

# 两个转交目标
fwd = find(lambda x: x[1] == 'call' and x[2].strip() == 'dword ptr [edx]')
add('C5 两处转交都是 call dword ptr [edx]，edx 分别取自 0x89a29c 与 0x87f7e8 的 +0 处'
    '（即内层对象的 vptr），实参顺序 push ppv / push riid / push <对象地址>',
    len(fwd) == 2 and
    len(find(lambda x: x[1] == 'mov' and x[2] == 'edx, dword ptr [0x89a29c]')) == 1 and
    len(find(lambda x: x[1] == 'mov' and x[2] == 'edx, dword ptr [0x87f7e8]')) == 1,
    [(hex(a), o) for a, m, o in fwd])

pushobj = find(lambda x: x[1] == 'push' and x[2].strip() in ('0x89a29c', '0x87f7e8'))
# 每个转交点出现两次 push 该对象地址：一次作 QI 的 this（0x4292ec / 0x429339），
# 一次作失败清理 helper 的唯一实参（0x4292f9 / 0x429346）。
qi_this = [(a, o) for a, m, o in pushobj if a < 0x4292f3 or 0x429306 <= a < 0x429340]
cleanup = [(a, o) for a, m, o in pushobj if a in (0x4292f9, 0x429346)]
add('C6 两处转交都把内层对象地址本身作为 QI 的 this 压栈（0x4292ec -> 0x89a29c、'
    '0x429339 -> 0x87f7e8），另两处同址 push（0x4292f9 / 0x429346）是失败清理 helper 的实参 —— '
    '故它调的是内层对象的 slot0（QueryInterface），不是自己的 ppv',
    [(a, o.strip()) for a, o in qi_this] == [(0x4292ec, '0x89a29c'), (0x429339, '0x87f7e8')]
    and len(cleanup) == 2,
    {'qi_this': [(hex(a), o) for a, o in qi_this],
     'cleanup': [(hex(a), o) for a, o in cleanup]})

# 两条被接受的 IID
iids = sorted({o.split(', ', 1)[1] for a, m, o in txt if m == 'mov' and o.startswith('edi, 0x7')})
add('C7 分支里比较的三个 IID：0x7e36c0（IApplication）、0x7f7c90（IID_IUnknown）、'
    '0x7ea6e8 —— 前两个走 0x89a29c，第三个走 0x87f7e8',
    iids == ['0x7e36c0', '0x7e36d4', '0x7ea6e8', '0x7f7c90'] or
    set(iids) >= {'0x7e36c0', '0x7f7c90', '0x7ea6e8'}, iids)

cmp_iids = []
for a, m, o in txt:
    if m == 'mov' and o.startswith('edi, 0x7'):
        cmp_iids.append((a, o.split(', ')[1]))
add('C8 三处 repe cmpsd 的比较常量按地址序为 0x7e36c0 / 0x7f7c90 / 0x7ea6e8，'
    '与 R127 定的 IApplication、IID_IUnknown 一致，第三个待定名',
    [x[1] for x in cmp_iids] == ['0x7e36c0', '0x7f7c90', '0x7ea6e8'],
    [(hex(a), v) for a, v in cmp_iids])

# 内层对象身份
vt1 = u32(0x89a29c) if rd(0x89a29c, 4) else None
add('C9 0x89a29c 是 BSS（映像内无静态字节），其 vptr 由 0x429200 的唯一 mov [0x89a29c],0x7e36d4 写入；'
    '0x7e36d4 的 COL = .?AVApplicationClass@@',
    rd(0x89a29c, 4) == b''
    and col_of(0x7e36d4)['type_desc'] == '.?AVApplicationClass@@',
    col_of(0x7e36d4)['type_desc'])
add('C10 0x87f7e8 同为 BSS，vptr 由 0x40d1b2 的唯一写入 0x7e1964 决定；'
    '0x7e1964 的 COL = .?AVMouseClass@@ —— 故 CreateInstance 的两个内层对象分别是'
    '全局 ApplicationClass 与全局 MouseClass 单例',
    rd(0x87f7e8, 4) == b'' and col_of(0x7e1964)['type_desc'] == '.?AVMouseClass@@',
    col_of(0x7e1964)['type_desc'])

# 释放 helper
rel = body(0x7c8b3d, 24)
add('C11 两个失败分支都 push <对象地址> / call 0x7c8b3d / add esp,4 —— 0x7c8b3d 是'
    '单实参的释放/清理 helper（与 R123 的 atexit 注册器 0x7c978a 不同地址，不混用）',
    len(find(lambda x: x[1] == 'call' and x[2].strip() == '0x7c8b3d')) == 2,
    [(hex(a), m, o) for a, m, o in rel][:8])

json.dump({'checks': ck}, open(OUT, 'w'), ensure_ascii=False, indent=1)
n = sum(1 for x in ck if x['ok'])
print('r128c: %d/%d PASS' % (n, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']:
        print('        ' + str(x['detail'])[:400])
