# W44 · UNKNOWNS（未覆盖 / 未定谳 / 待运行验证）

> 口径与 `E2E_RESULT.md §0` 一致。本文件只列**未闭环**项；不把「未测」写成「不成立」。

---

## U1 · 战役菜单徽章下简介文案的真实来源 `[待运行验证]`

`[本次实测]` 诊断臂 D_CSF_POS 把官方标签 `DESC:SOV1`（原值「蘇聯戰役 - 毀天滅地大行軍」）改成我方文本后，战役菜单截图与主链臂 **SHA-256 完全相同**（`0bdcfd8c…`），徽章下仍是「點選蘇聯圖示以開始蘇聯戰役。」。

⇒ 该文案**不是**由 `DESC:SOV1` 渲染。`[转引]` W27 §3 引官方 `BATTLEMD.INI` 注释称 `Description = string file label of text description of campaign for player choice list`、官方取值 `DESC:ALL1`/`DESC:SOV1`；但本卡实测表明徽章下的固定短句另有来源（可能是 exe 内建字符串、CSF 中另一标签、或硬编码 UI 文本）。

- 本卡**只**判定「把 `BATTLEMD98.INI Description=` 写成我方 CSF 标签后，简介区不渲染我方文本」，**不**臆造来源。
- 下一步：静态逆向 `GUI:CampaignMenu` 的文字绘制路径，或用穷举法逐个覆盖候选 CSF 标签并截图比对。

## U2 · 追加标签能否显示在**其它**可见 UI 槽位 `[待运行验证]`

本卡证明：追加标签 `RA2F:942506FC` 在内存被解析（`utf16le=3`、标签名 `ascii=2`、`MISSING=0`），但**战役菜单这一屏**无渲染槽位。未覆盖：
- 选中右侧 7 条列表槽（本环境为空且不可点 `[转引]` W27 §3）后是否出现说明区；
- 其它分辨率 / 汉化版本 / 难度下的战役菜单；
- 载入/存档对话框、任务简报屏等其它界面。

`[转引]` W40 §5 已记「追加标签如何显示到可见 UI 仍未闭合」，本卡未推进这一层。

## U3 · 按名字精确选中任意存档 `[待运行验证]`

`[本次实测]` `K2_load_selected=null`：`LB_GETITEMDATA` → UTF-16 指针读到的列表项名（`玩qsave`、`[]`、`[蘇聯 01 - 時空轉移]`…）未匹配 `W44Q3SAVE` / `SAVE4823`，读档实际依赖**高亮首槽**。与 W27 §5 的 `Q3_load_selected=null` 同型 `[转引]`。

- 未验证「按名字精确选中非首槽存档」。
- 下一步：改用 `LB_GETTEXT`/`LB_GETTEXTLEN` 逐项比对，或先清空存档槽再测。

## U4 · 追加战役 `RA2F1` 自身的菜单可达性 `[转引·结构封死]`

`[转引]` W27 Q1 / W32 / `REVIEW/LEAD_VERDICT_campaign_menu_q1.md`：`RT_DIALOG id=148` 只有 2 个徽章 Static，追加 battle id 不生成 UI 条目。本卡 S3/Q-A 截图复核（2 徽章 + 7 空槽）一致，**未**改变该事实，也未找到可达路径。

⇒ 本卡所有真机结论必须连写「借 `[SOV1]` 官方苏联入口」的作用域限定，**不得**外推成「追加式战役包可从菜单进入并通关」。

## U5 · A2 之后 / 末关终止行为 `[待运行验证]`

- `ECH02.MAP` 是 `EndOfGame=yes`、`survive(1800)`；本卡在 A2 存档/读档后即退出，**未**测打完 A2 后的 `EndOfGame` 终止路径。
- 未测 >2 关链、跨包升级后存读档、多包共存（whole-file `MAPSELMD.INI` 冲突，v11 设计上拒绝 `[转引]`）。

