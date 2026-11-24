# -*- coding: utf-8 -*-
# 独立复核样本 V6：静态测试数据，禁止执行。
def f(lib):
    return getattr(lib, 'OpenProcess')(0x1000, False, 1234)
