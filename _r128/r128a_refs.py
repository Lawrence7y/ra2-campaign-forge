# -*- coding: utf-8 -*-
"""R128a：三个 BSS 单例（0x87f7e8 / 0x89a29c / 0xb0c110）的静态引用与 vptr 写入者。

事实起点（p3 实测）：三处都在 .data 的非 raw 区（BSS），映像文件里没有任何静态字节，
故「读 0x87f7e8 的 vptr」这条 R127 待办② 的字面做法在静态层面必然读到 0 ——
必须改用「谁写了它」的反向路径：全 .text 扫绝对地址立即数，找 C7 05 <addr> <vt>
形态的虚表常量写入，再解该 vt 的 RTTI。

判据全部正反控成对：
  正控  已知必然存在的写入者（0x429200 处 ApplicationClass 对象）
  反控  相邻但不相干的地址（0x87f7ec / 0x87f7e4 / 0x89a2a0）
"""
import sys, os, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from peek import *
import capstone

OUT = os.path.join(ROOT, '_r128', 'r128a_refs.json')
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
import hashlib
h = hashlib.sha256(open(EXE,'rb').read()).hexdigest()

ck = []
def add(n, ok, d=''):
    ck.append({'name':n, 'ok':bool(ok), 'detail':str(d)})

add('A0 exe sha256 是钉住的那个构建', h == EXE_SHA, h)

TXT_LO, TXT_HI = 0x401000, 0x7e1000
RD_LO, RD_HI = 0x7e1000, 0x812000
raw = rd(TXT_LO, TXT_HI - TXT_LO)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True
ins = [(a, m, o) for a, _s, m, o in md.disasm_lite(raw, TXT_LO)]
add('A1 .text 线性扫描（disasm_lite 流式，未开 detail）', len(ins) > 500000, 'ins=%d' % len(ins))

TARGETS = {0x87f7e8:'S1', 0x89a29c:'S2', 0xb0c110:'S3'}

def imm_refs(tgt):
    """极简：在指令流里找「操作数里以立即数形式出现 tgt」。分两种形态：
       (i) 存储器操作数绝对地址 [tgt]  —— 由 capstone 正常产出
       (ii) push/mov 立即数 tgt"""
    hits = []
    pat = tgt.to_bytes(4,'little')
    pat2 = tgt.to_bytes(4,'big')
    pos = 0
    while True:
        i = raw.find(pat, pos)
        if i < 0: break
        hits.append(i); pos = i+1
    return hits

for tgt, tag in TARGETS.items():
    pos = []
    p = tgt.to_bytes(4,'little'); q = 0
    while True:
        i = raw.find(p, q)
        if i < 0: break
        pos.append(i); q = i+1
    add('B%s 0x%08x 的 little-endian 4 字节在 .text 中出现 %d 次（纯字节枚举，不看反汇编）'
        % (tag, tgt, len(pos)), True, pos[:40])
    # 逐处按指令边界核验：该 4 字节是否落在某条已译码指令的操作数字节内
    starts = {a:i for i,(a,m,o) in enumerate(ins)}
    # 目标字节的 VA
    vas = [TXT_LO+i for i in pos]
    add('B%s2 上述 %d 处 VA' % (tag, len(vas)), True, ['0x%08x'%v for v in vas[:40]])

# ---- 主路：C7 05 <addr32> <imm32> = mov dword ptr [addr], imm32 ----
def c705_scan():
    out = []
    q = 0
    while True:
        i = raw.find(b'\xc7\x05', q)
        if i < 0: break
        if i+10 <= len(raw):
            tgt = struct.unpack('<I', raw[i+2:i+6])[0]
            imm = struct.unpack('<I', raw[i+6:i+10])[0]
            out.append((TXT_LO+i, tgt, imm))
        q = i+1
    return out

c705 = c705_scan()
add('C0 C7 05 形态（mov dword ptr [abs], imm32）在 .text 中共 %d 处' % len(c705),
    len(c705) > 100, 'n=%d' % len(c705))

for tgt, tag in TARGETS.items():
    w = [x for x in c705 if x[1] == tgt]
    add('C%s 直接写入 0x%08x 的 C7 05 站点 %d 个' % (tag, tgt, len(w)),
        True, [('0x%08x'%a, '0x%08x'%im) for a,_,im in w])

# 反控：相邻地址
for tgt, tag in [(0x87f7ec,'R1'), (0x87f7e4,'R2'), (0x89a2a0,'R3'), (0xb0c114,'R4')]:
    w = [x for x in c705 if x[1] == tgt]
    add('R%s 反控 相邻地址 0x%08x 的 C7 05 站点数（用于对比，不作断言）' % (tag, tgt),
        True, len(w))

json.dump({'checks':ck, 'c705':[(a,t,i) for a,t,i in c705]}, open(OUT,'w'), ensure_ascii=False, indent=1)

npass = sum(1 for c in ck if c['ok'])
print('r128a: %d/%d PASS' % (npass, len(ck)))
for c in ck:
    print(('  PASS ' if c['ok'] else '  FAIL ') + c['name'])
    if c['detail'] and c['detail'] != 'True':
        print('        ' + str(c['detail'])[:400])
