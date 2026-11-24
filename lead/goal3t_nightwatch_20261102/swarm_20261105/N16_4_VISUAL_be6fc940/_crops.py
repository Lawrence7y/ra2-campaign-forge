# -*- coding: utf-8 -*-
# N16-4: crop + upscale the score-table region of each score-screen screenshot for cell-by-cell re-read.
from PIL import Image
import os

BASE = r'D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip'
OUT = r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261105/N16_4_VISUAL_be6fc940/crops'
os.makedirs(OUT, exist_ok=True)

targets = [
    ('archive_T33', 1), ('archive_T33', 2),
    ('archive_T34', 1), ('archive_T34', 2),
    ('archive_T36', 1), ('archive_T36', 2),
    ('archive_T38', 1), ('archive_T38', 2),
    ('archive_T39', 2),
    ('archive_T40', 1), ('archive_T40', 2),
    ('archive_T41', 1), ('archive_T41', 2),
    ('archive_T42', 1), ('archive_T42', 2),
    ('archive_T43', 1), ('archive_T43', 2),
    ('archive_T44', 1), ('archive_T44', 2),
    ('archive_T45', 1), ('archive_T45', 2),
    ('archive_T49_u0800', 1), ('archive_T49_u0800', 2),
    ('l1_20261023e4', 2),
    ('l3_20261023r', 2),
    ('ROOT', 1), ('ROOT', 2),
]

# table region in 800x600 screen
BOX = (85, 108, 545, 245)
for sub, w in targets:
    if sub == 'ROOT':
        src = os.path.join(BASE, 'measure_w%d_end_x.png' % w)
    else:
        src = os.path.join(BASE, sub, 'measure_w%d_end_x.png' % w)
    im = Image.open(src).convert('RGB')
    c = im.crop(BOX)
    c = c.resize((c.width * 3, c.height * 3), Image.LANCZOS)
    name = ('%s_w%d_table.png' % (sub, w)).replace('archive_', '')
    c.save(os.path.join(OUT, name))
    print('saved', name)
