# -*- coding: utf-8 -*-
"""按行 dump 函数反汇编（含字节）+ ③ 站点被调函数体，供人工逐字节核 ③b②。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R

WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(WORK,'analysis.json'), encoding='utf-8'))

def dump_insns(va, size, label, maxn=400):
    print("\n### %s  va=%08X size=%s" % (label, va, size))
    data = R.read_va(va, size)
    insns = R.disasm(va, data)
    for j, ins in enumerate(insns[:maxn]):
        if ins.id == 0:
            print("  %08X: db %s (skipdata)" % (ins.address, ins.bytes.hex())); continue
        print("  %08X: %-20s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic+" "+ins.op_str))

want = sys.argv[1:] if len(sys.argv)>1 else None
for rec in A:
    if want and rec['entry'] not in want:
        continue
    ea = int(rec['entry'],16)
    size = R.ATLAS.get(rec['entry'],{}).get('size')
    print("\n"+"="*110)
    print("#%d %s %s size=%s" % (rec['idx'], rec['entry'], rec['name'], size))
    dump_insns(ea, size, "BODY "+rec['entry'])
    ch = rec.get('chA',{})
    for st in ch.get('sites',[]):
        callee = st.get('callee')
        if callee:
            csize = R.ATLAS.get(R.hx(callee),{}).get('size')
            if csize:
                dump_insns(callee, csize, "CALLEE "+R.hx(callee)+" (for site %08X)"%st['call_addr'], maxn=120)
            else:
                print("\n### CALLEE %08X: no atlas size (indirect/unknown)" % callee)
        else:
            print("\n### site %08X: callee=None (INDIRECT call)" % st['call_addr'])
