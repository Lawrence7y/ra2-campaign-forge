# -*- coding: utf-8 -*-
"""负控：证明 _rc4_chain_verdict.py 的断言有判别力。

四段变异，各自必须转红并命中目标断言：

  N-1 CRASH_SITE 改一位 ⇒ 「Eip == 0x724737」转红。
  N-2 期望返回地址 0x00654418 改一位 ⇒ 栈对齐断言转红。
  N-3 **把守卫 cmp 地址放到危险 call 之前** ⇒ 「守卫在危险调用之后」转红。
      这是本轮最关键的判据。若它写反了（把后置守卫误判为有效），
      整份定案的因果方向就整体反了 —— 必须被负控覆盖。
  N-4 把无守卫函数头偏移 +1 ⇒ 解码错位 ⇒ 「没有测 ecx 的 cmp/test」转红。

做法：importlib 加载 → 改模块级常量 → 调 main()。
不启子进程（Mimosa 会拦），不落中间文件。
"""
import importlib.util
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(HERE, "_rc4_chain_verdict.py")


def load():
    spec = importlib.util.spec_from_file_location("rcv", MOD)
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


def m1(mod):
    mod.CRASH_SITE = mod.CRASH_SITE + 1


def m2(mod):
    mod.EXPECTED_RETS = [(a, (r + 1) if a == 0x00F9A358 else r, n)
                         for (a, r, n) in mod.EXPECTED_RETS]


def m3(mod):
    """把第一条 case 的 cmp 挪到 call 之前 ⇒ 断言应转红。"""
    fn, callva, cmpva, jccva, jtgt = mod.GUARD_CASES[0]
    mod.GUARD_CASES = [(fn, callva, callva - 0x10, jccva, jtgt)] + mod.GUARD_CASES[1:]


def m4(mod):
    """★ N-4 原版是「函数头 +1」—— 实测无判别力：capstone 从 0x654321 起的 60 条指令
    与从 0x654320 起完全同构（都止于 0x654413），因为 x86 变长编码允许自洽错位。

    ★ 二版试图改 ins.op_str —— capstone 的 Insn 属性是只读的，赋值静默无效。

    本版（三版）：在 main 解码完、做 ecx_tests 判定之前插入一条伪造项。
    手段是包装 check：不让它改，而是让 main 的 kinds 里真的多一条。
    最简单可靠的做法是替换 md.disasm 返回的生成器，在站点附近**追加**一条伪指令。
    """
    real_cs = mod.capstone.Cs

    class _FakeInsn(object):
        def __init__(self, addr, mnem, ops, size=2):
            self.address = addr
            self.mnemonic = mnem
            self.op_str = ops
            self.size = size

    def patched(*a, **k):
        ins = real_cs(*a, **k)
        orig = ins.disasm

        def disasm(code, addr):
            for i in orig(code, addr):
                # 在 0x6543C5（实测唯一 test eax,eax）的位置额外吐一条 test ecx,ecx
                if i.address == 0x006543C5:
                    yield _FakeInsn(0x006543C5, "test", "ecx, ecx")
                yield i
        ins.disasm = disasm
        return ins

    mod.capstone.Cs = patched


ok = True


def stage(name, mutate, must):
    global ok
    mod = load()
    rc, out = run(mod, mutate)
    fails = [l.strip() for l in out.splitlines() if "[FAIL]" in l]
    hit = any(must in l for l in fails)
    print("%-24s rc=%d FAIL=%d 命中目标=%s" % (name, rc, len(fails), hit))
    for l in fails[:3]:
        print("    " + l)
    if rc == 0 or not fails or not hit:
        print("  ★ %s 未按预期转红（或红在别处）" % name)
        ok = False


stage("N-1 崩溃点改一位", m1, "Eip == 0x724737")
stage("N-2 期望返回地址改一位", m2, "00654418")
stage("N-3 守卫挪到调用之前", m3, "守卫在危险调用")
stage("N-4 窗口内伪造 ecx 守卫", m4, "没有测 ecx")

if not ok:
    sys.exit(1)
print("★ 四段负控均按预期转红且命中目标断言")
sys.exit(0)
