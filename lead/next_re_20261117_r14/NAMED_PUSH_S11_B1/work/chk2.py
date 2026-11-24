import json
v=json.load(open('vtables2.json',encoding='utf-8'))
for c,lst in v.items():
    offs=sorted(set(e['col_offset'] for e in lst))
    print('%-28s offsets=%s  tables=%d' % (c, offs, len([e for e in lst if e.get('slot0')])))
