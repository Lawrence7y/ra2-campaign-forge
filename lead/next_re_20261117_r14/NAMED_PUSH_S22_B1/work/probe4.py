# -*- coding: utf-8 -*-
"""④ 取证：工厂自身 slot3(CreateInstance) 的活派发点。
工厂 vt 在 .rdata；ctor 把 vt 写进静态对象；调用方经 [obj+0xC] 派发 slot3。
判 ㉓：锚点若在析构器（atexit/标量删除析构）则 FAIL。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "analysis.json"), encoding="utf-8") as f:
    A = json.load(f)

# 收集每个工厂的 vt（来自 ring2 cands）和 ctor（来自 probe 手工；复用 vtable_writes）
def entry_vt(entry):
    r = next(x for x in A if x["entry"] == entry)
    c = r["ring2"]["cands"][0]
    return int(c["vtable_base"],16), c["rtti_name"]

# 静态对象：全 .data/.rdata 里 dword == vt 的位置（vptr 初值）；以及 .text 里 C7 05 <abs> vt 写
def global_vptr_writes(vt):
    needle = struct.pack("<I", vt)
    out = []
    # .text: C7 05 abs32 imm32  (imm==vt)
    td = R.TEXT_DATA; tv = R.TEXT_VA
    for off in range(6, len(td)-4):
        if struct.unpack_from("<I", td, off)[0] != vt: continue
        if td[off-6] == 0xC7 and td[off-5] == 0x05:
            absv = struct.unpack_from("<I", td, off-4)[0]
            out.append(("C705", R.hx(tv+off-6), R.hx(absv)))
    return out

# 找 call [reg+0xC] / ff 5x 0c 且 reg 由某静态全局地址载入
def slot3_dispatch_sites():
    """全 .text 扫 call dword ptr [reg+0xC]，记录站点与前面 8 条里 mov reg,[abs] 的 abs。"""
    sites=[]
    td=R.TEXT_DATA; tv=R.TEXT_VA
    for ins in R.disasm(td, tv):
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type==X86_OP_MEM:
            m=ins.operands[0].mem
            if m.disp==0xC and m.scale==1:
                sites.append((ins.address, ins.reg_name(m.base)))
    return sites

for r in A:
    if "TClassFactory" not in r["name"]: continue
    vt,name = entry_vt(r["entry"])
    gw = global_vptr_writes(vt)
    print("%s %-46s vt=%s rtti=%s  globalvptrwrites=%s" % (r["entry"], r["name"][:46], R.hx(vt), name, gw[:5]))
