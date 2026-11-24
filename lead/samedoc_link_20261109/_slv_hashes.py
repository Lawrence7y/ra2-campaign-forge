# -*- coding: utf-8 -*-
"""_slv_hashes.py — 复核员独立实算指纹。只读，输出 path sha256 bytes。"""
import hashlib
import sys


def main(argv):
    for p in argv:
        try:
            b = open(p, "rb").read()
        except OSError as e:
            print("%s | ERR %s" % (p, e))
            continue
        print("%s %s %d" % (p, hashlib.sha256(b).hexdigest(), len(b)))


if __name__ == "__main__":
    main(sys.argv[1:])
