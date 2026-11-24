from pehelp import *
import struct
tlo,thi=text_bounds()
target=0x485020

# Channel 1: capstone-linear E8 rel32 scan
c1=[]
for va in range(tlo,thi):
    if u8(va)!=0xE8: continue
    b=read(va,5)
    if len(b)<5: continue
    t=va+5+struct.unpack('<i',b[1:5])[0]
    if t==target: c1.append(va)

# Channel 2: raw byte scan for E8 <rel32 computed from each E8 occurrence>
c2=[]
data=pe.get_data(*[s for s in []]) if False else None
# raw find all E8 bytes then check rel
raw_all=pe.get_data(SECTIONS[0][2], SECTIONS[0][3])  # .text raw
v0=SECTIONS[0][0]
for i,b in enumerate(raw_all):
    if b!=0xE8: continue
    if i+5>len(raw_all): break
    rel=struct.unpack_from('<i',raw_all,i+1)[0]
    va=v0+i
    if va+5+rel==target: c2.append(va)

print(f"Channel1 (capstone E8 rel32): {len(c1)} callers -> {[hex(x) for x in c1]}")
print(f"Channel2 (raw E8 rel32):      {len(c2)} callers -> {[hex(x) for x in c2]}")
print("match:", set(c1)==set(c2))

# also FF /15 indirect? (not relevant for direct call)
# context for each caller
for va in c1:
    print(f"\n--- caller context {va:#x} ---")
    for ins in disasm(max(tlo,va-30), 44, count=14):
        mark=' <<<' if ins.address==va else ''
        print("   ",fmt(ins),mark)
