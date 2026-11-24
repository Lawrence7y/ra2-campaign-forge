# -*- coding: utf-8 -*-
# 静态测试数据，禁止执行。仅被 AST 解析。
import os, subprocess
def f(lib):
    g = getattr
    return g(lib, 'OpenProcess')(0x1000, False, 1234)
def h():
    return getattr(subprocess, 'Popen')
def k():
    os.popen('cmd /c echo hi')
    os.startfile('app.exe')
