# -*- coding: utf-8 -*-
"""Resolve Winsock IAT thunks in 0x7C8968..0x7C8A40, and dump each chA site's
call/test/jcc bytes + branch-path action signatures with HEX addresses."""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import *
from capstone.x86 import *

pe = R._pe
iatmap = {}
for desc in pe.DIRECTORY_ENTRY_IMPORT:
    dll = desc.dll.decode("latin1")
    for imp in desc.imports:
        if imp.address:
            iatmap[imp.address] = (dll, imp.name.decode("latin1") if imp.name else ("ord%d"%imp.ordinal))

print("=== Winsock thunk map 0x7C8960..0x7C8A40 ===")
for tva in range(0x7C8960, 0x7C8A40, 6):
    code = R.read_va(tva, 6)
    if len(code) >= 6 and code[0:2] == b'\xff\x25':
        iat = struct.unpack("<I", code[2:6])[0]
        print("thunk %08X -> IAT %08X -> %s" % (tva, iat, iatmap.get(iat, "???")))

THUNK = {}
for tva in range(0x7C8960, 0x7C8A40, 6):
    code = R.read_va(tva, 6)
    if len(code) >= 6 and code[0:2] == b'\xff\x25':
        iat = struct.unpack("<I", code[2:6])[0]
        THUNK[tva] = iatmap.get(iat, ("???","???"))[1]

rows = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"analysis.json"), encoding="utf-8"))
MD = Cs(CS_ARCH_X86, CS_MODE_32); MD.detail = True; MD.skipdata = True

def path_actions(insns, start_idx, maxn=14):
    out=[]
    for j in range(start_idx, min(start_idx+maxn, len(insns))):
        ins=insns[j]
        if ins.id==0: continue
        if ins.id==X86_INS_CALL:
            tgt = ins.operands[0].imm & 0xFFFFFFFF if ins.operands and ins.operands[0].type==X86_OP_IMM else None
            nm = THUNK.get(tgt)
            out.append("%08X:call %08X%s"%(ins.address, tgt if tgt else 0, ("["+nm+"]") if nm else ""))
        elif ins.id==X86_INS_RET:
            out.append("%08X:ret"%ins.address); break
        elif ins.id in (X86_INS_JMP,):
            out.append("%08X:jmp %s"%(ins.address,ins.op_str)); break
        else:
            out.append("%08X:%s %s"%(ins.address,ins.mnemonic,ins.op_str))
    return out

for r in rows:
    ea=r["ea"]; size=r["atlas"].get("size",0)
    insns=list(MD.disasm(R.read_va(ea,size),ea))
    idx={ins.address:i for i,ins in enumerate(insns)}
    print("\n"+"="*100)
    print("ENTRY %s %s"%(r["entry"], r["hint_name"]))
    for s in r["chA_sites"]:
        ca=int(s["call_addr"]); ta=int(s["test_addr"]); ja=int(s["jcc_addr"])
        callee=s["callee_profile"].get("callee_key")
        callee_int=int(callee,16) if callee else None
        print("  SITE call@%08X -> %s(%s)  test@%08X(%s imm=%s)  jcc@%08X %s" % (
            ca, callee, THUNK.get(callee_int,"?"), ta, s["test_kind"], s.get("test_imm"), ja, s["jcc_mnemonic"]))
        # print call..jcc bytes
        for ins in insns:
            if ins.address in (ca,ta,ja):
                print("      %08X: %-8s %-30s | %s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex()))
        # taken vs fallthrough actions
        tgt=s.get("jcc_target")
        ti=idx.get(tgt) if isinstance(tgt,int) else None
        ji=idx.get(ja)
        print("      TAKEN->%08X:"%(tgt if isinstance(tgt,int) else 0))
        for x in (path_actions(insns,ti) if ti is not None else ["<out-of-body>"]):
            print("         ",x)
        print("      FALLTHRU->%08X:"%(ja+6))
        for x in path_actions(insns,ji+1 if ji is not None else 0):
            print("         ",x)
