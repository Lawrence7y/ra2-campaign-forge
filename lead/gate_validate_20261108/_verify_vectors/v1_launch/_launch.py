# -*- coding: utf-8 -*-
# 独立复核样本 V1：静态测试数据，禁止执行。仅被 AST 解析。
import subprocess

def go():
    subprocess.Popen(['gamemd.exe', '-win'])
    subprocess.run(['ra2loader.exe'])
    if False:
        subprocess.check_output(['YURI.exe'])
