# -*- coding: utf-8 -*-
"""负控：证明 _object_source_verdict.py 的 PASS 有判别力。

四段变异：

  N-1 SINGLETON 改一位 ⇒ 「两个全局不同」仍绿，但 0x87F7E8 的 BSS 判断
      会因为落到别的地址而改变 ⇒ 「0x87F7E8 在文件内无内容」应红。
      （该地址若被改到 .data 有内容处，va2off 就返回非 None。）

  N-2 CUR_OBJ 改成 SINGLETON ⇒ 「两者是不同全局」必须红。
      这是最直接的一条：如果两者可以相等，整个「对象本体 vs 指针变量」的区分就垮了。

  N-3 DISP 改成 0x9C ⇒ 站点数不再是 29（0x9C 是 slot39，另一批站点）。
      「站点数 == 29」必须红。

  N-4 把 trace_reg 的「见 reg 直接给 None」短路掉 ⇒ UNKNOWN 回到 29，
      「UNKNOWN 不再是 29」必须红。
      ★ 这一段专门验「切片器真的追了 vtable 那一层」——
        这是本轮最大的 bug（首版 29 站全 UNKNOWN）。

做法：importlib 加载 → 改模块级常量/函数 → 调 main()。不启子进程。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    path = os.path.join(HERE, "_object_source_verdict.py")
    spec = importlib.util.spec_from_file_location("osv", path)
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
    print("%-32s rc=%d FAIL=%d 命中目标=%s" % (name, rc, len(fails), hit))
    for l in fails[:3]:
        print("    " + l)
    if rc == 0 or not fails or not hit:
        print("  ★ %s 未按预期转红（或红在别处）" % name)
        ok = False


stage("N-1 雷达本体地址改到有内容处",
      # ★ 首版用 0x87F000 —— 它**也在 BSS**（.data rsize 止于 0x87E000），故不红。
      #   改用 0x832000：位于 .data 的 rsize 内（文件里确有内容）⇒ va2off 非 None。
      lambda m: setattr(m, "SINGLETON", 0x00832000),
      "文件内无内容")
stage("N-2 指针变量 == 雷达本体",
      lambda m: setattr(m, "CUR_OBJ", m.SINGLETON),
      "不同的")
stage("N-3 DISP 改成 0x9C",
      lambda m: setattr(m, "DISP", 0x9C),
      "站点数 == 29")
stage("N-4 切片器退化为只看直接定义",
      lambda m: setattr(m, "trace_reg",
                        lambda seq, idx, md, reg, depth=0: (None, None)),
      "UNKNOWN 不再是 29")

if not ok:
    sys.exit(1)
print("★ 四段负控均按预期转红且命中目标断言")
sys.exit(0)
