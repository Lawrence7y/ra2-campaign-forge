# W25 状态：**未完成（代理中途死亡）**，但留下两处真实缺陷的失败证据

> run_id `NEXT_RE_20261112_R02`｜Lead 亲自复跑｜2026-11-13
> **本文件不是交付验收，是失败状态与遗留证据的登记。**

## 1 · 事实状态（[本次实测]，Lead 亲自跑）

| 项 | 结果 |
|---|---|
| `ra2forge_patched_v8/` 能否编译 | ✅ `py_compile` exit 0，`TOOL_VERSION = 0.8` |
| 回归套件能否运行 | ✅ 能跑完（39 用例，24 秒） |
| **套件结果** | **36 通过 / 3 失败，脚本 exit 1** |
| 报告类交付（`UNSEAL_FIX.md`/`UNCOVERED.md`/`DISAGREE.md`/`APPLY.md`） | **缺失**（代理死在写报告之前） |
| 真实游戏目录 | ✅ 未动：`RA2MD.INI` `c91c6a47…`、地图类 **277/277** |
| 残留游戏进程 | 0 |

## 2 · 三个失败项是什么（关键：不是测试坏了，是断言逮到了真缺陷）

### 2.1 `R1`（**17/17 全 PASS**）—— 它把"回滚声明被夸大"证实了

注入方式：在「install 记录已写、seal 未写」的窗口内，把**新记录**设为只读（`os.chmod(S_IREAD)`），
使 **① seal 写失败** 与 **② 回滚写自身失败** 两件事都成为**真实 OS 错误**（非合成 raise）。

断言全部通过，其中三条最有价值：
```
R1: the seal write failed with the REAL os.replace error (WinError 5, not a synthetic raise) ... PASS
R1: the NEW record STANDS - the manifest is NOT the previous bytes (the restore write failed and was swallowed) ... PASS
R1: the fresh manifest was locked read-only by the in-window act (its own undo is what failed) ... PASS
```
⇒ **`install.py` 里那处 `except OSError: pass` 会把"清单回滚失败"吞掉，导致新记录留存**，
随后 `verify` **exit 8**（seal 与清单不配对）。
**这直接否证了 v7 docstring 那句「install never leaves a seal-era record standing without its seal」的普适性**——
在"回滚自身也失败"的复合故障下，它会留下配不上的记录/seal 对。

### 2.2 `R2`（12/13，1 项 **FAIL**）—— 新证实：回滚失败时**包文件没被回滚**

失败断言原文：
```
R2: package files rolled back (created files removed) - the tree is exactly golden + the standing record ... FAIL
```
⇒ 在"记录回滚失败"的同一注入下，**本次安装创建的包文件没有被移除**，目录**不等于** `golden + 标准记录`。
即：**回滚不是原子的**——它会"删一部分就不删了"。

### 2.3 `F7`（22/23，1 项 **FAIL**）—— `uninstall` 的"actions 完整"仍未达成

```
F7 (W25): actions intact - every recorded file restored/removed and the record deleted ... FAIL
```
⇒ v8 的 `U1`（seal 只读时的 uninstall 容错）用例**通过了**，但**"每个记录文件都被还原/移除且记录被删除"这条更强断言仍失败**。
说明 W25 想修的收尾缺陷**只修好了一部分**。

### 2.4 U1–U6 全部通过（`uninstall` 容错主线是有效的）

```
PASS U1 (9/9) PASS U2 (6/6) PASS U3 (8/8) PASS U4 (6/6) PASS U5 (7/7) PASS U6 (23/23)
```
⇒ **三态语义 + `--json` 一致性 + 正常路径零变化 + 恢复路径** 这几件事**做到了**，
缺的是上面 §2.2/§2.3 两条硬骨头。

## 3 · 因此 W25 的正确处置

- **不签收**：报告类交付缺失，且 3 条断言失败。
- **不丢弃**：`regress_dlc_v8.py`（39 用例）是**可运行的失败证据**，比一份"全绿报告"更有价值——
  它把两个未修好的路径钉在了盘上。
- **v8 包**可用于后续演进（编译通过、U1–U6 有效），但**不得**被当作"已修复 uninstall 收尾"的成品。

## 4 · 下一张卡应做的事（明确、有界）

1. **修 R2 的语义**：回滚失败时，**包文件的回滚必须独立于记录回滚**——
   记录恢复失败**不得**中断"已创建文件的移除"。当前实现把两者绑在同一条失败链上。
2. **修 F7 的 `actions` 完整性**：`uninstall` 在 seal 只读时，`actions` 必须完整反映
   "哪些文件已还原/已移除/哪些没做成"，不能因收尾异常丢失。
3. **确认复合故障的最终状态是否可被工具恢复**：R1 已证会留下 `verify exit 8` 的对；
   要么提供**明确且安全**的恢复路径（重装同包重盖 seal），要么在文档里**明确写"不可恢复、需手工处理"**——
   不许含糊。
4. **保留 `regress_dlc_v8.py` 的 39 用例，一条不许减**；修好后 F7/R2 必须转绿。

## 5 · 一条方法论记录（本会话反复出现）

这是本会话**第二次**代理中途死亡（前一次 W13 attempt2 把探针放进自身上下文后台 job）。
两次的共同点是**长任务 + 大量文件产出**。有效对策已验证：
**探针/长任务用 WMI 脱离进程树 + `finally` 自愈**；而**报告类交付要尽早落盘**，
不要等到所有测试跑完才写——否则一旦死亡，只留下代码不留解释。

W25 这次至少把**失败证据**留在了盘上，这比留一份漂亮报告有用。
