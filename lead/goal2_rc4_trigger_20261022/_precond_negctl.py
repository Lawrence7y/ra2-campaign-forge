# -*- coding: utf-8 -*-
"""负控：证明 _precondition_verdict.py 与 _vtable_7f0344.py 的 PASS 有判别力。

五段变异，各自必须转红并命中目标断言：

  N-1（precond）把 VT_B 改一位 ⇒ 「唯一入口 = slot5」转红。
  N-2（precond）把 CTOR_B1 改一位 ⇒ 「0x652C00 在有效构造器集内」转红。
  N-3（precond）把 SINGLETON_VT_WRITE 挪远 ⇒ 「两对象初始化相距 < 0x100」转红。
  N-4（vt7f）把 SLOT_L3 从 42 改成 41 ⇒ 「slot[42]==0x4A8960」转红。
  N-5（vt7f）把 VT_HEAD 改一位 ⇒ 「表头由 ctor 立即数钉定」转红。

N-3 是本轮最关键的一段：它验的正是「两个对象在同一初始化函数里」这一
决定性事实。若该断言写成恒真（例如只比较两个常量是否非零），N-3 不会红。

做法：importlib 加载 → 改模块级常量 → 调 main()。不启子进程，不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    path = os.path.join(HERE, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
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


def stage(name, modname, mutate, must):
    global ok
    mod = load(modname)
    rc, out = run(mod, mutate)
    fails = [l.strip() for l in out.splitlines() if "[FAIL]" in l]
    hit = any(must in l for l in fails)
    print("%-26s rc=%d FAIL=%d 命中目标=%s" % (name, rc, len(fails), hit))
    for l in fails[:3]:
        print("    " + l)
    if rc == 0 or not fails or not hit:
        print("  ★ %s 未按预期转红（或红在别处）" % name)
        ok = False


stage("N-1 VT_B 改一位", "_precondition_verdict",
      lambda m: setattr(m, "VT_B", m.VT_B + 4), "唯一入口")
stage("N-2 CTOR_B1 改一位", "_precondition_verdict",
      lambda m: setattr(m, "CTOR_B1", m.CTOR_B1 + 1), "在有效构造器集内")
stage("N-3 初始化间距挪远", "_precondition_verdict",
      lambda m: setattr(m, "SINGLETON_VT_WRITE", m.SINGLETON_VT_WRITE - 0x400),
      "相距仅")
stage("N-4 SLOT_L3 改成 41", "_vtable_7f0344",
      lambda m: setattr(m, "SLOT_L3", 41), "slot[41]")
stage("N-5 VT_HEAD 改一位", "_vtable_7f0344",
      lambda m: setattr(m, "VT_HEAD", m.VT_HEAD + 4), "立即数即表头")

if not ok:
    sys.exit(1)
print("★ 五段负控均按预期转红且命中目标断言")
sys.exit(0)
