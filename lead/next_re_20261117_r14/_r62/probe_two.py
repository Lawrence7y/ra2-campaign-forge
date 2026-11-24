import io, os, json, collections

ROOT = r'D:\Project\ra2-campaign-forge'
targets = ['sweep.json', 'e8_sites_audit.json']
for bn in targets:
    ap = None
    for dp, _, fs in os.walk(os.path.join(ROOT, 'lead')):
        if bn in fs:
            ap = os.path.join(dp, bn); break
    print('=' * 78)
    if not ap:
        print('%s NOT FOUND' % bn); continue
    print('%s' % ap.replace(ROOT + '\\', ''))
    print('bytes =', os.path.getsize(ap))
    try:
        d = json.load(io.open(ap, encoding='utf-8', errors='replace'))
    except Exception as e:
        print('  JSON parse FAIL: %s' % str(e)[:80]); continue
    if isinstance(d, dict):
        print('  顶层 dict, keys =', list(d.keys()))
        for k, v in d.items():
            t = type(v).__name__
            n = len(v) if hasattr(v, '__len__') else '-'
            print('    %r : %s len=%s' % (k, t, n))
            if isinstance(v, dict):
                ks = list(v.keys())[:2]
                print('       前2键: %r' % ks)
                for kk in ks:
                    print('         [%r] -> %r' % (kk, str(v[kk])[:120]))
            elif isinstance(v, list) and v:
                print('       前2元素: %r' % (v[:2],))
    elif isinstance(d, list):
        print('  顶层 list, len = %d' % len(d))
        print('  首 2 元素: %r' % (d[:2],))
        ts = collections.Counter(type(x).__name__ for x in d)
        print('  元素类型: %s' % dict(ts))
    print()
