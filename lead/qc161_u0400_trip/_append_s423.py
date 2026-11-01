#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§423 追加器：字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §423 真机 H-1 三趟跑完 —— harness7 冒烟核心两臂全过，§422 修复被真机证实

**用户授权**：本轮起「只要用户不说拒绝，可自主真机实验」。三趟串行发射，
全程经发射器 `_launch_l1_20261023.py`（Arm A 原版直启 + 零注入），趟间做进程卫生。

## 一、发射前被门禁当场抓出的第二把错尺（§422b 已预检修正）

第 1 趟首发射 `--suffix h7a` 被发射器 **BLOCK**：
`out-dir 预演 len=131 (门禁 130) BLOCK`。
★ 我 §418 预检量的是 `out_dir\\ct`=110（判「余 17」放行），
  而发射器 `:250` 量的是**占位符全长** `out_dir\\ct\\c_000000000000_12345`=131。
  两尺差 21 字符 ⇒ 预检 16 条全绿却发射即 BLOCK。
★ 这是 §418b「sum 当总时长」的**同族第二次**：判据度量对象取错（不是阈值算错）。
  正解 = **逐字复用发射器公式**（消费方口径）。已在 `_preflight_h1.py` 修尺 +
  加阳性对照 P-GATE2（旧 suffix 同公式必须 >130，真机实证吻合）。
⇒ 改用 2 字符后缀 `ha/hb/hc`（占位符口径恰 130 ≤130 过门），发射器零改动、
  母本零污染，门禁原样生效。这是「门禁对、我尺子错」的正路：迁就门禁，不绕门禁。

## 二、三趟结果（全 rc=0，趟间无残留、无载体泄漏，母本四哈希未变）

| 趟 | 后缀 | 模式 | 用时 | 关键实测 |
|---|---|---|---:|---|
| 第1趟 | ha | 窗口 | 89.2 s | **nav INCOMPLETE**（failed_at=nav_menu） |
| 第2趟 | hb | 全屏短路 | **63.4 s** | frame=**0.079 s**，polls=0 |
| 第3趟 | hc | 全屏对照臂 | **184.2 s** | frame=**122.203 s**，polls=244 |

### 第2趟 hb —— harness7 核心收益实证（冒烟 4/4 PASS）

```
META.fullscreen=True  META.h7_fs_rect_wait_skipped=True
FRAME.h7_fs_rect_wait_skipped = {'skipped':True,'rect_at_skip':[0,0,2560,1440],...}
pre_capture_wait_polls = 0        stage_seconds:frame = 0.079 s
MEASURE.h7_nav_to_measure = {nav_to_measure_s: 0.079, limit_s: 90.0, late_start: False}
⇒ 判型 fullscreen_short，四条判据全 PASS
```
★ **短路把 frame 段从 harness6 的 122–127 s 压到 0.079 s**（≈1540×），
  与 §419 用恒等式反推的「采帧+分类=0.000–0.219 s」完全吻合（0.079 落带内）。
★ **边界 2 的唯一实测数到手：`nav_to_measure_s = 0.079 s`**（≪ 阈值 90 s）
  ⇒ 90 s 阈值**无需重标**，且证明短路后 nav→measure 几乎零间隔（设计预期兑现）。
★ 时长账：hb 63.4 s ≪ 预算 540 s；全程无 late_start。

### 第3趟 hc —— §422 修复的真机试金石（冒烟 5/5 PASS）

真机对照臂的**真实字段形态**（此前只有合成样本，§422 就是靠这个差异抓的缺陷）：

```
META.h7_fs_rect_wait_skipped  = False     ← :7378 写了
FRAME.h7_fs_rect_wait_skipped = None      ← 被 if skipped 挡住，真机不写 ✓
MEASURE.h7_nav_to_measure      = None      ← keep 臂不写 n2m ✓（§421 预期）
pre_capture_wait_polls = 244   stage_seconds:frame = 122.203 s
⇒ 判型 fullscreen_keep，五条判据全 PASS（含 late_start=None 通过 = 设计不变量兑现）
```
★★ **这趟直接证明 §422 修复是必要的**：判档器若还按旧码读 FRAME，
  真机 hc 会读到 `None` ⇒ 判「不是冒烟样本」⇒ **对照臂判据永不执行**（整趟白跑）。
  修复后读 META=False ⇒ 正确判 keep。合成样本三层都掩盖不了，真机一趟就揭穿。
★ keep 臂 122.203 s 复现 harness6 死等（A/B 对照成立）：hb 0.079 s ⇄ hc 122.2 s。
★ hc 184.2 s 超我 §418b 估的 161.7 s——因走全屏预算 540 s，未爆。
  但 w0 `pre_fps15=0.0 / units0=672` = 帧冻结死法（H-5/U8 家族），档位证据未取得。

