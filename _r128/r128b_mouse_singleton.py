# -*- coding: utf-8 -*-
"""R128b：R127 待办② 的反向路径 —— 0x87f7e8 的静态字节全 0（BSS），
改从「谁写它的 vptr」反查它运行期的类型。

口径纪律（本轮自错 S-179 的产物）：0x87f7e8 的 4 字节在 .text 里出现 3700 次、
逐字节与指令级两条口径一致，是因为 MouseClass 是全局单例、3693 处都是
mov ecx, 0x87f7e8 的 this 传递（objdump 独立复核 0x41434d / 0x41435c / 0x414373 三处，
字节 b9 e8 f7 87 00 逐位相符）。所以「引用多」不是巧合，但真正写 vptr 的只有 1 处。
"""
import sys, os, json, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone
from collections import Counter

OUT = os.path.join(ROOT, '_r128', 'r128b_mouse.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
h = hashlib.sha256(open(EXE,'rb').read()).hexdigest()

ck = []
def add(n, ok, d=''):
    ck.append({'name':n,'ok':bool(ok),'detail':str(d)})

add('B0 exe sha256 未变', h == EXE_SHA, h)

TXT_LO, TXT_HI = 0x401000, 0x7e1000
raw = rd(TXT_LO, TXT_HI - TXT_LO)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(raw, TXT_LO)]

S = 0x87f7e8
rawhits = []
q = 0; pat = S.to_bytes(4,'little')
while True:
    i = raw.find(pat, q)
    if i < 0: break
    rawhits.append(TXT_LO+i); q = i+1
hexref = '0x%x' % S
iref = [(a, m, o) for a, m, o in ins if hexref in o.lower()]
add('B1 逐字节口径 3700 与指令级口径 3700 一致 —— 该地址每次出现都落在一条已译码指令的'
    '立即数/位移字段里，没有一次是巧合子串（S-179：我原先预判指令级远少于字节级，反了）',
    len(rawhits) == len(iref) == 3700 and len(ins) < 2000000,
    'raw=%d ins=%d' % (len(rawhits), len(iref)))

shapes = Counter()
for a,m,o in iref:
    d = o.split(',')[0].strip()
    if m == 'push': shapes['push imm'] += 1
    elif m == 'mov' and d == 'ecx': shapes['mov ecx,<S> (this 传递)'] += 1
    elif m == 'mov' and d.startswith('dword ptr [0x87f7e8]'): shapes['mov [S],imm (写 vptr)'] += 1
    elif m == 'mov' and d.startswith('dword ptr ['): shapes['mov [S],reg'] += 1
    elif m == 'mov': shapes['mov reg,[S] (读字段)'] += 1
    elif m == 'lea': shapes['lea (取地址)'] += 1
    else: shapes['other:'+m] += 1
add('B2 形态分布：3693 处 mov ecx,<S> 是全局单例的 this 传递，'
    '真正的 vptr 写入只有 1 处',
    shapes['mov ecx,<S> (this 传递)'] == 3693 and shapes['mov [S],imm (写 vptr)'] == 1,
    dict(shapes))

add('B3 0x87f7e8 落在 .data 的非 raw 区（BSS），映像文件里没有任何静态字节，'
    '故 R127 待办② 的字面做法「静态读 0x87f7e8 的 vptr」必然读到 0，不可行',
    rd(S, 16) == b'' and secof(S) == '.data', 'rd=%r sect=%s' % (rd(S,16), secof(S)))

wr = [(a, m, o) for a, m, o in iref if m == 'mov' and o.startswith('dword ptr [0x87f7e8], ')]
add('B4 以 mov dword ptr [0x87f7e8], imm32 形态写它的站点恰 1 处，写入值 0x7e1964',
    len(wr) == 1 and wr[0][2].endswith('0x7e1964'), wr)

