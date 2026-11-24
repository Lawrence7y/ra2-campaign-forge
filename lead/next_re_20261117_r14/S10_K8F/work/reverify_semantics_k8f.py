"""Independent K8F byte-level recheck of the two disputed queue rules.
Read-only target; Python 3.12 + capstone 5.0.7(skipdata=True) + pefile.
"""
import hashlib
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
pe = pefile.PE(EXE, fast_load=True)
data = open(EXE, "rb").read()
base = pe.OPTIONAL_HEADER.ImageBase
assert hashlib.sha256(data).hexdigest().upper() == EXPECT

def off(va):
    return pe.get_offset_from_rva(va - base)

def u8(va):
    return data[off(va)]

def u32(va):
    return struct.unpack_from("<I", data, off(va))[0]

def zero_indexes(table):
    return [i + 4 for i in range(28) if u8(table + i) == 0]

outer = zero_indexes(0x41BAEC)
inner = zero_indexes(0x41BB10)
assert outer == inner == [4, 26, 27, 30, 31]
assert u32(0x41BAE4) == 0x41BAB2 and u32(0x41BAE4 + 4) == 0x41BAD3
assert u32(0x41BB08) == 0x41BAD3 and u32(0x41BB08 + 4) == 0x41BADE
# 0041BAC2: cmp eax,0x1b / ja 0041BADE; inner table index 0 is CALL, index 1 is DROP.
assert data[off(0x41BABF):off(0x41BACC)] == bytes.fromhex("83f81b771a33d28a9010bb4100")
# 005B3601: if cur==id, queued==id OR queued==-1 branches to 005B3621 (no write).
assert data[off(0x5B3601):off(0x5B3614)] == bytes.fromhex(
    "3bc8750f8b8eb40000003bc8741283f9ff740d"
)
# 0041B870: cur==0x1E jumps over the +0x6D2 clear.
assert data[off(0x41B870):off(0x41B880)] == bytes.fromhex(
    "83b9ac0000001e7407c681d206000000"
)

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
print("EXE_SHA256=" + EXPECT)
print("OUTER_ZERO_INDEX=" + repr(outer))
print("INNER_ZERO_INDEX=" + repr(inner))
print("OUTER_TARGETS=" + repr([f"{u32(0x41BAE4+4*i):08X}" for i in range(2)]))
print("INNER_TARGETS=" + repr([f"{u32(0x41BB08+4*i):08X}" for i in range(2)]))
print("INNER_INDEX_0=0041BAD3_CALL_005B35E0; INNER_INDEX_1=0041BADE_SWALLOW")
print("SWALLOW_RULE=cur in {4,26,27,30,31} AND [this+0x294]==0 AND id not in {4,26,27,30,31}")
print("ROW_IDS=1,2,15 ALL_OUTSIDE_DROP=True")
print("EARLY_RULE_4=cur==id AND queued in {id,-1}  # queued=[this+0xB4]")
print("CUR30_RULE=cur==0x1E skips clearing [this+0x6D2] before 005B3570")
print("\nDISASM 0041BAB2..0041BAE1")
for i in md.disasm(data[off(0x41BAB2):off(0x41BAE2)], 0x41BAB2):
    print(f"  {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}")
print("\nDISASM 005B35E0..005B3642")
for i in md.disasm(data[off(0x5B35E0):off(0x5B3643)], 0x5B35E0):
    print(f"  {i.address:08X}  {i.bytes.hex():<20} {i.mnemonic} {i.op_str}")
