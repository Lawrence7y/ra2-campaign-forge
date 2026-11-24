#!/usr/bin/env python3
"""T2: verify hash function 0x4A1DE0 and CRC table; validate against langmd.mix."""
import sys, os, struct, zlib
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *

OUT = []
def p(s=""):
    line = str(s)
    OUT.append(line)
    try: print(line)
    except UnicodeEncodeError: print(line.encode('ascii','replace').decode())

p("=== CRC table @0x81F7B4 (first 8 of 256 u32) ===")
TBL_VA = 0x81F7B4
tbl = [u32(TBL_VA + 4*i) for i in range(256)]
for i in range(8):
    p(f"  [{i}] = 0x{tbl[i]:08X}")

p("\n=== disasm hash fn 0x4A1DE0 (up to ret, cap) ===")
for ins in dis(0x4A1DE0, 0x240, 200):
    p(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic:8} {ins.op_str}")
    if ins.mnemonic == 'ret' and ins.address > 0x4A1DE0+0x100:
        break

# --- reimplement VERDICT model & compare with zlib on real mix index ---
def crc_extended(name_bytes):
    """VERDICT model: reflected CRC32 over dword-padded buf with tail rule.
    buf must be a mutable bytearray; engine hashes dword words.
    Returns final u32 (with the NOT storage convention resolved)."""
    b = bytearray(name_bytes)
    L = len(b)
    r = L % 4
    if r:
        # engine buffer[esi+8..] holds the LAST r bytes (b[L-r..L-1]).
        # tail: buf[r]=r ; buf[r+1..3]=buf[0] (= b[L-r])
        b.extend(b'\x00'*(4-r))
        b[L] = r & 0xFF
        for j in range(L+1, L+4-r):
            b[j] = b[L-r]
    # standard reflected crc32: init FFFFFFFF, final xor FFFFFFFF
    c = 0xFFFFFFFF
    for byte in b:
        idx = (c ^ byte) & 0xFF
        c = (c >> 8) ^ tbl[idx]
    return (c ^ 0xFFFFFFFF) & 0xFFFFFFFF

# read langmd.mix header + index
mixpath = ROOT + r'\ra2youli\langmd.mix'
with open(mixpath, 'rb') as f:
    head = f.read(160)
p("\n=== langmd.mix first 64 bytes ===")
for i in range(0,64,16):
    p(f"  {i:04X}: {head[i:i+16].hex(' ')}")

# parse header: new style u16(0)+u16 flags+u16 num+u32 bodySize
v0, flags, num, bodysize = struct.unpack_from('<HHHI', head, 0)
p(f"\nnew-style parse: v0={v0} flags=0x{flags:04X} num={num} bodySize={bodysize}")
# index at offset 10
p("first 10 index entries (id, offset, size):")
entries=[]
for i in range(10):
    eid, off, sz = struct.unpack_from('<III', head, 10+i*12)
    entries.append((eid,off,sz))
    p(f"  #{i:02d} id=0x{eid:08X} off=0x{off:08X} size=0x{sz:08X}({sz})")

# known names from VERDICT (index positions)
known = {
  0:'KEYBOARDMD.INI', 2:'RA2MD.CSF', 6:'GLSMD.PAL',
  7:'CREDITSMD.TXT', 8:'AUDIOMD.MIX', 9:'CAMEOMD.MIX',
}
# VERDICT gave 8 names; positions uncertain for some; try all known names against all ids
allnames = ['KEYBOARDMD.INI','RA2MD.CSF','GLSMD.PAL','CREDITSMD.TXT',
            'AUDIOMD.MIX','CAMEOMD.MIX','GLSLMD.SHP','MISSIONSMD.PKT']
expect = {'KEYBOARDMD.INI':0x930BE675,'RA2MD.CSF':0xBD835079,'GLSMD.PAL':0x366CBDFB,
          'CREDITSMD.TXT':0x373A7BC1,'AUDIOMD.MIX':0xFE9DF3BE,'CAMEOMD.MIX':0x16A802B6,
          'GLSLMD.SHP':0xB11D7C29,'MISSIONSMD.PKT':0x480B82E4}
p("\n=== hash model validation (extended vs zlib.crc32(name.upper())) ===")
p(f"  {'name':<18} {'expected':>10} {'extended':>10} {'zlib':>10} {'model':>6}")
for nm in allnames:
    h_ext = crc_extended(nm.encode('ascii'))
    h_zlib = zlib.crc32(nm.encode('ascii')) & 0xFFFFFFFF
    ok = (h_ext == expect[nm])
    p(f"  {nm:<18} {expect[nm]:08X} {h_ext:08X} {h_zlib:08X} {'OK' if ok else 'XX'}")
ids = set(e[0] for e in entries)
p(f"\nextended hashes landing in langmd index (first 10): {sum(1 for nm in allnames if crc_extended(nm.encode()) in ids)}/8")

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T2_hash_mix.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T2_hash_mix.txt]")
