import os, time, sys
from datetime import datetime
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
ROOTS = {
  'ZCode': r'C:\Users\Administrator\.zcode\cli\artifacts',
  'Antigravity': r'C:\Users\Administrator\.gemini\antigravity',
  'MiMo-roam': r'C:\Users\Administrator\AppData\Roaming\Xiaomi MiMo',
}
KEYS = ['v1.6.0','minimap_re_report','offsets_report','Hook_RadarPlot_Proxy','Hook_Building_Draw',
        'building_fog_residual','gap_generator_spysat','s_minimapForceRefresh','v1.5.9']
CUT = time.time() - 3*3600
rows = {}
for host, root in ROOTS.items():
    if not os.path.isdir(root): continue
    for base, dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(base, f)
            try: st = os.stat(p)
            except OSError: continue
            if st.st_mtime < CUT or st.st_size > 30*1024*1024: continue
            if os.path.splitext(f)[1].lower() not in ('.json','.jsonl','.txt','.log','.md'): continue
            try: data = open(p,'rb').read().decode('utf-8','ignore')
            except OSError: continue
            sess = os.path.basename(os.path.dirname(p))[:44]
            for k in KEYS:
                if k in data:
                    key=(host,sess,k); rows[key]=max(rows.get(key,0), st.st_mtime)
print(f"{'时间':<9} {'host':<12} {'会话':<46} 关键词")
print('-'*100)
for (host,sess,k),m in sorted(rows.items(), key=lambda x:(x[0][0], x[1])):
    print(f"{datetime.fromtimestamp(m):%H:%M:%S} {host:<12} {sess:<46} {k}")