#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 第三刀（本轮交付）：把「槽 4 = AbstractClass 第 5 个虚函数」做成可失败判据。

r193a/r193b 共 29 条断言里 14 条 FAIL，全部是判据缺陷（结论未受影响），本脚本逐处修：
  F1 bcds() 少一次解引用（pCHD+12 指向 BCD 指针数组）。
  F2 md.disasm 未在 ret 处截断 ⇒ n 记成窗口内全部指令数（0x410450 记成 80 条）。
  F3 this 别名只认 mov r,[esp+4]，漏掉本镜像主形态 `mov esi,ecx`。
  F4 「写」只在 mov [mem],x 里找，漏掉 `push dword ptr [reg+0xNN]`。
  F5 H1 的分母用错：954 张主表里大量模板容器类（VectorClass/DynamicVectorClass/
     CDFileClass 族）根本不继承 AbstractClass，用它们当分母必然 FAIL。改用
     「COL 链里真的含 .?AVAbstractClass@@」的血统集合做分母。
  F6 BCD 落在 .rdata 而不是 .data，用 .data 虚拟区间筛会全空（本轮新犯的一次）。

本轮主张（每条都可被数据否掉）：
  K1 双向唯一：0x410450 在全部 1,214 张表里只出现在槽 4 位置（不跨槽号）。
  K2 血统充分：链含 AbstractClass 的每一张主表槽数 > 4（槽 4 存在，无空缺）。
  K3 默认实现：血统表里槽 4 == 0x410450 的张数 + 覆写张数 == 血统张数，覆写者逐个列出。
  K4 语义形态：0x410450 全函数体 = 读 [this+0x20] 字节 → sete ⇒ 返回 !Dirty。
     K4c 该形态在血统表槽 4 上只对应 1 个不同地址。
  K5 字段归属：血统表里存在「槽 4 读 [this+0x20] 且槽 13 也触及 [this+0x20]」的表，
     这是不依赖 kb/22 的独立字节证据。
  K6 唯一的覆写者：HouseTypeClass 槽 4 = 0x512280，给出全函数体与它读的字段偏移。
反控：
  N1 ObjectClass 血统张数严格少于 AbstractClass 血统张数（子树）。
  N2 0x410450 在槽 5 出现 0 次。
  N3 「读 +0x20 + sete」形态扫槽 5 的 546 个实现，命中 0（形态不是普适垃圾判据）。
