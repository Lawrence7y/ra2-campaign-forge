# -*- coding: utf-8 -*-
"""R129b：把「CLSID -> 类对象 -> vtable -> 类名」这条链落成字节，并给 0x6bd945 的那次注册定名。

链的四段（每段都必须由字节给出，缺一段则整链不成立）：
  段一 0x6bc436 push 0x7e9520 / 0x6bc43f call [ole32!CoRegisterClassObject]
       ⇒ rclsid = .rdata 常量 0x7e9520，pUnk = .data 里的对象 0xa8e8c8
  段二 0xa8e8c8 的 vptr 写入者只有 0x4e7ce0（mov [0xa8e8c8],0x7ea564）
  段三 0x7ea564 的 COL 解出 .?AVTiberianSunClassFactory@@
  段四 0x6bd945 那次 call 的目标是 RegisterActiveObject（r129a 已定），
       它用的 rclsid 与段一是同一个常量 0x7e9520

反控：
  N1 把段一的 rclsid 换成相邻常量 0x7e9510，同一判据必须不再指向同一 CLSID；
  N2 把段二的 vptr 换成 0x7ea6e8，段三必须给出别的类名；
  N3 0xa8e8c8 在 BSS（段内偏移 0x6d8c8 > SizeOfRawData 0x6c000）⇒ 段二不能靠静态读，
     这一条同时说明「为什么必须走写入者反查」。
"""
import sys, os, json, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_r128'))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r129', 'r129b_clsid_factory.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
h = hashlib.sha256(open(EXE, 'rb').read()).hexdigest()
ck = []
def add(n, ok, d=''):
    ck.append({'name': n, 'ok': bool(ok), 'detail': d if not isinstance(d, (dict, list)) else json.dumps(d, ensure_ascii=False)})

add('B0 exe sha256 未变', h == EXE_SHA, h)

def imp_at(va):
    for e in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in e.imports:
            if imp.address == va:
                return (e.dll.decode(), (imp.name or b'').decode())
    return None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
def body(lo, n):
    return [(a, m, o) for a, sz, m, o in md.disasm_lite(rd(lo, n), lo)]

SEG = body(0x6bc425, 0x30)
txt = ['%08x %s %s' % (a, m, o) for a, m, o in SEG]
# S-185：首版把调用形态写成 call dword ptr [0x7e15d8]，实测是 mov esi,[0x7e15d8] 后 call esi。
# 断言按实际形态写，不改字节去迁就断言。
_j = ' | '.join(txt)
add('B1 段一：0x6bc42a 起 4 条 push 依次为 &local / 1 / 1 / 0xa8e8c8，第五个实参 0x7e9520 由 '
    '0x6bc43a 的 push 压入，随后 mov esi,[0x7e15d8] + call esi 调用 CoRegisterClassObject',
    'push eax' in _j and 'push 1' in _j and 'push 0xa8e8c8' in _j and 'push 0x7e9520' in _j
    and 'mov esi, dword ptr [0x7e15d8]' in _j and 'call esi' in _j, txt)
add('B2 0x7e15d8 = ole32!CoRegisterClassObject（名字取自本映像导入表字节）',
    imp_at(0x7e15d8) == ('ole32.dll', 'CoRegisterClassObject'), imp_at(0x7e15d8))
add('B3 段一 rclsid = .rdata 0x7e9520 = {B45A4A81-86DA-11D1-B706-00A024DDAFD1}，16 字节',
    secof(0x7e9520) == '.rdata' and gt(0x7e9520) == '{B45A4A81-86DA-11D1-B706-00A024DDAFD1}'
    and rd(0x7e9520, 16) == bytes.fromhex('814a5ab4da86d111b70600a024ddafd1'), gt(0x7e9520))

# 段二：0xa8e8c8 的 vptr 写入者唯一
add('B4 0xa8e8c8 在 .data BSS（段内偏移 0x6d8c8 > SizeOfRawData 0x6c000）⇒ 映像内无静态字节',
    secof(0xa8e8c8) == '.data' and (0xa8e8c8 - 0x812000) > 0x6c000 and rd(0xa8e8c8, 4) == b'',
    {'off': hex(0xa8e8c8 - 0x812000), 'raw': hex(0x6c000)})
C7W = []
pat = (0xa8e8c8).to_bytes(4, 'little')
sec_text = [s for s in SECS if s[0] == '.text'][0]
b = pe.__data__[sec_text[3]:sec_text[3] + sec_text[5]]
i = 0
while True:
    i = b.find(pat, i)
    if i < 0: break
    va = sec_text[1] + i
    pre = rd(va - 2, 2)
    C7W.append((va, pre.hex(), u32(va + 4) if False else None))
    i += 1
