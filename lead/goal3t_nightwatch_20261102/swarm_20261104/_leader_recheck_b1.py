# -*- coding: utf-8 -*-
"""§534 Leader 亲算 -- 复核第一批三条最关键锚点。

只读 gamemd.exe。零真机、零写入（除 stdout）。

复核对象（来自 P01/P02/P03 的自报结论）：
  R1 [0xA8ED80] 等待环：泵 0x5D4D50 是否含 DispatchMessageA（若是则非死锁）
  R2 [0xA8B230]+0x62C 的写点：0x684174(inc) / 0x684195(dec) / 0x6836D2(复位) 是否成立
  R3 CurrentFrame 10 写点：是否 9/10 写 0（常数 0）

任一不符 ⇒ 该子代理结论降级。
"""
import sys

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")

import struct  # noqa: E402

from ra2tool import Engine  # noqa: E402

e = Engine()
cov, n, rs = e.coverage
print("coverage=%.6f%% insns=%d resync=%d" % (cov, n, rs))
print("sha256=%s" % e.sha)
print()

fails = []


def chk(name, got, want):
    ok = got == want
    print("[%s] %-52s got=%r want=%r" % ("PASS" if ok else "FAIL", name, got, want))
    if not ok:
        fails.append(name)


print("=" * 78)
print("R1 泵 0x5D4D50 是否含 DispatchMessageA")
print("=" * 78)
# IAT 槽
for slot in (0x7E14C0,):
    print("  resolve_iat(%08X) = %r" % (slot, e.resolve_iat(slot)))

# 找泵函数内的 call [imm32]（间接调用）
lo, hi = 0x5D4D50, 0x5D4F00
disp = []
for va, bs, mn, op in e.disasm(lo, hi - lo):
    if mn == "call" and "dword ptr [" in op:
        try:
            addr = int(op.split("[")[1].split("]")[0], 16)
        except Exception:
            continue
        disp.append((va, addr, e.resolve_iat(addr)))
for va, addr, r in disp:
    print("  %08X  call [%08X] -> %r" % (va, addr, r))
has_dispatch = any(r and r[1] == "DispatchMessageA" for _, _, r in disp)
chk("泵内含 DispatchMessageA", has_dispatch, True)

# 泵的边界：找第一个 ret
rets, _ = e.func_rets(lo, hi)
print("  泵窗口内 ret: %s" % ", ".join("%08X" % r.address for r in rets))
print()

print("=" * 78)
print("R2 [GameLogic+0x62C] 的写点")
print("=" * 78)
for va in (0x684174, 0x684195, 0x6836D2):
    print("  %08X  bytes=%s  | %s" % (
        va, e.rd(va, 8).hex(" "),
        " ; ".join("%s %s" % (m, o) for a, b, m, o in e.disasm(va, 8))))
print()
# 反查：0x62C 家族的写点里是否真有这三个
hits = e.disp_hits_field(0x62C)
print("  disp_hits_field(0x62C) 共 %d 处：" % len(hits))
for a, rw, mn, op in hits:
    mark = ""
    if a in (0x684174, 0x684195, 0x6836D2):
        mark = "  <<< P01 点名"
    print("    %s %08X  %-8s %s%s" % (rw, a, mn, op, mark))
w_set = {a for a, rw, m, o in hits if rw == "W"}
chk("0x684174 是 +0x62C 写点", 0x684174 in w_set, True)
chk("0x684195 是 +0x62C 写点", 0x684195 in w_set, True)
print()

print("=" * 78)
print("R3 CurrentFrame 10 写点的写入值形态")
print("=" * 78)
ws = [h for h in e.disp_hits(0xA8ED84) if h[1] == "W"]
print("  写点总数 %d" % len(ws))
zero_cnt = 0
for a, rw, mn, op in ws:
    txt = op.replace(" ", "")
    is_zero = ", 0" in op or ",0" in txt
    if is_zero:
        zero_cnt += 1
    print("    %08X  %-8s %-32s %s" % (a, mn, op, "<- 写常数 0" if is_zero else ""))
print("  写常数 0 的个数 = %d / %d  (P03 自报 9/10)" % (zero_cnt, len(ws)))
chk("写常数 0 的个数", zero_cnt, 9)

print()
print("=" * 78)
print("VERDICT: %s" % ("ALL PASS" if not fails else "FAILED -> " + "; ".join(fails)))
print("=" * 78)
sys.exit(0 if not fails else 1)
