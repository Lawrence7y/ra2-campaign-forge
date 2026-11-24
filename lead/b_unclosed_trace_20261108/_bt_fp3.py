# -*- coding: utf-8 -*-
"""_bt_fp3.py — 三件新证据文件的 SHA256/字节数（hashlib 实算），只读。"""
import hashlib
for p in [
    r"D:\Project\ra2-campaign-forge\.zcode\workflow-drafts\B崩点2回件追溯.dwf.ts",
    r"D:\Project\ra2-campaign-forge\.zcode\workflow-drafts\R2维度B崩点补证.dwf.ts",
    r"D:\Project\ra2-campaign-forge\lead\gate_validate_20261108\_verify_gates\a7c7b5f9.py",
]:
    d = open(p, "rb").read()
    print(f"{p}\tsha256={hashlib.sha256(d).hexdigest()}\tbytes={len(d)}")
