# -*- coding: utf-8 -*-
"""GOAL 锚追加 2026-1026 状态块（纯追加，零改既有行；文件全 LF）。"""
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md")

BLOCK = """

---

## 状态块 · 2026-10-26（C26-01/02 执行轮，台账 §438）

**② 主崩溃（RC-4）**：c″ 候选件真机串行 A/B **差分成立**——CTRL（bail=0）僵尸复现 2/2
（150 s 0 退出、exitstate 闩 1 恒 1）；MAIN（bail=1）**WM_CLOSE 后 15.52 s / 15.71 s 自然退出、
exitcode=0** 2/2；无 #32770、except.txt 哈希不变、趟窗事件日志零 AV、母本四哈希不变、残留=0、
卸载双事务 FNV 相等（回滚实证）。运行期**实际布局**经独立进程 ReadProcessMemory 直读：
bail 站点 `0x6BE0E1`=`e9 1a 1f 94 17 90`→cave 0x18000000 36B 逐字节对规格镜像；CTRL 臂站点原字节阴性对照。
⇒ 按 C26-01 记「**RC-4 退出场景（菜单态关窗）候选修复通过**」——非②全闭、非部署现役。
**L1 进局回归抓到范围边界**：局内关窗臂 exitstate **恒 0**、150 s 不退=卡在 c″ 靶点之前的退出链
（与菜单态不同形）⇒ 局内关窗=新开放项（X 离线卡），不重跑同形真机。c″ 在位局内零干扰实证
（30 快照：帧钟推进 30.5 fps、hook 窗全程在位、无新窗）。独立核验已派异族通道（qfmodel，
persona 缓存失效登记），判定书在盘后回登。

**① 卡顿**：本开机会话（10-25 08:36）环境门恢复绿——e4 keep-rect 趟 `pre_fps15=30.692 ≥ 25`、
units0=702、W0 全窗 ok（fps_avg 29.44、max_stall 69.6 ms、>80 ms 占比 0）。
⇒ 31 档可判、**未复现真实卡顿** ⇒ 按 C26-02：C1/C2 保持冻结、不派优化实施。
W1/W2 帧数倒挂=关卡自然终局（H-5 家族），不作卡顿判据。短路臂 e1 趟 units0=0/no_advance 作废。

**③ 安全改动能力**：保持态无回归——本轮全程补丁副本制（驱动新件落自有写域、他线件五 sha 前后
实测一致、独立开关默认 0 实证、部署未动）。git 提交仍被 ZCode Bash 层整树闸拦（C26-03 留证停重试，
无消耗；台账随工作树落盘）。

**在飞/待办**：XVERIFY 判定书（qfmodel 代理）；X 局内关窗死因离线卡；① 战斗覆盖档择机；
提交积压分批（D-08 义务）。裁决台账：本轮无新 D-xx（C26-01/02 已裁死口径）。
"""

cur = TARGET.read_bytes()
assert cur.endswith(b"\n"), "anchor must end with newline"
TARGET.write_bytes(cur + BLOCK.encode("utf-8"))
new = TARGET.read_bytes()
print("appended:", len(new) - len(cur), "bytes; now", len(new))
print("CRLF:", new.count(b"\r\n"), "bareLF:", new.count(b"\n") - new.count(b"\r\n"))
