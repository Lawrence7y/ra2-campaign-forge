# W29 · DISAGREE（与既有研究 /  intuition 的差异登记）

> 本卡**未发现**与既有引擎行为结论的实质性冲突。以下为**澄清、补充、勘误级**差异，逐条给出双方表述与本次复核结果。既有文档一律只读，未改动。

## D1 · `CCFileClass::Open` 的顺序陷阱（补充，非冲突）
- **既有**：`docs/re/fs_mix_load_chain.md` §0 结论表第 1 行、§1.3、`docs/re/fs_mix_load_chain_deep.md` §0/§1.2 均以 `Get_File`（`0x473D10`）的"先磁盘 `0x473D2D`、失败才 MIX `0x473D68`"作为搜索顺序证据。§1.2 方法槽表里对 `Open`（`0x473C50`）的描述是"③`GetFileName()`→`0x5B4430`（MIX 存在性探测）→ 置状态=1；④`0x431F10`（RawFileClass::Open）"，即 **Open 内 MIX 探测先于磁盘**。
- **本次复核**：两者**都对**，但**容易误读**。逐字节确认 `0x473C8B call 0x5B4430` 确实在 `0x473CA2 call 0x431F10` 之前；而 `Get_File` 的 `0x473D2D` 在 `0x473D68` 之前。**若只盯 `Open` 会得出"MIX 优先"的相反结论**。
- **裁决**：以 `Get_File` 为准。Open 的 `0x5B4430` 是**无输出参数的可用性探测**（`edx=0`，命中只置 `[esi+0x68]=1`、不设置 `[esi+0x58]` 缓冲），不决定数据来源；取数由 `Get_File`/`Read` 决定。已在 `OVERRIDE_ORDER.md` §1.4 单列陷阱。分级 `[本次实测]`。

## D2 · `"ra2md.str"` / `"ra2.csf"` 的语义（实质性澄清）
- **既有**：`docs/re/fs_mix_load_chain_deep.md` §5.4 写："LANGUAGE.MIX 创建后… `0x6BD853 call 0x7346A0(名称 0x840D40 = "ra2md.str")`"，并注"提示文本写的是 `ra2.csf`，实际检查名是 `ra2md.str`"。该措辞容易被读成"引擎实际打开的是 `ra2md.str` 这个文件"。
- **本次复核（新增闭环）**：`0x7346A0` **并不打开 `ra2md.str`**。它把参数复制到 `0xB13EB0`，`0x7346F7 push '.'` → `0x734713 call 0x7CAF30`（`strchr`）→ `0x73471F mov byte[eax],0`（**截断扩展名**）→ `0x734722 mov edi,0x8457EC`(`".csf"`) → `0x73474B rep movsd`（**`strcat(".csf")`**）⇒ 实际请求名是 **`ra2md.csf`**。随后 `0x734758 CCFileClass ctor` → `0x734764 Open` → **`0x734777 Get_File(1)`** → `0x73478F Read(0x18)` → `0x734799 cmp " FSC"`。
- `"ra2.csf"` 的 3 处命中（`0x840C6E/0x840CAF/0x840CFD`）**全部是三语 MessageBox 文案**（`EVIDENCE/recon2_stdout.txt` 的 C 字符串上下文），是过时的 RA2 原版提示，**不是引擎请求的文件名**；`ra2md.csf` 字面量三编码全 0 命中，正因它是**运行时拼接**的。
- **裁决**：既有文档的"实际检查名是 `ra2md.str`"应理解为"**基名**是 `ra2md.str`"，真实文件请求为 `ra2md.csf`。这直接决定 C 线候选 1 应投放 **`ra2md.csf`**（而非 `ra2md.str`）。分级 `[本次实测]`。

## D3 · "MIX 内的 INI 是否被读"与 CSF 通道的关系（范围澄清）
- **既有**：deep 文档 §3 定谳"`BATTLEMD98.INI` 放进 MIX 永不加载"（通配走 `FindFirstFileA`，FS-only），§6 建议"BATTLEMD98.INI 一律散装投递"。本卡复核一致（`0x52CBA9`、`0x52CCC7`、`0x52CCCD`，且 `"BATTLEMD98.INI"` 字面量 0 命中）。
- **可能误外推**：不能由此推出"CSF 也只能散装/或 CSF 一定在 MIX 里"。二者是**不同通道**：INI 走**通配 `FindFirstFileA`**（看不到 MIX），CSF 走 **`CCFileClass::Get_File` 显式名**（磁盘优先 + MIX 回落）。本卡 §1.5 首次把 CSF 通道钉到 `Get_File`。
- **裁决**：既有结论成立，但**不要把 INI 的 FS-only 结论外推到 CSF**。分级 `[本次实测]`。

