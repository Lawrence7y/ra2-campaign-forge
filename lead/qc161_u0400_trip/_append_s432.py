#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§432 台账追加（字节级）：泵身份=真 Win32 消息泵；A 闩 1 后先 PostMessage(WM_QUIT) 再等 bump；
B 有 hwnd≠0 逃生门而 A 没有 ⇒ 僵尸只在 A；c″ 定稿=B 模式原样嫁接（E9@0x6BE0E1）。"""
import io, os

LEDGER = "lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

CONTENT = """# §432　★★ 泵身份定案 + A/B 逃生门不对称 ⇒ c″ 定稿（把 B 自己的 bail 原样嫁接给 A）：
#        E9@0x6BE0E1，cave=「hwnd==0 或 exitstate≠1 ⇒ 出环」；§431 风险行地址口径勘误

**性质**：纯静态（快照 `73201cc021497c95` 断言通过，同 §431），零真机趟。

## 一、泵 0x5D4D50 = 真 Win32 消息泵（IAT 名逐槽解出）

- 体内装载：`[0x7E14F4]=USER32!IsDialogMessageA`、`[0x7E14F8]=USER32!TranslateAcceleratorA`、
  `[0x7E14BC]=USER32!TranslateMessage`、派发走 `[0x7E14C0]`（同族槽）；取消息=本地
  `0x53E770/0x53E730`（MSG 结构封装）。⇒ 0x5D4D50 就是标准
  GetMessage→IsDialog/Translate→Dispatch 泵，**全镜像 43 个调用点**＝游戏的通用
  「模式等待」原语（等某个全局标志被回调置位，边等边泵）。
- 首分支 `mov eax,[0xB73550]; test; je 0x5D4E66(ret)`：hwnd 全局==0 ⇒ 泵整体跳过。
  ⇒ 僵尸态（hwnd 已被关闭块清零）下 43 个泵等待点全部退化为空转回环——**但只有 A
  的回环没有逃生门**（见二）。

## 二、A 闩 1 后的真实语义（0x6BE0B6..E7 逐条钉死）

```
0x6BE0B6 mov [0xA8EDD8], edi (=1)        ; 闩 1
0x6BE0BC mov ecx, 0xA83D10 / call 0x720770 / call 0x406D40   ; 前置清理
0x6BE0CB push ebx / push ebx / push 2 / mov ecx,[0xB73550] / push ecx
0x6BE0D6 call [0x7E14AC]                 ; = PostMessageA(hwnd, WM_QUIT=2, 0, 0)
0x6BE0DC call 0x5D4D50                   ; 泵一圈
0x6BE0E1 cmp [0xA8EDD8], edi / je 0x6BE0DC ; 等 bump 到 2
```
⇒ 设计意图：投递 WM_QUIT ⇒ 主循环出环 ⇒ 主循环路径把 exitstate bump 到 2 ⇒ 本函数
出环走 teardown（0x6BE0E9 起 20 个 call + CoDisconnect/OleUninitialize）。
**僵尸态三处全断**：hwnd 已=0 ⇒ PostMessage(0,WM_QUIT) 投递即败；泵首分支即 ret；
唯一写 2 的 0x777818 在 WndProc 关闭块内，bump 条件「进块时 exitstate≠0」——而 P1 趟
实证进块时 exitstate==0 被 je 跳过（§431 三），之后再无派发通道。三重独立证据
（静态块序 + §430 断点现场 + §429 150 s 轮询）⇒「等不来的 2」定案，无[推断]残留。

## 三、★★ A/B 不对称 = c″ 的正当性来源（不是我们发明的改法，是游戏自己的另一半）

