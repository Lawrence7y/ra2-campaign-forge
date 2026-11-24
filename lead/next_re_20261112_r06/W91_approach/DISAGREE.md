# W91_approach DISAGREE

本卡对任务卡/上游叙述的分歧与更正记录。只记证据可查的条目，逐条给落点。

## D-1（lead 2026-11-14 消息）：崩点签名归并需更正 —— P1 与 P2 是**两种不同** AV，lead 引用的 `EIP=0x006F36FE / Access=0x11378560` 只匹配 P2

- **证据**（`EVIDENCE\trip_P1_archived_except.txt`，sha256 前缀 `F8F6BC24…`，= `archived_late_except` 同哈希）：
  - `Error code: EXCEPTION_ACCESS_VIOLATION`
  - `Access address:00000000 was read from.`
  - `Details: Eip:00000000  Esp:00F9D058  Ebp:000022C0`（栈顶返回地址 `0047C500`，见 stack dump）
- **证据**（`EVIDENCE\trip_P2_archived_except.txt`，sha256 前缀 `3429FF45…`）：
  - `Access address:11378560 was read from.`
  - `Exception occurred at 006F36FE`
  - `Details: Eip:006F36FE  Esp:00F9D04C  Ebp:15B6AA98`
- **裁定**：lead 消息写「P1/P2 的 except.txt 是 EIP=0x006F36FE、Access=0x11378560」——对 P2 成立，对 P1 **不成立**（P1 是 Eip=0 的空指针调用）。按 lead 自己的纪律「不要合并」，本卡把 P1、P2 记为**两个独立条目**（见 UNKNOWNS U-1 / U-2），均与 W88 的 `0x47C538/[eax+0x2C]`、R03 转述的 `0x51C2D3/[eax+0x1D4]` 不同。`[本次实测]`
- 落点：`EVIDENCE\`（四份副本两两同哈希，P1 26,579 B / P2 26,497 B）。

## D-2（lead 2026-11-14 消息）：v1 设计对象数不可比 —— 采纳

- v1（P1/P2）玩家侧不放单位 ⇒ 场景 ~220 对象，对照臂 C6/CTRL_C6 = 1522 对象。P1 A=8.77 %、P2 A=10.91 % 远低于两带，主因是场景太轻（渲染+寻路对象基数差 7 倍），**不得**据此写「行军贡献 X 个百分点」。判读改为同趟内 A/B 比值（预注册 v2 已写死在 PROGRESS.md，早于 trip_P3 运行）。`[本次实测]`

## D-3（lead 2026-11-14 消息）：「Crewed=no（W88-C7-proven）」措辞错误 —— 采纳更正

- W88 C7 的结论是 **Crewed=no 并未阻止崩溃（1/1 崩）**，不是「已证有效」。P2 挂 Crewed=no 仍在接触后 ~7 s 崩溃，与 C7 一致。本卡此前 PROGRESS 步骤日志里的错误措辞以此条为准更正。`[静态推断]`（引 W88 记录）
