#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-KA 辅助 PNG 分析：只判「有无配对无-ghost 基线」，不据颜色下机制结论。"""
import os, json
from PIL import Image, ImageChops, ImageStat

EV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-J\EVIDENCE"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177_KA\EVIDENCE\ka_png_aux.txt"
P=[]
def p(s=''):
    P.append(str(s)); print(s)
files = ['j_menu_check.png','j_sk_setup.png','j_ingame.png','j_ghost_picked.png','j_hover_anchor.png','j_after_click.png']
ims = {}
for fn in files:
    f = os.path.join(EV, fn)
    im = Image.open(f).convert('RGB')
    ims[fn] = im
    p(f'{fn}: size={im.size} bytes={os.stat(f).st_size}')
# target area based on closed-loop anchor (113,62) at screen (1441,697), JY=(-55.6,25.9)
# footprint X[hover-1..hover+1], Y[hover..hover+1] => generous screen box
BOX = (1330, 640, 1550, 760)
p(f'target screen BOX={BOX} (derived from j_run.closed_loop.it2 screen [1441,697] hover_cell [113,62], JY=(-55.6,25.9))')

def stats(im, box):
    crop = im.crop(box)
    px = list(crop.getdata())
    n = len(px)
    green = sum(1 for r,g,b in px if g > r+25 and g > b+25 and g > 60)
    red = sum(1 for r,g,b in px if r > g+40 and r > b+40 and r > 70)
    bright = sum(1 for r,g,b in px if r+g+b > 480)
    st = ImageStat.Stat(crop)
    return {'n':n, 'green':green, 'red':red, 'bright':bright,
            'green_ratio':round(green/n,4), 'red_ratio':round(red/n,4),
            'mean':[round(x,1) for x in st.mean]}
for fn in files:
    p(f'{fn} target box stats: {json.dumps(stats(ims[fn], BOX))}')

# Pairwise same-box absolute difference, to test if j_ingame (no ghost) is a valid paired baseline
base = ims['j_ingame.png'].crop(BOX)
for fn in ['j_ghost_picked.png','j_hover_anchor.png','j_after_click.png']:
    d = ImageChops.difference(base, ims[fn].crop(BOX))
    st = ImageStat.Stat(d)
    changed = sum(1 for px in d.getdata() if max(px) > 12)
    p(f'diff j_ingame vs {fn} in BOX: mean={[round(x,1) for x in st.mean]} changed_px(>12)={changed}/{base.width*base.height} ({changed/(base.width*base.height):.3f})')
# whole-image diff coarse
for fn in ['j_ghost_picked.png','j_hover_anchor.png','j_after_click.png']:
    d = ImageChops.difference(ims['j_ingame.png'], ims[fn])
    st = ImageStat.Stat(d)
    p(f'whole-image diff j_ingame vs {fn}: mean={[round(x,1) for x in st.mean]}')
p('NOTE: j_ingame is no-ghost but taken BEFORE order/pickup; no same-frame no-ghost paired baseline exists for hover/click screenshots. Color judgement is AUX only.')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT,'w',encoding='utf-8').write('\n'.join(P)+'\n')
print('saved', OUT)
