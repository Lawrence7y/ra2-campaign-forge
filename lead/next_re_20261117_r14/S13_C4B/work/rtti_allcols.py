import pathlib,struct,json
import pefile
root=pathlib.Path(r"D:\Project\ra2-campaign-forge"); pe=pefile.PE(str(root/"ra2youli"/"gamemd.exe"),fast_load=False); ib=pe.OPTIONAL_HEADER.ImageBase; data=pe.__data__
def ro(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def u(va):
 o=ro(va-ib);return None if o is None else struct.unpack_from('<I',data,o)[0]
def c(va,n=200):
 o=ro(va-ib,1)
 if o is None:return None
 b=data[o:o+n];z=b.find(b'\x00')
 if z<0:return None
 try:return b[:z].decode('ascii')
 except:return None
ch=[]
cl=root/"lead"/"next_re_20261117_r14"/"SURVEY_D39"/"EVIDENCE"/"classification.tsv"
for ln in cl.read_text(encoding='utf-8').splitlines()[1:]:
 a=ln.split(chr(9))
 if len(a)>8 and a[1]=='S13' and a[2]=='C4':
  e=int(a[0],16); col=u(0x7e48d4-4)
  ch.append((a[0],a[4],a[8]))
print(' | '.join(map(str,ch[:5])))
# For selected entries, find all COL values via RTTI scan into TD where TD+8 name exists, then see if any table slot points to entry at plausible vt offset
selected={0x468670,0x629fd0,0x62a260}
cols={}
for va in range(0x7e1000,0x812000,4):
 x=u(va)
 if not x or not(0x7e1000<=x<0x812000):continue
 td=u(x+0xc)
 if not td or not(0x7e1000<=td<0x812000):continue
 nm=c(td+8)
 if nm and nm.startswith('.?AV'):cols[x]=(hex(va),hex(td),nm)
print('cols',len(cols))
for e in selected:
 hits=[]
 for col,(va,td,nm) in cols.items():
  # scan 0..512 after COL for slot equal e
  for off in range(0,0x400,4):
   if u(col+off)==e:
    vt=col+off
    hits.append((hex(vt),hex(col),hex(off),nm))
    break
 print(hex(e),hits[:10],len(hits))
