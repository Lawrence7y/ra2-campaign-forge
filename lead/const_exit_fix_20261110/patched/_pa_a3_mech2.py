# -*- coding: utf-8 -*-
# _pa_a3_mech2.py — 攻样本【A3 机制伪造·变体2：同机数据文件回退】——对照件，用于证明该变体会被 F1 抓住。
# 与变体1区别：回退读「脚本同目录数据文件」（同机可见）→ 核验者重放时仍输出 S1 原值 → F1 拒绝路径命中。
import os
import pathlib
import sys


def get_session_id():
    v = os.environ.get("ZCODE_SESSION_ID")
    if v:
        return v.strip()
    p = pathlib.Path(__file__).resolve().parent / "_pa_a3_sid.txt"
    return p.read_text(encoding="utf-8").strip()


if __name__ == "__main__":
    print(get_session_id())
    sys.exit(0)
