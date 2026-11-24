## §1061 · 书记员覆盖 R17 第 9 轮（槽73 语义闭环 + RTTI 交叉核对）：身份与覆写升为字节证实、语义仍缺，RTTI 对账仅判「不矛盾」

角色：书记员。本文件只起草、写入 `R17_LEDGER_1061\` 自身目录；台账由 Lead 逐字追加。镜像 `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，sha256 前缀 `73201CC0`（实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`）。下列指令地址均带 `0x`；entry 用 8 位大写十六进制不带 `0x`。全部数字已按卡面要求自行从盘上复算，复算明细见 `numbers.tsv`。

### 1 · `R17_R16_SLOT73_SEM`（hy4）· `0x6F4A70` 身份（语义仍未取得）
结论：**身份已取得；功能语义仍未取得（身份 ≠ 语义）**。
- 函数入口：前一函数于 `0x6F4A63` 以 `C3` 结束，其后 `0x6F4A64`..`0x6F4A6F` 为 12×`90` 填充，本函数自 `0x6F4A70` 起（首字节 `8B 44 24 04`）。理由：入口锚点字节逐字可验，故入口身份成立。
- thiscall：`0x6F4A75` 为 `8B F1`（mov esi,ecx，以 ecx 为 this）；`0x6F4A70` 读 `[esp+4]`（第 1 个栈参数）；`0x6F4A9A`、`0x6F4AA0` 两处 `C2 04 00`（ret 4）。理由：ecx 承载 this 且以 `ret 4` 清一个栈参数，形态与 thiscall 自洽。
- 非构造器：`0x6F4A70`..`0x6F4AA2` 函数体内没有把 vtable 写入 `[this]`/`[esi]` 的指令；唯一涉及 vptr 的是 `0x6F4A8B` `8B 16`（mov edx,[esi]）读取。理由：只读 vptr 不写 vptr，故按字节不是装表构造器，是方法。
- vtable 出现次数：TechnoClass 主表 `0x7F4960`（309 槽）中 `0x6F4A70` 仅 1 次，即 #73 @ `0x7F4A84`；BuildingClass 主表 `0x7E3EBC`（322 槽）中 0 次（其 #73 @ `0x7E3FE0` 为 `0x43F180`）。理由：按镜像 VA 逐槽比对得唯一命中与零命中，故归属 TechnoClass 槽 73 明确。
- **语义仍未取得**：字节事实只有读 `[esp+4]`、读 `this+0x418`、`vptr+0x274` 虚调用、直接 `call 0x5F5850`、返回 `al`、`ret 4`；不据此命名任何行为，不断言标志含义。理由：这些形态既可为布尔判定也可为通知路径，字节不足以区分，故语义写未取得。
证据路径：`lead\next_re_20261117_r14\R17_R16_SLOT73_SEM\REPORT.md`、`lead\next_re_20261117_r14\R17_R16_SLOT73_SEM\byte_checks.tsv`、`lead\next_re_20261117_r14\R17_R16_SLOT73_SEM\vtable_hits.tsv`、`lead\next_re_20261117_r14\R17_R16_SLOT73_SEM\DIS_6F4A70_body.txt`。

### 2 · `R17_R18_EDI_GAP`（hy4）· 把 R16 推断缺口补成字节证实
结论：**字节证实**。窗口 `[0x43F191, 0x43F5D8)` 内 `edi` 写点共 4 条（不含入口 `mov edi,ecx`）：`0x43F1DA` `pop edi`（case0 早退）、`0x43F387` `lea edi,[esi+edx]`（破坏）、`0x43F3DA` `mov edi,[esp+0x30]`（恢复）、`0x43F5C9` `pop edi`（al≠0 早退）。理由：按写寄存器 edi 的指令逐条枚举并剔除初始 mov，得 4 条，无遗漏。
- 到达 `0x43F5D8` 的路径恰 2 条：`0x43F220` `jne`（case1/3 体直跳）与 `0x43F5B1` `je`（主路径尾部）。理由：全段分支扫描仅此两条落入该地址，其余写点所在路径均早退。
- 路径 A（`0x43F220` 直跳）途中无 edi 写，`edi ==` 入口 `ecx == this`。理由：入口 mov 到调用点之间无写，传递值不变。
- 路径 B：`0x43F387` 的破坏循环 `0x43F379`..`0x43F3D4` 无提前出口（唯一出口为 `0x43F3D4` `jl` 失败落到 `0x43F3D6`/`0x43F3DA`），每次破坏必经 `0x43F3DA` 恢复。理由：循环体无分支跳出，破坏与恢复成对。
- 恢复值自洽：`0x43F194` 存 this 到 `S0-0x90`；`call 0x6F4A70`（ret 4）后 `S+0x30 == S0-0x90`；`0x43F194`..`0x43F3DA` 之间无指令写该槽（相邻写为 `S+0x34/0x36`）。理由：栈算术与槽写缺失双重确认恢复值正是入口 this。
⇒ `0x43F5D8` 的 `call 0x6F4A70` 传入的 this **就是本函数 this**。⇒ 「BuildingClass 槽 73 覆写为 `0x43F180`，并在其体内显式调用 TechnoClass 槽 73 的实现 `0x6F4A70`」由 §1060 时的**推断**升为**字节证实**。理由：同一 this 贯穿的缺口已由全区间字节闭合，与 R16 的「同一对象判定：强推断、未字节证实」形成互补，故可升级覆写结论（但 item 1 的函数语义仍不升）。
证据路径：`lead\next_re_20261117_r14\R17_R18_EDI_GAP\REPORT.md`、`lead\next_re_20261117_r14\R17_R18_EDI_GAP\edi_writes.tsv`、`lead\next_re_20261117_r14\R17_R18_EDI_GAP\work.py`。

### 3 · `R17_R17_SLOT73_MAP` 与 §1060 事项收尾更正（§1060 已并列，本节点明）
- `0x4264C0` 出现在 **15** 个类的 #107（不是 17）。理由：`reverse_map.tsv` 中 function_value=`0x004264C0` 且 slot=107 的行精确计数为 15，镜像逐槽复核亦为 15；17 是前轮误记，§1060 已并列报出，此处确认 15。
- `0x7E22A4`(Aircraft) 的 slot0 实为 `0x414290`、`0x7E8C94`(Foot) 的 slot0 为 `0x410260`，**二者并非同值**。理由：从镜像 VA 直接读 dword 得 `0x7E22A4`→`0x414290`、`0x7E8C94`→`0x410260`，与 A4 表一致，故「同值」的旧述作废。
- A4 分辨力论证里真正同 slot0 的一对是 `0x7E4EEC`(Cell) 与 `0x7E8C94`(Foot)，二者 slot0 同为 `0x410260`。理由：镜像读 dword 得 `0x7E4EEC`→`0x410260`=`0x7E8C94`→`0x410260`，正是同段默认实现却定名不同，才构成分辨力证据。
证据路径：`lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\REPORT.md`、`lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\reverse_map.tsv`、`lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\four_classes.tsv`、`lead\next_re_20261117_r14\R17_AUDIT_R13\VERDICT.md`（A4 表）、`lead\next_re_20261117_r14\R17_LEDGER_1060\numbers.tsv`。

### 4 · `R17_R19_RTTI_XCHECK`（hy4）· in-binary RTTI 类名核 coverage
**限制（必须先于数字；否则 220 必被下游误读为「名字错」）：**
① in-binary 名字只覆盖**有 RTTI 的类**——无 RTTI 的类不会进入 Q1 集合，故 RTTI_ONLY 不能解释为 coverage 一定错。
② coverage 的类名是**人写的语义文本**，本项靠 `Class` 后缀抽取，会漏（别名/缩写/无 Class 后缀）也会多（装饰残片、组合名、子系统名被当成类名）。
③ 因此 **BOTH 只说明「不矛盾」**，不是类名正确性判定；**COVERAGE_ONLY 不等于「名字错」**，只表示按本抽取口径未与 988 个有 RTTI 的裸名精确相撞。本项**不是**类名正确性判定。

在上述限制口径下的数字（已从盘上复算）：TD 名字 **988**（`.?AV` **962** / `.?AU` **26**，962+26=988）；从 `coverage.tsv` 第 4 列抽出以 `Class` 结尾的不同类名 **429** 个；三桶 **BOTH 209 / COVERAGE_ONLY 220 / RTTI_ONLY 779**（合计 1208）。
- 理由（复算口径互异于前项）：988/962/26 由 `rtti_names.tsv` 的 prefix 列精确计数；429 由 `coverage_classnames.tsv` 行数 = distinct 类名数；三桶由 `reconcile.tsv` 的 bucket 列按值分计，再以 209+220+779=1208 自校验。
证据路径：`lead\next_re_20261117_r14\R17_R19_RTTI_XCHECK\REPORT.md`、`lead\next_re_20261117_r14\R17_R19_RTTI_XCHECK\rtti_names.tsv`、`lead\next_re_20261117_r14\R17_R19_RTTI_XCHECK\coverage_classnames.tsv`、`lead\next_re_20261117_r14\R17_R19_RTTI_XCHECK\reconcile.tsv`、`COVERAGE\coverage.tsv`（只读）。

### 5 · 审计 R13 的 3 条必改（承接 §1060 事项 3；本节点明其内容已影响表述口径）
三条均属**报告表述修正，不推翻类名结论**（A1 链条成立、A2/A3/A4 AGREE 不受影响）。
- (1) `data_va_refs=0` 须限定为「仅数据节（`.rdata`/`.data`），不含 `.text` 内立即数」；`.text` 内另有 `3/3/3/3/3/3/3/3/26` 处（九个 vtable VA 按 dword 全节扫描复算一致），否则会被读成「这些 vtable 没人用」。理由：该 0 是数据节口径下的真值，脱离限定即误导。
- (2) `names.tsv` 的 `addr` 实为**名字 VA**（如 `0x815DE8`）非 TD VA，与 REPORT 的 `name−8` 说法冲突；`0x815DE8−8=0x815DE0` 才是 TD 头。理由：列名与内容不符会使下游把名字 VA 当 TD 起点，故属表述必改。
- (3) REPORT 缺正控/反控（正控 `0x7FC360`→1 / `0x818D60`→5 / `0x817B58`→5 / `0x7F9594`→988；反控节尾可读、跨节无命中、非对齐扫描），按 `§2.8` 规则 A 退回；无控的 0 不得进事实段。理由：规则 A 要求「0」必须有尺子不瞎的旁证，缺控则该事实不成立。
证据路径：`lead\next_re_20261117_r14\R17_AUDIT_R13\VERDICT.md`（必改 1/2/3 与 A5(b)）、`lead\next_re_20261117_r14\R17_AUDIT_R13\audit.py`。

### 6 · GLM 第三卡 `R17_GLM_TXT_3`（若产物存在）
结论：**未取得（产物未落盘）**。在 `lead\next_re_20261117_r14\` 下 `R17_GLM_TXT_3` 目录不存在（仅有 `R17_GLM_TXT_1`、`R17_GLM_TXT_2`），故其 8 项结论与 `OVERALL`、以及自报身份 `bigmodel-api/GLM-5.3-Flash` 均**未取得**，不编造。理由：目录未落盘即无一手产物可引，书记员不得据前两卡外推第三卡内容。
证据路径：`lead\next_re_20261117_r14\R17_GLM_TXT_1\VERDICT.md`、`lead\next_re_20261117_r14\R17_GLM_TXT_2\VERDICT.md`（仅供证前两卡存在；第三卡无路径）。

### 复算一致性小结
本轮所有可从盘上复算的数字（共 24 项，见 `numbers.tsv`）均与卡面一致，**与卡面不一致的数字个数 = 0**。两条强度红线分列：item 2 覆写=字节证实，item 1 语义=未取得；二者分别针对「同一 this 的传递」与「函数功能命名」，不混同。

本草为 §1061 草稿，由 Lead 逐字追加；书记员未自行改动台账。
