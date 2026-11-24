from PIL import Image, ImageEnhance
p=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\screen_p0b_S2_campaign_menu.png"
im=Image.open(p).convert("RGB")
c=im.crop((640,190,795,540))
c=ImageEnhance.Contrast(c).enhance(2.2)
c=ImageEnhance.Brightness(c).enhance(1.5)
c=c.resize((c.width*4,c.height*4),Image.LANCZOS)
c.save(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W27_campaign_live\out\crop_bars_enhanced.png")
print(c.size)
