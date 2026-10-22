# -*- coding: utf-8 -*-
"""负控：证明 _l3_direct_triggers.py 的 12 个 PASS 有判别力。

五段变异，各自必须转红并命中目标断言：

  N-1 L3 改成别的地址 ⇒ P1「恰 2 处直接 E8 调用」转红（站点数变）。
  N-2 SINGLETON 改一位 ⇒ P2「mov ecx,0x87F7E8」两处都不命中 ⇒ 转红。
  N-3 HOST1_STRS 换成不存在的串 ⇒ P3「显示模式路径」转红。
  N-4 WINONLINE_CO_PUSH 改一位 ⇒ P5「push 0xAC116C 是 OUT 参数」转红。
  N-5 RADAR_CMP 改成 0x68584F（cmp 之后那条）⇒ P6「xor 紧邻 cmp」转红。

N-2 / N-4 / N-5 是最关键的三段：
  N-2 验「this 直传单例」这条本轮最强证据；
  N-4 验「winonline 是 COM 指针」的排除依据；
  N-5 验 P6 复核（§350 那条差点被我误判的证据）。

做法：importlib 加载 → 改模块级常量 → 调 main()。不启子进程，不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    path = os.path.join(HERE, "_l3_direct_triggers.py")
    spec = importlib.util.spec_from_file_location("l3t", path)
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
    print("%-28s rc=%d FAIL=%d 命中目标=%s" % (name, rc, len(fails), hit))
    for l in fails[:2]:
        print("    " + l)
    if rc == 0 or not fails or not hit:
        print("  ★ %s 未按预期转红（或红在别处）" % name)
        ok = False


stage("N-1 L3 地址改一位",
      lambda m: setattr(m, "L3", m.L3 + 1),
      "恰 2 处直接 E8")
stage("N-2 SINGLETON 改一位",
      lambda m: setattr(m, "SINGLETON", m.SINGLETON + 4),
      "紧邻")
stage("N-3 显示模式字符串换无",
      lambda m: setattr(m, "HOST1_STRS", [b"NOSUCHMODESTRING"]),
      "显示模式切换路径")
stage("N-4 CO push 地址改一位",
      lambda m: setattr(m, "WINONLINE_CO_PUSH", m.WINONLINE_CO_PUSH + 1),
      "OUT 参数")
stage("N-5 RADAR_CMP 改成 cmp 之后那条",
      lambda m: setattr(m, "RADAR_CMP", 0x0068584F),
      "null 守卫")

if not ok:
    sys.exit(1)
print("★ 五段负控均按预期转红且命中目标断言")
sys.exit(0)
