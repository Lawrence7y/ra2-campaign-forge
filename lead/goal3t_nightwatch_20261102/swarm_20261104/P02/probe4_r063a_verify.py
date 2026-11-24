# -*- coding: utf-8 -*-
# P02 probe4: 独立复钉 r063a 关键字节 + 泵包装内嵌分派 + WinMain 自旋环 + 0x55D830 泵调用上下文
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()

def dump(title, va, n):
    print("== %s (0x%08X, %d bytes) ==" % (title, va, n))
    print("   raw: " + eng.rd(va, n).hex())
    for a, b, m, o in eng.disasm(va, n):
        print("   %08X  %-18s %s %s" % (a, b, m, o))
    print()

# 1) 写链核心：0x7778A0 门① / 0x7778AC-CF setne+写 / 0x7778D3 后继
dump("T2 门①+写链", 0x7778A0, 0x38)
# 2) 消息号判定链：0x77782B..0x777848
dump("T2 消息链头", 0x77782B, 0x20)
# 3) WndProc 头 0x7775C0
dump("T1 WndProc 头", 0x7775C0, 0x12)
# 4) 注册点 0x777C79 + RegisterClass 调用
dump("T1 注册点", 0x777C70, 0x40)
# 5) hwnd 存储 0x777CD6 / 0x777D7E
dump("hwnd 写点 A", 0x777CC8, 0x14)
dump("hwnd 写点 B", 0x777D70, 0x14)
# 6) WM_PAINT 门 0x7776C1
dump("WM_PAINT 门", 0x7776B5, 0x18)
# 7) 焦点字符串锚
for sva, nm in ((0x849E94, "Focus_Loss"), (0x849ECC, "Focus_Restore"),
                (0x849EF8, "Focus gained"), (0x849F08, "Focus lost"),
                (0x849F48, "窗口类/名")):
    raw = eng.rd(sva, 48)
    txt = raw.split(b"\0")[0].decode("ascii", "replace")
    print("== str %s @0x%08X == %r" % (nm, sva, txt))
print()
# 8) WinMain 自旋环 0x6BDD03 / 0x6BDD2E
dump("WinMain 自旋环 A", 0x6BDCF0, 0x30)
dump("WinMain 自旋环 B", 0x6BDD1B, 0x30)
# 9) 泵包装 0x53E770 全体（含内嵌分派 0x53E8A1）
dump("泵包装 0x53E770", 0x53E770, 0x160)
# 10) 泵包装 0x53E730
dump("泵包装 0x53E730", 0x53E730, 0x40)
# 11) 0x49F740（泵内 msg 预处理）
dump("泵内 0x49F740", 0x49F740, 0x30)
# 12) 0x55D830 MLF 帧体内的泵调用上下文
dump("MLF 帧体泵调用", 0x55D820, 0x20)
# 13) 激活沿后继 0x777930 (Focus_Restore call)
dump("激活沿后继", 0x777930, 0x24)
