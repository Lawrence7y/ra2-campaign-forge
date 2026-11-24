"""S8 · 一档 9 行的邻项/表类型核验（决定它们能否判 FUNC）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s3_channels as s3

img = s3.img


def rep(a):
    if not img.in_text(a):
        return "        (not in .text)"
    d = s3.chan_d(a)
    return "%08X d1=%d d2=%-15s pad=%2d %s" % (a, int(d["d1"]), str(d["d2_why"]), d["pad"], img.bytes_hex(a, 8))


def show_slot(slot, label, rows=(-3, 4)):
    print("--- %s (slot %08X) ---" % (label, slot))
    for i in range(rows[0], rows[1]):
        t = img.u32(slot + 4 * i)
        mark = " >>" if i == 0 else "   "
        if t is None:
            continue
        print(mark, rep(t))


for slot, label in ((0x86F054, "004A20F0"), (0x86F748, "004E7C20"), (0x86FE60, "0052D620"),
                    (0x872E78, "006E4080"), (0x872EB8, "006E62E0"), (0x872EF0, "006E80F0"),
                    (0x874CC0, "007E0000")):
    show_slot(slot, label)

print("--- struct-like array around 008421CC (006CA7B0) ---")
for q in range(0x8421B8, 0x8421D8, 4):
    v = img.u32(q)
    print("  %08X -> %08X" % (q, v), rep(v) if img.in_text(v) else "")

print("--- struct-like array around 0087C4AC (007D6830) ---")
for q in range(0x87C4A0, 0x87C4C0, 4):
    v = img.u32(q)
    print("  %08X -> %08X" % (q, v), rep(v) if img.in_text(v) else "")

print("text range", hex(img.text_start), hex(img.text_end))
