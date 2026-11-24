你是 RA2 Campaign Forge 项目的执行代理。任务：**修好 W25 遗留的两个具体缺陷，让 39 个用例全绿。**

## 现状（Lead 亲自复跑确认，可直接引用；**不要重做已完成的部分**）
上一个代理在写报告前死亡，但**代码与失败证据都在盘上**：

- `lead\next_re_20261112_r02\W25_dlc_unseal\ra2forge_patched_v8\ra2forge\` —— v8 包，**编译通过**（`py_compile` exit 0），`TOOL_VERSION = 0.8`。
- `lead\next_re_20261112_r02\W25_dlc_unseal\regress_dlc_v8.py` —— **39 用例，能跑完（24 秒）**。
- **Lead 复跑结果：36 通过 / 3 失败 / 脚本 exit 1。**
- 报告类文件（`UNSEAL_FIX.md` 等）**全部缺失**。

### 已确定修好的部分（U1–U6 全 PASS，**不要动**）
```
PASS U1 (9/9)  seal 只读时 uninstall 的主流程与报告
PASS U2 (6/6)  正常 uninstall 对照（seal 被删、无警告、exit 0）
PASS U3 (8/8)  U1 之后再 uninstall
PASS U4 (6/6)  U1 残留状态 verify
PASS U5 (7/7)  恢复路径（清障碍→重装同包→verify→uninstall）
PASS U6 (23/23) --json 三态与人类可读一致
```

### 只剩两个缺陷要修（**就是你唯一的任务**）

#### 缺陷 1：`R2` —— 回滚失败时，**包文件没被回滚**（回滚不原子）
失败断言原文：
```
R2: package files rolled back (created files removed) - the tree is exactly golden + the standing record ... FAIL
```
注入方式（`tools\v8_rollback_fault_driver.py`）：在「install 记录已写、seal 未写」的窗口内
把**新记录**设为只读（`os.chmod(..., S_IREAD)`），使 **① seal 写失败** 与 **② 清单回滚写自身失败** 都成为真实 OS 错误。

`R1`（17/17 PASS）已证明：此时**新记录会留存**、`verify` exit 8 —— 这是"记录回滚失败"的既定结果，**不需要你改这一点**。

**你要修的是**：`R2` 断言说，在同样注入下**本次安装创建的包文件没有被移除**，目录 ≠ `golden + 标准记录`。
⇒ **包文件的回滚必须与「清单回滚」解耦**：记录恢复失败**不得**中断/跳过"已创建文件的移除"与"已替换文件的还原"。

请定位 `ra2forge_patched_v8\ra2forge\install.py` 里回滚/undo 的执行顺序与异常传播：
很可能"记录恢复"排在"文件回滚"之前且未被隔离，一旦记录恢复抛错，后面的文件回滚就整段跳过。
修法方向（由你判断，但必须满足下面的判据）：
- 文件回滚与记录回滚**分别 try/except 隔离**，任一失败都要**继续做其余部分**；
- 全部失败项**汇总进同一个错误/警告结构**，不丢掉任何一项；
- 不得用"吞掉一切异常"的方式假装成功（必须显式记录"哪一步失败了"）。

#### 缺陷 2：`F7` —— `uninstall` 的 `actions` 完整性仍未达成
失败断言原文：
```
F7 (W25): actions intact - every recorded file restored/removed and the record deleted ... FAIL
```
（`F7` 是「seal 只读时 uninstall」场景；`22/23` 通过，只差这一条。）

⇒ `uninstall` 在收尾异常时，`actions` 必须**完整**反映：哪些文件**已还原**、哪些**已移除**、哪些**未做成**、
以及**记录是否被删除**。不得因收尾异常丢失已完成动作的报告。

## 硬性要求
1. **保留 39 个用例，一条不许减、不许放宽判据**；修好后 `F7` 与 `R2` **必须转绿**，`U1–U6` 必须**仍然全绿**。
2. 正常路径（无注入）行为**零变化**：`R0` 与 `U2` 必须仍 PASS。
3. 三处文档的退出码表保持**一致**：`--help`、`W23` 的 `VERIFY.md` 同族口径、以及你要新写的 `UNSEAL_FIX.md`。
4. **先写报告骨架再跑测试**（上一个代理死在写报告前，什么都没留下）。至少先落盘：
   `UNSEAL_FIX.md`（缺陷复述 + 修复设计 + 判据）、`UNCOVERED.md`、`DISAGREE.md`，跑测试后再补数字。

## 授权与安全（**严禁触碰真实游戏目录**）
- 用户已授予全部动作与自行裁决，但**全程隔离沙箱**：`lead\next_re_20261112_r02\W26_dlc_unseal_fix\sandbox\`。
- **绝不**对 `D:\Project\ra2-campaign-forge\ra2youli` 做任何写操作（那里有旧会话的 ra2forge 包 v0.3，属他人产物）。
- **禁止**修改仓库 `ra2forge/`，以及 `W21`/`W22`/`W23`/`W24`/`W25` 的既有文件。
  ⇒ 把 `W25_dlc_unseal\ra2forge_patched_v8\` **复制到你的写域**再改（`W26_dlc_unseal_fix\ra2forge_patched_v9\`）。
- **禁止** `git` 写操作。

## 环境
- 仓库根 `D:\Project\ra2-campaign-forge`，`main@3872ef6`。run_id = `NEXT_RE_20261112_R02`。
- **写域只有** `lead\next_re_20261112_r02\W26_dlc_unseal_fix\`。
- Python 3.12.10（Windows）。
- 只读参考：`W25_dlc_unseal\**`（v8 包、`regress_dlc_v8.py`、`tools\v8_rollback_fault_driver.py`、`out\R1.log`、`out\R2.log`、`out\F7.log`）。

## 交付（`W26_dlc_unseal_fix\`）
- `ra2forge_patched_v9\`（完整可运行包，`TOOL_VERSION` 建议 0.9）
- `PATCH_RELATIVE.diff`（**相对路径**）+ `APPLY.md`（改前/改后哈希、回滚步骤）
- `regress_dlc_v9.py` + `out\`（39 用例日志）
- `UNSEAL_FIX.md`：**缺陷 1/缺陷 2 的根因定位（给 文件:行）**、修复设计、39 用例结果表、退出码表
- `UNCOVERED.md`、`DISAGREE.md`

## 质量红线
- **不得**减用例、不得放宽判据、不得用"吞异常"假装通过。
- **不得**触碰真实游戏目录或他人交付目录。
- 每个失败修复都要给**注入前后的对照输出**，不能只说"修好了"。
- 「没测」≠「通过」；若某条你判断修不了，**如实写清根因与后果**，不要伪造绿色。

## 回给我的摘要（≤30 行）
① v9 基线哈希与改动文件（给 文件:行）；
② **缺陷 1 根因**（回滚顺序/异常传播的具体位置）与修法；
③ **缺陷 2 根因**与修法；
④ 39 用例结果：通过/失败/脚本退出码；**F7/R2 是否转绿**；**U1–U6 是否仍全绿**；
⑤ 正常路径零变化证据（R0/U2 结果）；
⑥ 三处退出码表是否一致；
⑦ 是否触碰真实目录（应为"否"）；
⑧ 未覆盖与不确定项。
