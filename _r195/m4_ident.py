#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""""R195 第四刀：把两处字节实证接到身份上。
U1 0x4105A0 安装的 4 个 vtable 立即数 -> COL 记录 5 字段全量 + d3 修饰名 + mdisp。
U2 0x410260 里 4 个 GUID 常量（0x7F7C90/0x7F7C80/0x7F7C70/0x7E9AE0）的 16 字节身份，
   并全镜像检索相同 16 字节还有哪些位置（用于判断是否是 IID）。
U3 0x410260 的 4 个 GUID 与 4 个安装 vtable 的宿主类名是否一一对应（按表头比对）。
U4 0x410220 / 0x410450 / 0x410470 等实现的目标表归属（哪些表装了它）。
U5 全镜像检索 .?AUIRTTITypeInfo@@ 与 .?AVAbstractClass@@ 等修饰名的位置。
"""
import sys, re, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def row(va):
    ws=[P.dw(va+4*k) for k in range(5)]
    nm=P.cstr(ws[3]+8,200) if ws[3] is not None else None
    return dict(va=va,d0=ws[0],d1=ws[1],d2=ws[2],d3=ws[3],d4=ws[4],
        name=nm.decode('latin1') if nm else None)
print('== U1 0x4105A0 安装的 4 个 vtable ==')
for imm in (0x7E1F50,0x7E1F34,0x7E1F2C,0x7E1F24):
    colva=P.dw(imm-4); r=row(colva) if colva else {}
    print('   vt=%08X  COL=%08X  d0=%s d1=%s d2=%s d3=%08X d4=%08X  name=%s' %
          (imm,colva or 0,r.get('d0'),r.get('d1'),r.get('d2'),r.get('d3') or 0,r.get('d4') or 0,r.get('name')))
print('\n== U2 0x410260 的 4 个 GUID 常量 ==')
GU=[0x7F7C90,0x7F7C80,0x7F7C70,0x7E9AE0]
for g in GU:
    raw=P.RAW[P.r2o(g):P.r2o(g)+16]
    d1,d2,d3=struct.unpack_from('<IHH',raw,0)
    b=raw[8:]
    print('   %08X  %s  {%08X-%04X-%04X-%s-%s}' % (g,raw.hex(),d1,d2,d3,b[:2].hex(),b[2:].hex()))
    # 全镜像检索同 16 字节
    hits=[];i=0
    while True:
        i=P.RAW.find(raw,i)
        if i<0: break
        hits.append(hex(0x400000+ (i - (P.r2o(0x401000)-0x401000))))
        i+=1
    print('        同 16 字节出现 %d 次（文件偏移换算 VA）：%s' % (len(hits),hits[:8]))
print('\n== U3 修饰名全镜像检索 ==')
for s in (b'.?AVAbstractClass@@',b'.?AUIRTTITypeInfo@@',b'.?AVObjectClass@@',b'.?AVHouseTypeClass@@'):
    hits=[];i=0
    while True:
        i=P.RAW.find(s,i)
        if i<0: break
        hits.append(i); i+=1
    print('   %-24s 出现 %d 次  前 6 文件偏移 %s' % (s.decode(),len(hits),[hex(x) for x in hits[:6]]))
print('\nFAILS=%d'%len(fails))
