#!/usr/bin/env python3
# W61: render CAMPAIGN.PCX to PNG for visual inspection (Q2 evidence).
import sys
from PIL import Image
src=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W61_third_badge_route\work\CAMPAIGN.PCX"
dst=r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W61_third_badge_route\work\CAMPAIGN.png"
im=Image.open(src)
print("format=%s size=%s mode=%s" % (im.format, im.size, im.mode))
im.convert("RGB").save(dst)
print("saved", dst)
