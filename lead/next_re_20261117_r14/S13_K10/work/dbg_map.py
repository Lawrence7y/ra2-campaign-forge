
import json,re,sys
cfg=json.load(open(sys.argv[1],encoding='utf8'))
entries=set(int(x,16) for x in cfg['entries'])
m={}
for line in open(cfg['map'],encoding='utf8'):
  mm=re.match(r'([0-9A-F]{8}) ([0-9A-F]{8}) .* VT=([0-9A-F]{8}) SLOT=(\d+)',line.strip())
  if mm:
    sa,ea,vt,sl=mm.groups()
    if int(ea,16) in entries: m[(int(vt,16),int(sl))]=int(ea,16)
print("map size:",len(m))
print("(0x7e17ec,2):", hex(m.get((0x7e17ec,2),0)))
print("(0x7e17cc,3):", hex(m.get((0x7e17cc,3),0)))
