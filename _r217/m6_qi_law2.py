# -*- coding: utf-8 -*-
"""R217 m6：律V 诚实版 —— 修 m5 的空判据自错。
m5 自错：对 180/184 的视图，抽取器只拿到 {0}（因为 0 恒属于 mdset），判定必然 PASS => 空判据。
本脚本：(1) 先定位 ppv 输出寄存器（函数首条 mov R,[esp+0x?] 且随后被 mov [R],X 写入）；
        (2) 抽取所有 lea S,[基址+imm] 且其后 <=10 条出现 mov [ppv],S 的 imm；
        (3) 只对 非零偏移数 > 0 的视图计入律V 判定，并单列覆盖率；
        (4) 反控：把 ppv 寄存器判据破坏（改成 [ebx]）后，非零命中应塌到 0。
"""
import sys,struct,collections,json
sys.path.insert(0,'_r185'); import pe185 as P
from capstone import *
md=Cs(CS_ARCH_X86,CS_MODE_32)
t=P.B['.text']; TLO=t['lo']; THI=TLO+t['rawsize']; D=P.RAW[t['rawptr']:t['rawptr']+t['rawsize']]
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pTD=w[k+3],pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL); VT={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VT[base+4*k+4]=v
def slots(vt,cap=256):
    out=[]
    for i in range(cap):
        v=P.dw(vt+4*i)
        if not (TLO<=v<THI): break
        out.append(v)
    return out
SL={v:slots(v) for v in VT}
def body(va,cap=0x300):
    o=P.r2o(va)-t['rawptr']; blob=D[o:o+cap]
    for j in range(len(blob)-3):
        if blob[j:j+4] in (b'\x90\x90\x90\x90',b'\xcc\xcc\xcc\xcc'): blob=blob[:j]; break
    return list(md.disasm_lite(blob,va))
def analyze(va,broken=False):
    ins=body(va)
    if not ins: return None
    # ppv 寄存器：首 3 条内 mov R,[esp+imm]
    ppv=None
    for a,s,mn,ops in ins[:4]:
        if mn=='mov' and ops.endswith(']') and 'esp +' in ops:
            reg=ops.split(',')[0].strip()
            if reg in ('eax','ebx','ecx','edx','esi','edi','ebp'): ppv=reg; break
    if ppv is None: return None
    if broken: ppv='ebx_never'
    res=set()
    for k,(a,s,mn,ops) in enumerate(ins):
        if mn!='lea' or ',' not in ops: continue
        p=ops.split(',')
        if '+' not in p[1]: continue
        dst=p[0].strip()
        try: imm=int(p[1].split('+')[1].strip().rstrip(']'),16)
        except: continue
        for j in range(k+1,min(k+1+10,len(ins))):
            a2,s2,mn2,ops2=ins[j]
            if mn2=='mov' and ops2.startswith('dword ptr [%s],'%ppv) and ops2.split(',')[-1].strip()==dst:
                res.add(imm); break
    return ppv,res
FAM=collections.defaultdict(list)
for v,col in VT.items(): FAM[COL[col]['pCHD']].append(v)
GLOBAL_MD={COL[c]['md_'] for c in COL}
rows=[];nq=0;nz=0;ok=bad=0;badr=[]
for fam,vs in sorted(FAM.items()):
    mdset={COL[VT[v]]['md_'] for v in vs}
    for v in sorted(vs):
        s=SL[v]
        if not s: continue
        o=P.r2o(s[0])-t['rawptr']
        if b'\xf3\xa7' not in D[o:o+0x200]: continue
        r=analyze(s[0])
        if not r: continue
        ppv,offs=r; nq+=1
        vals=offs|{0}
        extra=vals-mdset
        row=dict(vt=hex(v),cls=COL[VT[v]]['name'],qifn=hex(s[0]),ppv=ppv,md=COL[VT[v]]['md_'],mdset=sorted(mdset),offs=sorted(hex(x) for x in vals),extra=sorted(hex(x) for x in extra))
        if offs: nz+=1
        if extra: bad+=1; badr.append(row)
        else: ok+=1
        rows.append(row)
print('[律V-诚实] QI 视图=%d  其中抽出非零偏移=%d  成立=%d 违例=%d'%(nq,nz,ok,bad))
print('[覆盖率告警] 若只看非零偏移视图：判定数=%d'%nz)
for b in badr[:15]: print('   VIOL',b['cls'],'md',b['md'],'mdset',b['mdset'],'offs',b['offs'],'extra',b['extra'])
print('[非零偏移视图明细]')
seen=set()
for r in rows:
    if r['offs'] and r['offs']!=['0x0'] and r['qifn'] not in seen:
        seen.add(r['qifn']); print('   %s %-40s offs=%s mdset=%s'%(r['qifn'],r['cls'],r['offs'],r['mdset']))
# 反控
nb=0;nbz=0
for fam,vs in sorted(FAM.items()):
    for v in sorted(vs):
        s=SL[v]
        if not s: continue
        o=P.r2o(s[0])-t['rawptr']
        if b'\xf3\xa7' not in D[o:o+0x200]: continue
        r=analyze(s[0],broken=True)
        if r and r[1]: nbz+=1
print('[反控] 破坏 ppv 寄存器判据后 抽出非零偏移的视图数=%d（应=0）'%nbz)
json.dump(dict(nq=nq,nz=nz,ok=ok,bad=bad,badrows=badr[:20],trivial=nq-nz),open('_r217/m6.json','w'),indent=1)
