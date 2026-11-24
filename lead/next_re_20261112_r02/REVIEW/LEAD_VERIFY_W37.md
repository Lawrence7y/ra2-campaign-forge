# LEAD_VERIFY_W37 · 「借官方 id」可行性复核（含一条路线级修正）

> 复核人：Lead（本会话）｜ 日期：2026-11-13 18:52
> 卡：**W37**（Hy4 `work/cn:hy4free`）`lead\next_re_20261112_r02\W37_official_id_borrow\`
> 交付：`BORROW_FEASIBILITY.md` 53 KB / `DISAGREE.md` / `UNCOVERED.md` / `EVIDENCE\`（3 脚本全 exit 0：e1 22/22、e2 34/34、e3 15/15）

---

## 1. 它给的独立交叉验证（我认可）

`[本次实测]` W37 用**完全独立的第二条路径**定位了官方 `MAPSELMD.INI`：递归解码 Blowfish 加密条目表，找到 `id=0x922B8CE7` 的绝对起点**恰为文件偏移 `0x71D050`**，payload 与「直接按偏移切片」逐字节相同，SHA-256 `074ccccd…691D52`、261 行全 CRLF。

`[我的判断]` 这与**我自己**独立算出的起点与哈希一致（我是按「文本线索 + 哈希反查起点」得到的，见 `REVIEW\LEAD_W33_VERIFY.md` §3.1），也与 W34 落盘产物一致 ⇒ **三方独立吻合，这条事实可以定谳**。
`[顺带·已更正]` 该 id 是**容器条目**，`MAPSELMD.INI` 自身 id 就是普通 `crc32=0x922B8CE7`。容器名**已定谳为 `LOCALMD.MIX`**：`ts_crc_hash("LOCALMD.MIX")=0xFBE0D09D`（Lead 用它自己的实现复算通过）。注意：我曾用错误的填充规则（简单补零）"证伪"过这条，**该证伪已撤回** —— 见 `REVIEW\LEAD_VERIFY_W34.md` §3。

---

## 2. 会改变路线判断的两个发现

### 2.1 可借用入口只有 **2 个**，不是 3 个

`[转引]` `[Battles]` 14 条 = `1=ALL1` / `2=SOV1` / `3..14=ALL02..07 + SOV02..07`（12 个 `DebugOnly=yes` 占位）。**没有 `tut1` 条目，也没有任何 `[TUT*]` 段**。
`[本次实测]` 我自己核过：`all1`/`sov1`/`tut1` 三串在 `.data` 都存在（VA `0x825CA0`/`0x825C98`/`0x825C90`），但**字符串存在 ≠ BATTLEMD.INI 里有对应条目**——W32 已判 `0x6EB`(tut1) 是「模板无控件的残留」。W37 从 INI 侧独立确认了这一点。

⇒ **Q1 的 `[TUT*]` 一栏为空**；12 个 debug 段不产生徽章；**`SOV1` 是唯一有真机进图证据的通道**（W27 D2/D3），`ALL1` 代价对称但无证据。

### 2.2 「借用官方 id」在当前实现形态下有 **P0 级风险**（这条最重要）

`[转引]` W37 指出两个未闭环前置条件：
- **(A) 枚举顺序不保证**：最终胜者由 `FindFirstFileA`/`FindNextFileA` 顺序决定，`ARCHITECTURE_ATLAS.md:3646` 明言「引擎不保证字母序 ⇒ 工程上禁止跨文件重复 ID」。而 `ra2youli` 现状已有 `BATTLEMD.INI` + `BATTLEMD98.INI` 两个散装文件 ⇒ **在 `BATTLEMD98.INI` 里再写一个 `[SOV1]` 就是跨文件重复 ID**。
- **(B) MIX 回退分支在通配枚举之后**：`ARCHITECTURE_ATLAS.md:3611-3631` 的 `0x52CCCD → 0x52CD2C call 0x46CE10` 发生在通配枚举**之后**。若目标机**没有散装官方 `BATTLEMD.INI`**，MIX 内官方件会「后归并」翻盘覆写我方 `SOV1` ⇒ **借用 id 静默失效**。工程含义：安装器**必须保留**散装官方 `BATTLEMD.INI`。

### 2.3 我的修正：其实有**两条子路线**，风险不同（W37 把两者合并了）

`[本次读码]` W27 当年的 `BATTLEMD.INI.D2_sov1_ech01` 是 **2,730 B，而官方 `BATTLEMD.INI` 是 2,733 B** —— 即 **W27 是「直接改写散装官方 `BATTLEMD.INI` 本身」**（只把 `[SOV1] Scenario=` 换掉），**不是**在 `BATTLEMD98.INI` 里加重复 id。这正是不产生跨文件重复 ID 的原因，也是它能跑通的原因。

⇒ 两种子路线必须分开评估：

| 子路线 | 做法 | 跨文件重复 ID | 真机证据 | 主要风险 |
|---|---|---|---|---|
| **(a) 就地改写官方散装 `BATTLEMD.INI`** | 备份后改 `[SOV1] Scenario=` | **无** | **有**（W27 D2/D3 进图成功） | 改动官方文件（必须可逐字节还原）；(B) 回退分支不触发（因为散装文件在） |
| **(b) `BATTLEMD98.INI` 里写重复 `[SOV1]`** | 追加同 id 段 | **有** | 无 | (A) 枚举顺序；(B) MIX 回退翻盘；两者都可导致**静默失效** |

`[我的结论]` **路线 (b) 不具备工程可行性**（依赖不可保证的枚举顺序），**(a) 是唯一有真机证据且机制干净的通道**。
`[与 W34/v11 的关系]` v11 目前生成的是 `BATTLEMD98.INI`（追加式，即路线 b）——**这与 (a) 冲突**。若走 (a)，v11 需要新增「就地改写并备份」的模式，而不是追加。

---

## 3. W37 其它我认可的事实

- `[转引]` **`0x46CE10` 同 id 语义 = 对象复用 + `vtbl+0x64` 字段覆写（per-key last-write-wins），不是整段替换**：命中分支 `0x46CF58 mov esi,[eax+esi*4]` 只读已有对象指针，`new(0x3A0)` 只在未命中分支 `0x46CE97`；无 `Items[idx]` 写回、无旧对象析构。
- `[转引]` 但**「这决定卸载还原难度」在文件级不成立**：全局 Battle 表 `0xA83CF8` 是启动时从 INI 重建的内存结构、不持久化 ⇒ 卸载都是删/还原磁盘文件、重启生效，难度相同。
- `[转引]` `Battle::Read_INI 0x46CCD0` 对「缺失键」是跳过还是写默认值**未定谳** ⇒ 规避：覆写段**显式写全** `CD`/`Scenario`/`FinalMovie`/`Description`。
- `[本次实测]` **`FinalMovie=` 官方 14 段全空** ⇒ 借用任一 id 不引入影片引用。要留意的是 `MAPSELMD` 阶段段的 `MapVQ=NODMAP01.VQA` / `VoiceOver=NOD-01.AUD` / `ClickMap=NODCLK01.PCX` 等 UI 资源（`movies01/02.mix`、`movmd03.mix` 实存）。
- `[转引]` `Description` 是 CSF 标签位：沿用 `DESC:SOV1` 显示官方文案；写纯文本必 `MISSING:'…'`（W27 实测）。
- `[转引]` **`ra2youli\RA2MD.INI` 全文 118 行无任何战役进度键**，只有 `[Options] CampDifficulty=0` 与 `[Video] StretchMovies=no` ⇒ 进度载体是 `.SAV` 里的 `[Scen+0x125C]`/`[Scen+0x35A0]`，`RA2MD.INI` 应标 **MUST NOT MODIFY**。

`[我的补充]` 这条对回滚设计很有利：我们**根本不需要备份/还原 `RA2MD.INI` 的战役进度**，因为里面没有。

---

## 4. W37 的具体改法（`[转引]`，未验证）

必须克隆官方 5,573 B 全文；`[Nod]` L42-51 完全不改；只改
`[Sov01]` L195 → `Scenario=ECH01.MAP`、`[Sov02]` L205 → `ECH02.MAP`、`[Sov03]` L215 → `ECH03.MAP`，
其余 7 类 UI 字段与数字子项键（`2=Sov02`/`3=Sov03`）原样；段名/键名大小写照抄（引擎不归一化），值比对两边转小写故大小写不敏感；`ECH0x` 的 `NextScenario` 需与下一阶段 `Scenario=` 匹配。

`[待运行验证]` 末关子项 `[Sov03] 4=Sov04` 该删该留、MapSelect 交互能否点选、`[Scen+0x35A0]` 初值、散装覆盖端到端 —— 全部未验证。

---

## 5. 我不签发 / 保留

- W37 明确声明**未独立反汇编 `gamemd.exe`**，故全文代码级结论均 `[转引]`+`file:line`，**无 `[本次读码]`**。这个自我限定是诚实的，我照此引用。
- 它列的 9 项 `UNCOVERED`（U1 枚举顺序 / U2 回退分支 / U3 `Read_INI` 缺失键 / U4 整条推进链 / U5 `.SAV` 格式 / U6 电影容器索引 / U7 跨包互斥 / U8 CSF / U9 边界声明）我认可优先级排序，**均未闭环**。
- `ARCHITECTURE_ATLAS.md:3611-3631` 的回退分支条件在仓库内部有**三种不同措辞**（W29 Q4 / `fs_mix_load_chain.md:20` / `mix_hygiene_product.md:122`），W37 采信反汇编并列入 `DISAGREE D4`。我认可它采信反汇编，但这个分歧**本身尚未定谳**。

---

## 6. 交付物索引

`W37_official_id_borrow\BORROW_FEASIBILITY.md`（五问逐答 + 借用代价表 + 冲突面 10 项 + 9 槽位逐字节还原清单）、`DISAGREE.md`（3+1 条）、`UNCOVERED.md`（9 项）、`EVIDENCE\`（e1/e2/e3 + 官方 `MAPSELMD.OFFICIAL.INI` 5,573 B）
