# W28 · UNCOVERED —— 未覆盖 / 不确定 / 未能提取

标级同 `NEXTSCENARIO_FORM.md`。

## U1 · 未能提取 / 未能打开的容器 `[本次实测]`

| 容器 | 结果 | 原因 | 试过的替代 |
|---|---|---|---|
| `theme.mix` | ❌ 未打开 | `MixFile._read_index()` 抛 `ValueError: not a TS/RA2 MIX (C&C format unsupported)`（首 2 字节非 `0x0000`，即 C&C/TD 格式 MIX，mixlib 明确不支持） | 未自写解析器（任务禁止）；改用其它 15 个已打开的容器覆盖目标 |
| `thememd.mix` | ❌ 未打开 | 同上 | 同上 |

两者是音频/主题容器，与战役 `.MAP` 无关；**「未能打开」≠「官方图不存在」**，
本卡目标图已在 `mapsmd03.mix` 中全部找到，故不影响 T1/T2/T3。
未尝试 `language.mix`/`langmd.mix` 之外更多的 `*.mix` 变体（如 `maps*.mmx`），
因为任务指定的 `maps01/maps02/mapsmd03` 已足够且 `BATTLEMD.INI` 指向的图全部命中。

## U2 · MIX 索引无明文名 ⇒ 「大小写与容器条目一致」无法字面核验 `[本次实测]`

`MixFile.all_entries()` 只返回 `MixEntry(id, offset, size)`；`names()` 只给 `_XXXXXXXX` 占位。
**容器里没有保存原始文件名的大小写**，因此不能回答「`GDI2A.map` 的大小写是否与容器内
条目名一致」。本卡能回答的是：`crc_hash()` 对名字 `upper()` 后计算 CRC32
（`mixlib.py:205-207`），故大小写不影响命中。若需字面比对，须另找 XCC
`local mix database.dat`（本卡在 `mapsmd03.mix` 等容器中 **`get("LOCAL MIX DATABASE.DAT")`
未命中**，见 `out\_probe.json`）。

## U3 · 本安装没有「能工作的官方 NextScenario 链」正对照 `[本次实测]`

14 张 MD 战役图 + 大部分 RA2 图的 `NextScenario` 都是 `GDI2A.map` /
`AltNextScenario=GDI9C.MAP`（TS 时代占位名）；两个名字的 CRC
（`B639B8AC` / `A63E1B0F`）在 17 个容器、以及 `ra2youli\` 散装文件中都不存在。
⇒ 本卡证明的是**官方的写法/语法类**，**没有**证明「引擎用这个键成功推进过一关」。
也**没有**验证官方战役在本安装里点 Continue 是否也会失败（严禁启动游戏）。

## U4 · 未做全盘文件搜索 `[本次实测]`

按「禁全仓递归列举」，只在 `ra2youli\` 顶层、W26/W27 指定路径、`extracted\` 顶层
与 `extracted\yr_maps\` 内做了定点列举/搜索。因此「`GDI2A.MAP` 不存在」的准确表述是：
**在 17 个成功打开的 MIX 容器与 `ra2youli\` 顶层散装中未找到**，不等于全仓/全盘不存在。

## U5 · CRLF(官方) vs LF(ra2forge) 这一差异未被验证 `[待运行验证]`

官方 `[Basic]` 行是 `\r\n`，ra2forge 生成物是 `\n`（`maplib.py:216-239` 用 `w()` 拼接）。
W10 `VERDICT.md` 的 `crlf_not_the_cause` 针对的是**地图列表显示 `No Name`**，
与本卡目标（Continue 后「無法啟動選取地圖!」）**不是同一症状**，不能据此排除行尾。
本卡未做单变量行尾实验，也未启动游戏。若后续要查，这是 leftover 变量之一。

## U6 · 未验证的引擎行为（全部 `[静态推断]` / `[待运行验证]`）

1. 引擎推进时 `NextScenario` 的解析路径（文件系统 vs MIX/CRC 查找）**未反汇编、未读活进程**；
   「散装图在推进路径上找不到」只是能同时解释 W27 D2/D3 的假设。
2. 目标图是否必须在 `BATTLEMD*.INI` 战役链里登记（Lead 规划的 T2）**未测试**。
3. `AltNextScenario` 的语义、`Official=yes/no`、`SkipMapSelect=no`、`EndOfGame`、
   `NewINIFormat=4` 对推进的影响**未测试**。
4. 未检查 `CD=` / `FinalMovie=` / `Description=` 是否需要配套（W27 review §2.3 第 3 项）。
5. 未检查 `MISSIONMD.INI` / `MISSION.INI` 等可能的战役任务表：
   本卡在 9 个容器内 `get()` 这两个名字**均未命中**，但只覆盖了有限容器与名字变体。

## U7 · 副本差异，已隔离为「仅作旁证」 `[本次实测]`

- `extracted\ALL01UMD.MAP`(291,364 B) / `SOV01UMD.MAP`(318,638 B) 与本次 MIX 提取的
  301,077 / 329,188 B **字节不同**（前者是 INI 段裁剪/被改过的副本）。
  ⇒ 只用来交叉印证 `NextScenario` 文本，**未当作原始证据，也未修改**。
- `expandmd01.mix` 内另有一个 `ALL02UMD.MAP`（465,788 B），与 `mapsmd03.mix` 的
  465,825 B 不同（疑似补丁版）。本卡以 `mapsmd03.mix` 为规范来源，差异已记录。
- `ra2youli\ECH01.MAP.ra2forge.bak` 的 `NextScenario=` 为空（被 ra2forge 改前的散装图），
  仅作历史对照，未改动。

## U8 · 规格书的两处小出入 `[本次读码]`

1. 任务书称 `mixlib.py` 为 22,172 B；`W26...\ra2forge\` 下 `mixlib.py` 实为 **12,665 B**，
   22,172 B 是同目录 `maplib.py`。本卡按**指定路径**装载，确为 MIX 解析器，不影响结论。
2. 任务书称「官方战役图不在散装目录」：对 `ra2youli\` 成立；但仓库 `extracted\` 下
   已有团队先前提取的散装 `ALL01UMD.MAP` / `SOV01UMD.MAP`（见 U7）。
