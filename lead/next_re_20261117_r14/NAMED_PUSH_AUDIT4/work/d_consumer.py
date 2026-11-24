"""Inspect CLSID consumer sites: is this CoCreateInstance / CoGetClassObject?"""
import sys, json, os, re
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work")
from lib import Img, fmt
img = Img()
W = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT4\work"
IDX = json.load(open(os.path.join(W, "index.json")))
REFS = {int(k, 16): v for k, v in IDX['refs'].items()}
chain = json.load(open(os.path.join(W, "chain4.json")))

def ins_at(a):
    l = img.dis(a, 15); return l[0] if l else None

for r in ['006BF810','006BFF90','006C0A10','006C0E90']:
    cl = int(chain[r]['clsid'], 16)
    rs = REFS[cl]
    print("\n=== %s clsid %08X refs %s ===" % (r, cl, ['%08X' % x for x in rs]))
    for a0 in rs:
        print("  site %08X:" % a0)
        aa = a0 - 12
        for _ in range(16):
            i = ins_at(aa)
            print("    " + fmt(i))
            aa += i.size
            if i.mnemonic == 'call' and aa > a0:
                break