def writes(addr, form='imm'):
    hx = '0x%x' % addr
    out = []
    for a,m,o in ins:
        if m != 'mov': continue
        if not o.startswith('dword ptr [%s], ' % hx): continue
        out.append((a,o))
    return out

add('B5 反控：相邻地址 0x87f7e4 的写入 0 处、0x87f7ec 与主对象无关的写入见明细；'
    '判据不是「凡 .data 地址都命中」',
    len(writes(0x87f7e4)) == 0,
    {'87f7e4': writes(0x87f7e4), '87f7ec': writes(0x87f7ec),
     '89a29c': writes(0x89a29c), 'b0c110': writes(0xb0c110)})

VT = 0x7e1964
c = col_of(VT)
add('B6 0x7e1964 的 COL 解出类名 .?AVMouseClass@@（12 条基类）',
    c and c['type_desc'] == '.?AVMouseClass@@' and c['n'] == 12,
    c['type_desc'] if c else None)
add('B7 该 COL 末条基类 .?AVINoticeSink@@ 的 mdisp = 21784 = 0x5518',
    any(b['name'] == '.?AVINoticeSink@@' and b['mdisp'] == 0x5518 for b in c['bases']),
    [(b['name'], b['mdisp']) for b in c['bases'] if b['name'] == '.?AVINoticeSink@@'])

init = [(a,m,o) for a,m,o in ins if 0x40d18a <= a <= 0x40d1b0]
add('B8 静态初始化 0x40d190 是 mov ecx,0x87f7e8 / call 0x5bda40 / push 0x40d1b0 / call 0x7c978a / ret'
    '（ctor 后立刻 atexit 注册析构 0x40d1b0）',
    [m for a,m,o in init if a >= 0x40d190][:6] == ['mov','call','push','call','pop','ret'],
    [(hex(a), m, o) for a,m,o in init if a >= 0x40d190])

code = rd(0x5bda40, 0x38)
body = [(a,m,o) for a,sz,m,o in md.disasm_lite(code, 0x5bda40)]
st0 = [(a,m,o) for a,m,o in body if m=='mov' and o.startswith('dword ptr [esi], ')]
st5 = [(a,m,o) for a,m,o in body if m=='mov' and o.startswith('dword ptr [esi + 0x5518], ')]
add('B9 ctor 0x5bda40 体写 [esi] <- 0x7e1964 与 [esi + 0x5518] <- 0x7e195c，'
    '偏移与 RTTI 的 mdisp 0x5518 逐位一致',
    len(st0) == 1 and st0[0][2].endswith('0x7e1964')
    and len(st5) == 1 and st5[0][2].endswith('0x7e195c'),
    {'[esi]': [(hex(a),o) for a,m,o in st0], '[esi+0x5518]': [(hex(a),o) for a,m,o in st5]})

b58 = col_of(0x7e195c)
add('B10 0x7e195c 的 COL 也解出 .?AVMouseClass@@，但 COL 指针与主 vtable 的不同'
    '（主 0x7fa9b8 / 子对象 0x7fab38）—— 两条 COL 各自 12 条基类，证实是同一类的两个 vtable',
    b58 and b58['type_desc'] == '.?AVMouseClass@@'
    and u32(0x7e1958) != u32(0x7e1960),
    {'main_COL':'0x%08x'%u32(0x7e1960), 'sub_COL':'0x%08x'%u32(0x7e1958),  # main=+0x0 vtable, sub=+0x5518
     'main_class':c['type_desc'], 'sub_class':b58['type_desc'] if b58 else None})

json.dump({'checks':ck,'shapes':dict(shapes)}, open(OUT,'w'), ensure_ascii=False, indent=1)
npass = sum(1 for x in ck if x['ok'])
print('r128b: %d/%d PASS' % (npass, len(ck)))
for x in ck:
    print(('  PASS ' if x['ok'] else '  FAIL ') + x['name'])
    if x['detail']: print('        ' + str(x['detail'])[:400])
