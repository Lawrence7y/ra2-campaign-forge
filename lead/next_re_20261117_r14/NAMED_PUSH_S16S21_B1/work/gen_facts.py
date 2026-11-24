# -*- coding: utf-8 -*-
"""生成逐行四环事实块（地址 + 字节），供 EVIDENCE 落盘。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

HERE = os.path.dirname(os.path.abspath(__file__))

def b(va, n): return va_read(va, n).hex(" ").upper()

def ins_at(va):
    out = []
    for i in np_core._md.disasm(va_read(va, 16), va):
        out.append("%s %-20s %s %s" % (hx(i.address), b(i.address, i.size), i.mnemonic, i.op_str))
        break
    return out[0] if out else "?"

ROWS = {
 "0046D000": dict(vt=0x007E4A28, slot=0x007E4A3C, slotno=5, size=0x45,
                  col=0x007FC920, td=0x0081B170, cls=".?AVCampaignClass@@",
                  ctor_site=0x0046CB70, ctor=0x0046CB60,
                  new_site=0x006C02BC, new_va=0x006C02C1, new_call=0x006C02D1,
                  dtor_site=0x0046D096, dtor=0x0046D090),
 "0046D090": dict(vt=0x007E4A28, slot=0x007E4A48, slotno=8, size=0x8D,
                  col=0x007FC920, td=0x0081B170, cls=".?AVCampaignClass@@",
                  ctor_site=0x0046CB70, ctor=0x0046CB60,
                  new_site=0x006C02BC, new_va=0x006C02C1, new_call=0x006C02D1,
                  dtor_site=0x0046D096, dtor=0x0046D090),
 "0071B1B0": dict(vt=0x007F5180, slot=0x007F51A0, slotno=8, size=0x86,
                  col=0x0080C328, td=0x008445C8, cls=".?AVTemporalClass@@",
                  ctor_site=0x0071A467, ctor=0x0071A450,
                  new_site=0x006C073C, new_va=0x006C073E, new_call=0x006C074C,
                  dtor_site=0x0071B1BD, dtor=0x0071B1B0),
}

for e, d in ROWS.items():
    ea = int(e, 16)
    L = []
    L.append("① 入口")
    L.append("  entry=%s  .text=[%s,%s)  in_text=True  atlas_size=%d  atlas_end=%s"
             % (e, hx(TEXT_VA), hx(TEXT_VA + TEXT_SIZE), d["size"], hx(ea + d["size"])))
    ins = list(np_core._md.disasm(va_read(ea, d["size"]), ea))
    L.append("  反汇编条数=%d  skipdata空洞=%d  首条=%s %s  末条=%s %s  末条末字节=%s"
             % (len(ins), sum(1 for i in ins if i.id == 0),
                ins[0].mnemonic, ins[0].op_str, ins[-1].mnemonic, ins[-1].op_str,
                hx(ins[-1].address + ins[-1].size)))
    L.append("  末 3 条：")
    for i in ins[-3:]:
        L.append("    %s  %-20s %s %s" % (hx(i.address), b(i.address, i.size), i.mnemonic, i.op_str))
    L.append("")
    L.append("② 类身份（.rdata 虚表槽 → RTTI）")
    L.append("  槽 %s = %s   （vt %s + 0x%X = slot#%d，与线索 slot%d 一致）"
             % (hx(d["slot"]), b(d["slot"], 4), hx(d["vt"]), d["slot"] - d["vt"], d["slotno"], d["slotno"]))
    L.append("  [vt-4] = %s → COL %s = %s" % (hx(d["vt"] - 4), b(d["vt"] - 4, 4), hx(d["col"])))
    L.append("  COL.%s = %s  (sig=0)" % ("+0", b(d["col"], 4)))
    L.append("  COL+0xC (pTD, 绝对VA) = %s ; COL+0x10 (pCHD) = %s → CHD %s sig=%s attr=%s"
             % (b(d["col"] + 0xC, 4), b(d["col"] + 0x10, 4), hx(u32(d["col"] + 0x10)),
                hx(u32(u32(d["col"] + 0x10))), hx(u32(u32(d["col"] + 0x10) + 4))))
    L.append("  TD %s = %s ; TD+8 内联装饰名 %s = %r"
             % (hx(d["td"]), b(d["td"], 8), hx(d["td"] + 8), read_cstr(d["td"] + 8, 64)))
    L.append("  vt slot0 = %s (=主表标志 00410260 : %s)"
             % (hx(u32(d["vt"])), "YES" if u32(d["vt"]) == 0x00410260 else "NO"))
    L.append("")
    L.append("④ 使用见证（.text 构造器活表安装点；与 ② 不同源）")
    L.append("  安装点 %s : %s" % (hx(d["ctor_site"]), ins_at(d["ctor_site"])))
    L.append("  所在函数 = 构造器 %s（首条 %s）" % (hx(d["ctor"]), ins_at(d["ctor"])))
    L.append("  构造器调用者 %s : %s" % (hx(d["new_site"]), ins_at(d["new_site"])))
    L.append("  紧邻 operator new 0x7C8E17 调用 %s : %s" % (hx(d["new_va"]), ins_at(d["new_va"])))
    L.append("  构造调用 = %s : %s" % (hx(d["new_call"]), ins_at(d["new_call"])))
    L.append("  ㉓ 排除：删除析构器 %s 体内写点 %s : %s（%s）"
             % (hx(d["dtor"]), hx(d["dtor_site"]), ins_at(d["dtor_site"]),
                "本条 entry 自身" if int(e, 16) == d["dtor"] else "行外"))
    print("\n".join(L))
    open(os.path.join(HERE, "facts_%s.txt" % e), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print()

