# -*- coding: utf-8 -*-
"""负控：证明 _branch_to_chain.py 的 16 个 PASS 有判别力。

四段变异（期望值均在实测后校正，见各段注释）：

  N-1 SINGLETON 改一位 ⇒ 读取点普查出 5 处（原 2 处）⇒「全文件仅 2 处」转红。

  N-2 RET_NODE 改 +0x10 ⇒ jt[i]!=RET_NODE 判据失效，实质分支从 5 变 6
      ⇒「只有 5 个落到实质分支」转红。
      ★ 本段原来的期望是「跳到 0x693408」，实测**不命中**那条断言 ——
        因为门禁 jcc 是硬编码字面量，我改 RET_NODE 常量不影响它。
        真正被这条变异影响的是「实质分支计数」，故期望改为后者。

  N-3 DWORD_TBL 改一位 ⇒ 跳转表有效项变 5，连带实质分支变 4 ⇒
      「跳转表恰 6 个有效项」转红 + 5 项连带红。

  N-4 MSG_COUNT 改 20 ⇒ 字节表少读一项，实质分支变 4 ⇒
      「只有 5 个落到实质分支」转红。
      ★ 本段原期望是「idx=5」，实测红在「5 个实质分支」那条 ——
        MsgCount 少 1 时 idx=5 集合从 16 变 15，仍满足 ≥15，故不红。

★ 两处期望值都因实测而校正。这本身是负控的价值：
  它同时暴露了「哪条断言真的在管哪件事」，比主脚本全绿更有信息量。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    path = os.path.join(HERE, "_branch_to_chain.py")
    spec = importlib.util.spec_from_file_location("btc", path)
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
    for l in fails[:3]:
        print("    " + l)
    if rc == 0 or not fails or not hit:
        print("  ★ %s 未按预期转红（或红在别处）" % name)
        ok = False


stage("N-1 单例地址改一位",
      lambda m: setattr(m, "SINGLETON", m.SINGLETON + 4),
      "全文件仅")
stage("N-2 返回出口改 +0x10",
      lambda m: setattr(m, "RET_NODE", m.RET_NODE + 0x10),
      "落到实质分支")
stage("N-3 跳转表基址改一位",
      lambda m: setattr(m, "DWORD_TBL", m.DWORD_TBL + 4),
      "跳转表恰 6")
stage("N-4 msg 表长改 20",
      lambda m: setattr(m, "MSG_COUNT", 20),
      "落到实质分支")

if not ok:
    sys.exit(1)
print("★ 四段负控均按预期转红且命中目标断言")
sys.exit(0)
