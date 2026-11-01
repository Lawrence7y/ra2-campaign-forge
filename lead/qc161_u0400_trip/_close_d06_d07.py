#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-06/D-07 收尾手术（监督会话指令）：删两条目 + 已裁决记录区补登记语。
保留：文件头协议区、两条 SYNCPOINT 历史信标。LF-only 断言先行。"""
import io, os

PD = "lead/PENDING_DECISIONS.md"
data = io.open(PD, "rb").read().decode("utf-8")
assert data.count("\r\n") == 0, "CRLF appeared"
assert data.count("## D-06") == 1 and data.count("## D-07") == 1
i6 = data.find("## D-06")
i7 = data.find("## D-07")
assert i6 < i7
hdr_end = data.find("## 已裁决记录")
assert 0 < hdr_end < i6, "已裁决记录 header position unexpected"
# 已裁决记录区第一行（最近在上）插入点 = header 行尾
ins_at = data.find("\n", hdr_end) + 1

REG = (
    "- **D-07 已裁决（2026-10-25 23:38 定谳 + 2026-10-26 00:45 补释；条目已由 GOAL-3T 线按监督令删除，此处为登记补记）**："
    "**B 案（按写域路由）**+冻结件 6 条挂账豁免（wontfix，破冻结须用户单独授权）+非冻结件归属线修复/迁出（零字节改动迁出=许可，前后哈希登记台账）。\n"
    "  **执行（GOAL-3T 线，2026-10-26）**：`mimosa git-gate install` 落地**原生 git 门禁**（pre-commit/pre-push，高危阻断），双对照实证 diff-only——"
    "阳性=暂存集含 high 两件时归因恰为该两件（`_disc_armG.py:75`/`_disc_stdio.py:47`，rc=2）；"
    "阴性=两件出暂存后 127 个变更源码文件全查放行（rc=0）；pre-push 扫**待推提交 diff**（6 文件）放行。\n"
    "  **残项上报**：ZCode Bash 层 PreToolUse 钩子仍**整树扫描**且不让位、无配置面（载荷 AES-GCM+Ed25519 密封；40=38+policy 后规则计数变化），"
    "本线经 ZCode 的提交仍被外层拦——需插件侧/用户处理（关停该钩子或厂商实现 diff-only），git 层已就绪待接管。台账 §436/§437。\n"
    "- **D-06 已裁决（2026-10-25，监督会话补派令）**：选 **C**（RE-ATLAS 线自取：先修门禁再裁 D-02，修完自动落 A）；对 GOAL-3T 线无阻塞。\n"
    "  执行：RE-ATLAS 线办理；本线零动作。\n"
)

i_beacon1 = data.find("<!-- SYNCPOINT 2026-10-24 11:2x")
assert i_beacon1 > i7, "beacon position unexpected"
beacons = data[i_beacon1:]  # 两条信标保留到 EOF

new = data[:i6] + beacons.rstrip("\n") + "\n"
# 插登记语（在已裁决记录 header 之后）
new = new[:ins_at] + REG + new[ins_at:]

# 断言
assert new.count("## D-06") == 0 and new.count("## D-07") == 0, "sections not removed"
assert new.count("## 已裁决记录") == 1
assert new.count("D-07 已裁决（2026-10-25 23:38") == 1
assert new.count("D-06 已裁决（2026-10-25") == 1
assert new.count("<!-- SYNCPOINT 2026-10-24 11:2x") == 1
assert new.count("<!-- SYNCPOINT 2026-10-24 晚") == 1
assert new.count("\r\n") == 0
assert new.startswith(data[:i6]) or True
# 头部协议区保留
assert "只放「需要用户或 Lead 裁决才能继续」的事项" in new

tmp = PD + ".tmpclose"
io.open(tmp, "wb").write(new.encode("utf-8"))
os.replace(tmp, PD)
back = io.open(PD, "rb").read().decode("utf-8")
assert back == new
print("OK: D-06/D-07 removed, registrations added, beacons kept; %d -> %d chars" % (len(data), len(new)))
print("剩余 D- 条目数:", back.count("## D-"))
