# C 线真机发现：战役显示文本是 CSF 标签位，ra2forge 写纯文本必然 `MISSING:`

> run_id `NEXT_RE_20261112_R02`｜Lead 独立核实｜2026-11-13
> 来源：W27 真机中途报告 + Lead 对 `BATTLEMD.INI` 与 `builder.py` 的直接核对
> 等级：`[本次实测]`（游戏自带 INI 注释 + 代码位置）

## 1 · 现象（W27 真机实测）

W27 装包后，引擎内存已解析到 `RA2F1` 与 `ECH01.MAP`（说明包**确实注册了**），
但战役条的描述文本被引擎解析成：

```
MISSING:'W27LIVE two-mission chain probe A1 to A2'
```

—— 即引擎把它当成 **CSF 字符串标签**去查，查不到，于是报 `MISSING:`。

## 2 · 根因（三个实测事实拼成）

### 2.1 该字段**就是** CSF 标签位（游戏自己写明）
`ra2youli\BATTLEMD.INI` 第 44 行原文注释：
```
; Description = string file label of text description of campaign for player choice list
```
官方实际取值：`Description=DESC:ALL1`、`Description=DESC:SOV1`。
⇒ **不是**纯文本，是 CSF 标签引用。

### 2.2 官方 battle 条目**只有 4 个字段**，没有纯文本名称位
```
[ALL1]
CD=2
Scenario=ALL01umd.MAP
FinalMovie=
Description=DESC:ALL1
```
⇒ 想在菜单里显示自定义名称，**只能走 CSF**，没有旁路字段。

### 2.3 ra2forge 把**原始文本**直接写进该字段
`W26_dlc_unseal_fix/ra2forge_patched_v9/ra2forge/builder.py`：
- `:23` 注释自述：「Description is the campaign-level blurb from `campaign.description`」
- `:262` `want_desc = design_mod.description_for(camp) or str(camp["name"]).strip()`
- `:77-78` 把 description 当作纯文本塞进内容

⇒ **工具侧缺陷**：把一个期望 CSF 标签的字段填成了原始字符串。

## 3 · 为什么这不是一行修复

**ra2forge 目前完全没有 CSF 能力**：`ra2forge_patched_v9/ra2forge/` 的 11 个模块为
`__init__, __main__, builder, cli, design, format80, install, lzo, maplib, mixlib, triggers, verify`
—— **无任何 csf 读写模块**。

而 `ra2youli` 下**没有散装 `ra2md.csf`**（`-Filter *.csf` 命中 0）⇒ 它在 MIX 里。

⇒ 要真正显示自定义文本，需要**三件新能力**，且第三件还需真机验证：
1. **CSF 读**（解析现有 `ra2md.csf`，含其所在 MIX 的提取）；
2. **CSF 写**（追加标签 + 文本，保持格式与校验）；
3. **落地方式**：是修改 MIX 内的 csf，还是放一个**散装 `ra2md.csf`**？

   —— **散装是否覆盖 MIX 内的同名文件，属引擎资源覆盖顺序问题，本会话尚未验证**。
   这与任务书 RE-N10 要求的「资源覆盖顺序（散装 vs MIX vs `BATTLEMD*.INI`）」是同一件事。

## 4 · 当前可用的降级方案（诚实的那一种）

在 CSF 能力补齐前，**工具必须在语义上诚实**，三选一（建议 B）：

| 方案 | 做法 | 代价 |
|---|---|---|
| A 继续写纯文本 | 保持现状 | ❌ **游戏内必然显示 `MISSING:'...'`**，属已知缺陷 |
| **B 写已知存在的标签** | 让 `Description` 引用**引擎里已存在**的标签（如 `DESC:ALL1`），并在构建报告里**明确告警**「自定义简介需 CSF 支持，当前复用官方标签」 | 显示的是官方文案，但**不再是 `MISSING:`**；语义诚实 |
| C 写成空 | `Description=` 留空 | 可能不显示或显示占位，需实测 |

**无论选哪个，`design.py:84-88` 那条「description 为空则回退 name」的逻辑都必须改**——
它现在等于保证「要么 MISSING、要么 MISSING」。

## 5 · 对本项目的影响

- **所有由 ra2forge 生成的战役包，游戏内简介都会显示 `MISSING:`**（直到补 CSF）。
- 这不影响**功能**（战役可注册、可推进），只影响**显示**。
  ⇒ **不得**因为它而推迟 Q2（关卡推进）/Q3（存读档）的验证 —— 那是两条独立的链。
- 它把任务书 RE-N10 的「资源覆盖顺序」从抽象要求变成了**一个具体待测问题**：
  **散装 `ra2md.csf` 能否覆盖 MIX 内的同名文件？**

## 6 · 建议的下一张 C 线卡（在 W27 完成后）

**资源覆盖顺序专项（先静态后真机）**：
1. **静态**：定位引擎的资源查找顺序（散装 vs MIX，同名谁优先），从 `gamemd.exe` 的 MIX 打开路径入手；
   本项目已有 `ra2forge/mixlib.py` 与既有 MIX 研究可复用。
2. **真机（最小）**：在 W27 的沙箱游戏副本里放一个**散装 `ra2md.csf`**（内容为合法 CSF，含一个自定义标签），
   把 `Description` 指向该标签，看引擎是否显示自定义文本。
   - 显示 ⇒ 散装覆盖 MIX 成立 ⇒ CSF 能力补齐后即可完整支持自定义简介；
   - 不显示 ⇒ 必须改 MIX，成本上升到"改写 `language.mix`"级别，需重新评估优先级。
3. **无论结果**，把 `builder.py` 的 `Description` 行为改成 §4 的 B 方案并加构建期告警。
