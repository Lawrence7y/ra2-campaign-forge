import os, time, sys
from datetime import datetime
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

ROOTS = {
  'ZCode':       r'C:\Users\Administrator\.zcode\cli\artifacts',
  'Antigravity': r'C:\Users\Administrator\.gemini\antigravity',
  'MiMo-roam':   r'C:\Users\Administrator\AppData\Roaming\Xiaomi MiMo',
  'MiMo-app':    r'D:\mimo',
}
KEYS = ['vxl_render_sort','bullet_particle_fog','pathfinding_deep_dive','dirty_rect_deep_dive',
        'gap_spysat','net_sync','blitter_hooks','ra2render.h','HOOK_POINT','RE_COORDINATION']
CUT = time.time() - 4*3600
rows = {}
for host, root in ROOTS.items():
    if not os.path.isdir(root):
        continue
    for base, dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(base, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            if st.st_mtime < CUT or st.st_size > 30*1024*1024:
                continue
            if os.path.splitext(f)[1].lower() not in ('.json','.jsonl','.txt','.log','.md'):
                continue
            try:
                data = open(p, 'rb').read().decode('utf-8', 'ignore')
            except OSError:
                continue
            # 会话目录名（去掉 call_ 文件名），用于区分主会话/subagent
            sess = os.path.basename(os.path.dirname(p))
            if sess.startswith('sess'):
                pass
            elif 'brain' in base:
                sess = base.split('antigravity')[-1][:60]
            for k in KEYS:
                if k in data:
                    key = (host, sess, k)
                    rows[key] = max(rows.get(key, 0), st.st_mtime)

print(f"{'host':<12} {'会话/subagent':<52} {'关键词':<24} 最后命中")
print('-'*104)
for (host, sess, k), m in sorted(rows.items(), key=lambda x: (x[0][0], -x[1])):
    print(f"{host:<12} {sess[:50]:<52} {k:<24} {datetime.fromtimestamp(m):%H:%M:%S}")