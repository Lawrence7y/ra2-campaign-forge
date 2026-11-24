import re
d=open(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe",'rb').read()
locs=[m.start() for m in re.finditer(rb'\.\?[A-Z]',d)]
print('count',len(locs),'first offsets',[hex(x) for x in locs[:10]])
for x in locs[:5]:print(hex(x),d[x:x+60])
