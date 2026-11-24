# W40 · DISAGREE（与卡面预期 / 上游结论的差异登记）

> 本卡存在**一处实质性推翻**和若干澄清/勘误。既有文档一律只读，未改动。
> 分级沿用卡面：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。

---

## D1 · 【实质性推翻】「最小 CSF ⇒ 启动失败」不成立；W29 把魔数合法性误绑到标签完整性

**双方表述**

- **卡面 §1 测试 A 预期 / [转引] W29**：散装 `ra2md.csf` 必须是**完整合法 CSF（含全部官方标签）**，否则 CSF 加载器 `0x734799` 的 `" FSC"` 检查失败 → `0x6BD85A` 分支弹 `Unable to initialize 'ra2.csf'` 并**启动失败**。
  - W29 `OVERRIDE_ORDER.md` §0 第 25 行原文：「散装 CSF 必须是**完整合法 CSF**（含全部官方标签 + 自定义标签），否则 `0x734799` 的 `" FSC"` 魔数检查失败 → `0x6BD85A` 分支弹出 `Unable to initialize 'ra2.csf'` 并**启动失败**」。
  - W29 `DISAGREE.md` D6 原文：「只放自定义标签的『补丁式 CSF』会因 `0x734799` 魔数/内容检查导致 `0x6BD85A` 弹框并启动失败」。
- **[本次实测] 本卡**：用 W30 `csf.py` 生成一张**结构完全合法**的最小 CSF（115 B：`" FSC"` / v3 / language 9 / num_labels=1 / num_strings=1 / 唯一标签 `RA2F:TEST0001`），散装投放后：
  - 19.34 s 正常进入主菜单，**无弹窗、无崩溃、进程未自然退出**；
  - 截图 `screen_w40_A_minimal_main_menu.png`：所有主菜单按钮渲染为 `MISSING:'GUI:SinglePlayer'` 等；
  - 只读 RPM：我方文本 `|utf16le=2`、标签名 `|ascii=2`、`MISSING:|utf16le=780`（B/C 仅 13–17）⇒ 引擎**确实读了散装最小 CSF**，官方 5,211 标签一条都没被提供。

**裁决**：**推翻「含全部官方标签是启动条件」**。正确的两条边界是：

1. **结构合法性**（` FSC` 魔数 + 可读的 24 字节头）：不满足才弹 `Unable to initialize 'ra2.csf'` 并启动失败 —— 由附加 D（4 字节 `XXXX`）实测确认，W29 的 `0x734799 → 0x6BD85A` 分支本身**成立**；
2. **标签完整性**：**不是**启动条件，只决定 UI 文本是否 `MISSING:'<label>'`。

W29 §4 实验 A（用 4 字节 `XXXX` 做「故意损坏」）的预测**正确**，但 §0/D6 把它外推成「只放自定义标签也会弹框」是错的：只要 CSF 头部合法，1 个标签照样启动。卡面「测试 A 若没崩，照实写，不要放宽判据」——本卡未放宽判据（A 用的是 `csf.py` 严格生成并读回校验的合法 CSF），并额外用 D 复现 W29 原样的坏魔数实验作为对照。

**影响**：`install.py` 投递完整克隆的理由应从「否则启动失败」改为「否则官方 UI 全部变 `MISSING:`」；W29 `OVERRIDE_ORDER.md` §0、`DISAGREE.md` D6 建议勘误。

---

## D2 · 【勘误】卡面「从 `ra2bench\ra2md.mix` 取官方 CSF」路径不对

- **卡面 §1 测试 B 第 1 步**：「从 `ra2bench\ra2md.mix` 取官方 CSF……`id=0xBD835079`，332,973 B」。
- **[本次实测]**（`out/csf_variants.json` 的 `mix_probe`）：

| MIX | 大小 | 条目数 | `id=0xBD835079` |
|---|---:|---:|---|
| `ra2bench\ra2md.mix` | 204,527,696 B | 25 | **不存在** |
| `ra2bench\langmd.mix` | 84,643,206 B | 10 | **存在**，offset 39216，size 332,973 |
| `ra2youli\langmd.mix` | 84,643,206 B | 10 | 存在，同上 |
| 沙箱 `langmd.mix` | 84,643,206 B | 10 | 存在，同上 |

  三份 `langmd.mix` 提取结果 SHA-256 均为 `1b90bb0756137f46ff529af043fe798d7f1f9fa1713a4110f17e1d674de81f1c`，与 W30 `sandbox/extracted/ra2md.csf` **逐字节相同**。`ts_crc_hash("ra2md.csf")=0xBD835079`（TS 4 字节尾填充），普通 `crc_hash=0x42CBEDCB`（取不到，与 W30 `DISAGREE.md` §1 一致）。

- **裁决**：官方 `ra2md.csf` 在 **`langmd.mix`**，不是 `ra2md.mix`。W30 `CSF_CAPABILITY.md` §1 写的就是 `langmd.mix`，本卡按实测从 `langmd.mix` 提取。卡面为路径笔误，不影响结论（变体来源正确）。

---

## D3 · 【范围澄清】W29 §4 实验 B 的「显示 `W29_LIVE_OK`」前提与 W27 菜单实测冲突

