# -*- coding: utf-8 -*-
"""R212 d1：诊断 —— BCA 元素到底是什么、为何解析失败。
一次输出：5 个 sink + HouseClass 的 CHD 原始 16B、NB/pBCA、每个 BCA 元素的原始 6 dword、
以及按「任意偏移」尝试识别的名字，用于修正 COL 判据。
"""
import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def d6(a):
    return [P.dw(a+4*k) for k in range(6)]
TARGET={'NetUtilCCom':0x80e680,'ChatCCom':0x80e740,'CNetUtilEventSink':0x80e780,
        'CChatEventSink':0x80e7c0,'DownloadCCom':0x80e998}
for k,a in TARGET.items():
    print('='*100); print('%s  CHD=%s'%(k,hex(a)))
    print('  CHD 16B: %s'%[hex(x) if x else 0 for x in [P.dw(a+4*i) for i in range(4)]])
    nb=P.dw(a+8); pb=P.dw(a+12)
    print('  NB=%s pBCA=%s sec(pBCA)=%s'%(nb,hex(pb) if pb else pb,P.where(pb) if pb else None))
    if not pb or not nb: continue
    for j in range(nb):
        e=P.dw(pb+4*j)
        print('   [%d] elem=%s sec=%s  6dw=%s'%(j,hex(e),P.where(e),[hex(x) if x else 0 for x in d6(e)]))
        # 尝试：哪个 dword 指向可读字符串
        for off in range(6):
            v=P.dw(e+4*off)
            if not v: continue
            for delta in (8,-8,0,12,-12,16):
                c=P.cstr(v+delta,120)
                if c and (c.startswith(b'.?A') or c.startswith(b'.?AV') or c.startswith(b'.?AU')):
                    print('        +%d -> pTD?%s%s => %s'%(off*4,'+%d'%delta if delta else '',hex(v),c.decode('latin1')))
                    break
print('='*100)
# HouseClass
import json
d3=json.load(open('_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
for v in MD:
    if NM.get(v,'').startswith('.?AVHouseClass'):
        print('HouseClass COL=%s mdisp=%d pCHD=%s'%(hex(v),MD[v],hex(P.dw(v+16))))
        a=P.dw(v+16)
        print('  CHD 16B: %s'%[hex(x) if x else 0 for x in [P.dw(a+4*i) for i in range(4)]])
        nb=P.dw(a+8); pb=P.dw(a+12)
        print('  NB=%s pBCA=%s'%(nb,hex(pb) if pb else pb))
        for j in range(nb):
            e=P.dw(pb+4*j)
            print('   [%d] elem=%s sec=%s 6dw=%s'%(j,hex(e),P.where(e),[hex(x) if x else 0 for x in d6(e)]))
        break
