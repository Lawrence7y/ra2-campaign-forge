import json, collections, sys
scan = sys.argv[1]
items = json.load(open(scan, encoding='utf-8'))
if isinstance(items, dict):
    items = items.get('findings', [])
c = collections.Counter()
reah = []
BS = chr(92)
for x in items:
    p = (x.get('file') or x.get('path') or '').replace(BS, '/')
    c[p.split('/')[0]] += 1
    if p.startswith('re_atlas'):
        reah.append((x.get('rule') or x.get('id'), p))
print('total:', len(items))
print(dict(c))
print('re_atlas hits:', reah)
