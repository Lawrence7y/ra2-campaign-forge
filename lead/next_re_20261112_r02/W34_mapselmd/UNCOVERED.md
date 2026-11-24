# W34 · UNCOVERED / 未闭环清单

> 本卡是**纯离线实现卡**。下列项目**没有**在本卡闭环，均需后续独立卡（尤其真机卡）处理。
> 严禁据本卡写出「已修复战役推进」。本卡只交付：格式定谳、`ra2forge_patched_v11` 离线生成/安装能力、51 例离线回归。

---

## U1 · 真机端到端验证（最重要）

`[待运行验证]` 未启动 `gamemd.exe`、未 attach、未做任何运行期观察。未验证：

1. 散装 `MAPSELMD.INI` 是否真的覆盖 `ra2md.mix`/嵌套 `LOCALMD.MIX` 内同名文件并被 `0x005CEEF0` 加载（W29 Q1 只定谳了分支顺序）。
2. `SkipMapSelect=no`（v10/v11 builder 写出的值）通关后，`0x005AE220 -> 0x005CF760` 能否用我方 `Scenario=` 找到阶段、MapSelect 面板能否显示并让玩家点选到 `2=<下一阶段段名>`。
3. 最后一关（无数字子项 + 地图 `[Basic] EndOfGame=yes`）是否真的正常结束战役，而不是卡在选图面板或弹 `MSG:UnableMapSelect`。
4. `SkipMapSelect=yes` 手工改写场景：`0x005ADFD7` 从 `[Scen+0x35A0]` 取「当前阶段序号」。从 `BATTLEMD98.INI` 菜单**新建**我方战役时该字段的初值未经真机确认；若初值为 0，`0x005CF810` 会取官方首关阶段（`ALL01`/`Sov01`）而不是我方追加阶段。**本卡生成的地图一律 `SkipMapSelect=no`，因此不依赖该路径**；但任何把它改成 `yes` 的用法都未验证。

**最小真机实验建议**：用 `ra2bench` 的隔离副本，投放 v11 生成的散装 `MAPSELMD.INI` + 包，启动 → 新战役选我方条目 → 打通第 1 关 → 点 `GUI:Continue` → 观察是否进入第 2 关（而非「無法啟始選取地圖！」）；负控：删掉散装 `MAPSELMD.INI` 应复现 W27 报错。实验后按哈希逐字节还原。

---

## U2 · 追加阶段的 MapSelect 界面资源（离线只能保证「结构合法」）

`[待运行验证]` v11 追加阶段段的 UI 字段是**克隆该阵营官方最后一关**（`ALL07`/`Sov07`）的值：

| 字段 | 克隆值示例（Nod） | 未验证点 |
|---|---|---|
| `Description` | `791` | 沿用 Sov07 的 CSF 标签号 ⇒ 悬浮提示会显示官方文案，不是我方简介 |
| `VoiceOver` / `MapVQ` / `Overlays` | `NOD-01.AUD` / `NODMAP01.VQA` / `TN02A.SHP,TG02A.SHP` | 资源确实存在，但播放/淡入效果未观察 |
| `Targets` | `1,190,100` | 与 `2=` 颜色区域是否对齐未验证 |
| `ClickMap` | `NODCLK01.PCX` | **颜色 2 的可点击区域是否真的存在**未验证（选它只因 `[ALL01] 2=ALL02` / `[Sov01] 2=Sov02` 证明两阵营都有颜色 2） |
| `Text1..7` | 未写（官方也未填） | 引擎循环读 `Text1..7`，缺失时行为未观察 |

若要专属文案/专属选图界面，需要额外卡（CSF 标签 + ClickMap/VQA 资源）。

---

## U3 · `campaign.side = "yuri"` 被拒绝

`[静态推断]` + `[待运行验证]` 官方 `MAPSELMD.INI` 只有 `[GDI]`（Allied）与 `[Nod]`（Soviet）两个阵营段。加载器 `0x005ADF40..0x005ADF7B` 从 `SideClass+0x24` 取阵营名传给 `0x005CEEF0`；exe 中未找到独立 `Nod\x00` 字面量（只有 `TXT_NOD`），Yuri 阵营究竟请求哪个段名无法静态定谳。

⇒ `ra2forge/mapselmd.py::faction_for()` 对 `yuri` 抛 `MapselmdError`，**不臆造 `[Yuri]` 段**。若后续真机确认 Yuri 的段名，可按同一格式扩展 `SIDE_TO_FACTION`。MS1/MS2 只覆盖 soviet/allied。

