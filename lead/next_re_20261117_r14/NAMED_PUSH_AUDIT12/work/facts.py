"""汇总 11 行全部事实，生成 VERDICT.md 逐节 + verdict.tsv 逐行（一次算、分批落盘）"""
import json, re
import rt
from rt import im, vt_name, vt_slots
from check11 import ENTRIES, CLAIM_VT, body

# 由 bodies/prod/clsid 实测得到的常量（全部来自我自己的反汇编）
FACTS = {
 "006C5210": dict(cls="FactoryClass", prodvt=0x007E88D0, ctor=0x006C5140, cwrite=0x006C514B,
                  clsx="{34ECD9A8-0AB0-11D2-ACA7-006008055BB5}", regcall=0x006BD43C,
                  qisite=0x006C526A, test=0x006C526E, jge=0x006C5270, jge_dst=0x006C527B,
                  relsite=0x006C5278, newsize=0x74, newcall=0x006C523E, ctorcall=0x006C524C,
                  g1=0x006C521B, g2=0x006C5233, g3=0x006C5258),
 "006C5390": dict(cls="WarheadTypeClass", prodvt=0x007F6B30, ctor=0x006C52C0, cwrite=0x006C52CB,
                  clsx="{A8C54DA4-0F7B-11D2-8172-006008055BB5}", regcall=0x006BD479,
                  qisite=0x006C53EF, test=0x006C53F3, jge=0x006C53F5, jge_dst=0x006C5400,
                  relsite=0x006C53FD, newsize=0x1D0, newcall=0x006C53C1, ctorcall=0x006C53D1,
                  g1=0x006C539B, g2=0x006C53B3, g3=0x006C53DD),
 "006C5510": dict(cls="WeaponTypeClass", prodvt=0x007F73B8, ctor=0x006C5440, cwrite=0x006C544B,
                  clsx="{9FD219CA-0F7B-11D2-8172-006008055BB5}", regcall=0x006BD4B6,
                  qisite=0x006C556F, test=0x006C5573, jge=0x006C5575, jge_dst=0x006C5580,
                  relsite=0x006C557D, newsize=0x160, newcall=0x006C5541, ctorcall=0x006C5551,
                  g1=0x006C551B, g2=0x006C5533, g3=0x006C555D),
 "006C5690": dict(cls="ParticleClass", prodvt=0x007EF954, ctor=0x006C55C0, cwrite=0x006C55CB,
                  clsx="{0E272DCC-9C0F-11D1-B709-00A024DDAFD1}", regcall=0x006BD4F3,
                  qisite=0x006C56ED, test=0x006C56F1, jge=0x006C56F3, jge_dst=0x006C56FE,
                  relsite=0x006C56FB, newsize=None, newcall=None, ctorcall=0x006C55D1,
                  g1=0x006C569B, g2=0x006C56B3, g3=0x006C56DD),
 "006C5810": dict(cls="ParticleTypeClass", prodvt=0x007F0188, ctor=0x006C5740, cwrite=0x006C574B,
                  clsx="{703E044B-0FB1-11D2-8172-006008055BB5}", regcall=0x006BD530,
                  qisite=0x006C586F, test=0x006C5873, jge=0x006C5875, jge_dst=0x006C5880,
                  relsite=0x006C587D, newsize=None, newcall=None, ctorcall=0x006C5751,
                  g1=0x006C581B, g2=0x006C5833, g3=0x006C585D),
 "006C5990": dict(cls="ParticleSystemClass", prodvt=0x007EFB9C, ctor=0x006C58C0, cwrite=0x006C58CB,
                  clsx="{0E272DC8-9C0F-11D1-B709-00A024DDAFD1}", regcall=0x006BD56D,
                  qisite=0x006C59ED, test=0x006C59F1, jge=0x006C59F3, jge_dst=0x006C59FE,
                  relsite=0x006C59FB, newsize=None, newcall=None, ctorcall=0x006C58D1,
                  g1=0x006C599B, g2=0x006C59B3, g3=0x006C59DD),
 "006C5B10": dict(cls="ParticleSystemTypeClass", prodvt=0x007F00A8, ctor=0x006C5A40, cwrite=0x006C5A4B,
                  clsx="{703E044A-0FB1-11D2-8172-006008055BB5}", regcall=0x006BD5AA,
                  qisite=0x006C5B6F, test=0x006C5B73, jge=0x006C5B75, jge_dst=0x006C5B80,
                  relsite=0x006C5B7D, newsize=None, newcall=None, ctorcall=0x006C5A51,
                  g1=0x006C5B1B, g2=0x006C5B33, g3=0x006C5B5D),
 "006C5C90": dict(cls="AITriggerTypeClass", prodvt=0x007E2A50, ctor=0x006C5BC0, cwrite=0x006C5BCB,
                  clsx="{BA093524-4CF4-11D2-BC26-00104B8FB04D}", regcall=0x006BD5E7,
                  qisite=0x006C5CEF, test=0x006C5CF3, jge=0x006C5CF5, jge_dst=0x006C5D00,
                  relsite=0x006C5CFD, newsize=None, newcall=None, ctorcall=0x006C5BD1,
                  g1=0x006C5C9B, g2=0x006C5CB3, g3=0x006C5CDD),
 "006C5E10": dict(cls="NeuronClass", prodvt=0x007E3DF0, ctor=0x006C5D40, cwrite=0x006C5D4B,
                  clsx="{241AB316-4CF5-11D2-BC26-00104B8FB04D}", regcall=0x006BD624,
                  qisite=0x006C5E6A, test=0x006C5E6E, jge=0x006C5E70, jge_dst=0x006C5E7B,
                  relsite=0x006C5E78, newsize=None, newcall=None, ctorcall=0x006C5D51,
                  g1=0x006C5E1B, g2=0x006C5E33, g3=0x006C5E5D),
 "006C5F90": dict(cls="FoggedObjectClass", prodvt=0x007E8B38, ctor=0x006C5EC0, cwrite=0x006C5ECB,
                  clsx="{1C470B0E-69D7-11D2-B8F2-006008C809ED}", regcall=0x006BD661,
                  qisite=0x006C5FEA, test=0x006C5FEE, jge=0x006C5FF0, jge_dst=0x006C5FFB,
                  relsite=0x006C5FF8, newsize=None, newcall=None, ctorcall=0x006C5ED1,
                  g1=0x006C5F9B, g2=0x006C5FB3, g3=0x006C5FDD),
 "006C6110": dict(cls="AlphaShapeClass", prodvt=0x007E32A4, ctor=0x006C6040, cwrite=0x006C604B,
                  clsx="{623C7584-74E7-11D2-B8F5-006008C809ED}", regcall=0x006BD69E,
                  qisite=0x006C616A, test=0x006C616E, jge=0x006C6170, jge_dst=0x006C617B,
                  relsite=0x006C6178, newsize=None, newcall=None, ctorcall=0x006C6051,
                  g1=0x006C611B, g2=0x006C6133, g3=0x006C615D),
}

