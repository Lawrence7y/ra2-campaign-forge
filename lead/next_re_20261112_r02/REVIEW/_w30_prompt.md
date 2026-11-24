你是 RA2 Campaign Forge 项目的执行代理。任务：**给 ra2forge 补上 CSF 字符串文件的读/写能力**（纯离线代码任务，不启动游戏）。

## 为什么需要（真机已定谳的前提）
`ra2youli\BATTLEMD.INI` 自带注释（第 44 行）写得很清楚：
```
; Description = string file label of text description of campaign for player choice list
Description=DESC:ALL1
```
⇒ 战役条的 `Description=` 是 **CSF 字符串标签位**，不是纯文本。
而 `ra2forge` 目前把 `campaign.description` 的**原始文本**直接写进去
（`ra2forge/builder.py:262` `want_desc = design_mod.description_for(camp) or str(camp["name"]).strip()`），
真机实测结果：引擎显示 **`MISSING:'<我们的文本>'`**（把我们的文本当成标签名去查 CSF，查不到）。

**ra2forge 目前完全没有 CSF 能力**：`ra2forge/` 的模块只有
`__init__, __main__, builder, cli, design, format80, install, lzo, maplib, mixlib, triggers, verify`
—— 没有任何 csf 读写模块。而 `ra2youli` 下**没有散装 `ra2md.csf`**（在 MIX 里，如 `language.mix` 52,913,656 B / `langmd.mix` 84,643,206 B）。

