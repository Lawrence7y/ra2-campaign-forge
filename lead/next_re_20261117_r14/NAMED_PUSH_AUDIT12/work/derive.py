"""从字节完全派生 11 行全部要素（不硬编码任何指令地址）"""
import json, re, struct
import rt
from rt import im, vt_name, vt_slots
from check11 import ENTRIES, CLAIM_VT, body

def gval(op):
    m = re.match(r"^eax, (0x[0-9a-f]+)$", op)
    return int(m.group(1), 16) if m else None

def derive(e):
    ins = body(e)
    d = {"entry": e, "len": ins[-1].address + ins[-1].size - int(e, 16), "n": len(ins)}
    guards, dcall, icall = [], [], []
    test_i = jge_i = rel_i = qisite = None
    newsize = newcall = ctorcall = None
    for k, i in enumerate(ins):
        if i.mnemonic == "mov":
            v = gval(i.op_str)
            if v is not None:
                guards.append((i.address, i.bytes.hex(), v))
        if i.mnemonic == "push" and re.match(r"^0x[0-9a-f]+$", i.op_str):
            newsize = int(i.op_str, 16) if newsize is None else newsize
        if i.mnemonic == "call":
            m = re.match(r"^0x([0-9a-f]+)$", i.op_str)
            if m:
                t = int(m.group(1), 16)
                dcall.append((i.address, t, i.bytes.hex()))
                if t == 0x7C8E17:
                    newcall = i.address
                elif newcall and ctorcall is None and i.address > newcall:
                    ctorcall = i.address
                    d["ctor"] = t
            else:
                icall.append((i.address, i.op_str, i.bytes.hex()))
                if i.op_str == "dword ptr [eax]":
                    qisite = i.address
                if i.op_str == "dword ptr [edx + 0x20]":
                    rel_i = i.address
        if i.mnemonic == "test" and qisite and i.address > qisite and test_i is None:
            test_i = i.address
        if i.mnemonic == "jge" and test_i and jge_i is None:
            jge_i = i.address
            d["jge_dst"] = int(i.op_str, 16)
    d.update(guards=guards, newsize=newsize, newcall=newcall, ctorcall=ctorcall,
             qisite=qisite, test=test_i, jge=jge_i, relsite=rel_i,
             dcall=dcall, icall=icall)
    vt = CLAIM_VT[e]
    d["vt"] = vt
    d["slot_addr"] = vt + 0xC
    d["slot_val"] = im.u32(vt + 0xC)
    nm, col = vt_name(vt)
    d["vt_name"], d["col"] = nm, col
    ci = rt.col_info(col)
    d["td"], d["chd"], d["chd_numbase"] = ci["td"], ci["chd"], im.u32(ci["chd"] + 8)
    d["vt_slot0"] = im.u32(vt)
    d["vt_slot1"] = im.u32(vt + 4)
    d["vt_slot2"] = im.u32(vt + 8)
    d["vt_slot4"] = im.u32(vt + 0x10)
    d["vt_slot5_raw"] = im.u32(vt + 0x14)   # 应为下一张表的 COL
    # 工厂构造器：写 vt 到 [obj] 的唯一写点
    d["ctor_write"] = None
    if d.get("ctor"):
        pat = struct.pack("<I", vt)
        for i in im.dis(d["ctor"], 12, stop_ret=False):
            if i.mnemonic == "mov" and i.bytes.endswith(pat):
                d["ctor_write"] = i.address
                d["ctor_write_ins"] = f"{i.mnemonic} {i.op_str}"
            if i.mnemonic.startswith("ret"):
                break
        d["ctor_body"] = [f"{i.address:08X} {i.bytes.hex()} {i.mnemonic} {i.op_str}"
                          for i in im.dis(d["ctor"], 8, stop_ret=False)]
    return d

if __name__ == "__main__":
    res = {e: derive(e) for e in ENTRIES}
    json.dump(res, open("derive11.json","w"), indent=1, default=str)
    for e in ENTRIES:
        d = res[e]
        gs = " / ".join("%08X %s=%08X" % (a, b, v) for a, b, v in d["guards"])
        ctor = d.get("ctor")
        print("### %s  len=%dB insns=%d" % (e, d["len"], d["n"]))
        print("  2 vt %08X slot3@%08X=%08X  name=%s" % (d["vt"], d["slot_addr"], d["slot_val"], d["vt_name"]))
        print("     COL %08X TD %08X CHD %08X numBase=%s" % (d["col"], d["td"], d["chd"], d["chd_numbase"]))
        print("     slots 0=%08X 1=%08X 2=%08X 3=%08X 4=%08X nextdword=%08X" % (
            d["vt_slot0"], d["vt_slot1"], d["vt_slot2"], d["slot_val"], d["vt_slot4"], d["vt_slot5_raw"]))
        print("  3 guards: %s" % gs)
        print("     new@%08X size=%s ctor@%08X -> %s" % (
            d["newcall"] or 0, hex(d["newsize"]) if d["newsize"] else None,
            d["ctorcall"] or 0, ("%08X" % ctor) if ctor else None))
        print("     QI %08X | test %08X | jge %08X->%08X | free %08X" % (
            d["qisite"], d["test"], d["jge"], d["jge_dst"], d["relsite"]))
        print("  4 ctorwrite %s  %s" % (
            ("%08X" % d["ctor_write"]) if d["ctor_write"] else None, d.get("ctor_write_ins")))
        print()
