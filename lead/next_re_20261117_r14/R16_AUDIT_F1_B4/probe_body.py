# -*- coding: utf-8 -*-
"""核对 10 行 in-body 写点确实落在本 entry 的 atlas 体内（打印 size / 偏移 / 下一个函数起点）。"""
import io, os, sys, json, bisect
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify as V

sizes = V.load_atlas()
ranges = V.body_ranges(sizes)

d = json.load(io.open(os.path.join(V.HERE, 'verify_out.json'), encoding='utf-8'))
print('entry     size   next_start  in-body-site  offset  below_next  atlas_reported')
for r in d['rows']:
    if r['C2b']['n_in_entry_body'] == 0:
        continue
    e = int(r['entry'], 16)
    sz = sizes.get(r['entry'])
    i = bisect.bisect_right(ranges, (e, 1 << 62)) - 1
    nxt = ranges[i + 1][0] if i + 1 < len(ranges) else None
    for w in r['C2b']['in_entry_body']:
        s = int(w['site'], 16)
        print('%-9s %-6s %-11s %-13s %-7d %-11s %s'
              % (r['entry'], hex(sz), ('%08X' % nxt) if nxt else '-', w['site'],
                 s - e, s < (nxt or 1 << 32), w['func']))
