## §1057 · 书记员覆盖 R17 第 4 轮（R8/R9 双卡 + 两次异族审计 + 一次第三方裁决 + 派发通道切换）：调用者/槽偏移仍未取得，虚派发降级为推断，§1056 四项现状并列

> 本草为书记员草稿，全部数字由书记员本轮从盘上独立复算（gamemd.exe SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，4,825,360 B；复算细目见同目录 `numbers.tsv`）。书记员只起草，不改台账与任何控制文件。
> 地址口径（全节统一）：指令地址一律带 `0x` 前缀；entry 用 8 位大写十六进制不带 `0x`（如 entry `43F180`）。

### 事项 1 · R8 卡闭合 R7 四个「未取得」与三处锚点陷阱
- 证据：`lead/next_re_20261117_r14/R17_R8_RESIDUAL/REPORT.md`、`anchors.txt`、`sites.tsv`、`residual.md`、`work.py`。
- 四问结果：① 调用者——entry `43F180` 与 entry `449440` 各有且仅有 1 个静态数据引用（`.rdata:0x7E3FE0` / `0x7E4068`），直接 `E8`/`E9` 调用各 0；② `0x47C620` 精确尾界 `0x47CA7C`（函数体 `[0x47C620,0x47CA7C)`）；③ `0x43F5D8` 块内 `call 0x6F4A70` 返回值在 `0x43F5E3` 被 `32 C0` 覆盖（可字节证实的是返回值被丢弃；唯一作用=副作用是未标注推断）；④ case 0（`0x43F1CA`）/ case 2（`0x43F9A6`）均不产生拒绝、恒 `al=1`。
- 执行方自记三处锚点陷阱（复算确认）：C2 判序须终止符优先（否则 `0x43F1E9` 因 `0x43F1E8=90` 落在 `C2 04 00` 立即数内被误判无锚点）；节界须按 rawsize（否则 .text 的 vsize 吞掉 .rdata 起头，`0x43F1E9` 附近读成 `00 00 00`）；`0x47CA70` 须按标签从 `0x47CA6A` 的 `jne` 起步（否则解出 `add byte ptr [esi-0x16ffbc07],ah` 乱码）。
- 理由：R8 是闭合卡，其价值取决于四问是否各自有独立字节/扫描证据，而非复核 R7 结论；三处陷阱直接决定前两问的字节读数是否正确，必须与四问结果一并留痕，否则下游无法判断哪些 R7 数字被替换。

### 事项 2 · 审计 R8（跨家族 hy4）五项判定与五条必改
- 证据：`lead/next_re_20261117_r14/R17_AUDIT_R8/VERDICT.md`、`addr_authority.tsv`、`byte_checks.tsv`。
- 判定：A1 DISAGREE；A2 AGREE（但虚派发降级为推断）；A3 AGREE；A4 AGREE；A5 DISAGREE（唯一作用=副作用被放进事实段）。必改 5 条：① 三处 `0x43F24B/0x43F501/0x43F5AD` 改标 SIB 字节位置、指令起始权威值 `0x43F249/0x43F4FF/0x43F5AB`；② R7 jne 挂载行 `0x47C73D`→`0x47C73F`；③ R7 xor 地址 `0x47C853`→`0x47C856`（`0x47C853` 注明 `5F`/pop edi）；④ Q1 表界改为极大连续段 `[0x7E3EBC,0x7E43C4)` 或标注局部邻域；⑤ Q3 唯一作用=副作用移入推断段并标强度。
- 理由：异族审计的增量在表述纪律而非重算数值——A1 是口径、A2/A5 是推断降级、A3/A4 是复核一致；五条必改分布在执行方与 R7 正文维护者两个不同责任方，逐条留痕才能避免只改数值不改措辞的假闭合。

