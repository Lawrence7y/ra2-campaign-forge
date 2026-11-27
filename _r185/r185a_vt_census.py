#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R185 A：vtable 结构 census —— 在 .rdata 里机械复原「候选虚表」全集，并与 class_ids.txt 交叉。

判据（可失败）：
 J1 每个候选虚表 = 连续 k>=4 个 dword 全部落在 .text 且各值 %4==0，紧接一个 dword == 0
 J2 候选全集地址唯一、按 VA 严格递增
 J3 class_ids.txt 里每个 0x007Exxxx 的 vtable VA 都必须被 J1 扫描**命中**（覆盖率）
 J4 命中集里非 class_ids 的条目数 = 附注（不判红）
 J5 AbstractClass(0x7E1F50) 槽数 == 28 且 28 个槽全在 .text（逐值列出）
反控：
 N1 把 .text 上界改小 0x100000 ⇒ J3 覆盖率塌（真红）
 N2 把最小 run 长度改成 200 ⇒ 候选数归 0（真红）
 N3 在副本里把 0x7E1F50 槽[3] 改成 0x1000（非 .text）⇒ J5 红
 N4 副本槽[28] 之后填非 0 ⇒ J1 对 0x7E1F50 红（终止符维）
"""
import struct, sys, os, json
ROOT='/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
pe=struct.unpack_from('<I',raw,0x3c)[0]
nsec=struct.unpack_from('<H',raw,pe+6)[0]; optsz=struct.unpack_from('<H',raw,pe+20)[0]
opt=pe+24; IB=struct.unpack_from('<I',raw,opt+28)[0]
secs=[]
for i in range(nsec):
    o=opt+optsz+40*i
    nm=raw[o:o+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',raw,o+8)
    secs.append((nm,va,vs,ra,rs))
S={s[0]:s for s in secs}
TEXT_LO=IB+S['.text'][1]; TEXT_END=TEXT_LO+S['.text'][4]
RD_LO=IB+S['.rdata'][1]; RD_END=RD_LO+S['.rdata'][4]
def r2o(va):
    rva=va-IB
    for nm,v,vs,ra,rs in secs:
        if v<=rva<v+rs: return ra+(rva-v)
    return None
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))

MINRUN=4
MINTXT=TEXT_LO; MAXTXT=TEXT_END
def scan(buf, lo_va, n_dw, minrun=MINRUN, tlo=None, thi=None):
    tlo = TEXT_LO if tlo is None else tlo
    thi = TEXT_END if thi is None else thi
    vals = struct.unpack_from('<%dI'%n_dw, buf, 0)
    cands=[]
    i=0
    while i < n_dw:
        v=vals[i]
        if tlo <= v < thi and v % 4 == 0:
            j=i
            while j<n_dw and tlo <= vals[j] < thi and vals[j] % 4 == 0:
                j+=1
            k=j-i
            if k>=minrun and j<n_dw and vals[j]==0:
                cands.append((lo_va+4*i, k))
            i=j
        else:
            i+=1
    return cands, vals

off=r2o(RD_LO); ndw=S['.rdata'][4]//4
cands, rvals = scan(raw[off:off+ndw*4], RD_LO, ndw)
ck('A1 .text 范围', (TEXT_LO,TEXT_END)==(0x401000,0x7E038D), (hex(TEXT_LO),hex(TEXT_END)))
ck('A2 .rdata 范围', (RD_LO,RD_END)==(0x7E1000,0x80A000), (hex(RD_LO),hex(RD_END)))
addrs=[c[0] for c in cands]
ck('A3 J2 候选地址唯一且严格递增', addrs==sorted(set(addrs)), len(addrs))
ck('A4 候选数 >= 800', len(cands)>=800, len(cands))

# class_ids.txt 交叉
ci=open('re_atlas/evidence/class_ids.txt',encoding='utf-8',errors='replace').read().splitlines()
vts=[]
for ln in ci:
    m=None
    import re
    m=re.match(r'^0x[0-9A-Fa-f]{2}\s+\d+\s+(\S+)\s+(0x[0-9A-Fa-f]{8})\s',ln)
    if m: vts.append((m.group(1), int(m.group(2),16)))
ck('A5 class_ids 行数', len(vts)>0, len(vts))
cset=set(addrs)
hit=[(n,v) for n,v in vts if v in cset]
miss=[(n,v) for n,v in vts if v not in cset]
ck('A6 J3 覆盖率 100%', len(miss)==0, 'hit=%d miss=%d %s'%(len(hit),len(miss),[ (n,hex(v)) for n,v in miss[:5]]))
print('NOTE 非 class_ids 的候选数 =', len(cset - set(v for _,v in vts)))
print('NOTE class_ids 条目数 =', len(vts), ' 候选总数 =', len(addrs))

# AbstractClass vtable 逐槽
VT=0x7E1F50; vo=r2o(VT)
slots=[]
for i in range(64):
    v=struct.unpack_from('<I',raw,vo+4*i)[0]
    if v==0: break
    slots.append(v)
ck('A7 J5 槽数 28', len(slots)==28, len(slots))
bad=[(i,hex(v)) for i,v in enumerate(slots) if not (TEXT_LO<=v<TEXT_END and v%4==0)]
ck('A8 J5 28 槽全在 .text', not bad, bad[:5])
term=struct.unpack_from('<I',raw,vo+4*len(slots))[0]
ck('A9 终止符 dword == 0', term==0, hex(term))
prev=struct.unpack_from('<I',raw,vo-4)[0]
print('NOTE VT 前一 dword =',hex(prev),' 是否 .text 指针 =', TEXT_LO<=prev<TEXT_END)

json.dump({'cands':cands,'vts':vts,'slots':slots,'fails':fails},open('_r185/r185a.json','w'))
print('FAILS',fails)
