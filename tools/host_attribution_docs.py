import os, time, sys
from datetime import datetime
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass
ROOTS = {
  'ZCode': r'C:\Users\Administrator\.zcode\cli\artifacts',
  'Antigravity': r'C:\Users\Administrator\.gemini\antigravity',
  'MiMo-roam': r'C:\Users\Administrator\AppData\Roaming\Xiaomi MiMo',
  'MiMo-app': r'D:\mimo',
}
# 带 .md 的写入路径特征串，用于判定"谁写的这份文档"
KEYS = ['docs/re/vxl_render_sort.md','docs/re/bullet_particle_fog_deep_dive.md',
        'docs/re/pathfinding_deep_dive.md','docs/re/dirty_rect_deep_dive.md',
        'REVERSE_ENGINEERING_AND_PATCHES.md','docs/RE_COORDINATION.md']
CUT = time.time() - 5*3600
hits = []
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
            sess = os.path.basename(os.path.dirname(p))
            for k in KEYS:
                if k in data:
                    hits.append((st.st_mtime, host, sess[:46], k))
print(f"{'时间':<9} {'host':<12} {'会话':<48} 文档")
print('-'*104)
seen=set()
for m, host, sess, k in sorted(hits, key=lambda x: x[0]):
    key=(host,sess,k)
    if key in seen: continue
    seen.add(key)
    print(f"{datetime.fromtimestamp(m):%H:%M:%S} {host:<12} {sess:<48} {k}")