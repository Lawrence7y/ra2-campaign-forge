# W178-PATCH DISAGREE / 一致性核对

## 与 W178 / §933 的核心数字核对：**无 DISAGREE**

| 项 | W178/§933 | 本卡独立复核 | 一致 | 证据 |
|---|---|---|---|---|
| `call 0x724730` 命中 | 30 | 30 | ✓ | `EVIDENCE/core.json:call_count`；全 `.text` skipdata 线性反汇编 |
| 可达 NULL 站点 | 26 | 26 | ✓ | `core.json` `reachable∧static-ref`=26；`EVIDENCE/BASELINE.txt` BNUL 0/200 证明非基线假象 |
| 零静态引用站点 | 4 | 4 | ✓ | `006D1541/006D155C/006D15CB/006D1605` |
| `ecx` 最后写入 `[0x887368]` | 30/30 | 30/30 | ✓ | `DESIGN_FACTS.txt` `this=mem [0x887368]` |
| 零守卫 | 0/30 | 0/30 | ✓ | `core.json` `zero_guard`=0 |
| `0x6CD8CD` 可达 | 是（48 节点/12 项跳表 case 9） | 是（path_len=48，跳表 12 项） | ✓ | `core.json:s6` |
| 崩溃点 | `EIP=0x724737` fault `0x250` | 同（`mov eax,[ebp+0x250]`, ebp=ecx=0） | ✓ | `core.json:callee` |

## 引节号 / 文件
- `R14_COMMON.md` §0 表格 ②-a 行："`0x724730` 的 30 个无守卫调用点与 `0x6CD8CD` 仍是已知缺口" —— 本卡数字一致；本卡在其上补候选件，不改缺口结论。
- `STATUS_BOARD.md` ②-a 段与「Lead 口径裁定」：W178 记 26/30 —— 一致。
- `W178_guards\PROGRESS.md` §核心数字 1/2/3、`W178_guards\_audit\VERDICT.md` §1 —— 本卡全部独立复现。
- **沿用 W178 的措辞更正**：30 处是 `E8 rel32` **直接 thiscall**，非"虚调用"（`VERDICT.md` §2）。本卡一律写"无守卫直接调用点"。

## 与 W178 的方法差异（非结论冲突）
- W178 做风险分级（26 `[静态推断]` + 4 `[未证]`）；本卡在其上做**补丁候选件设计**与离线单测，不重判证据等级。
- 本卡新增发现：callee `ret 4` 决定朴素守卫会泄漏栈参数（`BASELINE.txt` B2 30/30）；此点 W178 未涉及，非冲突。
