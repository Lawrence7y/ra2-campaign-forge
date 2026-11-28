import struct
P='ra2bench/gamemd.exe'; data=open(P,'rb').read()
SEC=[('text',0x401000,0x1000,0x3e0000),('rdata',0x7e1000,0x3e1000,0x31000),
     ('data',0x812000,0x412000,0x6c000),('rsrc',0xb7a000,0x47e000,0x19000),('detour',0xb93000,0x497000,0x3000)]
fails=[]
def chk(n,c,d=''):
    print(('PASS' if c else 'FAIL'), n, d)
    if not c: fails.append(n)
BAND=(0x7c6000,0x7c6800)
KEY={'0x7c6270':'reset8','0x7c62ac':'unpacker','0x7c6620':'gridchk','0x7c6730':'reset4',
 '0x7c6752':'blk1_disp','0x7c6808':'blk1_dec'}
# scan every aligned dword in every section for values inside the band
hits=[]
for nm,va,off,rsz in SEC:
    n=rsz//4
    for k in range(n):
        v=struct.unpack('<I',data[off+4*k:off+4*k+4])[0]
        if BAND[0]<=v<BAND[1]:
            hits.append((nm, va+4*k, v))
print("=== aligned dword values inside [0x7c6000,0x7c6800) anywhere in image: %d ===" % len(hits))
for nm,a,v in sorted(hits,key=lambda x:x[1]):
    print("  %-6s @0x%x -> 0x%x"%(nm,a,v))
vals=set(v for _,_,v in hits)
print()
for k,lab in KEY.items():
    a=int(k,16)
    print("  %-8s %-10s pointed-to-by-data=%s"%(k,lab,a in vals))
chk('I1 blk1_dispatcher 0x7c6752 has no data pointer', 0x7c6752 not in vals)
chk('I2 blk1_decoder 0x7c6808 has no data pointer', 0x7c6808 not in vals)
chk('I3 0x7c6620 has no data pointer', 0x7c6620 not in vals)
chk('I4 0x7c62ac has no data pointer', 0x7c62ac not in vals)
chk('I5 0x7c6270 has no data pointer', 0x7c6270 not in vals)
chk('I6 0x7c6730 has no data pointer', 0x7c6730 not in vals)
chk('I7 at least one band pointer exists (positive control on the scan)', len(hits)>0, "%d hits"%len(hits))
print("FAILS",len(fails),fails)
