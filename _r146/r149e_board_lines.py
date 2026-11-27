#!/usr/bin/env python3
"""R149 E：看板写前归档判据（R138F：写前行数 + 本轮追加 <= 300 才免归档）。"""
import os
ROOT='/home/t628/projects/ra2-campaign-forge'
BOARD=os.path.join(ROOT,'lead/next_re_20261117_r14/STATUS_BOARD.md')
n=sum(1 for _ in open(BOARD,encoding='utf-8'))
print("写前看板行数:",n)
ADD=52
print("本轮预计追加:",ADD)
print("写后估计:",n+ADD)
print("<=300 ?", n+ADD<=300)
print("免归档门槛(写前<260) ?", n<260)
print("判决:", "必须归档" if (n+ADD>300 or n>=260) else "免归档")