- **W29 §4 实验 B 判据**：完整 CSF + 追加 `DESC:MYCAMP` + 散装 `BATTLEMD98.INI` 的 `Description=DESC:MYCAMP` → 「打开战役选择界面，观察该战役条简介」，预期显示 `W29_LIVE_OK`。
- **[本次实测] 本卡测试 B**：同样结构（追加 `RA2F:W40TEST` + `Description=RA2F:W40TEST`），CSF 标签**确实被解析**（C 的 `MISSING:'W27LIVE…'` 在 B 中消失、我方文本进内存），但 `GUI:CampaignMenu` 截图与负对照 C **逐项一致**（2 徽章 + 7 空槽），**没有任何可见的我方文本**。
- **[转引] W27 §3**：`GUI:CampaignMenu` 只呈现两个固定 side 徽章，追加 battle id 不生成可选条目；D1 证明「CSF 文本不是不可见根因」。
- **裁决**：W29 实验 B 隐含假设「追加战役条有可见简介承载位置」，该假设与 W27 的真机菜单结论冲突。本卡**未证成**实验 B 的显示判据；显示通道本身由附加 E（覆盖官方可见标签 `GUI:SinglePlayer`）单独证明。两者不能混为一谈：**「CSF 功能正确」≠「追加标签文本会出现在 UI」**。

---

## D4 · 【结案 + 范围澄清】W30 `UNCOVERED.md` §1 的两个问题

- **W30 原文**：「散装 `ra2md.csf` 放在游戏目录后引擎是否优先读取（覆盖 `langmd.mix` 内置的 `ra2md.csf`），以及在中文系统下是否真正替换 `BATTLEMD98.INI Description=RA2F:...` 为文本而非 `MISSING:'RA2F:...'`，本卡未验证，必须真机实测确认」。
- **[本次实测] 裁决**：
  - 「是否覆盖」→ **是**（A 的 MISSING 洪泛 / D 的坏魔数弹框 / E 的主菜单按钮文本替换，三趟独立证据）；W29 Q1 / C13 前半定谳。
  - 「是否真正替换而非 `MISSING:`」→ **是**（B vs C 单变量对照：`MISSING:'W27LIVE…'` 消失，且无 `MISSING:'RA2F:W40TEST'`）。
  - **仍未闭合的只有**：让该文本出现在**可见 UI**（卡在 W27 的菜单可达性，不是 CSF 能力问题）。
- W30 `UNCOVERED.md` §2（`install.py` 未接线）本卡**未改变**，见 `UNKNOWNS.md` U4。

---

## D5 · 【口径澄清】`W39_mapselmd_live2\sandbox_game` 不存在

- **卡面 §2**：「`W39_mapselmd_live2\sandbox_game` —— 已装 W27 Live Campaign 且刚通过真机验证（verify exit 0）。可直接复用」。
- **[本次读码] + [本次实测]**：该目录**不存在**（`Test-Path=False`）；W39 `tools/live_lib.py:39` 明确 `GAME = W35 / "sandbox_game"`，注释写明「prepared (verified) sandbox is REUSED in place from W35_mapselmd_live\sandbox_game」。W27/W35 各有 433 文件的沙箱，W35 的 `verify` exit 0。
- **裁决**：本卡按 W39 的实际 `GAME` 常量复用 `W35_mapselmd_live\sandbox_game`，并在开工/收尾各跑一次 `verify`（均 exit 0）。卡面是口径简写，不影响实验（沙箱状态、清单、seal 均核对过）。

---

## D6 · 【方法论提醒】「控件文本」≠「渲染文本」

- **W27/W39 的既有做法**：用 `EnumChildWindows` + `GetWindowTextW` 枚举可见控件文本来判 UI 内容。
- **[本次实测] 本卡测试 A**：控件文本枚举到的仍是 `GUI:SinglePlayer` / `GUI:WWOnline` / …，但**截图**显示这些按钮渲染的是 `MISSING:'GUI:SinglePlayer'` / `MISSING:'GUI:WWOnline'` / …。即：控件里存的是 **CSF 标签键**，渲染时才查表；查不到就显示 `MISSING:'<键>'`。
- **裁决**：判定「UI 上显示什么」必须以**截图/像素**为准，控件文本只能证明「有哪些控件、请求了哪些标签」。本卡所有「是否出现 `MISSING:` / 我方文本」的画面结论均引自截图；控件文本与内存命中只作辅助。这不影响 W27/W39 的结论（它们判的是「有哪些条目/按钮」，不是「按钮上写什么字」），但补上了 W40 需要的显示层判据。

---

## D7 · 【已核实一致】弹窗文案 `ra2.csf` vs 请求文件 `ra2md.csf`

- **[转引] W29 `DISAGREE.md` D2**：`"ra2.csf"` 的 3 处命中全是过时三语 MessageBox 文案，不是引擎请求名；`0x7346A0` 运行时把 `"ra2md.str"` 截断扩展名后拼成 `"ra2md.csf"`。
- **[本次实测] 附加 D**：投放的散装文件名是 `ra2md.csf`，弹窗文案却是 `Unable to initialize 'ra2.csf', please reinstall Red Alert.`（+ 德/法）——与 W29 的澄清**完全一致**，无分歧。记录在此以防后续读者误以为「投错文件名」。

---

## 汇总

| 项 | 性质 | 是否推翻上游结论 |
|---|---|---|
| D1 标签完整性 ≠ 启动条件 | **实质性推翻**（W29 §0 / D6 的因果表述） | **是** |
| D2 官方 CSF 在 `langmd.mix` | 卡面路径笔误 / 勘误 | 否（W30 文档本就正确） |
| D3 实验 B 的显示前提 | 范围澄清 + 与 W27 既有结论对齐 | 否（未证成，非证伪） |
| D4 W30 §1 两问题结案 | 结案 + 剩余范围澄清 | 否 |
| D5 W39 沙箱路径 | 口径澄清 | 否 |
| D6 控件文本 vs 渲染文本 | 方法论补充 | 否 |
| D7 `ra2.csf` 文案 | 已核实一致 | 否 |
