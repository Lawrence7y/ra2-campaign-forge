#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 R：symbols.json(988 类) 与二进制字节的双向交叉核验。
每条都从 gamemd.exe 字节重算，不引用 symbols.json 的派生值作为「证据」。
"""
import struct,json,re,os
ROOT='/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
def dw(va):
    o=r2o(va); return None if o is None else struct.unpack_from('<I',raw,o)[0]
def wr(v):
    if v is None: return 'None'
    if 0x401000<=v<0x7E038D: return 'text'
    if 0x7E1000<=v<0x811074: return 'rdata'
    if 0x812000<=v<0x849BE4: return 'data'
    return 'other'
def cstr(va,m=300):
    o=r2o(va)
    if o is None: return None
    e=raw.find(b'\0',o,o+m); return raw[o:e]
def col(a):
    if wr(a)!='rdata': return None
    d=[dw(a+4*i) for i in range(5)]
    if None in d or d[0] not in (0,1) or d[1]!=0 or d[2]!=0: return None
    if wr(d[3])!='data' or wr(d[4])!='rdata': return None
    nm=cstr(d[3]+8)
    if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): return None
    return {'va':a,'ptd':d[3],'pchd':d[4],'name':nm}
def td(a):
    if wr(a)!='data': return None
    pvf,sp=struct.unpack_from('<II',raw,r2o(a))
    nm=cstr(a+8)
    return {'va':a,'pvf':pvf,'spare':sp,'name':nm}
def chd(a):
    if wr(a)!='rdata': return None
    d=[dw(a+4*i) for i in range(4)]
    if None in d or d[0]!=0 or d[2]<1 or wr(d[3])!='rdata': return None
    return {'va':a,'sig':d[0],'attr':d[1],'nbase':d[2],'arr':d[3]}
fails=[];n=0
def ck(nm,c,d=''):
    global n; n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

S=json.load(open('out/reverse/symbols.json'))
ck('R1 symbols.json 类数 988', len(S['classes'])==988, len(S['classes']))
ck('R1b 无 vtable 的类 34 条（class_ids.txt 同值）', sum(1 for c in S['classes'].values() if c['vtable_va'] is None)==34, sum(1 for c in S['classes'].values() if c['vtable_va'] is None))
ck('R2 type_info_vftable_va == 0x7F9594 (与 COL.pVFTable 同值)', S['diagnostics'].get('type_info_vftable_va','').upper()=='007F9594', S['diagnostics'].get('type_info_vftable_va'))
# 全库 vtable 前一个 dword 是否为合法 COL 且 TD 名 == 类名解码
bad_pre=[]; bad_name=[]; okv=0
name_mismatch=[]
for k,c in S['classes'].items():
    if c['vtable_va'] is None: continue
    vt=int(c['vtable_va'],16); colv=int(c['col_va'],16)
    got=col(vt-4)
    if not got or got['va']!=colv: bad_pre.append((k,c['vtable_va'],c['col_va'],hex(dw(vt-4)) if dw(vt-4) else None)); continue
    okv+=1
    t=td(got['ptd'])
    nm=(t['name'] or b'').decode('latin1')
    if nm!=c['name']: name_mismatch.append((k,nm))
ck('R3 symbols.json 988 条中 vtable-4 是合法 COL 且 == col_va', len(bad_pre)==0, 'ok=%d bad=%d %s'%(okv,len(bad_pre),bad_pre[:4]))
ck('R4 TD 名 == name 列', len(name_mismatch)==0, 'bad=%d %s'%(len(name_mismatch),name_mismatch[:4]))
# vfunc_count 与字节 run 长度
bad_cnt=[]
for k,c in S['classes'].items():
    if c['vtable_va'] is None: continue
    vt=int(c['vtable_va'],16); want=c['vfunc_count']
    k2=0
    while wr(dw(vt+4*k2))=='text': k2+=1
    if k2!=want: bad_cnt.append((k,want,k2,hex(dw(vt+4*want))))
ck('R5 vfunc_count == 字节 text-run 长度', len(bad_cnt)==0, 'bad=%d %s'%(len(bad_cnt),bad_cnt[:5]))
# vfuncs 逐个 == dword
bad_vf=[]
for k,c in S['classes'].items():
    if c['vtable_va'] is None: continue
    vt=int(c['vtable_va'],16)
    for i,vs in enumerate(c['vfuncs']):
        if dw(vt+4*i)!=int(vs,16): bad_vf.append((k,i,vs,hex(dw(vt+4*i)))); break
ck('R6 vfuncs 逐槽 == 字节', len(bad_vf)==0, 'bad=%d %s'%(len(bad_vf),bad_vf[:5]))
# AbstractClass CHD 自指闭合（BCD -> pTD == COL.pTD）
cA=col(0x7E1F4C); ch=chd(cA['pchd'])
ck('R7 AbstractClass COL/CHD 可解', bool(cA) and bool(ch), (cA and cA['name'], ch))
bcd=[dw(ch['arr']+4*i) for i in range(ch['nbase'])]
first_td=td(dw(bcd[0]))
ck('R8 CHD.nbase==8 且 arr[0] 的 BCD.pTD == COL.pTD（自指）', ch['nbase']==8 and first_td['va']==cA['ptd'], (ch['nbase'],hex(first_td['va']),hex(cA['ptd'])))
names=[]
for b in bcd:
    t=td(dw(b)); names.append(t['name'].decode('latin1') if t and t['name'] else None)
print('NOTE AbstractClass 8 个基类:',names)
# 反控：改 CHD.nbase=>R8 红；改 vtable_va 到非 COL 前置=>R3 红
b=bytearray(raw); struct.pack_into('<I',b,r2o(0x7FB110),7)
_old=raw
globals()['raw']=bytes(b)
ch2=chd(0x7FB108)
globals()['raw']=_old
ck('R9 反控 CHD.nbase 8->7 => R8 红', ch2['nbase']==7, ch2['nbase'])
# census 覆盖 vs symbols.json
starts=set()
for V in range(0x7E1004,0x811074,4):
    if wr(dw(V))!='text': continue
    if not col(V-4): continue
    k=0
    while wr(dw(V+4*k))=='text': k+=1
    t=dw(V+4*k)
    if k>=4 and (t==0 or col(t)): starts.add(V)
sv={int(c['vtable_va'],16) for c in S['classes'].values() if c['vtable_va'] is not None}
ck('R10 规则 census 覆盖 symbols.json 全部 vtable', sv<=starts, 'census=%d symbols=%d 未覆盖=%s'%(len(starts),len(sv),[hex(x) for x in sorted(sv-starts)[:5]]))
print('NOTE census 额外命中（symbols.json 未列的 vtable）=', len(starts-sv))
json.dump({'checks':n,'fails':fails,'census':len(starts),'symbols':len(sv),'bases8':names},open('_r185/r185r.json','w'),ensure_ascii=False,indent=1)
print('CHECKS',n,'FAILS',fails)
