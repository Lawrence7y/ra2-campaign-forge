import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
exec(open(r'D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S22_CENSUS/work/explore_channels.py',encoding='utf-8').read().split("print('channel hits:'")[0])
for row in targets:
 if 'SpawnManager' in row[2] or '006B7F' in row[0] or '006B81' in row[0] or row[2].endswith('SpawnManagerClass') or 'SpawnManagerClass::' in row[2]:
  e=int(row[0],16)
  print(row[0],row[1],row[2],row[4], 'A1='+str(len(slot_to_members.get(e,[]))))
  print('  covsem',row[3][:120])
