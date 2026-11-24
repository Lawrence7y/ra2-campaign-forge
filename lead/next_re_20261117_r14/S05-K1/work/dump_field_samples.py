import json, os
ROOT=os.path.join('D:',os.sep,'Project','ra2-campaign-forge')
P=os.path.join(ROOT,'lead','next_re_20261117_r14','S05-K1','EVIDENCE','field_access_scan.json')
d=json.load(open(P))
OUT=os.path.join(ROOT,'lead','next_re_20261117_r14','S05-K1','work','field_samples.txt')
with open(OUT,'w',encoding='utf-8') as o:
    for off,f in d['fields'].items():
        o.write('=== field %s focus=%s note=%s ===\n'%(off,f['focus'],f['note']))
        o.write('total_w=%d total_r=%d attrib_w=%d attrib_r=%d\n'%(f['total_writes'],f['total_reads'],f['attributed_writes'],f['attributed_reads']))
        o.write('class_w=%s\n'%repr(f['class_write_hist'][:8]))
        o.write('class_r=%s\n'%repr(f['class_read_hist'][:8]))
        o.write('write funcs: %s\n'%repr([(('%08X'%x) if x else None,c) for x,c in f['write_funcs'][:10]]))
        o.write('focus write samples:\n')
        for r in f['focus_write_samples'][:8]:
            o.write('  %08X %-8s %-34s base=%s func=%s cls=%s\n'%(r['va'],r['mn'],r['op'][:34],r['base'],('%08X'%r['func']) if r['func'] else None,r['classes']))
        o.write('focus read samples:\n')
        for r in f['focus_read_samples'][:8]:
            o.write('  %08X %-8s %-34s base=%s func=%s cls=%s\n'%(r['va'],r['mn'],r['op'][:34],r['base'],('%08X'%r['func']) if r['func'] else None,r['classes']))
        o.write('\n')
print('wrote',OUT)