---

## U4 · INI 段名 / 键名的大小写敏感性

`[静态推断]` `INIClass::Get_String(0x528C00)` 用 `0x4A1DE0`（裸 CRC32，无 strupr）哈希段名/键名；`INIClass::Load(0x525A60)` 路径只观察到 `0x727CF0`（trim 空白），未见大小写归一。由此推断「段名/键名应按官方原样拼写」，但**未做运行期全称证明**（W29 §3 同为有界声明）。

v11 一律照抄官方拼写 `[GDI]` / `[Nod]` / `[ALL01]` / `[Sov01]`，不冒该风险。值比对的大小写不敏感已由 `0x7B5B30` + `0x7B4780` 定谳（`[本次读码]`）。

---

## U5 · 嵌套 MIX 的引擎装载路径未逆向

`[静态推断]` 本卡离线解码 `ra2md.mix` → 顶层条目 `0xFBE0D09D`（`LOCALMD.MIX`，`ts_crc_hash`）→ 第二级 MIX 内的 `MAPSELMD.INI`（`crc32`）。**引擎如何把一个 MIX 条目当作子 MIX 递归装载**，本卡未逐指令逆向（W33 `step10_close_gaps.py` 的 `scan_mix_bytes` 是离线递归，不是引擎证据）。官方战役能跑 ⇒ 引擎必然能取到该文件，但取法未闭环。所幸 v11 走**散装**路径（W29 Q1 磁盘优先），不依赖这条链。

---

## U6 · 多战役并存 / 覆盖第三方 `MAPSELMD.INI` 的合法路径

`[静态推断]` 实现约束，非缺陷但需知晓：

- `install.py` 对**已存在且未记录在 `ra2forge_install.json` 里**的 `MAPSELMD.INI` 一律 definite conflict 拒绝，且 `--allow-content-conflict` **也不释放**（防静默覆盖 whole-file 注册）。若用户确实想覆盖第三方文件，当前**没有自动化路径**，只能手工备份/移走再安装。
- `PKG-IDENT01` 既有的「不支持多包并存」规则未改 ⇒ 同一游戏目录**无法同时装两个带 `MAPSELMD.INI` 的追加战役包**（第二个包会因 identity mismatch 或 foreign-file conflict 被拒）。多包合并需要后续卡设计「合并式追加」。
- `--mapselmd-base` 允许自定义官方基础文件，但 `validate_official_base()` 硬编码校验 `ALL01..ALL07` / `Sov01..Sov07`；其它语言/版本若改名会被误判为「部分文件」而拒绝。

---

## U7 · `verify.py` 未新增 MAPSELMD 专项校验

`[本次实测]` `verify.py` 与 v10 **逐字节相同**（`V11_FILES.sha256.txt`），既有语义零削弱；`MAPSELMD.INI` 作为清单内文件自动享受「结构 / digest / 磁盘漂移 / 封印 / orphans」五项通用检查（MS5f 实测 exit 0）。但**没有**新增「官方 14 阶段仍在」「追加键连续」「末段无子项」这类 MAPSELMD 内容级校验——这些只在**构建时**由 `mapselmd._verify_output()` 自检（MS1/MS2），安装后的二次内容校验未做。若真机卡需要「安装后仍完整」的强证据，需另加 verify 规则（注意不得削弱既有语义）。

---

## U8 · 散装投放与 MIX 打包未做二选一真机对照

`[待运行验证]` 依 W29/W33，本卡只生成**散装** `MAPSELMD.INI`（磁盘优先）。未验证「把它打进 `expandmd98.mix` 是否也生效 / 是否会被 `ra2md.mix` 覆盖」；v11 也**不**把它打进 MIX（MIX 仍只放地图，builder 的 `_verify_mix_contents` 拒绝任何 INI 入包）。

---

## U9 · 回归覆盖边界

`[本次实测]` 51/51 通过（45 继承 + 6 新增），但回归是**离线文件级**：`MS1..MS6` 验的是字节、清单、预检与还原，不是引擎行为。沙箱内 `gamemd.exe` 是 inert 占位文件，从不执行。既有用例 CSF6 仍只读 `ra2youli/langmd.mix` 与 `ra2youli/ra2forge_install.json`（只读，未写回）。