### 第1趟 ha —— 窗口臂结构性不可测，非 harness7 缺陷（须单列裁决）

```
early_frame: rect=[0,0,2560,1440] capture_ok=False   ← 抓帧失败
WIN.stab_rect_series 全程恒 [0,0,2560,1440]（游戏按 cnc-ddraw windowed=false 全屏呈现）
NAV.wait_screen_pre: cap_ok=False → 主菜单签名判不出 → 2 次尝试均 pre_ok=False → INCOMPLETE
MEASURE.skipped={reason:'nav_verdict!=OK', windows_run:0}  ← 按设计不采窗
```
★ **根因 = 载体 `ddraw.ini` 的 `windowed=false`**（这是 boot-hang 修复配置，
  见 [[boot-hang-cnc-ddraw-windowed-stall-solved]]）。窗口模式 harness 要 800×600
  窗口矩形 + GetWindowDC 抓帧，但 `windowed=false` 下游戏恒全屏 ⇒ 抓不到 ⇒
  主菜单签名失效。**窗口臂与当前载体的呈现配置互斥，是测试构造矛盾，不是被测物缺陷。**
★ 历史窗口趟（archive_T*，polls=0 那 29 份）跑的是另一套 ddraw.ini（窗口态），
  与本载体的 boot-hang 修复版不同源。⇒ §419 的 `windowed.polls_max` 阈值仍成立
  （那些趟是窗口态载体产物），只是**本次载体开不出窗口趟**。

## 三、S399 §九 五条判据最终验收态

| 条 | 判据 | 真机结果 |
|---|---|---|
| 1 | 窗口模式不写 skipped | **N/A-环境**（窗口臂在本载体开不出，见上） |
| 2 | 全屏短路：skipped=True / polls=0 / frame<2s / nav_to_measure_s | **PASS**（0.079 s） |
| 3 | 对照臂：polls 回 244–253 / frame 回 ~125s / late_start 不出现 | **PASS**（244 / 122.2 / None） |
| 4 | 趟前后卫生：残留 0、母本哈希核对 | **PASS**（三趟全绿，四哈希未变） |
| 5 | 三趟都过⇒升在用件 | **部分**：2/3 全屏臂全过；第 1 臂环境不可测 → 见 D-08 |

★ 按 §九 第 5 条严格口径「三趟都过」未满足（第 1 趟非 harness7 之过）
  ⇒ **本轮不擅自升 harness7 为在用件**，交 D-08 裁决。

## 四、卫生与铁律

- 三趟串行，发射前 `taskkill` 清残留（A8=0 才发）；趟后进程 0、`out/ct`=空。
- 母本四哈希：harness6 `ff8245d2` / harness7 `d019e8be` / gamemd `73201cc0` /
  map `0add791d` **全部未变**。
- 全程 Arm A 原版直启、零注入；`--measure 1` 按 S399 设计。
- 载体三门禁（130 占位符 / 88 件清单 / 三 sha 预检）全部**原样生效**，
  未绕任何一条——迁就门禁改后缀，不改门禁。

## 五、待办移交（写进 D-08 与台账）

1. **窗口臂要么单独配一套 `windowed=true` 的 ddraw.ini 载体重跑第 1 趟**
   （须重做 boot-hang 规避，成本高），**要么正式把 §九 第 1 条改判 N/A**
   （核心理由：窗口模式的 skipped 语义已被 29 份历史窗口产物 + 本趟的
   MEASURE.skipped 设计行为双重佐证）。→ D-08 用户/Lead 裁。
2. **harness7 升级判定**挂起至 D-08 落定。
3. 三趟 w0 均未取得档位证据（ha 没进战局、hb units0=0 停 skirmish_setup、
   hc 帧冻结）⇒ **① 基线仍需 T55 spawnfix9 那一档**（与 H-1 冒烟正交，
   H-1 目标是验 harness7 补丁，不是测 fps 基线）。
"""


def main() -> int:
    before = LEDGER.read_bytes()
    assert b"\r\n" in before
    crlf0 = before.count(b"\r\n")
    assert before.endswith(b"\n")

    body = SECTION.lstrip("\n")
    payload = body.replace("\r\n", "\n").encode("utf-8")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, (
        "CRLF 数必须不变：before=%d after=%d" % (crlf0, after.count(b"\r\n")))

    LEDGER.write_bytes(after)
    print("appended %d bytes; total %d -> %d"
          % (len(payload), len(before), len(after)))
    print("CRLF preserved: %d" % crlf0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
