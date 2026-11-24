from PIL import Image
import numpy as np
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\screen_p0b_S2_campaign_menu.png"
a=np.asarray(Image.open(p).convert("RGB")).astype(int)
# right panel x range
sub=a[:,630:800,:]
R,G,B=sub[:,:,0],sub[:,:,1],sub[:,:,2]
bright=(R>110)&(G>110)&(B>110)
rows=bright.sum(axis=1)
# find rows with a long horizontal light line
cands=[(y,int(v)) for y,v in enumerate(rows) if v>90 and y<620]
print("horizontal light lines (y,count):",cands[:60])
# print rows with highest counts
top=sorted([(int(v),y) for y,v in enumerate(rows) if y<620],reverse=True)[:30]
print("top rows:",top)
# dark bar boundaries: look at column x=700 (global 700) vertical profile