def ins_at(va):
    for i in im.dis(va, 2, stop_ret=False):
        return i
    return None

def fmt1(va):
    i = ins_at(va)
    return f"{i.address:08X} {i.bytes.hex()} {i.mnemonic} {i.op_str}" if i else f"{va:08X} ?"

def facts(e):
    f = dict(FACTS[e])
    vt = CLAIM_VT[e]
    f["entry"] = e
    f["vt"] = vt
    f["slot_addr"] = vt + 0xC
    f["slot_val"] = im.u32(vt + 0xC)
    nm, col = vt_name(vt)
    f["vt_name"] = nm
    f["col"] = col
    ci = rt.col_info(col)
    f["td"] = ci["td"]
    f["chd"] = ci["chd"]
    f["prodvt_name"] = vt_name(f["prodvt"])[0]
    f["prodvt_slot0"] = im.u32(f["prodvt"])
    f["prodvt_slot1"] = im.u32(f["prodvt"] + 4)
    f["prodvt_slot8"] = im.u32(f["prodvt"] + 0x20)
    f["body_len"] = body(e)[-1].address + body(e)[-1].size - int(e, 16)
    f["n_insns"] = len(body(e))
    return f

if __name__ == "__main__":
    out = {e: facts(e) for e in ENTRIES}
    json.dump(out, open("facts11.json","w"), indent=1, default=str)
    for e in ENTRIES:
        f = out[e]
        print(f"{e} vt={f['vt']:08X} slot=+0x0C@{f['slot_addr']:08X}={f['slot_val']:08X} "
              f"name={f['vt_name']} COL={f['col']:08X} TD={f['td']:08X} chd={f['chd']:08X}")
        print(f"    prod {f['cls']:<24} vt={f['prodvt']:08X} {f['prodvt_name']:<42} slot0={f['prodvt_slot0']:08X} slot8={f['prodvt_slot8']:08X}")
        print(f"    ctor={f['ctor']:08X} write={f['cwrite']:08X} reg={f['regcall']:08X} CLSID={f['clsx']}")
        print(f"    QI site: {fmt1(f['qisite'])} | {fmt1(f['test'])} | {fmt1(f['jge'])} -> {f['jge_dst']:08X} | {fmt1(f['relsite'])}")
        print(f"    ③ 错误码: {fmt1(f['g1'])} | {fmt1(f['g2'])} | {fmt1(f['g3'])}")
        print()
