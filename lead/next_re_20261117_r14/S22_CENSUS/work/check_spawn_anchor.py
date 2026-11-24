import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for e in [0x6B7F10,0x6B8120,0x6B6EA0,0x6B6C90]:
 print(hex(e),'in slot_to_members?',e in slot_to_members)
 if e in slot_to_members: print(slot_to_members[e])
 print('  source row', [r for r in targets if int(r[0],16)==e][:1])