## D4 · `"散装文件优先"` 的证据等级（一致，本卡加严）
- **既有**：`fs_mix_load_chain.md` §1.3 标"[实证]（分支顺序）；端到端行为 [待实测]"；deep 文档 §0 同，且 §8 未闭环 2 明列"散装一定压过 MIX 的端到端验证"未做。
- **本次**：**完全一致**。本卡用 60/60 字节断言 + `ORDER_OK` 结构判据 + `--selftest` N2 反例独立复核，并把**端到端**继续留在 `[待运行验证]`（见 `UNKNOWNS.md` U1 与 §4 实验 A/B）。**未**把静态搜索写成运行期全称证明。
- **裁决**：无分歧，证据链加严（新增 CSF 通道的直接调用证据）。

## D5 · `langmd.mix` 索引布局与 CSF 条目（新增、尚未闭环）
- **既有**：两份文档均**未**解析 `langmd.mix` 的实际条目表；`fs_mix_load_chain.md` §6 提到 `local mix database.dat` 与 XCC 名字表，deep §5.4 提到"字符串表在 LANGUAGE.MIX 内或磁盘上必须存在"。
- **本次（[本次实测]）**：`langmd.mix` 未加密（flags=`0x0001`），布局 `4+6+10*12+bodySize+20 == filesize` 自洽、索引按**有符号 id** 升序；条目 2 起始即 `" FSC"`（一个 CSF 文件）。但 `crc32("RA2MD.CSF")` **不在**这 10 个 id 里；`language.mix` 加密、条目表不可明文读。
- **裁决**：**没有证据推翻**既有研究（它们未作此断言）；这是本卡新增的**未闭环项**，已写入 `UNKNOWNS.md` U2。特别提示：这不削弱"散装优先"——磁盘命中时 MIX 分支根本不执行。

## D6 · 与"直觉 / 常识"的差异（供 Lead 决策参考）
- 直觉常以为"MIX 是打包资源、应该优先于散装"或"覆盖同名条目需要改写 MIX"。**引擎实际相反**：`Get_File` 先 `CreateFileA`，且**散装文件不需要 MIX 内有同名条目**即可独立生效（磁盘命中即跳过 MIX 查找）。
- 直觉常以为"`Description=` 写文本即可"。**实际**它是 CSF 标签位（游戏自带 `BATTLEMD.INI:44` 注释），纯文本显示 `MISSING:'…'`。故 C 线候选 1 的前提是"能写 CSF"，而本卡证明**散装 CSF 在查找顺序上可行**。
- 反直觉的工程风险：散装 CSF **必须完整**（含全部官方标签）。只放自定义标签的"补丁式 CSF"会因 `0x734799` 魔数/内容检查导致 `0x6BD85A` 弹框并启动失败。这一点既有文档未强调，本卡在 `OVERRIDE_ORDER.md` §0 与 §4 实验 B 明确写出。

## D7 · 与 `ra2forge/mixlib.py` 的关系（红线复核）
- 本卡**未导入、未引用** `mixlib.py` 作为引擎行为证据。CRC32 一致性只用 `zlib.crc32` 直接计算，并与 `docs/re/fs_mix_load_chain.md` §6 记录的**真实 MIX 产物实测 id**（`BATTLEMD.INI=0x07E280DD`、`ECH01.MAP=0x8067D343`）交叉核对 —— 这是对**算法**的核对，不是对**引擎查找顺序**的推断。
- `mixlib` 的 `write_mix()` / `crc_hash()` 实现语义**未**被用作任何结论的前提。

---

## 汇总

| 项 | 性质 | 是否推翻既有结论 |
|---|---|---|
| D1 Open/Get_File 顺序 | 补充 + 易误读点 | 否 |
| D2 `ra2md.str` → `ra2md.csf` | **实质性澄清**（影响 C 线投放文件名） | 否（既有结论未断言文件名，但措辞易误导） |
| D3 INI 通配 vs CSF 显式名通道 | 范围澄清，防外推 | 否 |
| D4 散装优先的分级 | 一致，证据加严 | 否 |
| D5 langmd.mix 索引 / CSF 位置 | 新增未闭环 | 否（既有未涉及） |
| D6 直觉差异 | 决策提示 | — |
| D7 mixlib 红线 | 纪律复核 | — |

**结论：本卡与 `docs/re/fs_mix_load_chain*.md` 无实质性引擎行为冲突；核心新增是把 CSF 取数通道钉到 `CCFileClass::Get_File`、给出 `ra2md.csf` 的运行时构造证据，并把端到端验证留作真机卡。**
