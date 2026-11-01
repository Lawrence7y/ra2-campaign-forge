#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§438 追加 —— C26-01 执行：c″ 真机串行 A/B 全过（CTRL 僵尸 2/2 / MAIN 20s 内自然退出 2/2）
   + L1 进局回归的范围发现（局内关窗≠退出态臂）。零 git 写；只动自有台账+本线新产物。"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")

BODY = """# §438　★★ C26-01 执行轮：c″ 真机串行 A/B 差分成立（CTRL 僵尸 2/2、MAIN 20s 内自然退出 2/2）；
#        L1 进局回归抓到范围边界——局内关窗臂 exitstate 恒 0、150s 不退（新开放项）；① 本会话环境门绿

**性质**：真机时段（GOAL3T_PROMPT 2026-10-26 续推令 + RULINGS.md C26-01 裁决执行）。
本轮发射 6 趟：c2ab CTRL×2 / MAIN×2 / L1REG×1 + ① L1 环境门趟×1（e4，另 e1 短路臂无效趟
units0=0/no_advance 作废）。全部经本线写域 `lead/qc161_u0400_trip/`，他线件只读复用。

## 一、C26-01 前置复核（离线，零趟）

- 候选 DLL 完整 sha256 实测 = 裁决钉值 `edb9a0cde129c105e087db61f6661b4722a80787e5b5949bd0b0890e0354f2de` ✓
- 工件门禁 `_verify_c2_candidate.py` 复跑（Python312 真实路径曾写错 `D:\\Python312` ⇒ 系统找不到路径，
  改用 PATH 上的 `AppData\\Local\\Programs\\Python\\Python312`）⇒ **14/14 PASS，rc=0**
  （输出 `d09a_c2_candidate/_gate_rerun_20261026.out`）。
- 发射器 `_drive_c2_ab.py`（本线新件；d09b 机制+三键 ini 写回读验证+布局取证）。预检 8/8：
  探针 `b063052c…`/gamemd 母本 `73201cc0…`/母本 DLL `0e2a9995…`/loader `ebddf6a6…`/候选 sha256 全值。

## 二、运行期**实际安装布局**取证（C26-01「干跑字样不放行」的正面答复）

机制：趟内**独立进程 ReadProcessMemory** 直读运行中 gamemd 的 .text（非 DryRun 自述）——
- MAIN×2 趟：站点 `0x6BE0E1` hook 窗实读 `e91a1f941790` == E9(→0x18000000)+90 重算值；
  cave 基址 **0x18000000**（bail 独立池首提示命中）36B 实读
  `a15035b70085c00f84dce06be8833dd8eda800010f85cfe06be8e9bde06be8e9c5e06be8`
  == 按**实际基址**重算的规格镜像（rel32 三目标 0x6BE0E9/0x6BE0DC/0x6BE0E9 全对）；
  死重 `0x6BE0E7` 仍读到 `74f3`（原 je 成死代码、字节未被覆盖）⇒ 三检查 hook_win/cave_36b/dead_je_kept 全真。
- CTRL×2 趟（bail=0）：站点须保持原字节 `393dd8eda800` + `74f3` 在位 ⇒ 实读相符（阴性对照：
  判据不认「没装」的趟，也不认「装了却读不到」）。
- 开关读回=日志自证：CTRL `EnableRC4Guard=1 EnableRC4ExitBail=0`、MAIN `=1 …=1`、
  母本 `原字节比对 8/8 一致` + `[ra2rc4exitbail] 原字节比对 8/8 一致；hook 窗(6B) FNV …`（安装日志核验）。

## 三、串行 A/B 结果（CTRL 先 → MAIN 后，两轮重复；watch=150s/臂）

| 轮 | 臂 | 配置 | 结果 |
|---|---|---|---|
| 1 | CTRL | Guard=1 Bail=0 | **僵尸复现**：closed@7.63s，150s 0 退出（1477 样本）、exitstate 0→1 恒 1、无新窗、except 不变、a8 PASS |
| 1 | MAIN | Guard=1 Bail=1 | **15.52s 自然退出**，exitcode=0，154 样本即 WAIT_OBJECT_0，无 #32770、except 不变、a8 PASS、载体删净 |
| 2 | CTRL | Guard=1 Bail=0 | 僵尸复现（重复性 ✓） |
| 2 | MAIN | Guard=1 Bail=1 | **15.71s 自然退出**，exitcode=0（重复性 ✓） |

- exitstate 轨迹：MAIN 臂 first=0 → last=1（exit 前一行），允许 0→1 恒 1、未强求 1→2（C26-01 口径）；
  CTRL 臂闩 1 后恒 1 至观察终 = §429/§431 僵尸形态。
- **差分归因 c″**：同件同载体同会话同时段，唯一变量 `EnableRC4ExitBail`（独立开关，默认 0 已实证：
  CTRL 臂 .text 零 bail 改动=二节阴性对照）。CTRL 僵尸=装置阳性，**不充通过**；
- AV 通道：趟窗 13:32–13:48 事件日志 Id=1000/1001 **零命中**（12:13/12:49 有事件，归属 WorkBuddy.exe
  koffi.node 崩溃，与 RA2 无关——`_evscan_c2ab_20261026.ps1` 留证）；
- 母本四哈希趟后实测不变（gamemd/母本 DLL/母本 cpp/loader）；c″ 候选件零改动。

⇒ **判据 v2 全项达成：可记「RC-4 退出场景（菜单态关窗）候选修复通过」**（按 C26-01 措辞，
不是②全闭、不是部署现役；其他崩溃类型不被覆盖）。

## 四、★ L1 进局回归（已批准项）：抓到**范围边界**——局内关窗是另一条死法

`_drive_c2_l1_regress.py`（MAIN 配置；进局复用 harness7 在用件 `find_main_window/_focus_foreground/
click_logical` FS 直通映射 + NAV_SIG_PLAN 三连 (700,218)/(700,304)/(700,262)；
**进局正判据=帧钟 CurrentFrame 推进**，比截图签名强）。趟 `c2ab/20261026T161412_L1REG/`：

| 判据 | 实测 | 判定 |
|---|---|---|
| R1 进局 | nav 三步 focus_ok 全真，帧 166 起步、**60s 战斗窗推进 1770 帧（≈30.5 fps）** | ✓ |
| R2 局内非干扰 | 30 快照：exitstate 恒 0、hwnd≠0、单例≠0、hook 窗全程 `e91a1f941790` 在位、无新窗 | ✓ **c″ 在位不干扰对局** |
| R3 局内 WM_CLOSE | **150s 未退出**；close 后 exitstate **恒 0**（从未闩 1）、frame=0 | ✗ |
| R4 零错误 | 趟窗事件日志零 AV；#32770=0 | ✓（except_after=None 见下缺陷） |
| R5 回滚 | a8=PASS、载体删净、母本四哈希不变；卸载段（守卫+exitbail 两事务 FNV 相等）见日志 | ✓ |

**机制读法（观察事实，未定谳）**：局内关窗臂 exitstate 从未到 1 ⇒ 卡在 c″ 靶点（`exitstate==1` 才放行）
**之前**的退出链阶段——与菜单态臂（exitstate 闩 1 后僵尸）**不同形**。⇒ c″ 的「退出场景」判据范围
**实证限定为菜单态/退出序列已达臂**；局内关窗挂死是**新开放项**（X 系列离线分析下一张卡：
局内 WM_CLOSE 到 exitstate 写点 0x6BE0B6 之间的路径为何 150s 不达，帧钟=0 先于一切 ⇒ 疑主循环
在 teardown 前已停摆）。**不重跑同形真机**（C26-01 失败处置=保全现场+最小反证，本趟即现场）。

**本轮采证缺陷（如实登记，已修）**：L1REG 的 `_cleanup` 把 except.txt 检查放在 rmtree **之后**
⇒ `except_after=None`（AV 通道以事件日志零命中补齐）。脚本已改为先取证后删（`_drive_c2_l1_regress.py`
20261026 修注）。教训与 ab24「except 零新增≠没崩」同族：**物证必须先摘除再销毁**。

## 五、① 环境门（C26-02）：本开机会话（10-25 08:36）恢复可用

- e4 趟（harness7 keep-rect 对照臂，`--extra-argv` 值以 `=` 语法传入——`--extra-argv "--x"` 被
  argparse 当新选项拒收，e3 发射失败零副作用）：**pre_fps15=30.692 ≥ 25 ⇒ 31 档可判**，units0=702，
  NAV=OK，W0 verdict=ok（fps_avg 29.44 / p50 32.62ms / p99 61.0 / **max 69.58ms**；
  >34ms 37.8% / >40ms 15.5% / >50ms 5.3% / **>80ms=0**）⇒ 贴帽、**无塌方**。
- W1 logic_frames=-3557 / max_stall 15.7s、W2=0 帧 / 11.9s ⇒ 读法=**关卡自然终局**（§436/H-5
  家族），不是卡顿样本；不作卡顿判据。
- e1 趟（短路臂）：units0=0 + no_advance ⇒ **作废趟**（短路跳过矩形等待后 measure 早于进局，
  档位证据未取得——与 §423 hb 同型缺陷，判档器问题在他线已登记）。
- **C26-02 判定：环境合格、负载在位、未复现真实卡顿 ⇒ C1/C2 保持冻结、不派优化实施**；
  702 单位档浅尾（max<70ms）与 971 单位 T50 基线（p90 35.2-37.4、唯一 110.7ms）同向。
  要动 ① 需**持续战斗覆盖测量窗**的更深绞肉档（T55k 级），本轮不烧趟数。

## 六、独立核验（C26-05）与 persona 缓存实况

- `ra2-patch-verifier`（钉 qfmodel+**thoughtLevel max**）发射失败：qfmodel 现档面=disabled/enabled，
  max 不支持（reasoning-level-not-supported）；`ra2-re-analyst`（glm-5.3-flash）也失败
  （reasoning-level-missing）⇒ **两 persona 均不可启动，登记缓存失效**（不绕闸自改 persona 文件——
  那是他线写域资产；交用户/下轮按 C26-05 处理）。
- 改经通用代理直指在册异族档 `new-provider-3/qoder-cn:qfmodel` 派发 V1–V7 全清单核验
  （判定书应落 `c2ab/XVERIFY_C2AB_20261026.md`；**判据=查文件在盘**，completed≠交付）。
  本轮台账先行，核验结果（CONFIRMED/REFUTED）在判定书落地后回登。

## 七、卫生与账目

- 6 趟全在本线写域载体（≤130 门禁内）；趟间残留=0（每臂 a8 复验）；母本四哈希全程不变；
  ra2youli 未触碰（该路径本机不存在，现役安装零暴露）；`D:\\ra2dumps` 本轮零新增；
  except.txt 母本区零写入（各趟载体内哈希不变）。
- git：本轮**未提交**（C26-03：外层 Bash 整树闸未解除，台账随工作树落盘；无重试消耗）。
- PENDING：无新裁决点——C26-01 已把 A/B 授权、判据 v2、范围限定条款全部先行裁死；
  局内关窗新开放项**不是裁决、是排期**（下一张卡 §438 七.①）。

## 八、下一张就绪卡（不承诺轮数）

1. **X-局内关窗死因**（离线，快照 `73201cc0` 只读）：WM_CLOSE 局内路径 → 0x6BE0B6 写 exitstate=1
   之前断在哪；判据=分支图闭包，不用 NOP/首 ret 截断。产出=是否值得为局内臂扩第二靶点的设计件。
2. **XVERIFY 回执登记**：判定书在盘后逐条对照，红项按「抓不住变异降级不修补」处置。
3. ① 持续战斗负载档（T55k 级）择机——环境门已绿，缺的是「战斗覆盖测量窗」而非会话。
4. 提交积压（D-08 附带义务）继续分批；本线新件 `_drive_c2_ab.py`/`_drive_c2_l1_regress.py`/
   `c2ab/` 归本轮待提交清单。
"""

cur = TARGET.read_bytes()
lf_only = b"\r\n" not in BODY.encode("utf-8")
# 台账主体 LF、段间偶有 CRLF——按 §437 尾行行尾追加（尾 2 字节 = CRLF）
tail_nl = "\r\n" if cur.endswith(b"\r\n") else "\n"
add = tail_nl + BODY.replace("\n", tail_nl if tail_nl == "\n" else "\r\n")
new = cur + add.encode("utf-8")
TARGET.write_bytes(new)
print("appended %d bytes; file now %d bytes" % (len(add), len(new)))
print("CRLF count:", new.count(b"\r\n"), "bare LF:", new.count(b"\n") - new.count(b"\r\n"))
print("head of appended:", new[-len(add):][:60])
