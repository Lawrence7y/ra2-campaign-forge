"""
Find RTTI TypeDescriptors and vtables for CellClass / MapClass.
Technique: TD name string -> TD -> scan .rdata for dword pointing to a COL whose
pTypeDescriptor == TD.  The dword's address = vtable-4, so vtable = addr+4.
"""
import struct
from pehelp import *

def find_td_names(names):
    """Return dict name -> list of TD candidate addresses (name string addr - 8)."""
    out = {}
    for secname in ('.rdata', '.data'):
      sec = next((s for s in SECTIONS if s[4] == secname), None)
      if not sec: continue
      v, vs, raw, rs, _ = sec
      data = pe.get_data(raw, rs)
      for nm in names:
        pat = ('.?AV' + nm + '@@').encode()
        out.setdefault(nm, [])
        idx = data.find(pat)
        while idx != -1:
            name_va = v + idx
            td_va = name_va - 8
            vf = u32(td_va)
            secx = section_of(vf) if vf else None
            out[nm].append((td_va, name_va, vf, secx[4] if secx else None))
            idx = data.find(pat, idx + 1)
    return out

def find_vtables_for_td(td_va):
    """Scan all .data/.rdata dwords for COL pointers matching td_va."""
    results = []
    for secname in ('.rdata', '.data'):
        sec = next((s for s in SECTIONS if s[4] == secname), None)
        if not sec: continue
        v, vs, raw, rs, _ = sec
        data = pe.get_data(raw, rs)
        # iterate dword-aligned positions (COL pointers are 4-aligned)
        for off in range(0, rs - 3, 4):
            col = struct.unpack_from('<I', data, off)[0]
            if not (IMAGE_BASE <= col < 0x00C00000):
                continue
            # COL layout: +0 sig, +4 offset, +8 cdOffset, +C pTypeDescriptor,
            #            +10 pClassDescriptor, +14 pSelf
            ptd = u32(col + 0xC)
            if ptd != td_va:
                continue
            vtable_va = v + off + 4
            # confirm vtable[0] is a code address (in .text)
            vt0 = u32(vtable_va)
            s0 = section_of(vt0) if vt0 else None
            results.append((vtable_va, col, vt0, s0[4] if s0 else None))
    return results

if __name__ == '__main__':
    names = ['CellClass', 'MapClass']
    tds = find_td_names(names)
    for nm, lst in tds.items():
        print(f"== {nm} TypeDescriptor candidates: {len(lst)}")
        for td, name_va, vf, sec in lst:
            print(f"   TD={td:#x} name={name_va:#x} pVFTable={vf and hex(vf)} sec={sec}")
            vts = find_vtables_for_td(td)
            for vtable_va, col, vt0, s0 in vts:
                print(f"      vtable={vtable_va:#x} COL={col:#x} vtable[0]={vt0 and hex(vt0)} ({s0})")