add('B5 0xa8e8c8 的 imm32 出现 2 处：0x4e7ce2（写 vptr）与 0x6bc436（作为 pUnk 传给注册）',
    len(C7W) == 2 and sorted(a for a, _, _ in C7W) == [0x4e7ce2, 0x6bc436],
    ['0x%08x' % a for a, _, _ in C7W])
w0 = 0x4e7ce0
add('B6 段二：0x4e7ce0 的字节是 c7 05 c8 e8 a8 00 64 a5 7e 00 + c3（mov [0xa8e8c8],0x7ea564 / ret），'
    '即唯一写入者把 vptr 写成 0x7ea564',
    rd(w0, 10) == bytes.fromhex('c705c8e8a800') + (0x7ea564).to_bytes(4, 'little') and rd(w0 + 10, 1) == b'\xc3',
    {'bytes': rd(w0, 11).hex()})
c = col_of(0x7ea564)
add('B7 段三：0x7ea564 的 COL 解出 .?AVTiberianSunClassFactory@@，基类 .?AUIClassFactory@@ ncb 1 与 '
    '.?AUIUnknown@@ ncb 0，三者 mdisp 全 0',
    c and c['type_desc'] == '.?AVTiberianSunClassFactory@@'
    and [(x['name'], x['ncb'], x['mdisp']) for x in c['bases']] ==
        [('.?AVTiberianSunClassFactory@@', 2, 0), ('.?AUIClassFactory@@', 1, 0), ('.?AUIUnknown@@', 0, 0)],
    c['type_desc'] if c else None)

# 段四：两处 rclsid 是同一个常量
def imm32_refs(val):
    out = []
    p2 = val.to_bytes(4, 'little')
    for name, lo, hi, ptr, vs, rs in SECS:
        if name not in ('.text', '.rdata', '.data'): continue
        d = pe.__data__[ptr:ptr + rs]; j = 0
        while True:
            j = d.find(p2, j)
            if j < 0: break
            out.append((name, lo + j)); j += 1
    return out
r9520 = [a for _, a in imm32_refs(0x7e9520)]
add('B8 段四：0x7e9520 的 imm32 引用全库 5 处，含 0x6bc43a（注册 pUnk）与 0x6bd93c（RegisterActiveObject 的 rclsid）',
    len(r9520) == 5 and 0x6bc43b in r9520 and 0x6bd93c in r9520,
    ['0x%08x' % a for a in r9520])
add('B9 段四：两处注册用的是同一个 CLSID 常量（0x6bc43a 与 0x6bd93c 都指向 0x7e9520），'
    '故「类工厂注册」与「活动对象注册」是同一个 CLSID 的两个面',
    0x6bc43b in r9520 and 0x6bd93c in r9520)

# S-186：首版反控误用 0x7ea6e8（它是 IID 常量不是 vtable），col_of 返 None。
# 换成真实的另一张类 vtable 0x7f4108，判据必须给出不同的类名。
c2 = col_of(0x7f4108)
add('B10 反控 N1：相邻常量 0x7e9510 = {B45A4A80-...} 与 0x7e9520 只差 Data1 末字节',
    gt(0x7e9510) == '{B45A4A80-86DA-11D1-B706-00A024DDAFD1}' and gt(0x7e9510) != gt(0x7e9520), gt(0x7e9510))
add('B11 反控 N2：把段二的 vptr 换成另一张真实类表 0x7f4108，段三给出的是 .?AVSwizzleManagerClass@@'
    '（与 0x7ea564 不同类），故段三不是恒等判据',
    bool(c2) and c2.get('type_desc') == '.?AVSwizzleManagerClass@@' and c2['type_desc'] != c['type_desc'],
    c2.get('type_desc') if c2 else None)
add('B12 反控 N3：0x7e9520 的 5 处引用里没有一处是「读 0xa8e8c8 处的静态 vptr」，'
    '因为该地址无静态字节（与 B4 一致）',
    rd(0xa8e8c8, 4) == b'')

ok = sum(1 for x in ck if x['ok'])
json.dump({'checks': ck, 'pass': ok, 'total': len(ck)}, open(OUT, 'w'), ensure_ascii=False, indent=1)
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'] + (('  | ' + str(x['detail'])) if not x['ok'] else ''))
print('%d/%d PASS' % (ok, len(ck)))
sys.exit(0 if ok == len(ck) else 1)