## U6 · `SkipMapSelect=yes` 分支与失败分支收窄 `[转引·未分离]`

`[转引]` W39 §6.1 / `LEAD_VERDICT_Q2_CLOSED.md §5`：`skip_yes` 仍弹同一错误框，4 条 `MapSelect::Init` 失败分支（`Invalid side!` 等）只读 RPM 无法判别实际走哪条；`Invalid stage!` 仍是 `[静态推断]`。本卡只用 `SkipMapSelect=no`（W39 已证可行路径），未重跑 `yes` 臂，未收窄分支。

## U7 · `scen_stage_idx=8` 的字段语义 `[转引·非符号级]`

`[本次实测]` 本卡 K1/K2 均读到 `scen_stage_idx=8`（`[Scen+0x35A0]` 2 字节），与 W39 一致。但「当前阶段索引」语义来自既有反汇编 `[静态推断]`，**本卡未做符号级证明**，不据此宣称「引擎选中了第 8 阶段」。与 `LEAD_VERDICT_Q2_CLOSED.md §3` 口径一致。

## U8 · 其它分辨率 / ddraw 后端 / 汉化版本 `[待运行验证]`

三趟真机均在 `800×600` 游戏渲染区（窗口 rect `1707×960`，右/下黑边）、同一 ddraw 配置、同一繁体中文安装。未测其它组合。

## U9 · CSF 完整性守卫的边界行为 `[转引·本卡未测]`

`[转引]` `LEAD_VERDICT_CSF_live.md`：合法但不完整的 CSF 不会阻止启动，只会让未覆盖标签降级为 `MISSING:'…'`；**只有坏魔数**才弹 `Unable to initialize 'ra2.csf'`。本卡的包与诊断臂都走「完整官方克隆」（v12 `assert_complete_csf`），**未**投放最小/坏魔数 CSF，未复测该边界。

## U10 · 游戏运行对 `ECH01.sav` 的改写机制 `[待运行验证]`

`[本次实测]` 卸载后全树对比发现 `ECH01.sav` 被真机运行改写（相对正确基线 `changed=["ECH01.sav"]`），已从基线逐字节还原。未查清是 K1 存档、K2 读档还是游戏自动保存导致。不影响「卸载还原完整」结论（还原后 `IDENTICAL_TREE=True`），但记录为未知。

## U11 · 官方 CSF / MAPSELMD 容器的独立提取 `[转引·本卡未重做]`

`[本次实测]` 本卡复核了 `W40_csf_live/out/official_ra2md.csf`（332,973 B / `1b90bb07…`）与 v12 内置 `RA2MD.OFFICIAL.CSF` 字节相同、`MAPSELMD.OFFICIAL.INI`（5,573 B / `074ccccd…`）。但**未**亲自从 `langmd.mix` / `ra2md.mix` 重新提取一次（依 W41 EVIDENCE step1 `[转引]`）。容器归属（CSF 在 `langmd.mix`、`MAPSELMD.INI` 在 `ra2md.mix`）按签发事实引用，未独立复验。

---

## 未定谳清单（一句话版）

| ID | 状态 |
|---|---|
| U1 简介文案来源 | `[待运行验证]` |
| U2 追加标签其它槽位 | `[待运行验证]` |
| U3 按名字精确选存档 | `[待运行验证]` |
| U4 菜单可达性 | `[转引]` 结构封死，非本卡改动 |
| U5 末关/多关/多包 | `[待运行验证]` |
| U6 skip_yes / 4 分支 | `[转引]` 未分离 |
| U7 stage_idx 语义 | `[转引]` / `[静态推断]` |
| U8 分辨率/后端 | `[待运行验证]` |
| U9 CSF 坏魔数边界 | `[转引]` 未复测 |
| U10 `ECH01.sav` 改写 | `[待运行验证]` |
| U11 容器独立提取 | `[转引]` 未重做 |
