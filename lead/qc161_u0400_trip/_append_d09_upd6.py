#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-09 插入更新 6（LF 文件、锚定替换、断言先行，零删除他线内容）。"""
import io, os

PD = "lead/PENDING_DECISIONS.md"
data = io.open(PD, "rb").read()
assert data.count(b"\r\n") == 0, "file now has CRLF — re-check line endings"

D09 = data.find("## D-09".encode("utf-8"))
assert D09 != -1, "D-09 missing"
TIP = "- **提出**：2026-10-24（§426 同轮）".encode("utf-8")
assert data.count(TIP) == 1, "提出 anchor not unique"
assert data.find(TIP) > D09, "提出 anchor before D-09 start"
UPD5 = "\n- **更新 5（2026-10-25，D-09 来源会话".encode("utf-8")
assert data.count(UPD5) == 1, "update5 anchor not unique"

NEW = ("- **更新 6（2026-10-25，D-09 来源会话，D-09-A 机制闭合，新增首选改法 c′）**："
       "离线静态（台账 §431）钉死挂死机制：泵循环 `call 0x5D4D50`（hwnd==0 即 ret，不空转）"
       "＋`cmp [0xA8EDD8],1; je 回环`——**出环唯一通道＝全镜像唯一 `mov [0xA8EDD8],2`@0x777818**。"
       "该 bump 块 P1 趟证实闩 1 前已跑过一次、当时 exitstate==0 被 je 跳过；闩 1 后其再跑"
       "需要新派发，而块自身清了 hwnd⇒通道自断⇒永停 1＝静默僵尸。"
       "**新首选改法 c′**：守卫拦截 rc4 单例消息派发**且 [0xA8EDD8]==1 且 [0x887368]==0**（停机态）"
       "时补写 exitstate=2（等价把 0x777818 就地执行），泵即出环走正常 teardown。"
       "§430 的 a/b/c 降级（a 的「1→2→…递增」被 B@0x6BEC72 也写 1 否证）。"
       "附带风险：兄弟函数 B（闩 1 同构）出环后若再入 B 等待需同判据复查。"
       "选项 A/B/C 与裁决请求**不变**，本条为 D-09-A 设计输入补强。\n").encode("utf-8")

insert_at = data.find(TIP)
after = data[:insert_at] + NEW + data[insert_at:]
assert after.startswith(data[:insert_at])
assert after.count(UPD5) == 1, "update5 eaten"
assert after.count(b"## D-") == data.count(b"## D-"), "D-section count changed"
assert after.count(TIP) == 1
tmp = PD + ".tmp6"
io.open(tmp, "wb").write(after)
os.replace(tmp, PD)
back = io.open(PD, "rb").read()
assert back == after
print("OK update6 inserted before 提出; file %d->%d bytes, D- count=%d" % (
    len(data), len(back), back.count(b"## D-")))