B@0x6BEC50（另一条 PostMessage(WM_QUIT)+闩 1+等 bump，块头 0x6BEC50 另 3 调用点）
的等待环**自带逃生门**：
```
0x6BEC87 call pump / 0x6BEC8C cmp [exitstate],1 / jne 出环
0x6BEC94 mov eax,[0xB73550] / test eax,eax / jne 0x6BEC87   ; hwnd==0 ⇒ 放弃等待出环
```
⇒ **A 与 B 同构，唯独 A 少了「hwnd==0 放弃等待」这一条**。B 的调用点之一
（站点 0x6BDCFE，在 A 的块区内）紧贴 A 的另一个泵等待环 `call pump / test al,[0xA8ED80] /
je 回环`（0x6BDD03..0F）——同一退出流程里混用两种等待形态，A 这条是无 bail 的变体。
**c″=把 B 的 bail 原样嫁接进 A 的回环**，语义改动最小、不伪造任何值、不加计数器。

## 四、c″ 落位定稿（字节级，供 Lead 派工）

- 现窗：`0x6BE0E1: 39 3D D8 ED A8 00 | 74 F3`（cmp 6B + je 2B）。
- 补丁：E9 rel32 占 0x6BE0E1..E5 + `90` @0x6BE0E6（覆盖 6 字节 cmp；原 `74 F3`
  变死代码不碍事——E9 直跳 cave，不再落回）。
- cave 逻辑（伪码，等价于把 B 的两条 bail 条件并进 A）：
  ```
  mov eax, [0x00B73550]      ; hwnd 全局（B 用的同一个地址）
  test eax, eax
  je   0x006BE0E9            ; hwnd==0 ⇒ 出环（B 模式）
  cmp  dword [0x00A8EDD8], 1
  jne  0x006BE0E9            ; bump 已到 ⇒ 出环（原语义，用立即数 1 不依赖 edi）
  jmp  0x006BE0DC            ; 继续等（原回环入口）
  ```
- 足迹核查：0x6BE0E1..E8 与守卫 8 头（全在 0x724xxx 族）零重叠；与既有补丁窗零冲突。
- 出环后路径=游戏自身 teardown（0x6BE0E9 起 20 call 无一在守卫 8 头内；其中
  0x6BE0FA `ecx=0x87F7E8 / call 0x6D0270` 走 RC-4 单例静态本体，非指针解引用，安全）。
- 风险面（不变，登记）：若有合法流程在 hwnd==0 下仍需等 exitstate 变——B 的存在证明
  游戏作者自己认为「无窗即不等」；A 少这条更像疏漏而非设计。留真机趟验证：
  正常「进菜单→关窗」出环后无新对话框/无 except 新增 = 通过判据。

## 五、§431 勘误（地址口径）

§431 四风险行「B 调用者 0x54A8C5/0x5B3C75/0x647372/0x6BDD03」用的是**下一条指令地址**
（E8 扫描器 out.append(site+5) 口径）；真实 E8 站点=各自 −5：
0x54A8C0/0x5B3C70/0x64736D/0x6BDCFE。其中 0x6BDD03（下一条）本身是对**泵** 0x5D4D50 的
call（不是 B），紧邻 B 调用之后——本节一已钉。结论方向不变（B 调用点确实落在 A 块区）。

## 六、卫生

零真机趟；快照哈希断言通过；本轮探针全部 stdin heredoc 只读（无新落盘脚本），
判据产物=本节 + D-09 update 7。他线件零改动。
"""

def main():
    before = io.open(LEDGER, "rb").read()
    assert b"\xc2\xa7431" in before, "prev section missing"
    assert b"\xc2\xa7432" not in before, "duplicate"
    crlf_before = before.count(b"\r\n")
    add = CONTENT.replace("\n", "\r\n").encode("utf-8")
    after = before + b"\r\n" + add
    assert after.startswith(before)
    assert after.count(b"\r\n") == crlf_before + 1 + CONTENT.count("\n"), "crlf math off"
    tmp = LEDGER + ".tmp432"
    with io.open(tmp, "wb") as fh:
        fh.write(after)
    os.replace(tmp, LEDGER)
    check = io.open(LEDGER, "rb").read()
    assert check == after
    print("OK appended 432; ledger %d bytes crlf=%d" % (len(check), check.count(b"\r\n")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
