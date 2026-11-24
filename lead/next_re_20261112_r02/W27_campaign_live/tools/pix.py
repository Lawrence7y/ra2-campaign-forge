from PIL import Image
import numpy as np
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\screen_p0b_S0_main_menu.png"
a=np.asarray(Image.open(p).convert("RGB")).astype(int)
R,G,B=a[:,:,0],a[:,:,1],a[:,:,2]
mask=(R>140)&(G<90)&(B<90)
ys,xs=np.where(mask)
print("red pixels",len(xs),"x range",xs.min(),xs.max(),"y range",ys.min(),ys.max())
rows=mask.sum(axis=1)
groups=[];cur=None
for y,v in enumerate(rows):
    if v>15 and cur is None: cur=[y,y]
    elif v>15: cur[1]=y
    elif cur is not None: groups.append(tuple(cur));cur=None
if cur: groups.append(tuple(cur))
print("dense red row groups:",groups)
for g in groups:
    sub=mask[g[0]:g[1]+1,:]
    yy,xx=np.where(sub)
    print("  rows",g,"x min/max",xx.min(),xx.max())
