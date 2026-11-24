
import pefile, capstone, struct, sys
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE, fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase", hex(base))
# map VA->offset
def va2off(va):
    rva = va - base
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None
data = open(EXE,'rb').read()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

# Function 0x4309D0: disassemble ~0x200 bytes, find refs to PBEACON/RDRBEACN strings and globals
fn = 0x4309D0
off = va2off(fn)
print("fn off", hex(off))
buf = data[off:off+0x300]
found_strings=[]; found_globals=[]
for ins in md.disasm(buf, fn):
    opstr = ins.op_str
    # look for immediate addresses that are string refs
    for tok in opstr.replace(',',' ').split():
        t=tok.strip()
        try:
            v=int(t,16) if t.lower().startswith('0x') else int(t,16)
        except: 
            continue
        if 0x400000 <= v <= 0x900000:
            o2=va2off(v)
            if o2 is not None:
                raw=data[o2:o2+40]
                # extract ascii
                s=''
                for b in raw:
                    if 32<=b<127: s+=chr(b)
                    else: break
                if 'PBEACON' in s or 'RDRBEACN' in s or 'Beacon' in s:
                    found_strings.append((hex(ins.address), ins.mnemonic+' '+ins.op_str, hex(v), s))
    if '0x89c474' in opstr.lower() or '0x89c478' in opstr.lower():
        found_globals.append((hex(ins.address), ins.mnemonic+' '+ins.op_str))
print("\n-- string refs in 0x4309D0 body --")
for x in found_strings: print(x)
print("\n-- global refs 89C474/78 in 0x4309D0 body --")
for x in found_globals: print(x)

# caller at 0x687BB2
caller=0x687BB2
off=va2off(caller)
print("\n-- around caller 0x687BB2 --")
for ins in md.disasm(data[off-16:off+16], caller-16):
    mark=' <== CALL SITE' if ins.address==caller else ''
    print(hex(ins.address), ins.mnemonic, ins.op_str, mark)
