from PIL import Image
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\screen_p0b_S2_campaign_menu.png"
im=Image.open(p).convert("RGB")
for name,box in [("right",(620,0,810,600)),("left",(0,0,640,600)),("badges",(80,20,540,580)),("right2",(630,0,800,610))]:
    c=im.crop(box)
    c=c.resize((c.width*2,c.height*2),Image.LANCZOS)
    c.save(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\crop_"+name+".png")
    print(name,box,c.size)
