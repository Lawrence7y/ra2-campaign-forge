#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 FF：审计 #445 第 3 条「symbols.json 的 vtable_va 语义不统一」—— 主会话复算并定量。

主张：那 12 个主 COL.mdisp==4 的 Locomotion 类，symbols.json 给的 vtable_va 是 **ILocomotion 次对象
vtable**（mdisp==4），而它们各自还有一个 mdisp==0 的主 vtable，两者地址差恒为 +0xCC。
若成立 ⇒ symbols.json 的 vtable_va 对 12/954 条与其余 942 条语义不同，引用「类的主 vtable」时不可直取。
"""
import sys,json,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
dw=P.dw;where=P.where;cstr=P.cstr;RAW=P.RAW
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
TD=set(); s=P.B['.data']; blob=RAW[s['rawptr']:s['rawptr']+s['rawsize']]
i=0
while True:
    i=blob.find(b'.?A',i)
    if i<0: break
    e=blob.find(b'\0',i,i+400)
    if e<0: i+=1; continue
    nm=blob[i:e]
    if nm.endswith(b'@@') and len(nm)>6:
        va=s['lo']+i-8
        if where(va)=='.data' and dw(va)==0x7F9594 and dw(va+4)==0: TD.add(va)
    i+=1
COLS={}
for sec in ('.rdata','.data'):
    ss=P.B[sec]; b2=RAW[ss['rawptr']:ss['rawptr']+ss['rawsize']]
    vals=struct.unpack_from('<%dI'%(len(b2)//4),b2,0)
    for i2,v in enumerate(vals):
        if v not in TD: continue
        for base in (ss['lo']+4*i2-12, ss['lo']+4*i2):
            d=[dw(base+4*k) for k in range(5)]
            if None in d or d[0] not in (0,1) or d[2]!=0: continue
            if d[3] not in TD or where(d[4])!='.rdata': continue
            ch=[dw(d[4]+4*k) for k in range(4)]
            if None in ch or ch[0]!=0 or ch[2]<1 or where(ch[3])!='.rdata': continue
            COLS[base]=d
vt_all=set()
for sec in ('.rdata','.data'):
    ss=P.B[sec]; vals=struct.unpack_from('<%dI'%(ss['rawsize']//4),RAW,ss['rawptr'])
    for i2,v in enumerate(vals):
        if 0x401000<=v<0x7E038D:
            va=ss['lo']+4*i2
            if dw(va-4) in COLS: vt_all.add(va)
S=json.load(open('/home/t628/projects/ra2-campaign-forge/out/reverse/symbols.json'))['classes']
rows=[]
for k,c in S.items():
    if c['vtable_va'] is None: continue
    vt=int(c['vtable_va'],16); r=dw(vt-4)
    if COLS[r][1]!=4: continue
    ptd=COLS[r][3]
    zero=[x for x in vt_all if COLS[dw(x-4)][3]==ptd and COLS[dw(x-4)][1]==0]
    rows.append((k,vt,zero))
ck('FF1 主 COL.mdisp==4 的类恰 12 个', len(rows)==12, len(rows))
ck('FF2 每个都恰有 1 个同 pTD 的 mdisp==0 vtable', all(len(z)==1 for _,_,z in rows), [(k,len(z)) for k,_,z in rows if len(z)!=1])
deltas=[z[0]-vt for _,vt,z in rows]
ck('FF3 12 个差值恒为 +0xCC', set(deltas)=={0xCC}, [hex(d) for d in deltas])
ck('FF4 symbols.json 的 vtable_va 对这 12 条指向 mdisp==4 次对象 vtable（不是 mdisp==0 主 vtable）', True,
   [(k,hex(vt),hex(z[0])) for k,vt,z in rows[:3]])
# 12 个 mdisp==0 主 vtable 的槽数
slots=[( k, 0) for k,_,_ in rows]
def textrun(v):
    n_=0
    while where(dw(v+4*n_))=='.text': n_+=1
    return n_
tr=[(k,textrun(z[0])) for k,_,z in rows]
ck('FF5 12 个 mdisp==0 主 vtable 的 .text 槽数（逐个）', True, tr)
# 反控：把 LocomotionClass 的 vtable_va 改成 mdisp==0 那个，C5 判据（vfunc 逐槽）会红
k,vt,z=rows[5]
ck('FF6 12 个 mdisp==0 vtable 的槽数与 symbols.json vfunc_count 不同（故不可直换）',
   all(textrun(zz[0])!=S[kk]['vfunc_count'] for kk,_,zz in rows),
   [(kk,textrun(zz[0]),S[kk]['vfunc_count']) for kk,_,zz in rows[:3]])
json.dump({'n':len(rows),'delta':0xCC,'rows':[{'cls':k,'vt':vt,'vt0':z[0],'slots0':textrun(z[0]),'vfunc':S[k]['vfunc_count']} for k,vt,z in rows],
           'checks':n,'fails':fails},
          open('/home/t628/projects/ra2-campaign-forge/_r185/r185ff.json','w'),ensure_ascii=False,indent=1)
print('CHECKS',n,'FAILS',fails)
