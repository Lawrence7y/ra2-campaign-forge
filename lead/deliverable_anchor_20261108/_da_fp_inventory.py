# -*- coding: utf-8 -*-
"""_da_fp_inventory.py — 版本锚审计：对指定写域内全部文件实算 SHA256 与字节数。
只读盘点，不改任何既有文件。python -I -X utf8 运行。
"""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOTS = [
    r"D:\Project\ra2-campaign-forge\lead\a_residual_n1_20261108",
    r"D:\Project\ra2-campaign-forge\lead\perf_repair_n11_20261108",
    r"D:\Project\ra2-campaign-forge\lead\d13d14_cards_20261108",
    r"D:\Project\ra2-campaign-forge\lead\matrix_binding_20261108",
    r"D:\Project\ra2-campaign-forge\lead\slowframe_r3_20261108",
    r"D:\Project\ra2-campaign-forge\lead\criteria_r3_verify_20261108",
]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    for root in ROOTS:
        print("== %s" % root)
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name)
            if os.path.isfile(p):
                print("%s\t%d\t%s" % (name, os.path.getsize(p), sha256_of(p)))
            else:
                print("%s\t<dir>\t-" % name)
    print("== done")


if __name__ == "__main__":
    main()
