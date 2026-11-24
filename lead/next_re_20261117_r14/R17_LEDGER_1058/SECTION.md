## §1058 · 书记员覆盖 R17 第 5 轮（R10 / B3复核 / R11链 / 两审 / 镜像钉哈希）：11 事项全覆盖草稿

复算基准：ra2youli/gamemd.exe，size 4,825,360 B，sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476。副本：lead/next_re_20261117_r14/PATCH_D35R/work/run/gamemd.exe，size 4,825,360 B，sha256 36A875775DA89239E370AAF091DBE5D3D3C5F2F8017D9EFA6A15FCDD4801C7F4。numbers.tsv 已先于正文落盘。

### 1. R10 卡（R17-R10-DISPATCH）
Q1：三个 host 类名全部未取得。盘上装饰名 .?A 共 988 个，988/988 在 .data，.text 0 个；名字 VA 的 raw 匹配 6 处、valid 立即数引用 0 处，且无一落在 host 体内或前后 4KB 邻域。Q2：运行期索引派发假设被证伪；call [reg+reg*4] 窄口径 0 命中，jmp [reg*4+disp32] 387 处均为 switch 跳表，表地址 0x4059d0..0x87d44e（386 .text + 1 .data），槽段命中 0，不能触达 #73 / #107。卡面前置“装饰名在 .text”的口径须改为 .data，根因是 raw file offset 被误当 VA。
证据：lead/next_re_20261117_r14/R17_R10_DISPATCH/REPORT.md；lead/next_re_20261117_r14/R17_R10_DISPATCH/hosts.tsv；lead/next_re_20261117_r14/R17_R10_DISPATCH/dispatch_sites.tsv；lead/next_re_20261117_r14/R17_AUDIT_R10/names_by_section.tsv；lead/next_re_20261117_r14/R17_AUDIT_R10/name_refs.tsv；lead/next_re_20261117_r14/R17_AUDIT_R10/controls.tsv。
理由：本项用“名字是否存在”与“索引寻址是否存在”两条互不相交的否定链同时封口，类名和派发路径均不给猜测空间。

### 2. 审计 R10（hy4 跨家族）
裁定 A1 AGREE、A2 DISAGREE、A3 DISAGREE、A4 AGREE、A5 DISAGREE，必改 4 条。host2 真值 fn_end = 0x43BCDE；0x43BCDB 只是 C2 08 00（ret 8）的起始，三字节之后才是函数尾界，故执行方早值 0x43BCDB 错。387 处跳表真值为 0x4059d0..0x87d44e，386 .text + 1 .data，不是全在 .data；0x5C64C3 改判伪命中；A5 必须报 raw=6 / valid=0，不能把 6 个 raw coincidence 说成 6 个有效引用。
证据：lead/next_re_20261117_r14/R17_AUDIT_R10/VERDICT.md；lead/next_re_20261117_r14/R17_AUDIT_R10/bytes.tsv；lead/next_re_20261117_r14/R17_AUDIT_R10/candidates.tsv；lead/next_re_20261117_r14/R17_AUDIT_R10/controls.tsv；lead/next_re_20261117_r14/R17_AUDIT_R10/name_refs.tsv。
理由：本项的价值在逐项改错而非重复主结论，A2/A3/A5 的支撑叙述各自有独立硬错，必须按审计票面分别记账。

### 3. B3 第二源复核（R17-B3-REVIEW）
12 处装表写中 8 处成立为真 ctor 装表，4 处不成立；4 处全在 host 0x43BCF0，失败点均为 G5：收尾无 mov eax,esi、不返回 this。旁证是 operator new 0x7C8E17 的 call 物理位置在 0x43BC10，位于这 4 处 site 之后，故是对已存在对象重设 vftable，不是构造新对象。该 host 的 fn_end 实测为 0x43C0D0：0x43C0C9 为 C3，随后 6 个 90，下一函数起于 0x43C0D0。C3 四槽全 MATCH：0x7E3E90=0x410590、0x7E3E98=0x410580、0x7E3EA0=0x4105E0、0x7E3EBC=0x410260。与前来源 DISAGREE（局部）：应改述为 8 处 ctor 装表 + 4 处对象重初始化写 vftable；否定性主结论方向不变。
证据：lead/next_re_20261117_r14/R17_B3_REVIEW/VERDICT.md；lead/next_re_20261117_r14/R17_B3_REVIEW/g1g5.tsv；lead/next_re_20261117_r14/R17_B3_REVIEW/byte_checks.tsv；lead/next_re_20261117_r14/R17_IMG_PIN/region_check.tsv。
理由：本项把“位置成立”与“语义成立”拆开，靠 G5 返回约定和分配先后判定对象生命周期，而不是靠操作数形态下结论。