## 起点
`lead\next_re_20261112_r02\W26_dlc_unseal_fix\ra2forge_patched_v9\ra2forge\`（`TOOL_VERSION = 0.9`，完整可运行包，
其 `regress_dlc_v9.py` **39 用例全绿**，Lead 已亲自复跑）。
把整个包复制到你的写域演进为 `ra2forge_patched_v10/`，`TOOL_VERSION` 建议 1.0。

## 要做的事

### T1 CSF 读取（先读，后写）
实现一个**独立的** CSF 读模块（如 `ra2forge/csf.py`）：
- 解析 CSF 头（magic ` FSC`、版本、标签数、字符串数、语言码等）与每条标签（`LBL` 头 + `RTS`/`STR`/`WRTS` 等值类型）；
- 支持 `STR`（普通字符串）与 `WRTS`（带扩展名/额外字段的字符串），**其它类型如实报告并保留原始字节**；
- 给出 **CRC/校验字段**的处理方式（若存在），并说明你的理解依据；
- **不依赖第三方库**（本项目风格是纯标准库）。
**验收**：能从 `ra2youli` 的 MIX 里提取出的任一份 CSF（用项目自带 `mixlib.py` 提取到你的写域）
读回**至少 100 条**标签且 `DESC:ALL1` 这类官方标签能查到其文本；把读回结果抽样打印。
**若提取不到 CSF**（MIX 打不开等）：**如实报告**，并改用**自建最小 CSF**（自己按格式写一个含 3 条标签的文件）做往返测试，
并明确标注"未经官方 CSF 验证"。

### T2 CSF 写入/追加（关键）
实现 `append_or_set_label(csf_path, label, text)`：
- 在**不破坏**原文件的前提下追加/更新一条标签；
- **保持格式自洽**：标签计数、字符串计数、偏移/索引（若有）、CRC（若有）必须同步更新；
- **必须做往返验证**：写后用 T1 的读模块读回，断言标签与文本**逐字节一致**，且**原有标签一条不丢**。

### T3 与构建链的最小接线（**只做最小，不改语义**）
- 在 `builder.py` 里增加一个**可选**步骤：若 design 提供 `campaign.description`，则
  **不再把它当标签写进 `Description=`**，而是：
  1. 生成一个**稳定标签名**（如 `RA2F:` + 包 id 的短哈希，避免与官方标签冲突）；
  2. 把 `Description=` 写成该标签；
  3. 在**构建报告**里明确列出"需把文本写入哪份 CSF 的哪个标签"，
     并在**产物目录**里生成一个可直接使用的 `ra2md.csf`（若 T2 能写全量 CSF 的话）或一个**补丁片段清单**。
- **默认行为必须可关**：新增 CLI 开关（如 `--csf-out PATH`），**不传则行为与现在完全一致**（向后兼容）。
- **不得**修改 `verify.py` 的既有语义；**不得**削弱 W26 的 39 个用例。

### T4 回归
- **必须保留** `W26_dlc_unseal_fix\regress_dlc_v9.py` 的 39 个用例（复制演进为 `regress_dlc_v10.py`，**一条不许减**），
  全部重指向 v10 包并**仍全绿**。
- 新增 CSF 用例至少：
  | # | 用例 | 期望 |
  |---|---|---|
  | C1 | 自建最小 CSF 往返（写→读） | 标签与文本逐字节一致，原标签不丢 |
  | C2 | 对真实官方 CSF（若已提取）追加一条后读回 | 新标签可读、**原标签数与抽样文本不变** |
  | C3 | 标签名冲突（重复 append 同一标签） | 定义为"更新"而非"重复追加"，计数不翻倍 |
  | C4 | 空文本 / 超长文本（如 4000 字符） | 不崩溃，往返一致 |
  | C5 | 畸形 CSF（截断/魔数错） | 明确报错，不崩溃、不写坏原文件 |
  | C6 | 不传 `--csf-out` 时构建 | **产物与 v9 逐字节相同**（向后兼容硬证据） |
每用例给**命令 + 原始输出 + 退出码 + 逐项判据**；脚本末尾打印通过/失败统计，非零码表示失败。

## 授权与安全
- **纯离线**：**严禁启动游戏、attach、读活进程、挂起线程、注入**。
- **禁止**写 `ra2youli`（**只能读**，且只读也建议尽量少读大文件）；**禁止**改 `W21`–`W29` 他人交付目录；
- **禁止** `git` 写操作。
- 写域：`lead\next_re_20261112_r02\W30_csf_capability\`。

## 环境
- 仓库根 `D:\Project\ra2-campaign-forge`，`main@3872ef6`。run_id = `NEXT_RE_20261112_R02`。
- Python 3.12.10（Windows）。禁全仓递归列举。
- 可复用：`ra2forge_patched_v9\ra2forge\mixlib.py`（读 MIX 取 CSF）。

## 交付（`W30_csf_capability\`）
- `ra2forge_patched_v10\`（完整可运行包）
- `PATCH_RELATIVE.diff`（**相对路径**）+ `APPLY.md`（改前/改后哈希、回滚）
- `regress_dlc_v10.py` + `out\`（用例日志）
- `CSF_CAPABILITY.md`：CSF 格式理解（头/标签/值类型/校验）、读写的实现要点、
  **往返验证证据**、与 builder 的最小接线、**能力边界**（例如"未验证散装 `ra2md.csf` 是否覆盖 MIX 内同名文件——那是引擎行为，需真机"）
- `UNCOVERED.md`、`DISAGREE.md`

## 质量红线
- **不得**夸大：CSF 能读写 ≠ 游戏里一定显示；**必须**写清"散装 `ra2md.csf` 是否覆盖 MIX 内的，本卡未验证，需真机"。
- **不得**削弱 W26 的 39 用例；不传 `--csf-out` 时产物必须与 v9 逐字节相同（C6 硬证据）。
- 每个用例给命令+原始输出+退出码；失败写失败。
- 「没测」≠「通过」。

## 回给我的摘要（≤28 行）
① v10 基线哈希与新增/改动文件；
② CSF 读：能读官方 CSF 吗？读到多少标签、`DESC:ALL1` 文本是什么（前 40 字符）；
③ CSF 写：往返验证结果（逐字节一致？原标签数是否不变？）；
④ builder 最小接线：新增的 CLI 开关、生成的标签名形式、构建报告新增了什么；
⑤ 向后兼容硬证据（C6：不传 `--csf-out` 时产物与 v9 逐字节相同？）；
⑥ 回归：用例总数/通过/失败/脚本退出码；**W26 的 39 个是否仍全绿**；
⑦ 是否触碰 `ra2youli` 写 / 他人目录（应为"否"）；
⑧ 未覆盖与不确定项（特别是"散装 CSF 能否覆盖 MIX"这条）。