### 事项 3 · 地址权威表（A1 实质）
- 证据：`lead/next_re_20261117_r14/R17_AUDIT_R8/addr_authority.tsv`、`byte_checks.tsv`；盘上字节由书记员复算命中。
- 复算（`0x` 前缀为指令起始）：`0x43F249 = 88 5C 24 23`（mov byte [esp+0x23],bl）、`0x43F4FF = C6 44 24 23 01`（mov byte [esp+0x23],1）、`0x43F5AB = 8A 44 24 23`（mov al,[esp+0x23]）为指令起始权威值；`0x43F24B/0x43F501/0x43F5AD` 的 `24` 是 SIB=0x24 字节位置（口径差，非真错）。`0x47C73F = 0F 85 0E 01 00 00`（rel=`+0x10E`，目标 `0x47C853`）为 jne 起始，R7 挂 `0x47C73D`（实为 `3B C5` cmp eax,ebp）错、目标正确；`0x47C853 = 5F`（pop edi），`0x47C856 = 32 C0`（xor al,al），执行方对、R7 错。
- 理由：这六行同时存在口径差与真错两类，性质不同——前者两方可共存、后者必须二选一；若不做权威表而只列命中，下游会把 SIB 位置当指令起始继续传播错位，也会把 R7 的 jne/xor 两处真错当作无分歧。

### 事项 4 · R9 卡（独立复现 + 表形态否定）
- 证据：`lead/next_re_20261117_r14/R17_R9_VTABLE_CONSUMER/REPORT.md`、`tables.tsv`、`consumers.tsv`、`residual.md`。
- R9 先独立复现唯一静态引用：全 5 节逐字节 4 字节小端扫描，`0x43F180` 命中 1（`0x7E3FE0`）、entry `449440` 命中 1（`0x7E4068`），`E8/E9` 直接调用各 0——与 R8 一致。
- 随后判 R8 表形态不成立：以非 .text 指针即边界口径报连续 350 槽串 `[0x7E3E8C,0x7E4403]`，`0x7E3FE0` 为 #85、`0x7E4068` 为 #119（书记员复算：`0x7E3FE0` 的串内序号 `(0x7E3FE0-0x7E3E8C)/4=85`、`0x7E4068` 为 119，与 R9 自报一致）；零取用者（12 候选立即数 0 命中）；`call [reg+off]` 与槽偏移未取得；RTTI 类名未取得。
- 理由：R9 的方法论价值在先独立复现再否定——若跳过复现直接否表，就无法区分 R8 唯一引用错与 R8 表界错；本报告把两者分开，才使后续裁决卡能只裁决段界而不再动摇唯一引用这一共同前提。

### 事项 5 · 第三方裁决卡（R17-ADJ-RDATA-RUN，单问题）
- 证据：`lead/next_re_20261117_r14/R17_ADJ_RDATA_RUN/VERDICT.md`、`run.tsv`、`neighbors.tsv`。
- 裁决结论：text-only 极大连续槽段 = `[0x7E3EBC,0x7E43C4)`（半开，等价闭 `[0x7E3EBC,0x7E43C0]`）共 322 槽；`0x7E3FE0` = #73、`0x7E4068` = #107。两种 .text 上界口径（hi=`0x7E038D` 虚拟末尾 / hi=`0x7E1000`）结果一致（书记员复算两口径均 322 槽；整节 .rdata 落在灰区 `[0x7E038D,0x7E1000)` 的槽数 = 0）。
- 判甲（R8 段界）对、乙（R9）错：R9 左端早 12 槽、右端晚 16–17 槽、共多 28 槽（书记员复算 `0x7E3EBC-0x7E3E8C=0x30`→12 槽；`0x7E4403-0x7E43C0=0x43`→16.75 槽；`350-322=28`）；串内含 `0x7FC2B0`（`0x7E3E8C`）、`0x7FC360`（`0x7E3EB8`）、`0x7FC298`（`0x7E43C4`）等非 .text 值。
- 理由：这是本轮唯一一次两卡互斥后由第三方自算的实例——裁决卡不复用 R8/R9 任何一方脚本、只做 4 字节读数与区间比较，才能同时给出甲对乙错与两口径一致这两个互不依赖的判据；若由 Lead 自行择一，就失去独立第三方的意义。

