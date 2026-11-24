# -*- coding: utf-8 -*-
"""② 类身份全量：COL→TD→名串（TD+8 内联）+ CHD 基类链；并打印 TD+8 名字串的原始字节。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import u32, va_in, read_cstr, parse_col, parse_td
from analyze import rtti_chain, classify_table

VT = {
    "007F443C": "TActionClass",
    "007F44E0": "TagClass",
    "007F45C4": "TagTypeClass",
    "007F5578": "TEventClass",
    "007F5858": "TriggerClass",
    "007F5904": "TriggerTypeClass",
}


def raw(vb):
    col = u32(vb - 4)
    ch = rtti_chain(col)
    print("vtable %s  COL@%08X  sig=%s  td=%08X  name@%s = %r" %
          (("%08X" % vb), col, ch["sig_hex"], int(ch["td"]), ch.get("td_name_va"), ch["td_name"]))
    tb = R.read_va(int(ch["td_name_va"], 16), 48) if ch.get("td_name_va") else b""
    print("   TD+8 原始字节: %s" % " ".join("%02X" % b for b in tb))
    print("   TD+0..+8: %s" % " ".join("%02X" % b for b in R.read_va(int(ch["td"]), 8)))
    if ch["chd"]:
        c = ch["chd"]
        print("   CHD@%s attr=0x%X nbase=%s" % (c["va"], c["attr"], c["nbase"]))
        for b in c["bases"]:
            print("      base col=%s sig=%s td=%s name=%s" % (b["col"], b["sig"], b["td"], b["name"]))
    t = classify_table(vb)
    print("   vlen=%d slot0=%s %s" % (t["vlen"], t["slot0"], t["slot0_kind"]))


if __name__ == "__main__":
    for k in (sys.argv[1:] or list(VT)):
        raw(int(k, 16))
        print()
