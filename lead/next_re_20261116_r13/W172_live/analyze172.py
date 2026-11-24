import json, statistics as st
rows=[json.loads(l) for l in open('EVIDENCE/eip_buckets_90s.ndjson',encoding='utf-8')]
print('samples=%d  span=%.1fs' % (len(rows), rows[-1]['t']))
print()
print('%-6s %8s %7s %7s %8s %7s %7s %7s %8s' % ('#','t','frame','obj','lc','loco','tgt','moving','cpu_ms'))
for k,r in enumerate(rows[::15]):
    print('%-6d %8.1f %7s %7s %8s %7s %7s %7s %8.0f' % (k*15, r['t'], r['frame'], r['objects'], r['lc_count'], r['with_loco'], r['has_target'], r['moving'], r['cpu_ms'] or 0))
print()
for k in ('frame','objects','lc_count','with_loco','has_target','moving','bullets'):
    v=[r[k] for r in rows if r[k] is not None]
    if v: print('  %-10s min %-4d med %-6.1f max %-4d' % (k,min(v),st.median(v),max(v)))
print()
# 帧时间与 CPU
st_rows=[r for r in rows if r.get('cpu_ms') and r.get('frame') is not None]
if len(st_rows)>2:
    dframe=st_rows[-1]['frame']-st_rows[0]['frame']
    dms=st_rows[-1]['t']-st_rows[0]['t']
    dcpu=st_rows[-1]['cpu_ms']-st_rows[0]['cpu_ms']
    print('  墙钟 %.3f ms/帧 ; CPU %.3f ms/帧 ; duty %.3f' % (1000*dms/dframe, dcpu/dframe, dcpu/(1000*dms)))
    print('  ⇒ cpu/moving = %.4f ms' % (dcpu/dframe/st.median([r['moving'] for r in rows])))
