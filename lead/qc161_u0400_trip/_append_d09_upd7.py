#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-09 插入更新 7（§432 定稿级补丁规格；锚定+断言，LF-only 保持）。"""
import io, os

PD = "lead/PENDING_DECISIONS.md"
data = io.open(PD, "rb").read()
assert data.count(b"\r\n") == 0, "file has CRLF now"
D09 = data.find("## D-09".encode("utf-8"))
assert D09 != -1
TIP = "- **提出**：2026-10-24（§426 同轮）".encode("utf-8")
assert data.count(TIP) == 1 and data.find(TIP) > D09
assert data.count("更新 6（2026-10-25，D-09 来源会话".encode("utf-8")) == 1

NEW = ("- **更新 7（2026-10-25，D-09 来源会话，c″ 升格为定稿级补丁规格）**：泵 0x5D4D50 "
       "确证=真 Win32 消息泵（IsDialogMessage/TranslateMessage/Dispatch 逐槽解名，43 调用点）；"
       "A 闩 1 后先 `PostMessageA(hwnd,WM_QUIT)` 再等 bump——僵尸态三处全断（hwnd=0 投递即败、"
       "泵首分支即 ret、写 2 块通道自断），三重证据定案。**决定性发现**：兄弟函数 B 的等待环"
       "**自带** `hwnd==0 ⇒ 放弃等待` 逃生门，A 同构却少这一条 ⇒ c″ 不是我们发明的改法，"
       "是把游戏自己的另一半（B 的 bail）原样嫁接：`E9@0x6BE0E1 + 90@0x6BE0E6`，"
       "cave=「hwnd≠0 且 exitstate==1 才继续等」。足迹核查过：与守卫 8 头零重叠、"
       "出环后 20 call 无一被守卫拦。字节级规格与验证判据见台账 §432（含 §431 一处"
       "地址口径勘误）。**裁决请求升级为：授权本线出 c″ 补丁副本，或派工守卫他线**。\n").encode("utf-8")

insert_at = data.find(TIP)
after = data[:insert_at] + NEW + data[insert_at:]
assert after.count("更新 6（2026-10-25，D-09 来源会话".encode("utf-8")) == 1
assert after.count(b"## D-") == data.count(b"## D-")
assert after.count(TIP) == 1
tmp = PD + ".tmp7"
io.open(tmp, "wb").write(after)
os.replace(tmp, PD)
back = io.open(PD, "rb").read()
assert back == after
print("OK update7; %d bytes crlf=%d" % (len(back), back.count(b"\r\n")))