"""
import sys, struct, collections, json, capstone
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
X86 = capstone.x86
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True

fails = []; N = 0
def ck(nm, c, d=''):
    global N; N += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

T = P.B['.text']; LO = T['lo']; HI = T['hi_file']
def in_text(x): return x is not None and LO <= x < HI
def wv(sn):
    s = P.B[sn]; n = s['rawsize'] // 4
    return s['lo'], struct.unpack_from('<%dI' % n, P.RAW, s['rawptr']), n

COL = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n - 4):
        if w[i] not in (0, 1) or w[i + 2] != 0: continue
        if P.where(w[i + 3]) != '.data' or P.where(w[i + 4]) != '.rdata': continue
        nm = P.cstr(w[i + 3] + 8, 200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base + 4 * i] = dict(mdisp=w[i + 1], ptd=w[i + 3], pchd=w[i + 4], name=nm.decode('latin1'))
VT = {}
for sn in ('.rdata', '.data'):
    base, w, n = wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base + 4 * i - 4) in COL: VT[base + 4 * i] = P.dw(base + 4 * i - 4)
def nslot(vt):
    k = 0
    while in_text(P.dw(vt + 4 * k)): k += 1
    return k
NS = {vt: nslot(vt) for vt in VT}
grp = collections.defaultdict(list)
for vt in sorted(VT): grp[COL[VT[vt]]['name']].append(vt)
ck('A0 基线 COL=1214 VT=1214 槽=14044 组=954 多表组=94（与 R190..R192 四轮同值）',
   (len(COL), len(VT), sum(NS.values()), len(grp), sum(1 for v in grp.values() if len(v) > 1)) == (1214, 1214, 14044, 954, 94),
   (len(COL), len(VT), sum(NS.values()), len(grp)))

def chain(colva):
    c = COL[colva]
    n = P.dw(c['pchd'] + 8); arr = P.dw(c['pchd'] + 12)
    out = []
    for j in range(n):
        b = P.dw(arr + 4 * j)
        if b is None or P.where(b) in ('None', 'other'): continue     # F6 修
        ptd = P.dw(b)
        if ptd is None: continue
        nm = P.cstr(ptd + 8, 160)
        out.append(dict(bcd=b, ptd=ptd, ncb=P.dw(b + 4), mdisp=P.dw(b + 8),
                        name=(nm.decode('latin1') if nm else None)))
    return out
ch0 = chain(VT[0x7e1f50])
ck('A1 正控 0x7E1F50（AbstractClass 主表）链 8 条：AbstractClass@0 … INoticeSink@8 / INoticeSource@12',
   len(ch0) == 8 and ch0[0]['name'] == '.?AVAbstractClass@@' and ch0[0]['ncb'] == 7
   and ch0[-1]['name'] == '.?AVINoticeSource@@' and ch0[-1]['mdisp'] == 12,
   [(x['name'], x['mdisp']) for x in ch0])
ck('A1b 正控 0x7E3EBC（BuildingClass 主表，F02 已证 322 槽）链 15 条含 FlasherClass@240',
   NS[0x7e3ebc] == 322 and len(chain(VT[0x7e3ebc])) == 15
   and any(x['name'] == '.?AVFlasherClass@@' and x['mdisp'] == 240 for x in chain(VT[0x7e3ebc])),
   (NS[0x7e3ebc], len(chain(VT[0x7e3ebc]))))
ck('A1c 反控 0x7E1668（CDFileClass 主表，非 AbstractClass 血统）链里不含 AbstractClass',
   not any(x['name'] == '.?AVAbstractClass@@' for x in chain(VT[0x7e1668])),
   [x['name'] for x in chain(VT[0x7e1668])][:4])

CH = {vt: [x['name'] for x in chain(VT[vt])] for vt in VT}
AB = '.?AVAbstractClass@@'; OB = '.?AVObjectClass@@'
MAIN = [vt for vt in sorted(VT) if COL[VT[vt]]['mdisp'] == 0]
LIN = [vt for vt in MAIN if AB in CH[vt]]
LIN_OB = [vt for vt in MAIN if OB in CH[vt]]
print('   主表 %d 张；链含 AbstractClass %d 张；链含 ObjectClass %d 张' % (len(MAIN), len(LIN), len(LIN_OB)))
ck('K2 血统充分：AbstractClass 血统的每一张主表槽数 > 4（槽 4 存在）',
   all(NS[vt] > 4 for vt in LIN), [hex(v) for v in LIN if NS[v] <= 4])
ck('N1 反控：ObjectClass 血统张数严格少于 AbstractClass 血统张数',
   0 < len(LIN_OB) < len(LIN), (len(LIN_OB), len(LIN)))
print('   AbstractClass 血统主表类名（%d 张，前 60）：%s' % (len(LIN), ', '.join(
    sorted(COL[VT[v]]['name'].replace('.?AV', '').replace('@@', '') for v in LIN))[:1200]))

TGT = 0x410450
occ = collections.Counter(); tabset = set()
for vt in VT:
    for s in range(NS[vt]):
        if P.dw(vt + 4 * s) == TGT: occ[s] += 1; tabset.add(vt)
print('   0x410450 在全部 1,214 张表的槽号分布 %s；落在 %d 张表' % (dict(occ), len(tabset)))
ck('K1 双向唯一：0x410450 只出现在槽 4（其余槽号 0 次）', set(occ) == {4}, dict(occ))
ck('K1b 0x410450 落在 77 张表（与 R192 独立同值）', len(tabset) == 77, len(tabset))
s4 = [(vt, P.dw(vt + 16)) for vt in LIN]
c410 = sum(1 for vt, a in s4 if a == TGT)
other = [(vt, a) for vt, a in s4 if a != TGT]
print('   血统表槽 4：== 0x410450 的 %d 张；覆写 %d 张 %s' % (c410, len(other),
      [(hex(v), '%08X' % a, COL[VT[v]]['name']) for v, a in other]))
ck('K3 血统表槽 4 默认实现 == 0x410450，且 命中 + 覆写 == 血统张数',
   c410 >= 0.9 * len(LIN) and c410 + len(other) == len(LIN), (c410, len(other), len(LIN)))
ck('K1c 0x410450 的 77 张表 == 血统表槽 4 命中数（两口径闭合）',
   len(tabset) == c410, (len(tabset), c410))

def fn(va, limit=160):
    o = P.r2o(va)
    if o is None: return None
    ins = []
    for i in md.disasm(P.RAW[o:o + limit], va):
        ins.append(i)
        if i.mnemonic in ('ret', 'retn'): break          # F2 修
    if not ins: return None
    alias = {'ecx'}
    for i in ins[:5]:                                    # F3 修
        if i.mnemonic == 'mov' and i.operands[0].type == X86.X86_OP_REG:
            if i.operands[1].type == X86.X86_OP_REG and i.operands[1].reg == X86.X86_REG_ECX:
                alias.add(i.reg_name(i.operands[0].reg))
            elif i.operands[1].type == X86.X86_OP_MEM and i.operands[1].mem.base == X86.X86_REG_ESP \
                 and i.operands[1].mem.disp in (4, 8):
                alias.add(i.reg_name(i.operands[0].reg))
    refs = []
    for k, i in enumerate(ins):
        for oi, op in enumerate(i.operands):
            if op.type != X86.X86_OP_MEM: continue
            bn = i.reg_name(op.mem.base) if op.mem.base else None
            if bn not in alias or op.mem.disp == 0: continue
            use = 'READ'
            if i.mnemonic == 'mov' and oi == 0: use = 'WRITE'
            elif i.mnemonic == 'push' and oi == 0 and op.mem.base: use = 'ARG'   # F4 修
            elif i.mnemonic == 'mov' and oi == 1 and any(
                    j.mnemonic == 'push' and j.operands and j.operands[0].type == X86.X86_OP_REG
                    and i.reg_name(j.operands[0].reg) == i.reg_name(i.operands[0].reg)
                    for j in ins[k + 1:k + 4]): use = 'ARG'
            refs.append((op.mem.disp & 0xFFFFFFFF, use))
    sets = [i.mnemonic for i in ins if i.mnemonic.startswith('set')]
    return dict(va=va, n=len(ins), refs=refs, sets=sets,
                retimm=(ins[-1].operands[0].imm if ins[-1].mnemonic in ('ret', 'retn')
                        and ins[-1].operands else 0),
                hexb=P.RAW[o:o + 16].hex(),
                text=' ; '.join('%s %s' % (i.mnemonic, i.op_str) for i in ins))
g = fn(TGT)
print('   0x410450 全函数体（%d 条）：%s' % (g['n'], g['text']))
ck('K4 0x410450 = 6 条 / refs 仅 (0x20,READ) / sets 仅 sete / ret 4 / 16 字节 8b4c240433c08a512084d20f94c0c204',
   g['n'] == 6 and g['refs'] == [(0x20, 'READ')] and g['sets'] == ['sete'] and g['retimm'] == 4
   and g['hexb'].startswith('8b4c240433c08a512084d20f94c0c204'),
   (g['n'], g['refs'], g['sets'], g['retimm'], g['hexb']))
g9 = fn(0x4C9150)
ck('K4b 0x4C9150 = 2 条 xor eax,eax / ret 无立即数 / 字节 33c0c3（抽象桩形态）',
   g9['n'] == 2 and g9['refs'] == [] and g9['retimm'] == 0 and g9['hexb'].startswith('33c0c3'),
   (g9['n'], g9['refs'], g9['retimm'], g9['hexb']))
occ5 = [vt for vt in VT if NS[vt] > 5 and P.dw(vt + 20) == TGT]
ck('N2 反控：0x410450 在槽 5 出现 0 次', len(occ5) == 0, len(occ5))
shape = []
for vt, a in s4:
    f = fn(a)
    if f and f['sets'] == ['sete'] and any(o == 0x20 and u == 'READ' for o, u in f['refs']):
        shape.append(a)
print('   血统表槽 4 实现里「读 +0x20 + sete」的地址集合：%s' % ['%08X' % x for x in sorted(set(shape))])
ck('K4c 该形态在血统表槽 4 上只对应 1 个不同地址（= 0x410450）', set(shape) == {TGT},
   sorted(set(shape)))
hit5 = []
for vt in VT:
    if NS[vt] <= 5: continue
    f = fn(P.dw(vt + 20))
    if f and f['sets'] == ['sete'] and any(o == 0x20 and u == 'READ' for o, u in f['refs']):
        hit5.append(P.dw(vt + 20))
ck('N3 反控：同一形态在槽 5 上命中 0 个（形态不是普适垃圾判据）',
   len(set(hit5)) == 0, ['%08X' % x for x in sorted(set(hit5))][:5])

pair = []
for vt in LIN:
    if NS[vt] <= 13: continue
    a4 = fn(P.dw(vt + 16)); a13 = fn(P.dw(vt + 52))
    if not a4 or not a13: continue
    r4 = set(o for o, u in a4['refs'] if u == 'READ')
    r13 = set(o for o, u in a13['refs'])
    if 0x20 in r4 and 0x20 in r13: pair.append(vt)
print('   血统表里「槽4 读 +0x20 且 槽13 也触及 +0x20」的表 %d 张 %s'
      % (len(pair), [(hex(v), COL[VT[v]]['name']) for v in pair[:8]]))
ck('K5 血统表上存在该读写对（字段归属的独立字节证据，不依赖 kb/22）', len(pair) >= 1, len(pair))
if pair:
    v = pair[0]
    print('   例 %08X %s：槽4=%s | 槽13=%s' % (v, COL[VT[v]]['name'],
          fn(P.dw(v + 16))['text'], fn(P.dw(v + 52))['text'][:170]))

ov = None
if other:
    v, a = other[0]
    ov = dict(vt='%08X' % v, cls=COL[VT[v]]['name'], tgt='%08X' % a, fn=fn(a))
    print('\n   K6 唯一覆写者 %s 槽 4 = %08X：%s' % (ov['cls'], a, ov['fn']['text']))
    ck('K6 覆写者不是 0x410450，且其体首不与 0x410450 同形（不读 +0x20 sete）',
       a != TGT and not (ov['fn']['sets'] == ['sete'] and
                         any(o == 0x20 and u == 'READ' for o, u in ov['fn']['refs'])),
       (ov['cls'], ov['fn']['sets'], ov['fn']['refs'][:4]))
    ck('K6b 覆写者 ret 立即数 == 4（与 IsDirty 同调用约定，槽位替换不改契约）',
       ov['fn']['retimm'] == 4, ov['fn']['retimm'])

json.dump(dict(main=len(MAIN), lin=len(LIN), lin_ob=len(LIN_OB),
               lin_names=sorted(COL[VT[v]]['name'] for v in LIN), occ=dict(occ),
               tabset=len(tabset), slot4_hit=c410,
               overrides=[('%08X' % v, '%08X' % a, COL[VT[v]]['name']) for v, a in other],
               f410=g, shape=['%08X' % x for x in sorted(set(shape))],
               hit5=['%08X' % x for x in sorted(set(hit5))],
               pair=[('%08X' % v, COL[VT[v]]['name']) for v in pair], override_fn=ov,
               fails=fails), open('_r193/r193c.json', 'w'), ensure_ascii=False, indent=1)
print('\n断言 %d 条，FAIL %d 条 %s' % (N, len(fails), fails))
sys.exit(1 if fails else 0)
