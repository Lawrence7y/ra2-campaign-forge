import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img
img = Img()
print("sections:")
for name, base, vsz, praw, rsz in img.sections:
    print("  %-8s %08X .. %08X  vsz=%X raw=%X rawptr=%X" % (name, base, base + max(vsz, rsz), vsz, rsz, praw))
print()
for va in (0x7F37F8, 0x7F37FC, 0x7F3800, 0x7F3804, 0x7F3808, 0x7F380C, 0x7F3810):
    print("  %08X u32=%08X bytes=%s sec=%s" % (va, img.u32(va) or 0, img.hexb(va, 4), img.sec_of(va)[0]))
