import pathlib,struct,csv
import pefile
root=pathlib.Path(r"D:\Project\ra2-campaign-forge")
pe=pefile.PE(str(root/"ra2youli"/"gamemd.exe"),fast_load=False);ib=pe.OPTIONAL_HEADER.ImageBase;data=pe.__data__
def ro(r,n=4):
 for s in pe.sections:
  if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData) and r+n<=s.VirtualAddress+s.SizeOfRawData:return s.PointerToRawData+(r-s.VirtualAddress)
def c(va,n=180):
 o=ro(va-ib,1)
 if o is None:return None
 b=data[o:o+n];z=b.find(b'\x00')
 if z<0:return None
 try:return b[:z].decode('ascii')
 except:return None
conf=root/"lead"/"next_re_20261117_r14"/"COVERAGE"/"CONFLICTS.tsv"
rows=[]
for ln in conf.read_text(encoding='utf-8',errors='replace').splitlines():
 a=ln.split(chr(9))
 if any(any(f'{e:08x}' in x.lower() for x in a) for e in [0x468670,0x629fd0,0x62a260]): rows.append(ln)
print('conflicts',*rows,sep='\n')
# collect literal strings referenced inside entries from scan_raw
raw=pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_C4B\work\scan_raw.json")
import json
j=json.loads(raw.read_text(encoding='utf-8'))
for e in ['00468670','00629FD0','0062A260']:
 d=next(x for x in j['rows'] if x['entry']==e)
 print('entry',e,'strings',d['strings'])
 for a,s in d['strings']:
  va=int(a,16); o=ro(va-ib,1); print(' ',a,hex(va),repr(data[o:o+64]))
