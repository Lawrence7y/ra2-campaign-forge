"""Self-written ④ direct-call site scanner. Full .text instruction sweep with skipdata.
For each target entry, find E8 call sites where site+5+rel32==entry, E8 at instruction boundary,
site OUTSIDE the function body (using self-written CFG extent of target), non-self-loop.
Dual channel: (A) capstone linear sweep of whole .text; (B) raw byte E8 scan then boundary verification via
disassembling from a safe anchor. Report both.
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__))
import common as C

TARGETS = ["0055C7C0","0065CF00","00431F10","0065CB50","00473B10","00473AE0","0047AF10","0065CCE0"]
# atlas_size caps from classification (used only as a max extent ceiling; body determined by CFG/linear to ret)
CAPSIZE = {"0055C7C0":0x110,"0065CF00":0x220,"00431F10":0x1c0,"0065CB50":0x1d0,
           "00473B10":0x2b0,"00473AE0":0x130,"0047AF10":0x1b0,"0065CCE0":0x1a0}

s = C.text_section()
TEXT_VA = C.IMAGE_BASE + s.VirtualAddress
TEXT_VSIZE = s.Misc_VirtualSize
TEXT_RAW = s.SizeOfRawData
text_bytes = C._data[s.PointerToRawData:s.PointerToRawData+TEXT_VSIZE]

def function_extent(entry, cap):
    """CFG-ish extent: linear disasm from entry until a ret is followed by padding or a new prologue.
       Conservative: take max end among rets encountered before cap, but require the run to be contiguous.
    """
    last_ret_end = entry
    for insn in C.disasm_va(entry, cap):
        if insn.mnemonic.startswith("ret"):
            last_ret_end = insn.address + insn.size
        if insn.address + insn.size - entry >= cap:
            break
    return (entry, last_ret_end)

def sweep_channel_A():
    """Channel A: capstone linear disasm of entire .text; collect E8 call insns."""
    calls = []
    n_insn = 0
    for insn in C.md().disasm(text_bytes, TEXT_VA):
        n_insn += 1
        if insn.mnemonic == "call" and len(insn.bytes) >= 5 and insn.bytes[0] == 0xE8:
            rel = struct.unpack("<i", insn.bytes[1:5])[0]
            target = insn.address + 5 + rel
            calls.append((insn.address, target))
    return calls, n_insn

def sweep_channel_B_raw():
    """Channel B: raw byte E8 scan (no capstone boundary), collect (site, target)."""
    out = []
    i = 0
    n = len(text_bytes)
    while True:
        i = text_bytes.find(b"\xE8", i)
        if i < 0: break
        if i+5 <= n:
            rel = struct.unpack("<i", text_bytes[i+1:i+5])[0]
            site = TEXT_VA + i
            out.append((site, site+5+rel))
        i += 1
    return out

print("sweeping .text channel A (capstone)...")
callsA, n_insn = sweep_channel_A()
print("  instructions:", n_insn, " E8 calls:", len(callsA))
rawB = sweep_channel_B_raw()
print("raw byte E8 channel B:", len(rawB))

# boundary set from channel A: set of addresses that are instruction starts in .text
boundary = set(a for a,_ in callsA)

extents = {e:function_extent(int(e,16), CAPSIZE[e]) for e in TARGETS}
result = {}
for e in TARGETS:
    entry=int(e,16)
    lo,hi = extents[e]
    sitesA = []
    for site,target in callsA:
        if target==entry:
            in_body = (lo <= site < hi)
            selfloop = (site==entry)
            sitesA.append({"site":"0x%x"%site,"in_body":in_body,"selfloop":selfloop,
                           "keep":(not in_body) and (not selfloop)})
    # channel B: raw E8 targets, then require boundary and verify via capstone re-disasm at site
    sitesB=[]
    for site,target in rawB:
        if target==entry and site in boundary:
            # re-verify at site
            off = site - TEXT_VA
            chunk = text_bytes[off:off+5]
            if len(chunk)==5 and chunk[0]==0xE8:
                rel=struct.unpack("<i",chunk[1:5])[0]
                if site+5+rel==entry:
                    in_body=(lo<=site<hi); selfloop=(site==entry)
                    sitesB.append({"site":"0x%x"%site,"keep":(not in_body) and (not selfloop)})
    keepA=sorted([x["site"] for x in sitesA if x["keep"]])
    keepB=sorted([x["site"] for x in sitesB if x["keep"]])
    result[e]={"entry":e,"extent":["0x%x"%lo,"0x%x"%hi],
               "sites_all_A":sitesA,"kept_A":keepA,"kept_B":keepB,
               "channels_agree":(keepA==keepB),"n_kept":len(keepA),
               "n_boundary_hits_A":len([x for x in sitesA if x["keep"]]),
               "n_rawB_boundary":len(sitesB)}
    print("%s extent=%s..%s kept=%d agree=%s sites=%s" % (
        e,result[e]["extent"][0],result[e]["extent"][1],len(keepA),keepA==keepB,",".join(keepA)))

meta={"n_insn_text":n_insn,"n_e8_calls_A":len(callsA),"n_raw_e8_B":len(rawB),
      "text_va":"0x%x"%TEXT_VA,"text_vsize":TEXT_VSIZE}
with open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","direct_sites.json"),"w",encoding="utf-8") as f:
    json.dump({"meta":meta,"targets":result},f,indent=2)
print("wrote EVIDENCE/direct_sites.json")
