import os
from PIL import Image

OUT_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104\XVERIFY_S543_0a451d0b\V1"
p = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l3_20261023r\measure_w2_end_x.png"

im = Image.open(p).convert("RGB")
# Blue row is between header (y=160..190) and red row (y=220..250)
# So y: 190..220
im_blue = im.crop((80, 190, 620, 220)).resize(((620-80)*3, 30*3), Image.Resampling.NEAREST)
im_blue.save(os.path.join(OUT_DIR, "V1_l3_blue_player.png"))
print("Saved blue player row.")
