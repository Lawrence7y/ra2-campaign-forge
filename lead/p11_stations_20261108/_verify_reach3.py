# -*- coding: utf-8 -*-
# 修正版：所有条件/无条件跳转（含 jne/je/ja/jbe...）都算「函数内可达边」
import struct, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_GRP_JUMP
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
d=open(EXE,'rb').read()
def off(va): return va-0x400000
def u32(va): return struct.unpack_from('<I',d,off(va))[0]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True

# 站点 -> 声称宿主；检查「宿主起点」与「站点」之间的每个 ret 之后段起点，是否被宿主内的跳转到达
regions=[
    ('Aircraft v138',0x414A80,0x414B70,[0x414B24,0x414B64]),
    ('MISSION_MOVE',0x416D50,0x4174A0,[0x417481]),
    ('Foot v151',0x4D4280,0x4D4B04,[0x4D4314,0x4D4686,0x4D49A3]),
    ('Foot v132',0x4D4DC0,0x4D4F60,[0x4D4E3E]),
    ('v150',0x4DDF90,0x4DE0C0,[0x4DE056]),
    ('Infantry v266',0x51F330,0x51F3E0,[0x51F382]),
]

def jump_targets(lo,hi):
    """返回 (直接跳转目标集合, 跳表基址列表)，只统计 lo..hi 内的指令"""
    ds=set(); tbs=[]
    for ins in md.disasm(d[off(lo):off(hi)],lo):
        if ins.address>hi: break
        if CS_GRP_JUMP in ins.groups:
            # 直接跳转
            try:
                t=int(ins.op_str,16)
                if 0x401000<=t<0x7E0000: ds.add(t)
            except: pass
            # 间接跳表 [reg*4+disp]
            if '*4' in ins.op_str and 'ptr [' in ins.op_str:
                m=re.search(r'\+\s*(0x[0-9a-f]+)\]',ins.op_str)
                if m:
                    tb=int(m.group(1),16)
                    if 0x401000<=tb<0x7E0000: tbs.append((ins.address,tb))
    return ds,tbs

print('=== 修正版：ret 后段起点是否为宿主体内跳转目标 ===')
for tag,host,hi,sites in regions:
    ds,tbs=jump_targets(host,hi)
    # 收集 host..max(site) 内的 ret 及后继段起点
    segs=[]
    for ins in md.disasm(d[off(host):off(max(sites)+1)],host):
        if ins.address>max(sites): break
        if ins.mnemonic in ('ret','retf'):
            segs.append(ins.address+ins.size)
    tblvals=set()
    for a,tb in tbs:
        for i in range(80):
            v=u32(tb+4*i)
            if not (0x401000<=v<0x7E0000): break
            tblvals.add(v)
    print('\n[%s] host=0x%X direct-jump targets=%d tables=%d'%(tag,host,len(ds),len(tbs)))
    for s in segs:
        print('   ret 后段 0x%X : direct=%s in_table=%s'%(s, s in ds, s in tblvals))
    print('   stations:',[(hex(s), 'in-host-range' if host<=s<=hi else 'OUT') for s in sites])

print('\n=== 0x414A80 全函数反汇编（含 jne 0x414AE5）===')
for ins in md.disasm(d[off(0x414A80):off(0x414AE8)],0x414A80):
    print('  %08x %-6s %s'%(ins.address,ins.mnemonic,ins.op_str))

print('\nDONE')