### 事项 6 · 审计 R9（跨家族 hy4）四项判定与四条必改
- 证据：`lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md`、`controls.tsv`、`bounds.tsv`。
- 判定：B1 AGREE（12 候选立即数各 0 命中；正控 `0x5A9940`=54、`0x77D710`=56、`0x6A00A8`=126，`E8`→`0x47C620`=10；4 种反控全通过）；B2 DISAGREE（独立复算同为 322 槽，与裁决卡一致，确认 R9 错）；B3 DISAGREE（发现 12 处 ctor 形态立即数装表写）；B4 AGREE（.rdata 装饰名 0、无 pTD，未取得诚实）。
- 必改 4 条：① B2 段界 `[0x7E3E8C,0x7E4403]`/350 改 `[0x7E3EBC,0x7E43C4)`/322、#85/#119 改 #73/#107、明确 R8 对 R9 错；② B3 撤回 ctor 装表被否改为存在 12 处立即数装表写；③ B3 把 `0x7E3E90/0x7E3E98/0x7E3EA0/0x7E3EBC` 从字符串/常量地址更正为函数指针槽（内容均 .text）并登记取用者与位置断言；④ B1 12 个候选与实列 11 个不一致，补齐第 12 个（`0x7E406C`）或改口径为 11，零命中不变。
- 理由：审计 R9 与裁决卡虽同判段界，但 B2 是独立复算确认第三方、B3 是发现执行方遗漏的正向证据、B1/B4 是验证诚实性，四者的取证方式互不相同；把 B3 单列为 DISAGREE，才使零取用者这一负面结论被一条正向反例限定住边界。

### 事项 7 · B3 发现边界（12 处装表写消费的是串首附近，不是 #73/#107；审计单源）
- 证据：`lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md`、`controls.tsv`（B3 行）；书记员盘上字节复算见 `numbers.tsv`（B3_slot_* 行）。
- 12 处形态均为 `mov dword ptr [esi/ebp+off], imm32`，目标槽为 `0x7E3E90 / 0x7E3E98 / 0x7E3EA0 / 0x7E3EBC`：书记员复算四槽内容分别为 `0x410590 / 0x410580 / 0x4105E0 / 0x410260`（均落在 `.text`，即函数指针，非字符串常量）。每槽 3 处立即数写，共 12 处：`0x7E3EBC` 写点立即数地址 `0x43B721 / 0x43B9FC / 0x43BCFF`（`C7 06 …` 指令起始在立即数地址前 2 B，如 `0x43B71F`），`0x7E3EA0` 在 `0x43B728 / 0x43BA03 / 0x43BD08`，`0x7E3E98` 在 `0x43B72F / 0x43BA0A / 0x43BD0F`，`0x7E3E90` 在 `0x43B736 / 0x43BA11 / 0x43BD16`。
- 三 host 与位置断言（书记员复算两种口径——立即数地址与指令起始——均满足 `host <= site < fn_end`）：host `0x43B680–0x43B740`（site 指令起始 `0x43B71F/0x43B725/0x43B72C/0x43B733`）、host `0x43B740–0x43BCDE`（`0x43B9FA/0x43BA00/0x43BA07/0x43BA0E`）、host `0x43BCF0–0x43C0CA`（`0x43BCFD/0x43BD05/0x43BD0C/0x43BD13`）。
- ⇒ 这 12 个取用者消费的是串的前几个槽（`0x7E3E90`–`0x7E3EBC` 一带，含裁决段首 `0x7E3EBC`=#0），不是 #73（`0x7E3FE0`）也不是 #107（`0x7E4068`）；书记员复算 `0x7E3FE0/0x7E4068` 及其邻槽的立即数命中仍全为 0。
- 引用限制：该结论为审计单源（R17-AUDIT-R9 B3），书记员本轮只做字节层复算、未做二次独立审计复核，任何引用须标注审计单源。
- 理由：B3 把零取用者从全称否定修正为局部否定，但它的证据只有一份异族审计、且 site 地址存在立即数地址 vs 指令起始的口径差——两处都必须显式标注，否则下游极易把有 12 处取用者误读成 #73/#107 的取用者已取得。

