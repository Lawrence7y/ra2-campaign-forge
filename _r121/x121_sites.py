import sys, json, struct
sys.path.insert(0, '_r121')
from x121lib import PE

TARGET = 0x7f7c80
pe = PE('ra2bench/gamemd.exe')
ts = next(s for s in pe.sections if s['name'] == '.text')
start = ts['raw']
end = ts['raw'] + ts['vsize']
data = pe.buf

pat = b'\x68' + struct.pack('<I', TARGET)
sites = []
i = start
while True:
    j = data.find(pat, i, end)
    if j < 0:
        break
    sites.append(pe.image_base + ts['va'] + (j - ts['raw']))
    i = j + 1

print('sites', len(sites))
print([hex(x) for x in sites])

# reverse control 5a: imm = TARGET+1
pat_a = b'\x68' + struct.pack('<I', TARGET + 1)
sa = []
i = start
while True:
    j = data.find(pat_a, i, end)
    if j < 0:
        break
    sa.append(hex(pe.image_base + ts['va'] + (j - ts['raw'])))
    i = j + 1
print('ctrl5a', len(sa), sa)

# reverse control 5b: start at site+1
sb = 0
for s in sites:
    o = pe.off_va(s + 1)
    if data[o] == 0x68:
        sb += 1
print('ctrl5b', sb)

res = dict(target=hex(TARGET), section=ts, sites=[hex(x) for x in sites], count=len(sites),
           ctrl_5a=dict(imm=hex(TARGET + 1), count=len(sa), addrs=sa),
           ctrl_5b=dict(count=sb))
json.dump(res, open('_r121/x121exec_q1_sites.json', 'w'), indent=1)
