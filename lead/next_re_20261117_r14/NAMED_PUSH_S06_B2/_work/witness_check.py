# -*- coding: utf-8 -*-
"""对每个 vtable 的写点所在函数 dump 前 14 条指令，判构造器 vs 析构器（㉓）。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C2
WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(WORK,'analysis.json'), encoding='utf-8'))
seen = {}
for rec in A:
    for s in rec.get('ring2_slots', []):
        vt = s.get('vtable_base')
        if not vt or vt in seen: continue
        w = C2.find_vtable_writes(int(vt,16))
        pts = [g['write_va'] for g in w['global']] + ['%08X'%rw for rw in w['regdisp']]
        seen[vt] = {'rtti': s.get('rtti_name'), 'pts': pts, 'row': rec['entry']}
for vt, info in seen.items():
    print("="*100)
    print("VT %s rtti=%s (from row %s) write pts=%s" % (vt, info['rtti'], info['row'], info['pts']))
    for p in info['pts']:
        f = C2.find_containing_atlas_func(int(p,16))
        fva = f[0] if f else None
        atex = bool(C2.is_atexit_registered(fva)) if fva else False
        print("  -- write %s in_func=%s size=%s atexit=%s" % (p, R.hx(fva) if fva else None, f[2] if f else None, atex))
        if fva:
            insns = R.disasm(fva, R.read_va(fva, min(f[2], 80)))
            for ins in insns[:12]:
                print("       %08X: %-18s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic+" "+ins.op_str))
            insns2 = R.disasm(int(p,16)-8, R.read_va(int(p,16)-8, 18))
            print("       [around write]")
            for ins in insns2[:7]:
                print("       %08X: %-18s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic+" "+ins.op_str))