### 事项 8 · 本轮净结论（供后续引用）
- 证据：`lead/next_re_20261117_r14/R17_R8_RESIDUAL/REPORT.md`、`R17_AUDIT_R8/VERDICT.md`、`R17_R9_VTABLE_CONSUMER/REPORT.md`、`R17_AUDIT_R9/VERDICT.md`、`R17_ADJ_RDATA_RUN/VERDICT.md`（书记员逐项复算见 `numbers.tsv`）。
- entry `43F180` 与 entry `449440` 各有且仅有 1 个静态数据引用（`.rdata:0x7E3FE0` / `0x7E4068`，书记员全镜像复算各 1 命中）；`E8` 与 `E9` 直接调用均为 0；书记员复算 12 个候选槽地址（`0x7E3FDC/0x7E3FE0/0x7E3FE4/0x7E3FE8/0x7E4050/0x7E4054/0x7E4058/0x7E405C/0x7E4060/0x7E4064/0x7E4068/0x7E406C`）在 .text 的 4 字节立即数命中全为 0 ⇒ 没有任何指令以立即数装载这两个槽或其邻槽。
- ⇒ 调用者与槽偏移均未取得；虚派发仍为推断（强度中）。该区间确为 vtable 型数据：前几槽有 12 处 ctor 装表实证（审计单源，见事项 7）；但 #73/#107 无装表点、无取用点，故不得把虚派发升格为已证。
- 理由：本轮三次取证（R8/R9/裁决）加两次审计的共同收敛点是一个否定性结论——唯一能升级为事实的只有各 1 个静态引用 + 0 直接调用 + 0 立即数装载，其余全是推断；把结论写成未取得 + 推断双层，是为了在同一段里既保留 vtable 形态的正向证据、又不越界宣称派发链已闭合。

### 事项 9 · §1056 四项「未取得」的现状（并列，防下游误引）
- 证据：`lead/next_re_20261117_r14/STATUS_BOARD.md`（R17 各段上下文）、`lead/next_re_20261117_r14/LEAD_LOCK`（末尾 P–S 节）；技术底座 `lead/next_re_20261117_r14/R17_R8_RESIDUAL/REPORT.md`。
- 现状并列：① `0x47C620` 精确尾界已取得 = `0x47CA7C`（函数体 `[0x47C620,0x47CA7C)`，书记员复算区间内 `C2 0C 00` 共 10 条：`0x47C6CA/0x47C6DA/0x47C760/0x47C833/0x47C85C/0x47C875/0x47C9A4/0x47CA30/0x47CA4A/0x47CA79`；1 个成功 epilogue（`0x47CA70`→`0x47CA79`，`al=1`）+ 9 条 early-exit 尾巴，`0x47CA79` 后 `0x47CA7C..7F = 90 90 90 90`、`0x47CA80` 为新函数）；② case 0（`0x43F1CA`，`0x43F1DD = B0 01`）/ case 2（`0x43F9A6`，`0x43FAFC = …B0 01…`）已取得 = 均不产生拒绝（恒 `al=1`）；③ `0x6F4A70` 语义仍未取得（仅标为推断、强度中：失败播报/音效类副作用，字节只证实 `mov esi,ecx`、读 `[esi+0x418]`、`call [edx+0x274]` 传 `0xD`、`ret 4`、返回值被 `0x43F5E3` 的 `xor al,al` 丢弃）；④ 两函数调用者仍未取得（同事项 8：各 1 静态引用、`E8/E9`=0、立即数装载 0）。
- ⇒ 引用 §1056 的这四项必须同引 §1057：①②已被本轮闭合、③④维持未取得，单独引 §1056 会把尾界未取得/槽语义未取得误当现态。
- 理由：四项分处已取得与仍未取得两种状态，且同一函数（`0x47C620`）既贡献了已取得的尾界又关联未取得的 `0x6F4A70` 语义——只有逐项并列，才能防止下游把整段 §1056 当作同等级证据整体引用或整体作废。

