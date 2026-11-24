# -*- coding: utf-8 -*-
"""swarm 环境自测门：任何子代理开工前必须先让这条命令 exit 0。

只读 gamemd.exe。零真机、零写入（除 stdout）。
判定：重同步解码覆盖 100%，且四条已定谳锚点逐位命中。
任一不成立 ⇒ exit 1（工作流据此中止，不放子代理进现场）。
"""
import sys

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")

from ra2tool import Engine  # noqa: E402

fails = []


def check(name, got, want):
    ok = got == want
    print("[%s] %-46s got=%r want=%r" % ("PASS" if ok else "FAIL", name, got, want))
    if not ok:
        fails.append(name)


e = Engine()
cov, ninsn, resync = e.coverage
print("[INFO] coverage=%.2f%% insns=%d resync=%d" % (cov, ninsn, resync))

check("覆盖率 == 100.00%", round(cov, 2), 100.00)
check("指令总数（台账口径）", ninsn, 1394120)

# 1. CurrentFrame 写点数（ATLAS §8.4：共 10 处写）
fw = [h for h in e.disp_hits(0x00A8ED84) if h[1] == "W"]
check("CurrentFrame 写点数", len(fw), 10)
check("CurrentFrame 唯一定常 inc 三字节", e.rd(0x55DE7E, 1).hex(), "42")
check("CurrentFrame 写回指令字节",
      e.rd(0x55DE81, 6).hex(), "891584eda800")

# 2. 焦点旗标唯一写者（R-063a）
fo = [h for h in e.disp_hits(0x00A8ED80) if h[1] == "W"]
check("焦点旗标写点数", len(fo), 1)
check("焦点旗标唯一写者 VA", "%08X" % fo[0][0] if fo else None, "007778CE")
check("焦点旗标写点字节", e.rd(0x7778CE, 5).hex(), "a280eda800")

# 3. IAT 身份（本轮自解析）
check("0x7E11F0 IAT", e.resolve_iat(0x7E11F0), ("KERNEL32.dll", "Sleep"))
check("0x7E1530 IAT", e.resolve_iat(0x7E1530), ("WINMM.dll", "timeGetTime"))

# 4. MLF 三出口 + 两条不经 inc 的冻结出口
rets, _ = e.func_rets(0x55D360, 0x55DEE0)
ret_vas = ["%08X" % r.address for r in rets]
check("MainLogicFrame ret 集合", ret_vas, ["0055D877", "0055DEC7", "0055DEDB"])
reach = e.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)
frozen = ["%08X" % r.address for r in rets if r.address in reach]
check("不经 inc 可达的冻结出口", frozen, ["0055D877", "0055DEDB"])

loops = [("%08X" % a, "%08X" % t) for a, t, m in e.loop_backedges(0x55D360, 0x55DEE0)]
check("睡眠/泵自旋回边 0x55D3AE->0x55D38D", ("0055D3AE", "0055D38D") in loops, True)

print()
print("VERDICT: %s" % ("OK" if not fails else "FAILED: " + ", ".join(fails)))
sys.exit(0 if not fails else 1)
