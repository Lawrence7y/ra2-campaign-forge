import json,os
E=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10-K2\EVIDENCE'
with open(os.path.join(E,'t2_final_slots.json'),encoding='utf-8') as f: j=json.load(f)
slots=j['slots']
L=['| 槽 | disp | Mission(派发映射) | 有实现的类:地址 | 全桩? | 分级 |',
   '|---|---|---|---|---|---|']
for s in range(129,157):
    d=slots[str(s)]
    ms=';'.join('%d:%s'%(i,n) for i,n in d['missions']) if d['missions'] else '-'
    impls=','.join(d['impls']) if d['impls'] else '(全桩: '+','.join(d['stubs'][:2])+')'
    grade='[已证]' if d['missions'] else '[未证]'
    L.append('| v[%d] | 0x%X | %s | %s | %s | %s |'%(s,4*s,ms,impls,'YES' if d['all_stub'] else 'no',grade))
with open(os.path.join(E,'slot_table.md'),'w',encoding='utf-8') as f:
    f.write('\n'.join(L)+'\n')
print('wrote',len(L),'lines UTF-8')
