"""V1 probe C: crop and upscale regions so the 'time' field location is established from
pixels + visual inspection, NOT from the original document's asserted rectangle.

Reference set: l3_20261023r/w2 (claimed full score screen), archive_T33/w1 (claimed score),
archive_T42/w1 (claimed 'battle, no panel'), archive_T34/w1.
"""
import os
from PIL import Image

ROOT = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V1"

REFS = ["l3_20261023r/measure_w2_end_x.png",
        "archive_T33/measure_w1_end_x.png",
        "archive_T42/measure_w1_end_x.png",
        "archive_T34/measure_w1_end_x.png"]

# (name, box) boxes in full-image coords
REGIONS = [
    ("topright_y0_40", (620, 0, 800, 45)),        # yellow band rows 9-23 cols 676-753
    ("doc_timer_region", (430, 118, 640, 150)),  # the rectangle the original document asserts
    ("hdr_band_120_180", (85, 118, 545, 182)),   # yellow bands rows 124-138 / 160-174
    ("topband_45_105", (200, 45, 760, 105)),     # yellow band rows 48-100
    ("full_upper", (0, 0, 800, 200)),            # context strip
]

for rel in REFS:
    tag = rel.replace("/", "_").replace(".png", "")
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    im = Image.open(p).convert("RGB")
    for name, box in REGIONS:
        crop = im.crop(box)
        scale = 4 if (box[2] - box[0]) <= 400 else 2
        crop = crop.resize((crop.width * scale, crop.height * scale), Image.NEAREST)
        out = os.path.join(OUT, "V1_crop_%s_%s.png" % (tag, name))
        crop.save(out)
        print("saved", os.path.basename(out), "box", box, "scale", scale, "->", crop.size)
