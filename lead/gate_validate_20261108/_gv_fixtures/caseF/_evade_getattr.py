# -*- coding: utf-8 -*-
# 【违规样本 F】门禁回归测试数据 —— getattr 动态解析逃逸面。禁止执行。
import ctypes


def f_plain(lib):
    # 明文串 getattr：原门禁子串扫描可命中；修正实现按 getattr-逃逸判边
    return getattr(lib, 'OpenProcess')(0x1000, False, 1234)


def g_split(lib):
    # 拆串 getattr：原门禁与修正实现均不可见（静态分析固有盲区，登记残留风险）
    return getattr(lib, 'Open' + 'Process')(0x1000, False, 1234)
