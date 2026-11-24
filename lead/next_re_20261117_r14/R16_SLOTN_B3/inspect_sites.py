# -*- coding: utf-8 -*-
"""R16_SLOTN_B3 只读：对每个候选 vt 列 install sites 并解码 imm32；判类一致。"""
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
ts = probe.TextScan(img)

def decode_imm(site_hex):
    s = int(site_hex, 16)
    code = bytes(img.buf[s-img.base:s-img.base+12])
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    ins = next(md.disasm(code, s))
    imm = None
    if ins.mnemonic == 'mov' and len(ins.operands) == 2 and ins.operands[1].type == capstone.x86.X86_OP_IMM:
        imm = ins.operands[1].imm & 0xFFFFFFFF
    return ins.mnemonic + ' ' + ins.op_str, ('%08X'%imm if imm is not None else None)

# 关注的候选 vt
targets = {
 'MissionClass':'007EDCC0','RadioClass':'007F0508',
 'InfantryClass':'007EB058','BuildingClass':'007E3EBC',
 'MixFileClass':'007EDF50','RadarClass':'007F0344','RawFileClass':'007F0904',
 'SlaveMgr':'007F315C','SpawnMgr':'007F35E4','TechnoClass':'007F4960',
}
for nm, vt in targets.items():
    sites = ts.installs_of(int(vt,16))
    print('===',nm, vt, 'nsites', len(sites))
    for s,d in sites:
        txt,imm=decode_imm('%08X'%s)
        print('   site=%08X imm=%s  %s'%(s,imm,txt))

print()
print('site_of 0043B71F ->', decode_imm('0043B71F'))
print('site_of 005B2DE9 ->', decode_imm('005B2DE9'))
print('site_of 005B3C52 ->', decode_imm('005B3C52'))
print('site_of 00652B45 ->', decode_imm('00652B45'))
print('site_of 0065CA03 ->', decode_imm('0065CA03'))
print('site_of 006AF13D ->', decode_imm('006AF13D'))
print('site_of 006B6C2D ->', decode_imm('006B6C2D'))
print('site_of 006F3130 ->', decode_imm('006F3130'))
