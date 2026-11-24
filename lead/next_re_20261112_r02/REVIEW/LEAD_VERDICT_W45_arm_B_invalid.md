# LEAD_VERDICT · W45 双轨对照的 B 臂**无效**（根因已定位）

> 判定人：Lead（本会话）｜ 时间：2026-11-13 21:18
> 依据：W45 落盘的原始日志（非其摘要）

---

## 1. 结论

**W45 的 B 臂（改造臂）根本没有装上包，因此 A/B 等价性对照目前是 A vs A，结论无效。**

`[本次实测]` 证据链（全部来自 W45 自己的 `out\`）：

1. `cmd_B1_install_v13.log`：
   ```
   CMD: python -B -m ra2forge install --package "...\pkg_v13\W45 Equivalence Probe"
        --game ...\sandbox_B1 --json
   EXIT: 2
   stderr: python -m ra2forge: error: unrecognized arguments: --json
   ```
   ⇒ **安装命令直接失败（exit 2）**，v13 的 `install` 子命令**不接受 `--json`**。

2. `cmd_B1_verify_post.log`：`EXIT: 0`，但输出是
   ```
   "manifest_present": false,
   "warnings": ["no ra2forge_install.json in ... - nothing to verify
                (an install with 'python -m ra2forge install' writes it)"]
   ```
   ⇒ 这是**空过**：无安装记录时 `verify` 恒返回 0，语义是「没东西可查」，**不是「通过」**。

3. `out\dual_track_results.json` 三臂 `battle_cnt` 全 **14**（A1 / A2 / B1），而 `[转引·W44]` 真机装包后应为 **15**（14 官方 + `RA2F1`）。
   ⇒ 与「B 臂未安装」完全自洽。

4. `out\w45_dual_track.ndjson` 里与阶段相关的记录只有 `arm_start` / `arm_end` 各 3 条，**没有任何 install 事件**（安装失败，脚本未把它当致命错误记录为独立事件）。

---

## 2. 这暴露的两层问题

### 2.1 卡侧：两个驱动缺陷
- **A. 安装命令参数错**：`install --json` 不被 v13 接受 ⇒ exit 2。卡未把非零退出当致命错误，继续跑完 B 臂。
- **B. 把 `verify exit 0` 当安装成功证据**：无 manifest 时 `verify` 恒 0，这是**空过陷阱**。W23 已明写「`package_digest` 只能证明清单内部一致，不能证明磁盘上是什么」，此处是它的镜像问题：**没有清单时，exit 0 什么都不能证明。**

### 2.2 产品侧：v13/v14 的 CLI 不一致（真实缺陷，非卡的责任）
`[本次实测]` `verify --json` 可用（返回结构化 JSON），但 `install --json` **不被识别**。
⇒ 这不是卡的笔误，而是 **ra2forge 自身的 CLI 参数不一致**。应作为缺陷登记，由 W46/W47 之后的卡修（或 W46 若已包含则确认）。

---

## 3. 对 B 线的后果

`[签发]` **B 线「行为等价性验证」仍未兑现**，且这次是**「看起来做了、对照组是空的」**——比没做更危险。
`[纪律]` 在 W45 交出结果文档后，我必须核：
1. 它**是否如实披露** B 臂安装失败（若不披露、或把 A vs A 写成"等价成立"，则该卡**不予签发**）
2. 它是否已重跑修正后的 B 臂（21:10 起它在跑 `cmd_A2_*`，可能是重做）
3. `UNKNOWNS.md` 是否列出此项

---

## 4. 给后续任何"等价性/对照"类卡的强制要求（新增纪律）

1. **驱动脚本必须把子命令非零退出当致命错误**，不得继续下一臂。
2. **不得用 `verify exit 0` 证明"已安装"**：必须同时要求 `manifest_present: true` 且 `files` 非空且含预期文件。
3. **对照臂必须有"自变量确实生效"的独立证据**（本例应为 `battle_cnt` 由 14 → 15）。若自变量没变，**该臂作废**，不得记为"无差异"。
4. **A 与 A 的差异只能当噪声基线**，不能当等价证据。
