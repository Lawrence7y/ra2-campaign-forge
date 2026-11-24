"""Write 12x zoom crops of the timer field for a chosen list of screenshots (one file each),
plus full score-table crops, so each value can be read individually."""
import os, json
from PIL import Image, ImageDraw, ImageFont

R = r"D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
OUT = r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0f4bd824/V2/pix"
os.makedirs(OUT, exist_ok=True)
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 20)
except Exception:
    FONT = ImageFont.load_default()

LIST = ["archive_T34/measure_w1_end_x.png", "archive_T44/measure_w1_end_x.png",
        "archive_T39/measure_w2_end_x.png", "archive_T49_u0800/measure_w1_end_x.png",
        "measure_w1_end_x.png", "archive_T38/measure_w2_end_x.png"]

# f0 per window straight from the json, not from any report
def f0_of(rel):
    dr = rel.split("/")[0] if "/" in rel else "."
    w = rel.split("measure_w")[1][0]
    jr = os.path.join(R, dr, "measure_w%s.json" % w) if dr != "." else os.path.join(R, "measure_w%s.json" % w)
    d = json.load(open(jr, encoding="utf-8"))
    fe = d.get("frame_edges") or []
    return (fe[0][0] if fe else None), (d.get("gate") or {}).get("units0")

for i, rel in enumerate(LIST):
    q = os.path.join(R, rel.replace("/", os.sep))
    f0, u0 = f0_of(rel)
    im = Image.open(q).convert("RGB")
    crop = im.crop((440, 118, 545, 145))
    big = crop.resize((crop.width * 12, crop.height * 12), Image.LANCZOS)
    d = ImageDraw.Draw(big)
    d.rectangle([0, 0, big.width - 1, big.height - 1], outline=(0, 255, 0), width=3)
    d.text((6, 2), f"#{i} {rel}  f0={f0} units0={u0}  f0/31.2={None if f0 is None else round(f0/31.2,2)}s", fill=(255, 255, 0), font=FONT)
    p = os.path.join(OUT, f"timerzoom_{i}.png")
    big.save(p)
    print("[ZZ]", p, big.size, rel, "f0=", f0, "f0/31.2=", None if f0 is None else round(f0 / 31.2, 2))