### 事项 10 · 一处 Lead 级环境发现（live profile 截面漂移）
- 证据：`C:/Users/Administrator/.dsh/profiles/desktop/package.json`（书记员盘上实读）、`pnpm-lock.yaml`、`node_modules/dsh-purge-community/package.json`；`lead/LEAD_LOCK`（末尾 R 节，记 1.6.93 #commit 钉死与装后核对）。
- 书记员盘上复算：live profile `package.json` 的 `dsh-purge-community` 规格为 `https://github.com/kingcharleslzy-ai/dsh-purge/releases/download/v1.7.20/dsh-purge-community-1.7.20.tgz`，`node_modules/dsh-purge-community/package.json` 的 version = 1.7.20（非 LEAD_LOCK §R 记的 1.6.93 #commit `accadd4062d6aa739d3bbf83f355515c99423baf` 钉死）；`package.json` mtime = 2026-11-21T06:25:23.838Z（= 14:25:23 +08:00），晚于 LEAD_LOCK §R 记录时刻；该 profile 的 `dependencies`（仅 `@dsh-external/dsh-harness-pilot`、`dsh-plugin-grill-me`、`dsh-purge-community`）与 `node_modules/@deepseek-ai/`（空目录）中已无任何 @deepseek-ai/* 包。
- ⇒ 通道可用性是实测事实（本书记员即经内部 subagent 通道挂载运行；provider magpie-anthropic、4 个模型可选，见事项 11），但安装来源为未取得；不得把 LEAD_LOCK §R 的装后核对当作当前截面。
- 理由：这一项是截面而非结论——LEAD_LOCK §R 记录的是某一时刻的装后状态，而当前盘面已与之不符；若照引旧记录，会把 @deepseek-ai/* 全家零漂移误当现态，掩盖安装来源不可追溯这一事实，故必须以当前盘为准并把来源留白。

### 事项 11 · 派发通道切换（内部 subagent，身份仍不可校验）
- 证据：`lead/LEAD_LOCK`（末尾 P–S 节）、`C:/Users/Administrator/.dsh/profiles/desktop/cordis.patch.yml`（书记员实读 whitelist）；`lead/next_re_20261117_r14/STATUS_BOARD.md`（R17 通道实况段）。
- 本轮起派发改走内部 subagent 工具；首个探测回执 OK / 自报模型: 未回报 ⇒ 身份仍不可校验（与旧 pi 通道同病：pi 通道 provider/model 亦未回报）。书记员实读 `cordis.patch.yml` 的 `subagent-model-selection-settings.allowedModels` 共 4 条（provider 均 magpie-anthropic）：`work/cn:deepseek-v4.1-flash`、`work/cn:hy4flash-free`、`work/cn:hy4flash`、`zcode/GLM-5.3-Flash`——4 个模型可选与卡面一致（LEAD_LOCK §S 步骤 1 只点名 3 个，漏 `work/cn:hy4flash`）。
- ⇒ 本轮全部结论的可信度建立在异族审计 + Lead 对盘复算上，不建立在通道身份上。
- 理由：配置层白名单有 4 个模型与运行层自报模型未回报是两件事——前者只说明工具已挂载，后者才是身份可校验性的判据；把两者分开记，才能解释为何通道可用却仍不能作为结论的可信度来源。

### 事项 12 · 方法学（本轮两次生效，建议入 COMMON）
- 证据：`lead/next_re_20261117_r14/R17_AUDIT_R8/VERDICT.md`（正控/降级的实例）、`R17_AUDIT_R9/controls.tsv`（正控/反控表）、`R17_ADJ_RDATA_RUN/VERDICT.md`（裁决实例）、`R17_AUDIT_R9/VERDICT.md`（B3 单源实例）。
- ① 负面结论必须自带正控与反控，否则 0 命中不可采信（本轮 B1 用 `0x5A9940`=54/`0x77D710`=56/`0x6A00A8`=126 与 `E8`→`0x47C620`=10 作正控，4 种反控全过，才使 12 候选 0 命中可采信）；② 单源结论一律降级为推断并标强度（A2 虚派发、B3 12 处装表写取用者均按此处理）；③ 独立分析互相矛盾时，用单问题裁决卡由第三方自算，禁止 Lead 自行推断或默认采信一方（R8 段界 vs R9 段界 → R17-ADJ-RDATA-RUN 自算 322 槽）。
- 理由：三条方法学各自堵住本轮一类具体失误——①堵扫描器失效的假空、②堵单源当已证、③堵 Lead 在互斥卡间择一——它们是本轮两次审计与一次裁决反复触发的规则，不是空泛倡议，故建议入 COMMON 供后续直接引用。

---

本草为 §1057 草稿，由 Lead 逐字追加；书记员未自行改动台账。
