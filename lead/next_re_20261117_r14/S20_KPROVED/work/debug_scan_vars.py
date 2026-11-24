import runpy
g=runpy.run_path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\work\scan_s20.py')
print('VT_FOR_ENTRY',len(g['vt_for_entry']))
print('RTTI_TEST',g['rtti_at_vt']('007E1E2C'))
print('HITS',g['slot_hits'].get('0040EEC0',[])[:2])
print('NAME',g['name_by_va'].get('0040EEC0'))
