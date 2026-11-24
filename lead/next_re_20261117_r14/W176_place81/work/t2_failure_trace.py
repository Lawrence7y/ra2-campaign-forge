"""W176 Task 2: full, non-truncated failure-branch traces for 0x43F180.

Dumps:
  - 0x47C620 callee head/tail (return polarity)
  - branch A: can-place #1 (0x43F218) failure -> 0x43F5D8 .. ret 0x43F5EC
  - branch B: per-cell 0x47C620 (0x43F2AE) al==0 -> 0x43F504 .. loop .. 0x43F5AB .. 0x43F5D8 .. ret
  - branch C: can-place #2 (0x43F678) failure -> 0x43F5E0 .. ret 0x43F5EC
  - all secondary 'je 0x43F504' sites (skip-cell, not failure-return)
Every instruction from the branch instruction to the ret is printed; no '...' elision.
"""
import capstone, pefile, os, bisect

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\EVIDENCE"
pe = pefile.PE(EXE, fast_load=True)
ib = pe.OPTIONAL_HEADER.ImageBase

def read(va, n):
    for s in pe.sections:
        v = ib + s.VirtualAddress
        if v <= va and va+n <= v + s.SizeOfRawData:
            off = s.PointerToRawData + (va-v)
            return pe.__data__[off:off+n]
    raise ValueError(hex(va))

def md():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m

def dump_range(start, end, path, title, skip_until=None):
    """Linear disasm start..end (end exclusive), never truncates."""
    m = md()
    lines=[title, 'linear disasm skipdata=True from %08X to %08X (both inclusive/exclusive as given)'%(start,end), '']
    n=0
    for ins in m.disasm(read(start, end-start), start):
        if ins.id==0:  # skipdata byte: still emit so no truncation
            lines.append('  %08X .byte %02X   [skipdata]'%(ins.address, ord(ins.bytes[:1]) if ins.bytes else 0))
            continue
        lines.append('  %08X %-9s %s'%(ins.address, ins.mnemonic, ins.op_str))
        n+=1
    lines.append('TOTAL real instructions: %d'%n)
    open(os.path.join(OUT,path),'w',encoding='utf-8').write('\n'.join(lines)+'\n')
    print('wrote',path,'insns',n)

# 0x47C620 full function: atlas size unknown here, dump 0x500 bytes
dump_range(0x47C620, 0x47C620+0x500, 'T2_callee_47C620.txt',
           'W176 T2 · callee 0x47C620 (per-cell validation) first 0x500 bytes; skipdata=True')

# Branch A: can-place #1 failure: from 0x43F218 to ret 0x43F5EC
dump_range(0x43F218, 0x43F5F0, 'T2_branchA_canplace1.txt',
           'W176 T2 · branch A: can-place #1 @0x43F218 to ret 0x43F5EC (linear, full, no elision)')

# Branch B: per-cell failure: from 0x43F2AE to 0x43F5EC (covers loop + final failure ret)
dump_range(0x43F2AE, 0x43F5F0, 'T2_branchB_cellfail.txt',
           'W176 T2 · branch B: 0x47C620 al==0 @0x43F2AE to ret 0x43F5EC (linear through loop+final gate; no elision)')

# Branch C: can-place #2 failure: check site 0x43F678..0x43F686, then target 0x43F5E0..ret
dump_range(0x43F678, 0x43F687, 'T2_branchC_check_canplace2.txt',
           'W176 T2 · branch C check: can-place #2 @0x43F678 .. 0x43F686 (jne target 0x43F5E0)')
dump_range(0x43F5E0, 0x43F5F0, 'T2_branchC_failure_ret.txt',
           'W176 T2 · branch C failure target 0x43F5E0 .. ret 0x43F5EC (full, no elision)')

# short path mode gate region 0x43F5EF .. 0x43F691
dump_range(0x43F5EF, 0x43F692, 'T2_shortpath_43F5EF_43F691.txt',
           'W176 T2 · short path: 0x43F5EF .. 0x43F691 (incl. cmp ebp,3 @0x43F658)')
