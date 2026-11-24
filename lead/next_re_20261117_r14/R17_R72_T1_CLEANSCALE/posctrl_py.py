#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""posctrl_py.py — Q5 正控「法 2」：与 measure_clean.py **独立**的 Python 实现（只读，只 print）。

与 measure_clean.py 的独立性：
  - 不用 os.walk，用 os.scandir 自写 BFS 栈；
  - 不做任何自产物分类（Q5 只测档 A）；
  - 排除逻辑重新写一遍（.git 任意深度 + out 目录），不看 symlink 标志而用 os.stat(follow_symlinks=False)。

共用项（不可回避，如实声明）：同一 OS 文件系统、同一条 stat 语义（SIZE 字段）、同一 Python 运行时。
因此法 2 与法 1（PowerShell/.NET）才算跨运行时独立。
"""
from __future__ import annotations

import collections
import json
import os
import stat as statmod
import sys

LEAD = r"D:\Project\ra2-campaign-forge\lead"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
EXTS = {".tsv", ".txt", ".json", ".md", ".csv", ".log"}


def main():
    out_nc = os.path.normcase(os.path.abspath(OUT))
    files = []
    denied = []
    stack = [os.path.abspath(LEAD)]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for ent in it:
                    try:
                        if ent.is_dir(follow_symlinks=False):
                            if ent.name.lower() == ".git":
                                continue
                            if os.path.normcase(os.path.abspath(ent.path)) == out_nc:
                                continue
                            # 不跟随目录链接：reparse 点 is_dir(follow_symlinks=False) 仍为 True，
                            # 故再判一次——与 PowerShell 版保持一致
                            st = ent.stat(follow_symlinks=False)
                            if getattr(st, "st_file_attributes", 0) & 0x400:   # FILE_ATTRIBUTE_REPARSE_POINT
                                continue
                            stack.append(ent.path)
                        else:
                            if os.path.splitext(ent.name)[1].lower() not in EXTS:
                                continue
                            st = ent.stat(follow_symlinks=False)
                            files.append((os.path.relpath(ent.path, LEAD).replace("\\", "/"), st.st_size))
                    except OSError:
                        denied.append(ent.path)
        except OSError:
            denied.append(d)
    files.sort()
    n = len(files)
    total = sum(sz for _, sz in files)
    by_ext = collections.Counter(os.path.splitext(rel)[1].lower() for rel, _ in files)
    print(f"posctrl_py files={n} bytes={total}")
    print(f"posctrl_py by_ext={dict(sorted(by_ext.items()))} denied={len(denied)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
