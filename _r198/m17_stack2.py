#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第十七刀：18 个「栈」归属补一跳确认。
 T1 对每个 CRC 调用点，取其所在函数 H（0x90 填充定界）。
 T2 找 H 的所有直接调用点，在调用点前 24 字节内找 lea reg,[esp+K]，即「调用者为 H 准备栈缓冲」。
 T3 统计命中数、给出 lea 地址与偏移；未命中的列出来。
反控：窗口 24 -> 64。
"""
import sys,struct,collections,json,bisect
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
def in_text(x): return x is not None and LO<=x<HI
J=json.load(open('/home/t628/projects/ra2-campaign-forge/_r198/m16_selfcheck.json'))
SITES=[int(r['crc_call'],16) for r in J['rows']]
ck('T0a 待确认站点数', len(SITES)==18, len(SITES))
def fstart(va):
    p=va-LO;q=p
    while q>16:
        if (BUF[q-1]==0x90 and BUF[q-2]==0x90) or (BUF[q-1]==0xCC and BUF[q-2]==0xCC): return LO+q
        q-=1
    return None
CALLAT=[];CALLTGT=set()
pos=0
while pos<len(BUF):
    for off,sz,mn,op in md.disasm_lite(BUF[pos:pos+65536],LO+pos):
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t)); CALLTGT.add(t)
    pos+=65536
CALLERS=collections.defaultdict(list)
for c,t in CALLAT: CALLERS[t].append(c)
SORT=sorted(CALLTGT)
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
out=[]
for s in SITES:
    h=host_of(s) or fstart(s)
    ups=CALLERS.get(h,[])
    hits=[];hits64=[]
    for u in ups:
        for a,sz,mn,op in md.disasm_lite(BUF[max(LO,u-24)-LO:u-LO],max(LO,u-24)):
            if mn=='lea' and 'esp' in op: hits.append((hex(a),op,hex(u)))
        for a,sz,mn,op in md.disasm_lite(BUF[max(LO,u-64)-LO:u-LO],max(LO,u-64)):
            if mn=='lea' and 'esp' in op: hits64.append((hex(a),op,hex(u)))
    out.append(dict(site=hex(s),host=hex(h),ncallers=len(ups),hit24=hits[:3],hit64=hits64[:3]))
ck('T2a 有调用者的站点数', True, sum(1 for r in out if r['ncallers']>0))
ck('T2b 24B 窗口命中 lea[esp] 的站点数', True, sum(1 for r in out if r['hit24']))
ck('R1a 64B 窗口命中数', True, sum(1 for r in out if r['hit64']))
for r in out: print('   T3 %-10s host=%-10s callers=%d  hit24=%s'%(r['site'],r['host'],r['ncallers'],r['hit24'][:1]))
json.dump(dict(rows=out,hit24=sum(1 for r in out if r['hit24']),hit64=sum(1 for r in out if r['hit64']),
  asserts=N,fails=fails),open('/home/t628/projects/ra2-campaign-forge/_r198/m17_stack2.json','w'),
  ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
