from PIL import Image
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\screen_p3_I1_A1_ingame.png"
im=Image.open(p).convert("RGB")
c=im.crop((170,130,640,480))
c=c.resize((c.width*2,c.height*2),Image.LANCZOS)
c.save(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\crop_map_error.png")
print(c.size)
