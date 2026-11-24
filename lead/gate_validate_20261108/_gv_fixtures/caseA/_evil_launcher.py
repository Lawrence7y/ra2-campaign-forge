# -*- coding: utf-8 -*-
# 【真违规样本 A】门禁回归测试数据 —— 模拟「新建脚本以 subprocess 启动游戏进程」。
# ★ 禁止执行本件：它只应被静态检查器（AST）读取。launch/launch_never 均为死代码定义。
import subprocess


def launch():
    subprocess.Popen(['gamemd.exe', '-win'])
    subprocess.run(['ra2loader.exe'])


def launch_never():
    if False:
        subprocess.check_output(['YURI.exe'])
