# -*- coding: utf-8 -*-
"""Verify ring-4 anchors are NOT in a destructor: containing atlas function of
the registration site, its atexit/destructor status, CoRegisterClassObject IAT load,
CLSID pushed before reg call. Read-only on target.
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C
from capstone.x86 import *

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "gather.json"), encoding="utf-8") as f:
    G = json.load(f)

IAT_REGISTER = 0x7E15D8  # ole32!CoRegisterClassObject (per B1)

def find_iat_load_in_func(func_va, size, iat):
    """Find `mov esi,[0x7E15D8]` (8B 35 <iat>) or any reg load of the IAT within func."""
    hits = []
    for ins in R.disasm_body(func_va, size):
        if ins.id == X86_INS_MOV and len(ins.operands) == 2:
            a, b = ins.operands
            if a.type == X86_OP_REG and b.type == X86_OP_MEM and b.mem.disp == iat \
               and b.mem.base in (X86_REG_INVALID, 0) and b.mem.index in (X86_REG_INVALID, 0):
                hits.append((R.hx(ins.address), ins.mnemonic + " " + ins.op_str))
    return hits

def clsid_before_reg(callva, window=40, lower=0):
    """Scan backward from the `call esi` reg call for `push <imm>` CLSID (68 imm32),
    not going below `lower` (the ctor call), so a previous factory's CLSID is excluded."""
    hits = []
    for ins in R.disasm_body(max(callva - window, lower), min(window, callva - lower)):
        if ins.id == X86_INS_PUSH and ins.operands and ins.operands[0].type == X86_OP_IMM:
            v = ins.operands[0].imm & 0xFFFFFFFF
            if 0x7E0000 <= v <= 0x7FFFFF:  # .rdata GUID region
                hits.append((R.hx(ins.address), R.hx(v), ins.bytes.hex(" ")))
    return hits

def analyze(r):
    fc = int(r["factory_ctor"], 16)
    ctor_call = int(r["reg_sites"][0]["ctor_call"], 16)
    cf = C.find_containing_atlas_func(ctor_call)
    host_va = cf[0] if cf else None
    host_size = R.ATLAS.get(R.hx(host_va), {}).get("size") if host_va else None
    host_atexit = C.is_atexit_registered(host_va) if host_va else None
    iat_loads = find_iat_load_in_func(host_va, host_size, IAT_REGISTER) if host_va else []
    # reg call: find the FIRST `call esi` strictly AFTER the ctor_call (this factory's reg),
    # not the previous factory's reg call that appears earlier in the window.
    reg_call = None
    clsid = []
    for w in r["reg_sites"][0]["window"]:
        if w["text"] == "call esi" and int(w["addr"], 16) > ctor_call:
            reg_call = w["addr"]
            clsid = clsid_before_reg(int(reg_call, 16), window=40, lower=ctor_call)
            break
    # alloc site (push 8; call operator-new) just before ctor_call
    alloc = None
    for w in r["reg_sites"][0]["window"]:
        if w["text"].startswith("call 0x7c8e17") and int(w["addr"], 16) < ctor_call:
            alloc = w["addr"]
            break
    return {
        "entry": r["entry"], "factory_ctor": r["factory_ctor"],
        "ctor_call": R.hx(ctor_call), "alloc": alloc,
        "host_func": R.hx(host_va) if host_va else None,
        "host_size": host_size, "host_atexit": host_atexit,
        "iat_loads": iat_loads, "reg_call": reg_call, "clsid_pushes": clsid,
        "fc_atexit": r["fc_atexit"], "fc_callers": r["fc_callers"],
    }

def main():
    out = [analyze(r) for r in G]
    with open(os.path.join(HERE, "ring4.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for x in out:
        print("%s host=%s(size=%s) host_atexit=%s iat=%d alloc=%s ctor_call=%s reg_call=%s clsid=%s fc_atexit=%s" % (
            x["entry"], x["host_func"], x["host_size"], x["host_atexit"],
            len(x["iat_loads"]), x["alloc"], x["ctor_call"], x["reg_call"],
            [c[1] for c in x["clsid_pushes"]], x["fc_atexit"]))

if __name__ == "__main__":
    main()
