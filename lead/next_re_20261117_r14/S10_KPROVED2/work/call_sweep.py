"""S10-KPROVED2 own toolkit part 2: full .text linear sweep with skipdata,
instruction-boundary set, direct E8 call-site map. Independent of function_atlas.
"""
import struct, sys
from capstone import *
from capstone.x86 import *
from re_core import PE, EXE, IB

def full_text_sweep(pe):
    """Linear sweep of .text with skipdata=True. Returns:
    insns: dict va -> (mnem, size, bytes) for every decoded instruction boundary
    e8_sites: dict target_va -> [site_va,...] for E8 rel32 calls at boundaries
    e8_site_vas: set of site VAs where an E8 was decoded at a boundary
    """
    text = [s for s in pe.sects if s[0]=='.text'][0]
    _, va0, va1, praw, sz = text
    code = pe.image[praw:praw+sz]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    md.skipdata = True
    insns = {}
    e8_sites = {}
    e8_site_vas = set()
    n = 0
    for ins in md.disasm(code, va0):
        n += 1
        va = ins.address
        insns[va] = (ins.mnemonic, ins.size, bytes(ins.bytes))
        if ins.bytes and ins.bytes[0] == 0xE8 and ins.size == 5:
            rel = struct.unpack('<i', ins.bytes[1:5])[0]
            tgt = va + 5 + rel
            e8_sites.setdefault(tgt, []).append(va)
            e8_site_vas.add(va)
    return insns, e8_sites, e8_site_vas, n

def verify_direct_sites(pe, e8_sites, e8_site_vas, entry, claimed_sites):
    """For each claimed direct site, verify: E8 at boundary, target==entry,
    non-self-loop (site not inside [entry, entry+body_end)).
    Returns list of dicts.
    """
    res = []
    for s in claimed_sites:
        rec = {'site':s, 'at_boundary':False,'target':None,'target_ok':False,'self_loop':None}
        if s in e8_site_vas:
            rec['at_boundary'] = True
        # direct bytes check regardless of boundary
        b = pe.bytesva(s, 5)
        if b is None or b[0]!=0xE8:
            res.append(rec); continue
        rel = struct.unpack('<i', b[1:5])[0]
        tgt = s+5+rel
        rec['target'] = tgt
        rec['target_ok'] = (tgt==entry)
        rec['self_loop'] = (entry <= s < entry+0x4000)  # rough self-loop guard; refined later with extent
        res.append(rec)
    return res

if __name__=='__main__':
    pe = PE()
    insns, e8_sites, e8_site_vas, n = full_text_sweep(pe)
    print('decoded insns:', n)
    print('distinct E8 targets:', len(e8_sites))
    print('total E8 sites:', sum(len(v) for v in e8_sites.values()))
    # verify 8 candidates
    cands = {
      0x004D5690:[0x0052236E,0x00741689],
      0x004D74E0:[0x00417C4E,0x0051F1EF,0x00738902],
      0x004D85D0:[0x0051A9FC,0x0073A4FB,0x0073B0A0],
      0x00706640:[0x004DAFAB],
      0x004D7D50:[0x00417C94,0x0051F2AF,0x0073895D],
      0x00702D40:[0x00744790],
      0x004DBAD0:[0x0041B619,0x00521C99,0x00744649],
      0x006F3AD0:[0x0045392C,0x004539FF,0x005232C8],
    }
    for e, sites in cands.items():
        v = verify_direct_sites(pe, e8_sites, e8_site_vas, e, sites)
        ok = all(r['at_boundary'] and r['target_ok'] and not r['self_loop'] for r in v)
        print(f'{e:08X} verified={ok}')
        for r in v:
            print('   ',hex(r['site']),'boundary',r['at_boundary'],'tgt',hex(r['target']) if r['target'] else None,'tgt_ok',r['target_ok'],'self',r['self_loop'])
