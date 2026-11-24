
import sys,json,struct
secs=json.load(open(sys.argv[1])); exe=open(sys.argv[2],'rb').read()
def off(va):
 rva=va-0x400000
 for s in secs:
  if s['va']<=rva<s['va']+max(s['vs'],s['rs']): return s['raw']+rva-s['va']
targets=[int(x,16) for x in sys.argv[3:]]
# scan dwords across image where value == target (little endian)
for t in targets:
 hits=[]
 needle=struct.pack('<I',t)
 start=0
 while True:
  k=exe.find(needle,start)
  if k<0: break
  va=k+0x400000
  # map fileoff -> va precisely
  for s in secs:
   if s['raw']<=k<s['raw']+s['rs']:
    va=s['va']+(k-s['raw'])+0x400000; break
  hits.append(va); start=k+1
 print('0x%08X refs=%d %s'%(t,len(hits),' '.join('0x%X'%h for h in hits[:60])))
 # group into vtable candidates: refs in .rdata
 print('  rdata:', ' '.join('0x%X'%h for h in hits if 0x7E0000<=h<0x830000)[:1000])
