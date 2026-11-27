#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 H：vtable -> RTTI COL -> TypeDescriptor 的字节链机械复原（69 个职业/类型类 vtable 全覆盖）。

命题（可失败）：
  P1  每个 class vtable 的 **前一个 dword** 是一个 .rdata 指针，指向一个合法 MSVC COL:
       {sig in (0,1), offset==0, cdOffset==0, pTD in .data, pCHD in .rdata}
  P2  TD 在 pTD: {pVFTable == 0x7F9594, spare == 0, name 以 b'.?AV' 开头, 以 b'@@' 结束}
  P3  TD 名字里的类名 == class_ids.txt 的 class 列（逐条）
  P4  pCHD 指向 CHD {sig, attr, numBase, pBaseArray}，pBaseArray 指向 COL 指针数组，
      其中至少有一个元素 == 本 vtable 的 COL（自指闭合）
  P5  引擎名映射：class 名去掉 Class 后缀 == class_ids.txt 的 engine name 列（69 条里能对上的计数）
反控（真红）：
  N1 COL.sig 改 2 => P1 红
  N2 TD 名字改一个字节 => P3 红
  N3 vtable 指针 +4（错位）=> P1 红
"""
import struct,os,re,json,sys
ROOT='/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
IB=0x400000
SEC={'text':(0x401000,0x7E038D),'rdata':(0x7E1000,0x811074),'data':(0x812000,0x849BE4)}
def r2o(va):
    if 0x401000<=va<0x7E038D: return 0x1000-0x401000+va
    if 0x7E1000<=va<0x811074: return 0x3E1000-0x7E1000+va
    if 0x812000<=va<0x849BE4: return 0x412000-0x812000+va
    return None
def where(v):
    for k,(a,b) in SEC.items():
        if a<=v<b: return k
    return 'other'
def dw(va):
    o=r2o(va)
    return None if o is None else struct.unpack_from('<I',raw,o)[0]
def rd(va,n):
    o=r2o(va)
    return None if o is None else struct.unpack_from('<%dI'%n,raw,o)
def cstr(va,maxlen=256):
    o=r2o(va)
    if o is None: return None
    e=raw.find(b'\0',o,o+maxlen)
    return raw[o:e] if e>=0 else None

fails=[]; n=0
def ck(nm,cond,detail=''):
    global n; n+=1
    if not cond: fails.append(nm)
    print(('PASS ' if cond else 'FAIL ')+nm+((' | '+str(detail)) if detail!='' else ''))

# ---- 读 class_ids ----
rows=[]
for ln in open('re_atlas/evidence/class_ids.txt',encoding='utf-8',errors='replace'):
    m=re.match(r'^(0x[0-9A-Fa-f]{2})\s+(\d+)\s+(\S+)\s+(0x[0-9A-Fa-f]{8})\s+(.*)$',ln.rstrip('\n'))
    if m: rows.append({'id':int(m.group(1),16),'size':int(m.group(2)),'cls':m.group(3),'vt':int(m.group(4),16),'eng':m.group(5).strip()})
ck('H1 class_ids 解析出 69 条', len(rows)==69, len(rows))

def parse_col(colva):
    d=rd(colva,5)
    if d is None: return None
    sig,off,cd,ptd,pchd=d
    return {'va':colva,'sig':sig,'off':off,'cd':cd,'ptd':ptd,'pchd':pchd}
def parse_td(tdva):
    d=rd(tdva,2)
    if d is None: return None
    nm=cstr(tdva+8)
    return {'va':tdva,'pvf':d[0],'spare':d[1],'name':nm}

res=[]; p1=0; p2=0; p3=0; p4=0; p5=0; det_p1=[]; det_p2=[]; det_p3=[]; det_p4=[]
for r in rows:
    vt=r['vt']; pre=dw(vt-4)
    col=parse_col(pre) if pre is not None and where(pre)=='rdata' else None
    ok1 = bool(col) and col['sig'] in (0,1) and col['off']==0 and col['cd']==0 and where(col['ptd'])=='data' and where(col['pchd'])=='rdata'
    td=parse_td(col['ptd']) if (col and ok1) else None
    ok2 = bool(td) and td['pvf']==0x7F9594 and td['spare']==0 and td['name'].startswith(b'.?AV') and td['name'].endswith(b'@@')
    name_cls=None; ok3=False; name_eng=None
    if ok2:
        s=td['name'][4:-2].decode('latin1')
        name_cls=s
        ok3 = (s==r['cls'])
        if not ok3: det_p3.append((r['cls'],s))
        base=s[:-5] if s.endswith('Class') else s
        name_eng=base
        ok5 = (base==r['eng'] or base==r['eng'].replace(' ',''))
        if not ok5: det_p5=getattr(sys,'_x',None)
    # P4 CHD chain
    ok4=False
    if col:
        chd=rd(col['pchd'],4)
        if chd and chd[0] in (0,1) and chd[2]>=1 and where(chd[3])=='rdata':
            arr=rd(chd[3],chd[2])
            if arr and col['va'] in arr: ok4=True
    if not ok1: det_p1.append((r['cls'],hex(vt),hex(pre) if pre is not None else None,where(pre)))
    if ok1 and not ok2: det_p2.append((r['cls'],hex(pre)))
    if not ok4: det_p4.append((r['cls'],hex(vt),hex(col['pchd']) if col else None))
    p1+=ok1; p2+=ok2; p3+=ok3; p4+=ok4
    res.append({'cls':r['cls'],'id':r['id'],'size':r['size'],'vt':vt,'col':col,'td_name':td['name'].decode('latin1') if td and td['name'] else None,'ok':[ok1,ok2,ok3,ok4]})
ck('H2 P1 COL 链 69/69', p1==69, 'p1=%d bad=%s'%(p1,det_p1[:4]))
ck('H3 P2 TD 链在 P1 通过者上全通过', p2==p1, 'p2=%d bad=%s'%(p2,det_p2[:4]))
ck('H4 P3 TD 名 == class 列 69/69', p3==69, 'p3=%d bad=%s'%(p3,det_p3[:4]))
ck('H5 P4 CHD 自指闭合', p4==69, 'p4=%d bad=%s'%(p4,det_p4[:4]))
# P5 引擎名
p5=sum(1 for x in res if x['td_name'] and x['td_name'][4:-2].replace('Class','')== next((r['eng'] for r in rows if r['cls']==x['cls']),''))
ck('H6 P5 引擎名 == 去 Class 后缀', p5==69, p5)

# ---- 反控 ----
import shutil
buf=bytearray(raw)
def ctl(label, mutate, expect):
    b=bytearray(raw); mutate(b)
    # 用同一解析器对 buf 重新算（替换全局 raw）
    global raw_
    return b
# 直接在字节层面验证：把副本写到 /tmp 并重跑解析（只用一次性函数，避免递归）
def run_with(mutate):
    b=bytearray(raw); mutate(b)
    o=r2o(0x7E1F4C)
    orig=raw
    globals()['raw']=bytes(b)
    try:
        pre=dw(0x7E1F50-4); col=parse_col(pre) if pre and where(pre)=='rdata' else None
        ok1=bool(col) and col['sig'] in (0,1) and col['off']==0 and col['cd']==0
        ok3=False; nm=None
        if col and ok1:
            td=parse_td(col['ptd'])
            if td and td['name']: nm=td['name'].decode('latin1'); ok3=(nm=='AbstractClass')
        return ok1, ok3, nm
    finally:
        globals()['raw']=orig
# N1: COL.sig 改 2
b=bytearray(raw); struct.pack_into('<I',b,r2o(0x7FB118),2)
o1,o3,o5=run_with(lambda bb: struct.pack_into('<I',bb,r2o(0x7FB118),2))
ck('H7 反控 N1 COL.sig=2 => P1 红', o1 is False, (o1,o5))
# N2: TD 名字改一个字节
def m2(bb):
    o=r2o(0x8177C8)+8+4  # 'AbstractClass' 的第 4 字节
    bb[o]=bb[o]^0x01
o1,o3,o5=run_with(m2)
ck('H8 反控 N2 TD 名改 1 字节 => P3 红', o3 is False, (o1,o5))
# N3: vtable 指针 +4（用 0x7E1F54 当 vtable）
def m3(bb): pass
globals()['raw']=bytes(raw)
pre=dw(0x7E1F54-4); c=parse_col(pre) if pre and where(pre)=='rdata' else None
globals()['raw']=bytes(raw)
ck('H9 反控 N3 vtable+4 => dword@-4 不再是 .rdata COL 指针', (pre is None) or where(pre)!='rdata' or not (c and c['sig'] in (0,1) and c['off']==0), (hex(pre) if pre else None, where(pre) if pre else None))

# ---- 附：AbstractClass 真实槽数（末尾 3 个 RDATA + 1 个 thunk 属于紧随的单槽接口 vtable）----
vt=0x7E1F50
slots=[dw(vt+4*i) for i in range(40)]
k=next(i for i,v in enumerate(slots) if where(v)!='text')
ck('H10 AbstractClass 首个非 .text 槽索引 == 24', k==24, k)
seq=[(hex(vt+4*i),hex(slots[i]),where(slots[i])) for i in range(23,29)]
print('NOTE AbstractClass 槽 23..28:',seq)
# 后随单槽接口 vtable：COL 在 vtable-4
iface=[]
for cva in (slots[24], slots[26]):
    tva=cva+4
    td=parse_td(dw(dw(cva+12)))
    iface.append((hex(cva),hex(tva),hex(dw(tva)),td['name'].decode('latin1') if td and td['name'] else None))
print('NOTE 后随单槽 vtable:',iface)
ck('H11 两个后随接口 vtable 各 1 槽且同指 0x4C9150', all(x[2]=='0x4c9150' for x in iface) and len(iface)==2, iface)

out={'p1':p1,'p2':p2,'p3':p3,'p4':p4,'p5':p5,'rows':res,'fail':fails,'checks':n,'iface':iface}
json.dump(out,open('_r185/r185h.json','w'),ensure_ascii=False,indent=1)
print('CHECKS',n,'FAILS',fails)