### 4. R11 链卡（R17-R11-CTOR-CHAIN）
链首 entry 记为 43B680、43B740、43BCF0。host1 主链 0x43B680 -> 0x6F4300 -> 0x65A7E0 -> 0x5F3B50 三层逐边字节证实，下一边 0x5F3B58 -> 0x4101C0；host2 主链 0x43B740 -> 0x6F2B40 -> 0x65A750 -> 0x5B2DA0 三层逐边字节证实，下一边 0x5B2DA3 -> 0x5F3900。host3 第 1 层断开：10 个 call 无一具 ctor 形态。连到 TechnoClass 层级 = 未取得；0x6F2B40 与 0x6F4300 互不调用，全镜像各 2 个直接 caller（host + 旁支）。盘上旁支 call site 为 0x4D31EA -> 0x6F2B40 与 0x4D3548 -> 0x6F4300；卡面写 0x4D31E0 / 0x4D3540，并列报出：卡面值 0x4D31E0 -> 盘上值 0x4D31EA（偏 10 字节，盘上该处为 E8 51 F9 21 00），卡面值 0x4D3540 -> 盘上值 0x4D3548（偏 8 字节，盘上该处为 E8 B3 0D 22 00），差异解释为卡面落在序言段而非 call 指令起点。
Q3 = 不重合。0x7E3EBC 族安装站点全镜像 3 处；盘上 C7 06 BC 3E 7E 00 的模式起点为 0x43B71F / 0x43B9FA / 0x43BCFD，卡面写 0x43B721 / 0x43B9FC / 0x43BCFF。并列报出：0x43B721 -> 0x43B71F、0x43B9FC -> 0x43B9FA、0x43BCFF -> 0x43BCFD，三处卡面值均是 imm32 字段起点（相对指令起点各偏 +2），不是 c7 06 的起始字节。0x6F2B40 体内 vt 写为 0x6F306A [esi+0x440]=0x7E4E78，以及 0x6F3130 / 0x6F3136 / 0x6F313D / 0x6F314A 的 0x7F4960 / 44 / 3C / 34，不含 0x7E3EBC 族；site 与写目标均不同，只有对象同一（host2）成立。
证据：lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/REPORT.md；lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/residual.md；lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/chain.tsv；lead/next_re_20261117_r14/R17_AUDIT_R11/edges.tsv；lead/next_re_20261117_r14/R17_AUDIT_R11/byte_checks.tsv；ra2youli/gamemd.exe。
理由：本项以 call 位移和目标入口锚点证明层级，但把类身份、站点起点和旁支 call 起点分成三类证据强度，故能保留链结论同时暴露五处地址口径差。

### 5. 审计 R11 v1 读错镜像（结论作废）
R17_AUDIT_R11 自述对象是 D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/PATCH_D35R/work/run/gamemd.exe，sha256 36A875775DA89239E370AAF091DBE5D3D3C5F2F8017D9EFA6A15FCDD4801C7F4，不是基准 73201CC0...。因此其 B1–B4、8/8 边等字节级结论一律作废，须以镜像钉哈希后的平移结论替代。但其第〇节的 §2.6 文字判定有效，因为读的是 R14_COMMON 文本，与镜像无关。
证据：lead/next_re_20261117_r14/R17_AUDIT_R11/summary.json；lead/next_re_20261117_r14/R17_AUDIT_R11/VERDICT.md；lead/next_re_20261117_r14/R17_IMG_PIN/hashes.tsv。
理由：本项先判定证据对象身份，再分离文本证据与字节证据，避免把“镜像错”扩大成“文字判定也错”。

### 6. R11 执行卡未记录镜像 sha256
R17_R11_CTOR_CHAIN 全目录逐文件搜索 sha256、64 位 hex 和“哈希”命中 0 处。执行卡未钉死实际打开的镜像路径与哈希，违反其余卡片纪律，是这次镜像漂移未被更早发现的直接原因。
证据：lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/REPORT.md；lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/residual.md；lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/work.py；lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/chain.tsv；lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/calls.tsv。
理由：本项记的是可追溯性缺口而不是某个字节结论，缺口使后续审计无法在发生时识别对象错位。

