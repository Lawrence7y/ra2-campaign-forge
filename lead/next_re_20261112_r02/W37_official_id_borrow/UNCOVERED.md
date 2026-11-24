# UNCOVERED · W37 未覆盖 / `[待运行验证]` 项

> 按对「借用官方 id」路线的影响排序。每项给「是什么 / 为何本卡未做 / 取证方法 / 建议归哪张卡」。
> 本卡边界：**纯离线只读**，不启动游戏、不 attach、不读活进程、不改任何游戏目录；未对 `gamemd.exe` 做独立反汇编（代码级结论全部 `[转引]`）。

---

## U1 · 同 id 覆写的「最终胜者」未经真机确认（**最高优先**）

- **是什么**：`0x46CE10` 合并时同 id 后装载者覆写，但先后 = `FindFirstFileA/FindNextFileA` 目录枚举顺序，`[转引 ARCHITECTURE_ATLAS.md:3646]` 明言「引擎不保证字母序 ⇒ 工程上禁止跨文件重复 ID」；`W29 OVERRIDE_ORDER.md:22` 把最终胜者标为 `[静态推断-弱]/[待运行验证]`。而借用官方 id **必然**制造跨文件重复 ID（`BATTLEMD.INI` + `BATTLEMD98.INI` 同含 `SOV1`）。
- **为何未做**：需要运行时观测归并次序（调试器下断），本卡纯静态只读。
- **取证方法** `[转引 W29 UNKNOWNS.md:30 / fs_mix_load_chain_deep.md:434]`：投两个散装 `BATTLEMD01.INI` / `BATTLEMD02.INI`，同一战斗 ID 但不同 `Description`，在 `0x46CF60`（`call [edx+0x64]` 覆写点）下断记录覆写次序，或直接读全局表 `0xA83CFC` 该对象的 `+0x2A0` 最终值。
- **建议归**：真机/调试器卡（W27 真机同族），优先级 P0——它是「借用 id 是否稳定生效」的地基。

## U2 · 回退分支（`0x52CCCD`）的触发条件与「无散装官方 `BATTLEMD.INI`」的后果

- **是什么**：`[转引 ARCHITECTURE_ATLAS.md:3611-3631]` 显示回退分支在通配枚举之后调用同一 `0x46CE10`。若目标机没有散装官方 `BATTLEMD.INI`，MIX 内官方件可能**后归并**并翻盘覆写我方 `SOV1`（`[静态推断]`，见 `BORROW_FEASIBILITY.md` §2.3 条件 B）。且仓库内 W29 / `fs_mix_load_chain.md` / `mix_hygiene_product.md` 对该分支触发条件有三种不同措辞（详见 `DISAGREE.md` D4）。
- **为何未做**：`0x52CCC5/CCC7` 处 `al`/`bl` 标志的精确语义、以及回退分支是否真在无官方名时被走到，需运行期断点/日志；本卡只读了已有反汇编文本。
- **取证方法**：在目标机**只放** `BATTLEMD98.INI`（覆写 `SOV1`）、移走散装官方 `BATTLEMD.INI`，启动游戏读全局表 `SOV1` 对象的 `+0x9C`(Scenario)；或静态逐指令跟完 `0x52CBB1 / 0x52CC4E / 0x52CCC5 / 0x52CCC7` 的控制流。
- **建议归**：与 U1 同一张真机卡；同时给 `docs/re/` 的三处措辞做一次口径统一。

## U3 · `Battle::Read_INI 0x46CCD0` 对「缺失键」的处理未定谳

- **是什么**：`0x46CE10` 命中同名对象后调用 `vtbl+0x64`（`Battle::Read_INI`）覆写字段。本卡已判定这是**对象复用 + 字段覆写**而非整段替换（`[转引 fs_mix_load_chain.md:260-285]`），但 `Read_INI` 对**本 INI 段里没写的键**是「跳过」还是「按默认值写 0/空串」，仓库材料未给逐指令证据（`W32 UNKNOWNS.md:60` 只说它读这些键）。
  - 影响：若散装 `[SOV1]` 只写 `Scenario=`，官方的 `CD=2` / `Description=DESC:SOV1` 是保留还是被清空，直接决定「覆写段必须写全几个键」。
- **为何未做**：需要 `0x46CCD0` 全函数反汇编 + `INIClass::Get_String/Get_Int` 缺失分支语义，本卡未做独立反汇编。
- **取证方法**：静态反汇编 `0x46CCD0`（键读取点 `0x46CD04/1E/38/58/73/9B` 见 `[转引 re_atlas_reassess_20261112/step2_r036_rerun.stdout.md:2882-2889 / W32 MENU_ENTRIES.md:322]`）；或真机在 `0x46CF60` 后 dump 对象 `+0x98 / +0x29C / +0x2A0`。
- **规避（本卡已给）**：覆写段显式写全 `CD` / `Scenario` / `FinalMovie` / `Description`，两种分支结果一致（`BORROW_FEASIBILITY.md` §2.2）。
- **建议归**：静态反汇编补卡（低成本）。

## U4 · 「打一关 → 进下一关」整条链未经真机验证

- **是什么**：Q3 给出的 `MAPSELMD.INI` 改法只保证 `0x5CF760` 按 `Scenario=` 反查能命中（`[转引 W34 MAPSELMD_SPEC.md:95-98]`）。但：
  - `SkipMapSelect=no` 路径下 MapSelect **交互式界面能否被玩家点选到下一关**，`[转引 W34 MAPSELMD_SPEC.md:164]` 明确「未经真机验证」；
  - `[Scen+0x35A0]`（当前阶段序号）在借用 `SOV1` 时的初值未确认（`[转引 W34 UNCOVERED.md:15]`）；
  - 末关 `[Sov03] 4=Sov04` 子项是否该删、`ECH03` 的 `NextScenario=` 空 + `EndOfGame=yes` 的真实行为，均未验证；
  - 散装 `MAPSELMD.INI` **端到端覆盖** MIX 内同名：`[转引 W34 DISAGREE.md:86 / W29 Q1]` 只定谳分支顺序，端到端 `[待运行验证]`。
