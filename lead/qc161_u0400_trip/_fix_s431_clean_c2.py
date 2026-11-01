#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§431 四·c′ → c″ 干净改写 + D-09 update 6 同步。

设计根据（盘上实测字节）：泵体 0x5D4D50 首分支 `mov eax,[0xB73550]; test; je ret`
——游戏自己认定「hwnd==0 ⇒ 无窗口可等 ⇒ 直接回」。挂死只在**外层循环无视这一点、
拿着已闩死的 1 反复回环**。所以正确改法不是加计数器、也不是补 bump，而是
**让外层的「等」在 hwnd==0 时判定为「已满足」**。
"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
data = io.open(LEDGER, "rb").read()

OLD = ("- **c′（新首选）**：0x777803 块本身已有「exitstate==1 才 bump」分支——守卫在拦截\r\n"
       "  单例派发**且 [0xA8EDD8]==1 且 [0x887368]==0**（停机态）时，补写 `mov [0xA8EDD8],2`\r\n"
       "  （等价于把 0x777818 的效果就地执行）。改守卫件=他线写域，仍需 Lead 派/授权。\r\n").encode("utf-8")
NEW = ("- **c′（作废）**：「守卫拦截单例派发时补写 2」有结构缺陷——僵尸期泵体首分支即 ret、\r\n"
       "  **无任何派发**，守卫钩子永不触发。**由 c″ 取代**。\r\n"
       "- **c″（首选：让外层的等待在「无窗口」时判定为已满足，不加计数器、不补 bump）**：\r\n"
       "  依据=游戏自己的语义——泵体 0x5D4D50 头 `mov eax,[0xB73550]; test eax,eax;\r\n"
       "  je 0x5D4E66(ret)` 已认定「hwnd==0 ⇒ 没有窗口可等 ⇒ 立刻回」；挂死只因外层\r\n"
       "  0x6BE0DC..E7（`call 泵体 / cmp [exitstate],1 / je 回环`）**无视这一点、拿已闩死的 1\r\n"
       "  无限回环**。⇒ 改一处条件即可：外层的「回环继续等」分支加上 **hwnd≠0** 前置\r\n"
       "  （trampoline 到 cave：`cmp dword[0xB73550],0; jne 走原回环; jmp 出环 0x6BE0E9`）。\r\n"
       "  出环后 0x6BE0E9 起的 20 个 call 全是现成正常 teardown 路径，无需伪造任何值。\r\n"
       "  语义=「窗口已关 ⇒ 视为等待结束」，比补 bump/计数器更贴游戏原意、抢跑风险更低\r\n"
       "  （正常关闭时 hwnd 清零先于/伴随闩 1，同一条件本就成立；风险面=若某流程合法地\r\n"
       "  在 hwnd==0 下仍要等 exitstate 变，会提前出环——登记为待验，非已知冲突）。\r\n").encode("utf-8")
assert data.count(OLD) == 1, "anchor §431-四 miss"
d2 = data.replace(OLD, NEW)
tmp = LEDGER + ".tmp431c2"
io.open(tmp, "wb").write(d2)
os.replace(tmp, LEDGER)
assert io.open(LEDGER, "rb").read() == d2
print("OK §431 c″落位; %d bytes" % len(d2))

PD = "lead/PENDING_DECISIONS.md"
p = io.open(PD, "rb").read()
OLDP = ("**新首选改法 c′**：守卫拦截 rc4 单例消息派发**且 [0xA8EDD8]==1 且 [0x887368]==0**（停机态）"
        "时补写 exitstate=2（等价把 0x777818 就地执行），泵即出环走正常 teardown。").encode("utf-8")
NEWP = ("**首选改法 c″（取代 c′，后者作废：僵尸期无任何派发、守卫钩子不触发）**："
        "依据泵体 `test eax,eax; je ret` 游戏自己认定「hwnd==0 即无窗可等」——把外层回环分支\r\n"
        "加一个 hwnd≠0 前置（trampoline 到 cave：`cmp [0xB73550],0; jne 回环; jmp 出环`），\r\n"
        "出环后 0x6BE0E9 起的 20 个 call 全是现成正常 teardown，**不伪造任何值、不加计数器**。"
        "落位=守卫 cave 家族或独立小补丁；他线写域，仍需 Lead 派/授权。").encode("utf-8")
assert p.count(OLDP) == 1, "anchor D09-u6 miss"
p2 = p.replace(OLDP, NEWP)
t2 = PD + ".tmpu6c"
io.open(t2, "wb").write(p2)
os.replace(t2, PD)
assert io.open(PD, "rb").read() == p2
print("OK D-09 update6 c″同步; %d bytes" % len(p2))
