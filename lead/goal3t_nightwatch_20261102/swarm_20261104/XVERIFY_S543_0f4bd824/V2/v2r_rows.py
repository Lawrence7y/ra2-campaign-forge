"""High-zoom crops of just the two data rows of the l3_20261023r score table (and of archive_T33's),
no annotation text overlapping, for an unambiguous read of 摧毁数/损失数/建造数/分数."""
import os
from PIL import Image

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"

for rel, tag, rows in (("l3_20261023r/measure_w2_end_x.png", "l3r", [(189, 223), (225, 274)]),
                       ("archive_T33/measure_w1_end_x.png", "T33", [(189, 223), (225, 274)])):
    im = Image.open(os.path.join(R, rel.replace("/", os.sep))).convert("RGB")
    for i, (y0, y1) in enumerate(rows):
        crop = im.crop((95, y0 - 2, 545, y1 + 2))
        big = crop.resize((crop.width * 6, crop.height * 6), Image.LANCZOS)
        p = os.path.join(OUT, f"row_{tag}_{i}.png")
        big.save(p)
        print("[ROW]", p, big.size)
    # numeric columns only, x 150..545
    crop = im.crop((150, 186, 545, 276))
    big = crop.resize((crop.width * 6, crop.height * 6), Image.LANCZOS)
    p = os.path.join(OUT, f"nums_{tag}.png")
    big.save(p)
    print("[NUM]", p, big.size)
