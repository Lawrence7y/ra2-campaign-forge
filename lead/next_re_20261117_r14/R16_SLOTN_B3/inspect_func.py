# -*- coding: utf-8 -*-
"""R16_SLOTN_B3 只读：为选定装表点求宿主函数体（atlas 命中 or capstone 定界）。"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe
import capstone
sys.dont_write_bytecode = True
EXE = os.path.join(os.path.dirname(os.path.dirname(R14)), 'ra2youli', 'gamemd.exe')
img = probe.Image(EXE)
atlas = probe.load_atlas_sizes()
ranges = probe.body_ranges(atlas)

chosen = {
 '005B3060':'005B2DE9',   # MissionClass
 '005B3570':'00517D9D',   # InfantryClass fix
 '005B35E0':'00521A11',   # InfantryClass fix
 '005B3650':'005B2DE9',   # MissionClass
 '005B36B0':'005B2DE9',   # MissionClass
 '005B4630':'005B3C52',   # MixFileClass
 '00653100':'00652B45',   # RadarClass
 '0065CBF0':'0065CA03',   # RawFileClass
 '006B1850':'006AF13D',   # SlaveMgr
 '006B1900':'006AF13D',   # SlaveMgr
 '006B8660':'006B6C2D',   # SpawnMgr
 '006B8710':'006B6C2D',   # SpawnMgr
 '006F9E50':'006F3130',   # TechnoClass
}
def capstone_body(site):
    s=int(site,16)
    lo=s-0x80; hi=s+0x80
    code=bytes(img.buf[lo-img.base:hi-img.base])
    md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail=True; md.skipdata=True
    insns=list(md.disasm(code,lo))
    start=None; end=None
    prev_start=None
    cands=[]
    for ins in insns:
        if ins.address<=s and ins.mnemonic in ('push','sub','xor','mov'):
            cands.append(ins.address)
    if cands:
        start=cands[-1]
    for ins in insns:
        if ins.address>s and ins.mnemonic in ('ret','retf'):
            end=ins.address; break
    return start,end

for e,site in chosen.items():
    sv=int(site,16)
    wb=probe.which_body(ranges,sv)
    st,en=capstone_body(site)
    print(e, 'site',site, 'which_body', ('%08X'%wb if wb else None),
          'cap_near_start', ('%08X'%st if st else None), 'cap_ret', ('%08X'%en if en else None))
