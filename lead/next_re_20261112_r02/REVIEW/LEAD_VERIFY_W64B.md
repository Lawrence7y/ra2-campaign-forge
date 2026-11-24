# LEAD_VERIFY_W64B · `tut1`/Boot Camp 官方数据盘点：**部分自带**（YR 可用部分为零）

> 记录人：Lead｜时间：2026-11-13 23:59｜卡：W64b（Hy4；W64 原派 GLM 零产出后改派）
> 交付：`W64_bootcamp_inventory\BOOTCAMP_INVENTORY.md` + `UNKNOWNS.md`(10) + `DISAGREE.md`(D1–D7) + `EVIDENCE\`(全部 exitcode 0)

## 1 · 五问答案（我采纳）

| 问 | 答案 |
|---|---|
| Q1 有 `[TUT1]` battle 条目吗 | **YR 加载路径上不存在**：散装 `BATTLEMD.INI`（2,733 B，SHA `7e40691a…`）、`BATTLEMD98.INI`、MIX 内 `BATTLEMD.INI`（同 SHA）全部无 `[TUT1]`、`[Battles]` 无 `N=tut1`（14 条 = ALL1/SOV1/ALL02-07/SOV02-07） |
| Q2 有官方 tutorial 地图吗 | **没有**。33 个顶层 MIX **0/33 有 name table** ⇒ 文件名不可证，改用「生成 1,003 个候选名 × 13,007 个 CRC id（2,125 个嵌套容器）成员测试」⇒ **0 命中**。635 个 map-like 条目里 198 个带 `Brief:TRN01` 等串，都是 vanilla 遗留在多人图里的字符串，**不是教程地图** |
| Q3 W61 报的 7 处 `TUT1` 命中性质 | W61 的原始输出其实是「7 容器 / **8 条目**」；全量扫后 **21 个去重位置 / 17 组 / 10 个顶层 MIX**。其中 **2 条是 CSF 标签**（`DESC:TUT1`）、**6 条是 .MAP 内 base64 打包行的巧合字节**、**1 条是真 INI 键值**（见下）、其余 12 个位置是 SHP/PCX/BIK 像素巧合 |
| Q4 `MAPSELMD.INI` 有 tutorial 阶段吗 | **没有**。官方 5,573 B（`074ccccd…`）20 段、14 个阶段全为 `ALL01..07` / `Sov01..07`，全文 `TUT*/SCG*/TRN*/BOOT*` **无匹配** |
| Q5 三分结论 | **`部分自带`**（按"可用的"口径等价 `完全没有`）：自带的是 **UI/文案/音效**（W61 已证）+ **一份 YR 不加载的 vanilla `BATTLE.INI` 残骸**；缺 **YR 可加载的 battle 登记、全部地图、全部阶段表、第三徽章美术** |

## 2 · ★ 本卡最有价值的发现（W61 漏掉的）

`[本次实测]` `ra2.mix` 里嵌套 **`LOCAL.MIX`**（id `0xA8548FD9 = ts_crc_hash("LOCAL.MIX")`，33.18 MB），其内含条目 `0x889C5B31 = ts_crc_hash("BATTLE.INI")`，**4,054 B，SHA `a5752a8d…`**，内容就是 **vanilla RA2 的 `BATTLE.INI`**：

```ini
[Battles]
1=TUT1
...
[TUT1]
CD=0
Scenario=trn01t.MAP
Description=DESC:TUT1
```

**但它不被 YR 加载**：`[本次实测]` `gamemd.exe` 里只有 `"BATTLEMD*.INI"`@`0x4261A8` 与 `"BATTLEMD.INI"`@`0x426198`，字符串 `"BATTLE.INI"` 出现 **0 次**。
⇒ **官方确实设计过 TUT1 训练营入口**（这把我裁决书 §5 的产品叙事从"推测"升为"有官方件为证"），**但对 YR 是死数据**。
`[W61 为什么漏了]` 它的 `q2_scan.py` 跳过 `size > 2,000,000` 的条目 —— 33 MB 的 `LOCAL.MIX` 正被跳过。**这是"过滤条件吃掉证据"的典型，值得记一条方法论教训。**

## 3 · 这条对两条路线的影响

- **路线 (a)**：无影响。已经真机贯通（W63）。
- **路线 (c)**：成本明细变清楚了 ——
  - **可直接抄的**：`[TUT1]` 段格式（有官方件 `BATTLE.INI` 作模板，不用从零编）、`CD/Scenario/Description` 三个键的官方取值形态
  - **官方自带、零改动复用**：`DESC:TUT1`、`STT:CampaignAnimTutorial`、`GUI:TutorialCampaign`、`BootCampSelect` 音效、官方 VQA/PCX/SHP/AUD 资源
  - **必须自造**：① `[Battles] 15=TUT1` 登记 ② `[TUT1]` 段 ③ **至少 1 张全新 `.MAP`**（`trn01t.MAP` 实体不在任何 MIX，我另行核实了 0 命中）④ `MAPSELMD.INI` 阶段追加（克隆官方 5,573 B + 约 10 行）⑤ 第三徽章美术 ⑥ exe 资源补丁（W61 已打通）

## 4 · 签发与边界

- `[签发]` `部分自带（YR 可用部分为零）`；**"官方 Boot Camp 战役可用"这句话不成立**，不得写。
- `[签发]` 官方 **没有** tutorial 地图、**没有** tutorial 阶段表 —— 这两条是路线 (c) 的硬缺口。
- `[转引·待核]` Q2 用的是"CRC 成员测试"而非文件名匹配（因为 MIX 无 name table）。这**不能证明"文件不存在"**，只能证明"这 1,003 个候选名对应的 CRC 不在这些容器里"。W64b 自己标了 `[待运行验证]` 边界，我认可这个力度。
- `[方法学教训]` **过滤条件会吃掉证据**：W61 跳过 >2 MB 条目 → 漏掉 33 MB 的 `LOCAL.MIX` 内的官方 `BATTLE.INI`。今后凡是"全量扫描"，必须写明过滤条件，并单独列"因过滤而跳过的候选"。
