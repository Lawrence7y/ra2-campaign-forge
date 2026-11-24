# -*- coding: utf-8 -*-
"""独立核验 B5：抽取每行关键 ②④ 事实 + 枚举虚表全部写点并分类构造/析构。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True
IAT_DELETE = set()

def u32(va): return W.u32(va)
def hx(x): return "%08X" % (x & 0xFFFFFFFF)

print("###### 每行的 ②（RTTI 槽）与 ④（direct/构造安装点）摘要 ######")
for r in rows:
    print("\nENTRY", r["entry"], r["hint_name"], "direct=", r["direct_callers"])
    for s in r["slots"]:
        if not s.get("rtti_name"):
            print("   slot", s["slot_va"], s.get("section"), "NO-RTTI"); continue
        print("   slot_va=%s vt=%s off=+%d(%d) name=%s" % (
            s["slot_va"], s["vtable_base"], int(s["slot_off"]), int(s["slot_off"])//4, s["rtti_name"]))
        print("     slot_content=%s col=%s td=%s" % (
            hx(u32(int(s["slot_va"],16)) or 0), s["col"], s["td"]))
        for g in s.get("global_writes", []):
            f=g.get("in_func")
            print("     write %s in_func=%s atexit=%s global=%s" % (
                g["write_va"], ("%08X"%f[0]) if f else "?", g.get("atexit"), g.get("global")))

# 唯一化所有涉及 vtable base
vts = {}
for r in rows:
    for s in r["slots"]:
        if s.get("rtti_name"):
            vts.setdefault(s["vtable_base"], set()).add(s["rtti_name"])
print("\n\n###### 涉及 vtable base 列表 ######")
for vb,nms in sorted(vts.items()):
    print(vb, sorted(nms), "slot0=", hx(u32(int(vb,16)) or 0), "[-4]=", hx(u32(int(vb,16)-4) or 0))

# 枚举每个 vtable 在 .text 的全部写点（C7 05 abs-imm / C7 [reg+disp] imm / B8+r imm）
def find_writes(vt):
    res=[]
    T=R.TEXT_DATA; V=R.TEXT_VA
    needle=struct.pack("<I", vt)
    off=0
    while True:
        i=T.find(needle, off)
        if i<0: break
        va=(V+i)&0xFFFFFFFF
        if T[i-6:i-4]==b"\xc7\x05":
            absv=struct.unpack_from("<I",T,i-4)[0]
            res.append(("C7 05 [glob]", (V+i-6)&0xFFFFFFFF, absv))
        elif T[i-2]==0xC7:
            res.append(("C7 [rm]", (V+i-2)&0xFFFFFFFF, None))
        elif 0xB8<=T[i-1]<=0xBF:
            res.append(("B8+r imm load", (V+i-1)&0xFFFFFFFF, None))
        off=i+1
    return res

print("\n\n###### 每个 vtable 的全部 .text 写点 + 所在函数 ######")
for vb in sorted(vts):
    vt=int(vb,16)
    wr=find_writes(vt)
    print("\nVT", vb, "writes total=", len(wr))
    for kind, wa, g in wr:
        f=W.find_containing_atlas_func(wa)
        print("   %-16s @%08X in_func=%s atexit=%s" % (
            kind, wa, ("%08X"%f[0]) if f else "?", bool(f and W.is_atexit_registered(f[0]))))

# 反汇编每个安装函数全文，分类构造/析构
print("\n\n###### 安装函数全文反汇编（判构造 vs 析构） ######")
funcs=set()
for vb in vts:
    for kind,wa,g in find_writes(int(vb,16)):
        f=W.find_containing_atlas_func(wa)
        if f: funcs.add(int(f[0],16) if isinstance(f[0],str) else f[0])
for fa in sorted(funcs):
    info=R.ATLAS.get(hx(fa),{})
    sz=info.get("size",0)
    code=R.read_va(fa, sz if sz else 256)
    ins=list(MD.disasm(code,fa))
    # 统计 vptr 写次数 / delete 调用 / 对基类函数区间的 call / 二次栈操作
    vptr_writes=0; delete_calls=0; calls=[]; rets=0
    for x in ins:
        if x.id==0: continue
        if x.id==X86_INS_CALL:
            rets+=0
            op=x.operands[0] if x.operands else None
            if op:
                t=(op.imm & 0xFFFFFFFF) if op.type==X86_OP_IMM else None
                calls.append(t)
                if t and t in IAT_DELETE: delete_calls+=1
        if x.id==X86_INS_RET: rets+=1
        # mov [reg/...], imm  where imm matches any vtable base
        if x.id==X86_INS_MOV and len(x.operands)==2 and x.operands[1].type==X86_OP_IMM:
            if (x.operands[1].imm & 0xFFFFFFFF) in set(int(v,16) for v in vts):
                vptr_writes+=1
    print("\nFUNC %08X size=%s vptr_writes=%d ret=%d calls=%s" % (
        fa, sz, vptr_writes, rets, [hx(c) for c in calls if c]))
    for x in ins[:6]:
        print("    %08X: %s %s" % (x.address, x.mnemonic, x.op_str))
    print("    ...")
    for x in ins[-6:]:
        print("    %08X: %s %s" % (x.address, x.mnemonic, x.op_str))

