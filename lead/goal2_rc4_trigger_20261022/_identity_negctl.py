# -*- coding: utf-8 -*-
"""负控：证明 _driver_identity.py 的 14 个 PASS 有判别力。

四段变异（期望值均在实测后校正）：

  N-1 NAME_STR 改一位 ⇒ 红在「0x8392DD 处字符串以…开头」与「只被 1 处引用」。
      ★ 原期望写「自报名」，但那条用的是 EXPECT_NAME 与新解码结果比，
        改 NAME_STR 不影响它。期望已按实测校正。

  N-2 VIEWPORT_FN 换成 DRIVER ⇒ R9 两条断言必须红。
      ★ 本段最关键：R1 与 R9 用同一个提取函数，若实现上共用了缓存，N-2 不会红。

  N-3 DRIVER 换成 0x4A8960（完全无关的函数）⇒ R1「自报名」必须红。
      ★ 首版用 DRIVER+1，**实测全绿** —— 因为 0x652CF1 起的 `mov esi,ecx`
        与 0x652CF0 起的 `push esi`+`mov esi,ecx` 字节同构，仍能解出同一段。
        这是 x86 变长编码允许自洽错位的老问题（§346 已记录同类）。
        故改用「换到无关函数」，才有判别力。

  N-4 EXPECT_NAME 换成等长串 ⇒ R1 与精确匹配双红。

做法：importlib 加载 → 改模块级常量 → 调 main()。不启子进程，不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    path = os.path.join(HERE, "_driver_identity.py")
    spec = importlib.util.spec_from_file_location("did", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(mod, mutate):
    mutate(mod)
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        rc = mod.main()
    finally:
        sys.stdout = old
    return rc, buf.getvalue()


ok = True


def stage(name, mutate, must):
    global ok
    mod = load()
    rc, out = run(mod, mutate)
    fails = [l.strip() for l in out.splitlines() if "[FAIL]" in l]
    hit = any(must in l for l in fails)
    print("%-30s rc=%d FAIL=%d 命中目标=%s" % (name, rc, len(fails), hit))
    for l in fails[:3]:
        print("    " + l)
    if rc == 0 or not fails or not hit:
        print("  ★ %s 未按预期转红（或红在别处）" % name)
        ok = False


stage("N-1 名字字符串地址改一位",
      lambda m: setattr(m, "NAME_STR", m.NAME_STR + 1),
      "只被 1 处引用")
stage("N-2 VIEWPORT_FN 换成 DRIVER",
      lambda m: setattr(m, "VIEWPORT_FN", m.DRIVER),
      "Set_View_Dimensions")
stage("N-3 DRIVER 换成 0x4A8960",
      lambda m: setattr(m, "DRIVER", 0x004A8960),
      "自报名")
stage("N-4 EXPECT_NAME 换成等长串",
      lambda m: setattr(m, "EXPECT_NAME", b"RadarClass::Two_Time()"),
      "自报名")

if not ok:
    sys.exit(1)
print("★ 四段负控均按预期转红且命中目标断言")
sys.exit(0)