### 7. 镜像钉哈希（R17-IMG-PIN）
两文件 size 同为 4,825,360 B；基准 sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476，副本 sha256 36A875775DA89239E370AAF091DBE5D3D3C5F2F8017D9EFA6A15FCDD4801C7F4。整文件连续差异 9 处：8 处各 3 字节 + 1 处 49 字节，合计 73 差异字节，VA 依次 0x4A8B76、0x640428、0x6D059C、0x6D0635、0x6D0941、0x6D09FB、0x6D1294、0x6D1633、0x7DF781。两个 ctor 区间、三个 host 区间、8 处单点 8 字节邻域共 13 行，diff_bytes 全 0；上一轮在副本上的字节结论可无损平移到基准。该事件是流程缺陷，不是结果缺陷。
证据：lead/next_re_20261117_r14/R17_IMG_PIN/REPORT.md；lead/next_re_20261117_r14/R17_IMG_PIN/hashes.tsv；lead/next_re_20261117_r14/R17_IMG_PIN/diff_ranges.tsv；lead/next_re_20261117_r14/R17_IMG_PIN/region_check.tsv；ra2youli/gamemd.exe；lead/next_re_20261117_r14/PATCH_D35R/work/run/gamemd.exe。
理由：本项用全文件差异闭包与关心区间闭包两层对照，证明结果可平移的同时把责任限定在流程层。

### 8. Lead 自查结掉的一处分歧
Lead 直接读基准镜像：0x65A7E8 = E8 63 93 F9 FF，rel32 = -421021，目标 = 0x5F3B50；审计 v1 对，执行方写 E8 63 C6 E1 FF 是笔误。同批核对命中：0x43B74B = E8 F0 73 2B 00（-> 0x6F2B40）、0x43B688 = E8 73 8C 2B 00（-> 0x6F4300）、0x6F322F = 0C 01、0x6F3237 = 88 46 14、0x65A753 = E8 48 86 F5 FF。
证据：ra2youli/gamemd.exe；lead/next_re_20261117_r14/R17_AUDIT_R11/VERDICT.md；lead/next_re_20261117_r14/R17_AUDIT_R11/byte_checks.tsv；lead/next_re_20261117_r14/R17_AUDIT_R11/edges.tsv。
理由：本项靠 rel32 和下一条指令地址反算目标，消除的是单一 call 字节串笔误，不改动边本身成立的事实。

### 9. Lead 错误 R17-2（单列）
我在 R17-R11-CTOR-CHAIN 卡面把 0x6F322F -> 0x6F3237 写成“②-b 那个 vtable 的唯一写点”，错。R14_COMMON §2.6（第 194、199 行）一直写的是 or reg8,1 -> mov [reg+0x14],reg8，bit0 恒 1、唯一写点 0x6F322F，即 bit0 标志写点，从来不是 vtable 写点。字节：0x6F322F = 0C 01（or al,1）、0x6F3237 = 88 46 14（mov [esi+0x14],al）。结论：§2.6 无误，错在卡面。执行方据此在 REPORT.md 写“Q0 关键前提更正”并在回执里主张“§2.6 需更正”，该主张不得入账。审计 R11 第〇节独立判定“§2.6 无需更正”，并指出该措辞出自派发卡面。
证据：lead/next_re_20261117_r14/R14_COMMON.md:194；lead/next_re_20261117_r14/R14_COMMON.md:199；lead/next_re_20261117_r14/R17_AUDIT_R11/VERDICT.md；ra2youli/gamemd.exe。
理由：本项纠正的是错误归因链，必须把文本原意、实际字节和执行方转述三层分开，绝不能因执行方“更正” wording 而改判 §2.6。

### 10. 流程缺陷 R17-3（新纪律）
本轮“审计读了非基准镜像”和“执行卡未记哈希”两件事叠加。即日起：卡面必须钉死镜像绝对路径与 sha256；报告第一行必须写实际打开路径与实际算出的 sha256；不写即作废，不进入事实底座。
证据：lead/next_re_20261117_r14/R17_AUDIT_R11/summary.json；lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN；lead/next_re_20261117_r14/STATUS_BOARD.md:245。
理由：本项不是对旧事实的追加解释，而是从两起独立事故的交叉点提炼准入条件，故单列为纪律缺陷。

### 11. 本轮净结论（供后续引用）
三个 host 类名仍未取得，全文件只有 6 处装饰名 raw 引用、valid 为 0，均不在 host 内。322 槽段族属 TechnoClass 派生只能算推断：host2 字节证实调用 0x6F2B40，而 §2.6 记录 0x6F2B40 为 TechnoClass ctor，依赖既有记录的推断，不是字节证实。0x43F180 / 0x449440 的调用者与槽偏移仍未取得；虚派发仍为推断；逐槽立即数、直接调用、索引派发三条路径均已排除。
证据：lead/next_re_20261117_r14/STATUS_BOARD.md:247；lead/next_re_20261117_r14/R17_R10_DISPATCH/residual.md；lead/next_re_20261117_r14/R17_R11_CTOR_CHAIN/residual.md；lead/next_re_20261117_r14/R17_AUDIT_R11/VERDICT.md。
理由：本项按“已证 / 推断 / 未取得”三档收束后续可引用结论，避免把链证据越权升级成类身份字节证据。

本草为 §1058 草稿，由 Lead 逐字追加；书记员未自行改动台账。
