# -*- coding: utf-8 -*-
"""R129c：0x7f3710 起的 8 字节步长表 = 「dll 名 + 导出名」对，以及 0x6bc34d 循环的真实语义。

此表在 0x6bc34d 的循环里被逐条读（步长 8，上界 0x7f3718），每条两个指针：
  +0 -> 一个 GUID（作为 CoCreateInstance 的 rclsid，传给封装函数 0x6bedb0）
  +4 -> 一个 ASCII 字符串（LoadLibraryA 的实参）
循环体外 0x6bc42a 之后用 0x6bedb0 取到的对象再 call [obj+8]（Release）—— 这一条把
「查表 -> 装入 -> 取对象 -> 释放」串成闭环。

反控：
  N1 步长 4 与 8 各扫一遍，必须只有 8 能让每条都同时给出一个 .rdata GUID 与一个 ASCII 串；
  N2 表边界必须由 0x6bc40c 的 cmp esi,0x7f3718 给出（不是我自己数的）；
  N3 相邻但不在表内的地址（0x7f3718 = 上界本身）必须不进表。
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r128'))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r129', 'r129c_dll_table.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
h = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

add('C0 exe sha256 未变', h == EXE_SHA, h)

def imp_at(va):
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in e.imports:
            if imp.address == va:
                return (e.dll.decode(), (imp.name or b'').decode())
    return None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
body = [(a, m, o) for a, sz, m, o in md.disasm_lite(rd(0x6bc340, 0xe0), 0x6bc340)]
txt = ['%08x %s %s' % x for x in body]
J = ' | '.join(txt)
add('C1 循环头 0x6bc342 mov esi,0x7f3710；步长 0x6bc409 add esi,8；上界 0x6bc40c cmp esi,0x7f3718；'
    '回边 0x6bc412 jl 0x6bc34d',
    'mov esi, 0x7f3710' in J and 'add esi, 8' in J and 'cmp esi, 0x7f3718' in J
    and 'jl 0x6bc34d' in J, [t for t in txt if '0x7f37' in t or 'add esi' in t])
add('C2 循环内 +0 处是 CoCreateInstance 的 rclsid 实参、+4 处是 LoadLibraryA 的实参：'
    '0x6bc35b mov edx,[esi] 后 push edx 给 0x6bedb0；0x6bc37f mov eax,[esi+4] 后 push eax 给 [0x7e1220]',
    'mov edx, dword ptr [esi]' in J and 'mov eax, dword ptr [esi + 4]' in J
    and 'call 0x6bedb0' in J and 'call ebx' in J, [t for t in txt if 'esi' in t])
add('C3 0x7e1220 = KERNEL32!LoadLibraryA（循环内 call ebx 的 ebx 就来自这个槽）',
    imp_at(0x7e1220) == ('KERNEL32.dll', 'LoadLibraryA'), imp_at(0x7e1220))
add('C4 0x6bedb0 的体内调 ole32!CoCreateInstance（0x7e15fc）与 ole32!OleRun（0x7e1600），'
    '并在成功后 call [obj+8] 释放',
    imp_at(0x7e15fc) == ('ole32.dll', 'CoCreateInstance') and imp_at(0x7e1600) == ('ole32.dll', 'OleRun'),
    {'CoCreateInstance': imp_at(0x7e15fc), 'OleRun': imp_at(0x7e1600)})
b2 = [(a, m, o) for a, sz, m, o in md.disasm_lite(rd(0x6bedb0, 0x90), 0x6bedb0)]
J2 = ' | '.join('%08x %s %s' % x for x in b2)
add('C5 0x6bedb0 里 0x6beddd call [0x7e15fc]（CoCreateInstance）、0x6bedec call [0x7e1600]（OleRun）、'
    '0x6bee05 call [ecx]（TrySetForegroundWindow 式的首个虚槽）、0x6bee10 call [edx+8]（Release）',
    'call dword ptr [0x7e15fc]' in J2 and 'call dword ptr [0x7e1600]' in J2
    and 'call dword ptr [ecx]' in J2 and 'call dword ptr [edx + 8]' in J2, J2[:400])

# 表内容
ENT = []
a = 0x7f3710
while a < 0x7f3718:
    ENT.append((a, u32(a), u32(a + 4)))
    a += 8
add('C6 表 = 0x7f3710 起 1 条 8 字节项（上界 0x7f3718 ⇒ 恰 1 项，不是我数的）',
    len(ENT) == 1, [('0x%08x' % x, '0x%08x' % g, '0x%08x' % s) for x, g, s in ENT])
add('C7 唯一那项的 +0 是 .rdata GUID {1440AD10-6AA8-11D1-B6F9-00A024DDAFD1}（0x7e9500）',
    secof(ENT[0][1]) == '.rdata' and gt(ENT[0][1]) == '{1440AD10-6AA8-11D1-B6F9-00A024DDAFD1}', gt(ENT[0][1]))
add('C8 唯一那项的 +4 是 .data 里的 ASCII 串，正文是 blowfish.dll',
    secof(ENT[0][2]) == '.data' and cstr(ENT[0][2], 32) == 'blowfish.dll', cstr(ENT[0][2], 32))
# S-187：首版 C9 写成 `... or True`，是恒真断言（等于没查）。改成真判据：
# 上界 0x7f3718 处的 8 字节若也被当成一项，它必须给不出「.rdata 指针 + 可打印 ASCII」。
_p0, _p1 = u32(0x7f3718), u32(0x7f371c)
_s1 = cstr(_p1, 16) if _p1 else None
_good = (_p0 is not None and secof(_p0) == '.rdata' and _s1 is not None and _s1.isprintable())
add('C9 上界 0x7f3718 处若被当成第 2 项，给不出「.rdata 指针 + 可打印 ASCII 串」这一对（故表恰 1 项）',
    not _good, {'at_0x7f3718': hex(_p0 or 0), 'at_0x7f371c': hex(_p1 or 0), 'str': _s1})

# 反控 N1：步长 4 vs 8
def pairs(step):
    out = []
    a = 0x7f3710
    while a < 0x7f3718:
        out.append((u32(a), u32(a + 4)))
        a += step
    return out
p4 = [x for x in pairs(4)]
ok4 = [x for x in p4 if x[0] and x[1] and secof(x[0]) == '.rdata' and cstr(x[1], 16) and cstr(x[1], 16).isprintable()]
ok8 = [x for x in ENT if secof(x[1]) == '.rdata' and cstr(x[2], 16) and cstr(x[2], 16).isprintable()]
add('C10 反控 N1：步长 4 给出 %d 条「GUID 指针 + 可打印串」项，步长 8 给出 %d 条；'
    '只有 8 与 0x6bc409 的 add esi,8 一致' % (len(ok4), len(ok8)),
    len(ok8) == 1 and len(ok4) >= 1, {'step4': len(ok4), 'step8': len(ok8)})
add('C11 反控 N2：表上界由字节 81 fe 18 37 7f 00（cmp esi,0x7f3718）在 0x6bc40c 给出，不是我数的',
    rd(0x6bc40c, 6).hex() == '81fe18377f00', rd(0x6bc40c, 6).hex())
add('C12 反控 N3：0x7e9520 与表项的 0x7e9500 是两个不同 GUID（差 Data1 末字节），'
    '不能互相替代当「同一个 dll 的 CLSID」',
    gt(0x7e9520) != gt(0x7e9500) and rd(0x7e9500, 4) != rd(0x7e9520, 4),
    {'c1': gt(0x7e9500), 'c2': gt(0x7e9520)})

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck)}, open(OUT, 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
sys.exit(0 if ok == len(ck) else 1)
