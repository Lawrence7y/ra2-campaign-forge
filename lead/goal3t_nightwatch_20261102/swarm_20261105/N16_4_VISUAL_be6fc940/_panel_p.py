# -*- coding: utf-8 -*-
# N16-4 auxiliary: recompute panel p for the 25+2 end screenshots using the ruling's PC formula.
# p is NOT used to classify; classification comes from direct visual opening of each file.
import glob, os

BASE = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
PANEL = (85, 108, 630, 275)

from PIL import Image

def panel_p(path):
    im = Image.open(path)
    c = im.convert('RGB').crop(PANEL)
    px = list(c.getdata())
    n = len(px)
    hit = sum(1 for r, g, b in px if b > r + 18 and b > g + 10 and 40 <= b <= 190 and r < 150)
    return hit / n if n else 0.0

files = sorted(glob.glob(os.path.join(BASE, '*', 'measure_w*_end_x.png'))) + \
        sorted(glob.glob(os.path.join(BASE, 'measure_w*_end_x.png')))
for p in files:
    rel = os.path.relpath(p, BASE).replace('\\', '/')
    print('%.6f  %s' % (panel_p(p), rel))
