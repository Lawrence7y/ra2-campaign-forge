import io, os, json, collections

ROOT = r'D:\Project\ra2-campaign-forge'
bn = 'mesh_imm32.json'
ap = None
for dp, _, fs in os.walk(os.path.join(ROOT, 'lead')):
    if bn in fs:
        ap = os.path.join(dp, bn); break
assert ap, 'not found'
print('file:', ap.replace(ROOT + '\\', ''))
print('bytes:', os.path.getsize(ap))

d = json.load(io.open(ap, encoding='utf-8', errors='replace'))
print('top keys:', list(d.keys()))
for k in d:
    v = d[k]
    print()
    print('=== key %r : type=%s' % (k, type(v).__name__))
    if isinstance(v, dict):
        print('  条目数 = %d' % len(v))
        ks = list(v.keys())[:5]
        print('  前 5 个键: %s' % ks)
        for kk in ks[:3]:
            print('    [%r] -> %r' % (kk, v[kk]))
    elif isinstance(v, list):
        print('  长度 = %d' % len(v))
        print('  前 3 元素: %r' % (v[:3],))
        ts = collections.Counter(type(x).__name__ for x in v)
        print('  元素类型分布: %s' % dict(ts))
        if v and isinstance(v[0], (list, dict)):
            print('  首元素明细: %r' % (v[0],))
