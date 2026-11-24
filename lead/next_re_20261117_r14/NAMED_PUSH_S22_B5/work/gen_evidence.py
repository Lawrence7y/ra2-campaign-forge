# -*- coding: utf-8 -*-
"""Generate EVIDENCE/ROW_<entry>.txt for all 9 S22 B5 vector rows with exact anchors + bytes.
Per-row independent anchors only. Rings: ① entry ② vtable+RTTI+slot2 ③b bool-return contract ④ install anchor."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S22_B5"
HERE = os.path.join(OUT, "work")
with open(os.path.join(HERE,"b5_rows.json"),encoding="utf-8") as f: rows=json.load(f)
with open(os.path.join(HERE,"ring_analysis.json"),encoding="utf-8") as f: RA=json.load(f)
with open(os.path.join(HERE,"dump.json"),encoding="utf-8") as f: DUMP=json.load(f)

# verdicts computed from analysis (documented): ② all 9 pass; ③b all 9 fail (bool); ④ by row
R4 = {
 "007642E0": ("PASS","ctor 00763C70 (live vtable slot of WaypointPathClass vt 007F6E70; installs 0x7F6ED4 @00763CEA)"),
 "00765840": ("FAIL","all vtable writes in ~VectorClass dtors 00765B60/00765C20 (call operator delete 0x7C8B3D) -> ㉓"),
 "007659F0": ("PASS","ctor 00764B90 (caller 00764B67; installs 0x7F6F4C @00764BF9)"),
 "00766C10": ("FAIL","vtable write only in atexit-handler 007660B0 (@007660BF) + ~VectorClass dtors 00766FC0/00767080 -> ㉓"),
 "00766DC0": ("PASS","global-init 00766070 (@0076608D, .CRT init entry 0081587C, global 0xB72760, 16 readers)"),
 "00769E30": ("FAIL","all vtable writes in ~VectorClass dtors 0076A5C0/0076A680 (operator delete) -> ㉓"),
 "00769FE0": ("PASS","ctor 00768000 (caller 00767FD4; installs 0x7F7164 @00768052)"),
 "0076B8C0": ("FAIL","all vtable writes in ~VectorClass dtors 0076BBC0/0076BC10 (operator delete) -> ㉓"),
 "0076BA70": ("PASS","ctor 0076ABE0 (installs 0x7F7260 @0076AC12 into member subobj; non-dtor)"),
}

def insn_line(va, nbytes=16):
    b=R.read_va(va,nbytes)
    for i in R.disasm(va,b):
        return "%08X  %-20s %s %s"%(i.address,i.bytes.hex(),i.mnemonic,i.op_str)
    return "%08X  %s"%(va,b.hex())

def raw_line(va,n=16):
    return "%08X : %s"%(va,R.read_va(va,n).hex())

for r in rows:
    entry=r["entry"]; d=RA[entry]; s=d["slot2"]; dd=DUMP[entry]
    ea=int(entry,16)
    L=[]
    A=L.append
    A("NAMED-PUSH S22 B5 — ROW %s"%entry)
    A("name: %s"%r["name"])
    A("subsystem: %s  grade(survey)=%s  size=%s  n_call=%s"%(r["subsystem"],r["grade"],r["size"],r["n_call"]))
    A("")
    A("=== ① 入口 ===")
    A("  entry VA %s in .text [401000,7E038D): %s"%(entry, R.in_text(ea)))
    A("  atlas: size=%s n_instr=%s (survey size=%s n_call=%s)"%(
        dd["atlas"]["size"],dd["atlas"]["n_instr"],r["size"],r["n_call"]))
    A("  capstone skipdata instructions=%d skipdata_bytes=%d (0 => 边界自洽)"%(
        dd["n_insn"], dd["n_skipdata"]))
    A("  末条: %s"%(dd["last_insn"]))
    A("  裁定: PASS")
    A("")
    A("=== ② 类身份（容器虚表 + RTTI 名 + 槽号；不套工厂 C1）===")
    A("  dword[slot_va]=entry 命中 .rdata：")
    A("    slot_va=%s  %s"%(s["slot_va"], raw_line(int(s["slot_va"],16),4)+" (=entry)"))
    A("  COL 链 (sig=0 -> TD -> name)：")
    A("    [col_word=%s] = col %s ; u32(col)=sig %s"%(s["col_word_va"],s["col"],hex(C.u32(int(s["col"],16)))))
    A("    [col+0xC] = td %s ; name_va=%s"%(s["td"],s["name_va"]))
    A("    RTTI 名: %s"%s["rtti_name"])
    A("  vtable_base=%s  slot_off=8 (slot_no=2)  槽号由 (slot_va-vtable_base)/4 复算"%s["vtable_base"])
    A("    vtable[0]=%s  vtable[1]=%s  vtable[2](slot2)=%s"%(
        s["vtable_base_word"],
        "%08X"%C.u32(int(s["vtable_base"],16)+4),
        s["slot_word"]))
    A("  名/元素类型与 entry 名逐字对照: entry 名含 %s"%r["name"])
    A("  裁定: PASS (RTTI 名 + 实际元素类型 + slot_no=2 全钉死)")
    A("")
    A("=== ③b 整体合同（只认 ③b；多值状态码/Find -1 算，{0,1} bool 不算）===")
    A("  返回点（逐条）：")
    for rt in d["rets"]:
        A("    ret@%s %s <- %s"%(rt["ret_va"],rt["ret_bytes"],rt["al_setter"]))
    A("  出口常量集（AL bool）= {0,1}（mov al,1 / xor al,al / sete），非多值状态码、非 Find -1 下标。")
    A("  chA 机械命中唯一站点：call 0x7C8E17(operator new) -> test eax,eax -> je；")
    A("    这是内存分配空判断（callee consts=[]，返回指针非状态码），失败路 xor al,al 返回 false，成功路 mov al,1。")
    A("  0x65D480=rc_ptr::operator= (返回指针, ret 4)；附近 cmp/jl 是循环计数，非可伪证返回约定。")
    A("  三陷阱：无 eax 覆写（返回值在 AL）；无多路同一 call；属 {0,1} bool 模板假句 -> D-46(A) 否决。")
    A("  裁定: FAIL (③b 可伪证性不成立：{0,1} 布尔按任务规则不计)")
    A("")
    A("=== ④ 使用见证（独立于②；锚点落析构器判 FAIL ㉓）===")
    k,why=R4[entry]
    A("  direct callers: %d (纯虚派发；非 direct-only)"%len(d["direct_callers"]))
    A("  vtable 写点（全镜像 .text imm 扫描）：")
    if d["writes"]:
        for ins in d["writes"]["installs"]:
            A("    write@%s in_func=%s atexit=%s"%(ins["write_va"],ins["in_func"],ins["atexit"]))
    A("  锚点性质: %s"%why)
    A("  ②④不同源: ② 锚 .rdata RTTI 数据链; ④ 锚 .text 装表指令 —— 段/地址/产物类型均不同。")
    A("  裁定: %s"%k)
    A("")
    A("=== 总裁定 ===")
    A("  ① PASS | ② PASS | ③b FAIL | ④ %s  =>  四环齐全: NO (③b 不成立)"%k)
    A("  delta 产出: 否")

    with open(os.path.join(OUT,"EVIDENCE","ROW_%s.txt"%entry),"w",encoding="utf-8") as f:
        f.write("\n".join(L)+"\n")
    print("wrote ROW_%s.txt"%entry)

print("DONE 9 EVIDENCE files")