- **为何未做**：任务明确「纯离线，不启动游戏」。
- **取证方法**：沙箱内按 Q3 片段装配，真机打完 `ECH01` 点 `GUI:Continue`，观察是否出现 MapSelect 界面、`GUI:Continue` 后是否进 `ECH02.MAP`、`frame` 是否推进；对照 W27 D2 的 `MSG:UnableMapSelect` 是否消失。
- **建议归**：W35/W36 之后的真机贯通卡（承接 W34 v11 与 W27 D2/D3）。

## U5 · 官方战役存档（`.SAV`）的格式与冲突检测未做

- **是什么**：Q4 判定「安装前官方苏军存档在安装后可能反查失败」「运行期新建存档卸载后成孤儿」，但两者都是 `[静态推断]`。本卡**未解析任何 `.SAV`**（`W27` 有 `SAVE4823.SAV` 559,553 B 与内存串证据 `[转引]`，但无格式规范）。
- **为何未做**：本卡只读了 INI / MIX / 文件清单；解析 `.SAV` 需要格式逆向，且属用户数据（`USER_AUTHORIZATION_20261112.md:24` 不修改用户存档）。
- **取证方法**：只读比对安装前/后 `.SAV` 内嵌的 `.MAP` 名字串与阶段序号；真机读档观察是否弹 `MSG:UnableMapSelect`。
- **建议归**：存档专项卡；卸载器只需「绝不改存档 + 报告明示」，不依赖格式解析。

## U6 · 电影/UI 资源容器未解索引

- **是什么**：e3 实测 `ra2youli` 有 `movies01.mix` / `movies02.mix` / `movmd03.mix`（357/304/394 MB），并从官方 `MAPSELMD.INI` 抽出 `MapVQ=NODMAP01.VQA`、`VoiceOver=NOD-01.AUD`、`ClickMap=NODCLK01.PCX`、`Overlays=*.SHP` 等资源名。但本卡**未解这三个 MIX 的条目表**，因此「这些资源名确实在容器内」只由「官方文件这么写 + 官方游戏能跑」间接支持，未逐项自证。
- **为何未做**：非本卡目标（借用 id 的代价评估），且三个容器合计 >1 GB。
- **取证方法**：解 MIX 索引核对 `crc32` 条目名；或改后 `MAPSELMD.INI` 与官方全集做值差集（本卡 e3 已给出官方全集，可直接复用）。
- **建议归**：若产品决定新造阶段段（而非 Q3 的「沿用官方段」），再做；沿用方案不需要。

## U7 · 其它包的 `BATTLEMD*.INI` 冲突只做了静态清单，未做跨包互斥验证

- **是什么**：`[本次实测 e3]` `ra2youli` 已有一个 453 B 的 `BATTLEMD98.INI`（`15=RA2F1`）。Q4 建议「另投 `BATTLEMD99.INI` 避开」或「REPLACE + 备份」，但两方案与既有包的共存、以及 `original_absent` 在多包下的语义，未在真实安装器上跑过。`[转引 W21 UNCOVERED.md:21-23]` 亦明示「多活动包并存（A→B）未实现也未触碰」。
- **取证方法**：在沙箱用 W26 v9 工具装「既有追加包 + 本借用包」，跑 install/verify/uninstall 全周期并做逐字节 diff。
- **建议归**：安装器集成卡（W21–W26 谱系延续）。

## U8 · `Description` 自定义文案（CSF）链路本卡只登记，未展开

- **是什么**：`[转引 W27 D1 / LEAD_FINDING_campaign_text_is_csf.md]` `Description=` 是 CSF 标签位；沿用 `DESC:SOV1` 显示官方文案，写纯文本必 `MISSING:'…'`。要自定义需 CSF 读/写 + 散装 `ra2md.csf`（且必须完整合法，否则启动失败，`[转引 W29 OVERRIDE_ORDER.md:25]`）。本卡未评估 CSF 落地成本，只在 Q4 #8 与 Q5 表 #7 登记为潜在 CREATE 槽。
- **建议归**：W30 `CSF_CAPABILITY` 后续卡。

## U9 · 未做的独立反汇编 / 真机实验（边界声明）

- 本卡**没有**对 `gamemd.exe` 做 Capstone 反汇编，故全文**不签发 `[本次读码]`**；所有地址语义均为 `[转引]` 并附 `file:line`。若需把 `0x46CE10` / `0x52CB90` / `0x5CEEF0` 的结论升为本卡自证，需另做静态复算卡。
- 本卡**没有**验证 `RT_DIALOG id=148` 的 13 控件清单（`LEAD_VERDICT_campaign_menu_q1.md:42,98` 自列 `[未复核]`），沿用 W32 结论。
- 本卡**没有**验证 `frame=210` 时 `[Scen+0x125C]` 的实际内容（`LEAD_VERDICT_map_start_root_cause.md:54` 自列 `[待运行验证]`），沿用其「不得写已定位根因」的口径。

---

## 分级汇总

| 等级 | 数量 | 项 |
|---|---|---|
| 必须真机 | 4 | U1、U2、U4、U5（部分）|
| 可静态闭环 | 3 | U3、U6、U7 |
| 边界声明 | 2 | U8、U9 |
