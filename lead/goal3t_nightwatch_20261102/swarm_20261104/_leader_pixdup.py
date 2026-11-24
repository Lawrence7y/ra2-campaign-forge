# -*- coding: utf-8 -*-
"""§543 证据完整性检验：25 张「冻结窗末截图」彼此是否像素重复。

若大量截图逐像素相同 ⇒ 它们是陈旧/复制件，不能作为逐趟证据。
若各不相同且计时器 = frame/31.2 ⇒ 可作为真实现场证据。

判据：
  pixhash = sha256(整幅 RGB 原始字节)，忽略 PNG 编码差异；
  panelhash = sha256(计分屏面板区 RGB 原始字节)。
"""
import glob
import hashlib
import os

from PIL import Image

BASE = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
PANEL = (85, 108, 630, 275)

rows = []
for p in sorted(glob.glob(os.path.join(BASE, "*", "measure_w*_end_*.png"))):
    im = Image.open(p)
    im.load()
    rgb = im.convert("RGB")
    ph = hashlib.sha256(rgb.tobytes()).hexdigest()[:16]
    pan = rgb.crop(PANEL)
    panh = hashlib.sha256(pan.tobytes()).hexdigest()[:16]
    rows.append((os.path.basename(os.path.dirname(p)), os.path.basename(p), ph, panh))

print("%-20s %-24s %-18s %-18s" % ("trip", "png", "整幅 pixhash", "面板 pixhash"))
for r in rows:
    print("%-20s %-24s %-18s %-18s" % r)

print()
full = {}
for t, n, ph, panh in rows:
    full.setdefault(ph, []).append("%s/%s" % (t, n))
print("=== 整幅逐像素相同的组 ===")
dups = {k: v for k, v in full.items() if len(v) > 1}
if not dups:
    print("  无重复")
for k, v in dups.items():
    print("  %s : %s" % (k, v))

print()
pan = {}
for t, n, ph, panh in rows:
    pan.setdefault(panh, []).append("%s/%s" % (t, n))
print("=== 面板区逐像素相同的组 ===")
pdups = {k: v for k, v in pan.items() if len(v) > 1}
if not pdups:
    print("  无重复")
for k, v in pdups.items():
    print("  %s (%d 张): %s" % (k, len(v), v))

print()
print("独立整幅: %d / %d" % (len(full), len(rows)))
print("独立面板: %d / %d" % (len(pan), len(rows)))
