#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 第二刀：把「槽 4 读 [this+0x20]」从「任意 mem 偏移里恰好有 0x20」升级为
「this 指针可达的字段引用」，并区分 读 / 作为调用参数传出 / 写 三种用法。

r193a 的 15 条断言里 7 条 FAIL，全部是判据缺陷（不是结论缺陷），本脚本逐处修正：
  F1 bcds() 少一次解引用（pCHD+12 指向「BCD 指针数组」，不是 BCD 内联数组）。
  F2 偏移普查把 [esp+4]/[esp+0x0] 这类栈引用与 [ecx+0x20] 字段引用混计
     ⇒ 0x4/0x0 排在前两名，0x20 只在第三。
  F3 写检测只认 mov [mem],x，漏掉本镜像序列化的真实形态
     `push dword ptr [esi+0x10]` / `mov cl,byte ptr [esi+0x20]; push ecx; call`。
本脚本口径：
  this 寄存器 = 入口的 ecx；若入口出现 mov r,[esp+4] / mov r,[esp+8] 也登记为 this 别名。
  字段引用 = mem.base ∈ this 别名集合 且 disp != 0。
  用法分三类：READ（仅被读）、ARG（读出的值被 push 或作为 call 参数传出）、WRITE（mov [mem],x）。
"""
import sys, struct, collections, json, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P

fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
grp=collections.defaultdict(list)
for vt in sorted(VT): grp[COL[VT[vt]]['name']].append(vt)
ck('A0 基线 COL=1214 VT=1214 槽=14044 组=954 多表组=94',
   (len(COL),len(VT),sum(NS.values()),len(grp),sum(1 for v in grp.values() if len(v)>1))==(1214,1214,14044,954,94),
   (len(COL),len(VT),sum(NS.values()),len(grp),sum(1 for v in grp.values() if len(v)>1)))
MAIN=[vt for vt in sorted(VT) if COL[VT[vt]]['mdisp']==0]
ck('A0b 主表数 954', len(MAIN)==954, len(MAIN))

def bcds(colva):
    c=COL[colva]
    n=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12)      # F1: 数组元素是 BCD 指针
    out=[]
    for j in range(n):
        b=P.dw(arr+4*j)
        if P.where(b) is None or P.where(b)=='other': continue
        ptd=P.dw(b); nm=P.cstr((ptd or 0)+8,160)
        out.append(dict(bcd=b,ptd=ptd,ncb=P.dw(b+4),mdisp=P.dw(b+8),pdisp=P.dw(b+12),
                        name=(nm.decode('latin1') if nm else None)))
    return out
ch0=bcds(VT[0x7e1f50])
print('   正控 0x7e1f50 链：%s'%[(x['name'],x['mdisp'],x['ncb']) for x in ch0])
ck('A1 正控 0x7e1f50 链 8 条 / 首条 .?AVAbstractClass@@ ncb7 mdisp0 / 末条 INoticeSource mdisp12',
   len(ch0)==8 and ch0[0]['name']=='.?AVAbstractClass@@' and ch0[0]['ncb']==7
   and ch0[0]['mdisp']==0 and ch0[-1]['name']=='.?AVINoticeSource@@' and ch0[-1]['mdisp']==12,
   (len(ch0),ch0[0]['name'],ch0[-1]['name']))
ck('A1b 反控：同一链里 INoticeSink 的 mdisp == 8（与 AbstractClass 的 0 不同）',
   [x['mdisp'] for x in ch0 if x['name']=='.?AVINoticeSink@@']==[8])

CH={vt:[(x['name'],x['mdisp'],x['ncb']) for x in bcds(VT[vt])] for vt in VT}
AB='.?AVAbstractClass@@'
HAS=[vt for vt in MAIN if any(n==AB for n,_,_ in CH[vt])]
NO=[vt for vt in MAIN if not any(n==AB for n,_,_ in CH[vt])]
print('   主表链含 AbstractClass 的 %d 张 / 不含 %d 张'%(len(HAS),len(NO)))
if NO:
    print('   不含例（前 6）：%s'%[(hex(v),COL[VT[v]]['name'],[n for n,_,_ in CH[v]][:3]) for v in NO[:6]])
ck('H1 全部 954 张主表链都含 .?AVAbstractClass@@（若无则槽 4 不能一概按 AbstractClass 解释）',
   len(NO)==0, (len(HAS),len(NO)))

md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True
X86=capstone.x86
def this_fields(va,limit=96):
    o=P.r2o(va)
    if o is None: return None
    ins=list(md.disasm(P.RAW[o:o+limit],va))
    if not ins: return None
    alias={'ecx'}
    for i in ins[:4]:
        if i.mnemonic=='mov' and i.operands[0].type==X86.X86_OP_REG \
           and i.operands[1].type==X86.X86_OP_MEM \
           and i.operands[1].mem.base==X86.X86_REG_ESP and i.operands[1].mem.disp in (4,8):
            alias.add(i.reg_name(i.operands[0].reg))
    refs=[]
    for k,i in enumerate(ins):
        for oi,op in enumerate(i.operands):
            if op.type!=X86.X86_OP_MEM: continue
            bn=i.reg_name(op.mem.base) if op.mem.base else None
            if bn not in alias: continue
            if op.mem.disp==0: continue
            use='READ'
            if i.mnemonic=='mov' and oi==0: use='WRITE'
            elif i.mnemonic=='push' or (i.mnemonic=='mov' and oi==1
                 and any(j.mnemonic=='push' and j.operands and j.operands[0].type==X86.X86_OP_REG
                         and i.reg_name(j.operands[0].reg)==i.reg_name(i.operands[0].reg)
                         for j in ins[k+1:k+4])):
                use='ARG'
            refs.append((op.mem.disp&0xFFFFFFFF,use))
        if i.mnemonic in ('ret','retn'): break
    return dict(va=va,n=len(ins),refs=refs,alias=sorted(alias),
                retimm=(ins[-1].operands[0].imm if ins[-1].mnemonic in ('ret','retn') and ins[-1].operands else 0),
                hexb=P.RAW[o:o+16].hex(),
                text=' ; '.join('%s %s'%(i.mnemonic,i.op_str) for i in ins))
f=this_fields(0x410450)
print('   正控 0x410450：%s'%(f['text'],))
ck('A2 正控 0x410450 ⇒ 6 条 / this 字段引用仅 (0x20,READ) / ret 4 / 字节 8b4c240433c08a5120',
   f['n']==6 and f['refs']==[(0x20,'READ')] and f['retimm']==4
   and f['hexb'].startswith('8b4c240433c08a5120'), (f['n'],f['refs']))
ck('A2b 正控 0x4C9150 ⇒ 2 条 / 无字段引用 / ret 0 / 字节 33c0c3',
   (lambda g:(g['n'],g['refs'],g['retimm'],g['hexb'][:6]))(this_fields(0x4C9150))==(2,[],0,'33c0c3'))
f13=this_fields(0x410410)
print('   0x410410 槽13：%s'%f13['text'])
ck('A2c 正控 0x410410 ⇒ 字段引用含 0x10 与 0x20（0x20 以 mov cl,[esi+0x20]; push ecx 形态传出）',
   (0x10,'ARG') in f13['refs'] and (0x20,'ARG') in f13['refs'], f13['refs'])
ck('A2d 反控：0x410410 的 0x20 不是 WRITE（本镜像经 push+call 序列化，不是直接写）',
   (0x20,'WRITE') not in f13['refs'])

def census(slot):
    d=collections.defaultdict(list)
    for vt in MAIN:
        if NS[vt]<=slot: continue
        d[P.dw(vt+4*slot)].append(vt)
    return d
INFO={}
def info(va):
    if va not in INFO: INFO[va]=this_fields(va)
    return INFO[va]
res={}
for slot in (4,5,13):
    d=census(slot); res[slot]=dict(nimpl=len(d),ntab=sum(len(v) for v in d.values()))
    offr=collections.Counter(); offw=collections.Counter(); offa=collections.Counter()
    for va in d:
        I=info(va)
        if not I: continue
        for off,use in I['refs']:
            (offw if use=='WRITE' else offa if use=='ARG' else offr)[off]+=1
    print('\n== 槽 %d：%d 张表 / %d 个实现'%(slot,res[slot]['ntab'],len(d)))
    print('   READ 偏移前 6 %s'%[(hex(k),v) for k,v in offr.most_common(6)])
    print('   ARG  偏移前 6 %s'%[(hex(k),v) for k,v in offa.most_common(6)])
    print('   WRITE偏移前 6 %s'%[(hex(k),v) for k,v in offw.most_common(6)])
    res[slot].update(read={('%X'%k):v for k,v in offr.items()},
                     arg={('%X'%k):v for k,v in offa.items()},
                     write={('%X'%k):v for k,v in offw.items()})
    top=sorted(d.items(),key=lambda kv:-len(kv[1]))[:6]
    res[slot]['top']=[dict(va='%08X'%va,cnt=len(l),refs=[(hex(o),u) for o,u in (info(va)['refs'] or [])],
                           hexb=info(va)['hexb'],text=info(va)['text'][:90]) for va,l in top]
    for t in res[slot]['top']: print('   %s x%-3d %s'%(t['va'],t['cnt'],t['text'][:96]))

d4=census(4)
ck('H2 槽 4 Top1 = 0x410450 77 张表（与 R192 独立一致）',
   sorted(d4.items(),key=lambda kv:-len(kv[1]))[0][0]==0x410450
   and len(sorted(d4.items(),key=lambda kv:-len(kv[1]))[0][1])==77)
off4=collections.Counter()
for va in d4:
    for off,use in (info(va)['refs'] or []): off4[off]+=1
print('\n   槽 4 全实现的 this 字段偏移（不分用法）前 8：%s'%[(hex(k),v) for k,v in off4.most_common(8)])
ck('H2b 修 F2 后：0x20 是槽 4 的众数字段偏移', off4.most_common(1)[0][0]==0x20, off4.most_common(3))
d5=census(5)
off5=collections.Counter()
for va in d5:
    for off,use in (info(va)['refs'] or []): off5[off]+=1
print('   槽 5 对照：%s'%[(hex(k),v) for k,v in off5.most_common(6)])
ck('N1 反控：槽 5 的众数字段偏移不是 0x20', off5.most_common(1)[0][0]!=0x20, off5.most_common(3))
d13=census(13)
w13=collections.Counter(); a13=collections.Counter()
for va in d13:
    for off,use in (info(va)['refs'] or []):
        if use=='WRITE': w13[off]+=1
        if use=='ARG': a13[off]+=1
print('   槽 13 写偏移 %s / 传出参数偏移 %s'%([(hex(k),v) for k,v in w13.most_common(5)],
                                        [(hex(k),v) for k,v in a13.most_common(5)]))
ck('H3 修 F3 后：槽 13 有实现把 [this+0x20] 作为参数传出（AbstractClass::Save 序列化 Dirty）',
   a13.get(0x20,0)>0, a13.most_common(4))
pair=[]
for vt in MAIN:
    if NS[vt]<=13: continue
    a=info(P.dw(vt+16)); b=info(P.dw(vt+52))
    if not a or not b: continue
    if any(o==0x20 and u=='READ' for o,u in a['refs']) and any(o==0x20 for o,u in b['refs']):
        pair.append(vt)
print('   「槽4 读 [this+0x20] 且 槽13 触及 [this+0x20]」的主表数 = %d'%len(pair))
ck('H3b 同一张主表上存在该读写对（字段归属的独立字节证据）', len(pair)>0, len(pair))
res['pair']=[('%08X'%v,COL[VT[v]]['name']) for v in pair[:12]]
res['pair_n']=len(pair)
if pair:
    v=pair[0]; print('   例 %08X %s 槽4=%08X 槽13=%08X'%(v,COL[VT[v]]['name'],P.dw(v+16),P.dw(v+52)))

json.dump(dict(main=len(MAIN),has_ab=len(HAS),no_ab=[('%08X'%v,COL[VT[v]]['name']) for v in NO],
               census=res,off4={('%X'%k):v for k,v in off4.items()},
               off5={('%X'%k):v for k,v in off5.items()},fails=fails),
          open('_r193/r193b.json','w'),ensure_ascii=False,indent=1)
print('\n断言 %d 条，FAIL %d 条 %s'%(N,len(fails),fails))
sys.exit(1 if fails else 0)
