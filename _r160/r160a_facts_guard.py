#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r160a_facts_guard.py —— FACT_INDEX 守门（FDF 门禁）设计与生成。

R159 待办第 2 项的结构性缺口：check_disc.py 全文 grep 'FACT' 命中 0
（本脚本 A0 实测并断言），即 FACT_INDEX.tsv 的任何改动对现有 31 项门禁
完全不可见。本脚本不修改 check_disc.py，而是生成一个独立守门脚本
facts_floors.py，并用沙箱证明它「抓住的每一种破坏都不会被现有门禁抓住」。

守门维度（每条都必须是「能 FAIL 的」，不是恒真）：
  D0  存在性 + sha256 指针（当前版 V543）
  D1  LF-only（CR 计数 == 0）
  D2  表头 5 列逐字
  D3  54 行 / 每行恰 5 列
  D4  fact_id 集合与顺序（F01..F54）
  D5  grade 闭集（4 个取值）且逐 id 计数不漂
  D6  逐 fact 的 statement / limitations 字节下界（= 建表实测的一半）
  D7  evidence_paths 失联不变量：43 项 / 16 去重路径，逐路径引用计数
  D8  总字节下界
  D9  自检：D6 下界表本身的 sha256（防「同改表与常量」）

边界（如实声明）：D6/D8 是常量表，同改表与常量者仍可过；D0 的 sha 指针
若与 D6 表一起改也仍可过。本门禁的价值不是「不可能绕过」，而是把
「FACT_INDEX 完全不被读」变成「任何缩水/删行/改 id/改 grade 都会撞到一条会 FAIL 的断言」。

写入纪律：wx 独占创建备份 -> 断言旧 sha256 -> 一次性写 -> 回读校验。
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time

R = '/home/t628/projects/ra2-campaign-forge'
D = R + '/lead/next_re_20261117_r14'
CUR = D + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
BD = D + '/R17_LEAD_BASELINE'
OUT = R + '/_r160/facts_floors.py'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

def rb(p):
    with open(p, 'rb') as f:
        return f.read()

def sha(b):
    return hashlib.sha256(b).hexdigest()

print('== A0 · 前置断言：现有门禁对 FACT_INDEX 完全不可见 ==')
g = io.open(D + '/check_disc.py', encoding='utf-8', newline='').read()
n_fact = g.count('FACT')
ck('A0.1 check_disc.py 中 FACT 出现 0 次（缺口存在）', n_fact == 0, n_fact)
ck('A0.2 check_disc.py 不引用 V543 路径', 'FACTINDEX_V' not in g)
ck('A0.3 check_disc.py 不引用 FACT_INDEX.tsv', 'FACT_INDEX' not in g)
if fails:
    print('[abort] 前置断言不成立，说明缺口已被别处补上，本卡前提失效'); sys.exit(1)
