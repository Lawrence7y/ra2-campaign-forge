"""V1 probe Q: read the score-table numeric cells with the SAME 5x9 digit library that
was used for the time field (probes H/I), by building the mask from measured colour.

Step 1: dump the actual RGB values inside a known digit cell (time field) and inside the
table body, to pick a defensible 'bright text' predicate rather than guessing one.
Step 2: column-run segmentation of the table rows, bbox-normalised sig -> digit label.
"""
import os
import numpy as np
from PIL import Image

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"

for rel, box, tag in [
        ("l3_20261023r/measure_w2_end_x.png", (524, 127, 529, 136), "time last digit (known 6)"),
        ("l3_20261023r/measure_w2_end_x.png", (344, 194, 370, 210), "row1 col3 area"),
        ("l3_20261023r/measure_w2_end_x.png", (495, 194, 529, 210), "row1 score area"),
        ("l3_20261023r/measure_w2_end_x.png", (99, 194, 200, 210), "row1 name area"),
        ("archive_T33/measure_w1_end_x.png", (344, 194, 370, 210), "T33 row1 col3"),
        ("archive_T33/measure_w1_end_x.png", (495, 194, 529, 210), "T33 row1 score"),
        ("archive_T33/measure_w1_end_x.png", (344, 233, 370, 249), "T33 row2 col3"),
]:
    a = np.asarray(Image.open(ROOT + "/" + rel).convert("RGB"))
    x0, y0, x1, y1 = box
    sub = a[y0:y1, x0:x1]
    print("== %s  %s  box=%s" % (rel, tag, box))
    print("   min=%s max=%s mean=%s" % (sub.reshape(-1, 3).min(0), sub.reshape(-1, 3).max(0),
                                        np.round(sub.reshape(-1, 3).mean(0), 1)))
    vals, cnts = np.unique(sub.reshape(-1, 3), axis=0, return_counts=True)
    order = np.argsort(-cnts)[:8]
    for i in order:
        print("     colour %s x%d" % (vals[i], cnts[i]))
