# LEAD_NOTE · W45 双轨对照的可疑点（待它自己交付后核对）

> 记录人：Lead（本会话）｜ 时间：2026-11-13 21:10
> 状态：**观察记录，未下最终判定** —— 卡尚未交付 `EQUIVALENCE_RESULT.md`（截至 21:10，仅 `EQUIVALENCE_SPEC.md` / `UNKNOWNS.md` / `DISAGREE.md` / `REAL_DIR_PROOF.txt` + `out\`）

## 1. 观察到的事实（`[本次实测]`）

`out\dual_track_results.json` 三臂：

| 臂 | `scen_filename` | `battle_cnt` | frame（局内 → 计时后 → 存档后） |
|---|---|---|---|
| A1 | `SOV01UMD.MAP` | **14** | 60 → 2417 → 2418 |
| A2 | `SOV01UMD.MAP` | **14** | 44 → 2399 → 2509 |
| **B1** | `SOV01UMD.MAP` | **14** | 39 → 2396 → 2397 |

`out\w45_dual_track.ndjson` 里与阶段相关的记录**只有 6 条**：
```
arm_start {arm:A}   arm_end {arm:A}
arm_start {arm:A}   arm_end {arm:A}
arm_start {arm:B}   arm_end {arm:B}
```
⇒ **B 臂没有任何 build / install / verify 事件**。

## 2. 为什么这构成问题

`[转引·W44]` 装 v12 包后真机实测 `battle_cnt = 15`（14 官方 + `RA2F1`）。
`[本次实测]` 而 B1 显示 **14** ⇒ 与未装包的 A 臂相同。
`[推断]` **B 臂很可能没有真正安装包**，因此 A 与 B 实际是同一状态，**这个"等价性对照"目前是空的**（A vs A）。

`[卡自己的规格明令]` `EQUIVALENCE_SPEC.md:140`：「**A 与 B 必须成对**：不得把 A 换成另一天/另一台机/另一份 `RA2MD.INI` 的读数…」
`[卡自己列的白名单]` `EQUIVALENCE_SPEC.md:32`：「装包必然引入**安装态差异**（新增文件、清单/seal、**`battle_cnt` +1** 等）。这些是设计预期的自变量结果」——**即它自己预期 B 臂应有 `battle_cnt` +1**。实测没有 +1。

## 3. 我要在签发时核对的四件事

1. `EQUIVALENCE_RESULT.md` 是否**如实披露** B 臂未安装、或给出安装成功的证据（install 日志/`verify` exit 0/清单）
2. 若 B 臂确实未装包，**是否把这一臂的结论作废**，而不是把"A vs A 无差异"写成"行为等价成立"
3. `UNKNOWNS.md` 是否已把这项列为未闭合
4. 若它提出"B 臂装了但 `battle_cnt` 仍 14"的其它解释（例如它用了不含 battle 条目的 design），是否给出可核验依据

## 4. 此刻不下结论的理由

`[纪律]` 卡还在跑（`arm_end` 之后应还有收尾与报告）。**在它交付结果文档之前，我不把"对照为空"写成定论** —— 但这条观察必须留痕，避免它交出一份"等价成立"的报告时我无据可查。
`[若最终证实 B 臂未装包]` 则 B 线「行为等价性」**仍未兑现**，且这次是"看起来做了、其实对照组是空的"，比没做更危险。
