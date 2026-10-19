# POISON_GEN_DESIGN · crashspec #4 毒值事件发生器骨架设计

> 版本：骨架草案 v0（2026-10-18，主会话代拟——np4 通道三连空返回后的止损产物；待分析员补深水）。
> 性质：纯设计提案，零代码实施、零真机执行；施用须主会话按补丁纪律审批。
> 依据：`crashspec_v4\RC_SPEC_V4.md` §0-1/§3.1（[实证] 机制链）、`claims_rc_guard_windows.txt`、#14 双定谳。

## 1. 目标与语义

#4 A/B 协议 = 在低负载语料无自然毒值事件时，**人工制造一次真实的 SBH freelist 腐化事件**，端到端验证 P1/P2 捕获链路「能抓到」。P2=读点守卫（RC-1 补丁位 0x7CFC9B 的 freelist 节点合法性守卫）；P1=写点捕获（unlink 落点 0x7CFD30/0x7CFD39 的写者指认）。

## 2. 注入选型（三案对比）

| 案 | 机制 | 安全域 | 可逆性 | 观测扰动 | 裁定 |
|---|---|---|---|---|---|
| A 调试宿主 | 独立宿主进程 DebugActiveProcess/WriteProcessMemory，运行时发现 SBH freelist 后写 4B | 零文件改动（纯内存） | 高（仅 4B 写，进程自带毒值消费） | 最低（单点 4B；调试附加有被检风险→**用非调试式 VM_WRITE**：仅 WriteProcessMemory 不 DebugActiveProcess，无异常直达） | ★主案 |
| B 载体内联补丁 | 改 gamemd 磁盘字节加注入口 | 触碰冻结镜像（违反 G0.1/G0.2） | 低（需镜像回滚） | 高 | 拒（与 #14 语义冲突） |
| C DLL 内钩子 | 注入 DLL 挂 __sbh_alloc_block | 引入第三方模块 | 中 | 高（新模块改变捕获现场） | 回退案（仅当 A 的堆发现失败） |

## 3. 毒值事件精确定义

- **写什么**：`DWORD 0xFE00FFFF`（MSVC6 SBH「无节点」哨兵，映像内零立即数命中——#14 哨兵短路定谳的合法毒值）。
- **写哪里**：任一 **当前非空 SBH freelist 的 head->next 槽**。运行时发现算法：定位 `__sbh_heap_info`（签名扫：`HeapAlloc(0x41C4)` 句柄的堆基址区间内，按 SPEC §0-1 的 `heap_info + class*0x204 + 0x144` 布局逐 class 验证 `head → node` 链一致性，≥2 个 class 链一致才认定基址）。**禁止硬编码 0x1498FB8C**（那是崩溃语料环境的偶发基址）。
- **写哪个 class**：class 4（80B 块，req 57–72B——与崩溃现场同类，业务写入压力高、毒值被消费快）。
- **时机**：游戏进战术画面后（帧钟 >600，且 CPU 占用平稳段），一次性注入 **1 次 4B**。
- **预期后果**：下一次 class 4 分配走到 `__sbh_alloc_block` 取 head->next=毒值 → P2 守卫（若装）在 0x7CFC9B 拦截降级；裸奔态（无守卫）则复现 0xC0000005@FE00FFFF 崩溃现场（= 原始崩溃的忠实复刻，except.txt 可比对）。

## 4. 验收判据

1. **注入成功且只注入该写的**：写前读后做 64B 窗口内存差分——**有且仅有目标 4B 变化**。
2. **P2 端到端**：装守卫态下，注入后该 class 下一次分配触发守卫日志（`SbhGuard=poison-hit` 或等价哨兵）且游戏不崩（降级生效）。
3. **裸奔端到端**：无守卫态下，注入后 except.txt 出现与 §0-1 逐字节同构的崩溃现场（Access address:FE00FFFF / EDX=FE00FFFF / EDI=4）。
4. **假阳排除**：空跑（不注入）同时长对照局零命中。
5. **假阴排除**：注入后若 60 游戏秒内无消费，重新选一个新分配的 freelist head 再注入一次（≤3 次预算；SBH 块复用可能吃掉毒值）。

## 5. 风险表+回退梯

| 风险 | 缓解/回退 |
|---|---|
| 堆基址发现误判→写崩无关内存 | 链一致性验证 ≥2 class；写前快照整 freelist 链，写后立即校验链形态符合预期；不符即回写原值 |
| 毒值被良性分配消费（无守卫态=直接崩=预期；守卫态=降级） | 非风险，是验收本身 |
| 调试附加被反作弊/游戏检测 | 用非调试 VM_WRITE（不 attach 调试对象） |
| 写时机撞上游戏正在操作该链 | 帧钟阈值+写后链校验；失败即回写重试（≤3） |
| 镜像身份漂移 | 宿主先跑 G0.1 同款 sha 校验（73201cc0…）再开工 |

## 6. 集成点（提案级）

- **trip harness**：不动锚定脚本；发生器=独立宿主工具（建议 `qc_poison_gen.py`），由趟前脚本以独立进程启动（与 qc134/qc135 同级），产物=注入日志+差分证据件入 evidence/。
- **时序**：trip 导航进战术面后由外部触发注入（发生器自轮询帧钟）。
- **与 A5 八跑**：载体/判读链可复用（A5 悬停标定臂的 21 脉冲/对拍基建直接可用）；#4 只增「注入步」。

## 7. 未决问题（留主会话批）

1. P1（写点捕获）的仪器形态未定——写点 0x7CFD30/39 的捕获需页面保护（guard page）或逐写断点，均高扰动；先 P2 后 P1 的次序请裁决。
2. 注入宿主的写域归属（crashspec 写域 or qc 工具写域）。
3. 裸奔态崩溃复刻是否在 A/B 范围内（会终结该局=语料消耗）。

---

# 深水补章节 §A1–§H1（分析员追加，2026-10-19）

> 性质：**纯追加（append-only）**——上方 §1–§7 骨架原文零改动；方向性分歧一律在本节「勘误」显式标注，不静默改写。
> 通道注记：np4 断连，本件为 GLM 兜底强交付；**增量落盘制**（每完成一节立即写盘）。
> 结论标注口径：**[事实]** = 所引 path:line 可直接复核；**[推断]** = 由证据链推理已显式标注；**[INSUFFICIENT]** = 证据不足，缺什么已点名。
> 铁律自查：本文撰写全程零真机动作（未启动 gamemd/ra2loader/YURI、未 taskkill、未跑 qc151_trip/qc134/qc135）；唯一写入=本文件；未触碰 QC161 签署块与任何母本。

> ---
> ★★★ **修订层 v1（2026-10-19 · 独立修订者）**：依独立审读报告 `DESIGN_REVIEW.md`（8 修订点 R1–R8，总裁决 NEEDS REVISION）逐条**就地修订**本层 §0–§H2；骨架 §1–§7 :1-:56 仍基线零改动（骨架面缺陷一律以勘误条目显式呈现，不改骨架原文）。本层原「append-only 不改写」自律自本版起由「**修订留痕**」取代：凡被 R# 触及的原文一律就地改写并逐条登记于文末 **§R 修订对照表**；R1–R8 处置回执=同目录 `REVISION_RECEIPT.md`。修订全程零真机动作；唯一写入=本文件+该回执。

## 0. 输入件与证据基线（含 INSUFFICIENT 登记）

已实读证据件：
- 骨架：本文件 §1–§7（5,010 B，2026-10-18 主会话代拟）。
- `crashspec_v4/RC_SPEC_V4.md`（751 行）：G0.1 指纹 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`（:7、:419）；崩溃现场寄存器/字节（:60-62、:74）；EIP 与文件偏移逐字节全等（:83）；class 4=80B 块/req 57–72（:91）；崩溃指令窗 `0x7CFC9B→0x7CFC9F`（:93-96）；unlink 写点 `0x7CFD30/0x7CFD39`（:99）；毒址算式 `0x1498FB8C=head(7,4)+4`（:102-103）；空表自环（:104）；NULL→Win32 兜底（:106）；region 描述符 `[0xB78B94]/[0xB78B98]`（:109）；毒值 imm32 映像 0 命中（:113）、判别式 `&3==3`（:114）；A/B 协议 E1-8 判据 J1–J6+红线（:137）；except_gate 旗标（:141-142）；EIP 分区（:143）；SEH 写 except.txt（:147）；守卫窗伪码与遥测（:485-:525、:545-:547、:588-:592）；#4 行（:698）。
- `lead/qc171_offline_batch_20261018/OFFLINE_BATCH_VERDICT.md`：#14 双定谳=堆锁无旁路（3/3 调用点持锁）+ 哨兵短路必须（健康堆不可达/腐化堆可达，head mod16=8）（:53-68、:208）。
- P1 验件 `lead/qc161_patch_QC205_verify_20261018/QC205_VERIFY.md`：qc135_objloc.py 锚 `1355dead…e77e`/299,887B（:73）、`l3_poison_poll` 被动轮询链与 A 臂等价（:193、:197；边界申报 :292-297〔v1 修正 · R8：原引 :307 落在结论节〕）、AST 禁用 API=0/19 名（:267）。
- P2 验件 `lead/qc161_patch_QC209_20261018/QC209_VERIFY.md`：qc134_attach.py 锚 `6378b538…5810`/237,098B（:8、:32-36）、`p05_scan_poison`/in_domain（:76-79）、槽算术 `addr=entry+0x24`（:83）、`c4_active_set` cell 算术（:118-119）、退出码 31/32/33/34（:94）、只读边界（:87）。
- 仪器源码点读：`lead/qc135_objloc/qc135_objloc.py` `BAD_VALUE=0xFE00FFFF`（:190）、`L3P_WINDOW_MAX_S=15.0`（:245）、`l3_poison_poll`（:3629）、毒值事件记账（:3721、:4191）。
- `lead/qc170_spec_triage_20261018/SPEC_TRIAGE.md`：#1（:31）、#4=事件发生器（:32、:78）、执行排序（:76-78）。
- `lead/GOAL_THREE_TARGETS_20261018.md`：P1 QC205 放行（:30）、P2 P05 新锚 6378b538（:31）、A5 八跑判别升级（:36）、T24/25/27 误进 MP29U2 教训（:42）、T32 真进 U0400+W0 基线+W1/W2 帧钟停摆（:65）、C1C2 W0 窗尾冻结（:66）、EVID 1.8GB/趟磁盘税（:87）、火绒内存防护（:97）。
- `ra2youli/except.txt`（格式样板）：`Error code:`/`Access address:… was read from.`/`Exception occurred at 00724737`/寄存器块/`Bytes at CS:EIP` 行式。

**[INSUFFICIENT] 登记（缺什么）**：
- **I-1（v1 撤销改记 · R8）**：原登记「`D:\Project\ra2-campaign-forge\cards\QC161.md` 不存在 ⇒ 卡 §块不可达」**作废**——卡片实际存在于 `lead\cards\QC161.md`（808 行；另有 `QC161.md.bak_pre_QC190_20261017` 历史副本），系起草代理读件**路径拿错**（审读已定谳）。卡内 §T27(:502-508)、§T28(:512-518)、§T32(:549-554)、§T34(:568-573)、§T53(:746-753) 等结果块经独立审读逐点复核与设计件引用一致，本修订（R2 等）已直接对卡引用；**卡 §7 签署栏仍未读（纪律不变）**。
- **I-2**：守卫 trip 事件的日志行格式（骨架所称 `SbhGuard=poison-hit` 字符串）**未定稿**——SPEC 只钉死 `s_sbhGuardTrips` 计数器（RC_SPEC_V4.md:511、:546、:592）与「trip 日志 MUST 锁外产出」纪律（:521）；`SbhGuard=<tag>` 证据面仅有安装/门禁族 tag（:389、:419-423、:589）。判据以计数器为主（§D1）。
- **I-3**：守卫遥测「独立只读接口」（RC_SPEC_V4.md:399）的取数形态未落地（M 轨未建），计数器如何被外部读到无证据。
- **I-4**：SBH group 数上限无实证（现场单点 g=7，RC_SPEC_V4.md:60-65；region 计数动态，:109）；§A1 扫描上界 `GROUPS_MAX=32` 为 [推断] 工程裕度。
- **I-5**：P05 快照窗内目标进程死亡时 readings 收尾行为未验证（QC209_VERIFY 全离线，:150-151 自报零真机）。
- **I-6**：火绒/HIPS 对无签名宿主进程 WPM 的实际处置无历史证据（GOAL :97 仅登记等用户关内存防护）。
- **I-7（v1 措辞随 R2 更新）**：自然毒值基线发生率无数据（原措辞限定「低负载语料」，主用图换 spawnfix8 后负载档不设限，见 §F1）；B 臂首跑将首次给出。
- **I-8（v1 新增 · R1）**：**RC-1 守卫补丁（cave/安装器/`EnableSbhGuard` INI 开关）全链无实现证据**——工作链内 `EnableSbhGuard` 仅命中 spec/注记类 .md（RC_SPEC_V4.md:409 起、M1_RULING_ANNOTATION、SAFETY_REVIEW 等），无任何安装器/ra2render 产物；OFFLINE_BATCH_VERDICT.md:212（#15 行）明证 M 轨交付物「文档确未建（find 0 命中）」；I-3 自认「M 轨未建」。⇒ 批 1/2（守卫 ON）与 DEGRADED 判据悬于未建件上；处置=§C1「批 1/2 前置门」+§G1 G-0e（NOT_RUNNABLE 门）。
- **I-9（v1 新增 · 外部依赖登记）**：环境级 boot hang 定谳在案（卡 §T55 :726，真机全线暂停；复跑条件=:733「1 次独立 boot 探针通过」）、火绒内存防护判别链在途（GOAL :97）⇒ 本设计全部「真机批内」项的**共同前置=环境解锁**；离线项（G-0a–G-0d、D-6 匹配器、§A1.2 伪码评审）不受阻。

## 0-bis. 勘误（对骨架 §1–§7 的显式方向性修正）

- **勘-1（§3「时机」；v1 措辞修订=R8）**：骨架以「帧钟 >600」为注入触发单条件。**方向修正**：T32 已实证本语料存在帧钟停摆现场（W1/W2 停摆，GOAL :65，D-128 登记；**停摆位置**=W0 窗尾，GOAL :66 系 C1C2 设计时代的位置/形态记录——后续卡 §T32 :552/§T34 :570 定谳：冻结实为**战局终局计分板**静态画面，根因=U0400 原图出生点元数据损坏 ⇒ `HouseClass::AI` 逐帧判败 ⇒ frame≈738 记分板；对观察端的含义见勘-6 与修订点 R2）⇒ 帧钟闸门有**无限期挂起**风险。改为：主条件=harness 战术面进入确认（in_tactical 标志）+ 墙钟稳定窗；帧钟降为辅证字段（记录不判门）；注入器自带墙钟硬超时（默认 120 s），超时→NOT_ATTEMPTED。
- **勘-2（§7 未决 1）**：骨架称「P1 的仪器形态未定」。**已过时**：P1=QC205 被动轮询形态（`l3_poison_poll`）已 7/0/0 全 CONFIRMED 放行真机（QC205_VERIFY:33〔v1 修正 · R8：放行结论在 :33，:25 为判定计数行〕、GOAL :30）。「先 P2 后 P1 的次序请裁决」遂失去对象——本设计 §E1 按轮询形态作互扰分析；写点断点形态（`0x7CFD30` HW brk）仍属未来件（SPEC_TRIAGE:76 第 1 顺位后半），启用前须重评 §E1-路径3。
- **勘-3（§6 集成点）**：「由外部触发注入（发生器自轮询帧钟）」按勘-1 同步修正；并追加**台账先写后写纪律**：注入台账行（含 old dword）必须在 WPM 之前落盘，WPM 结果事后补写——保证事后关联不可被结果污染（§E1-5）。
- **勘-4（§4 验收 3 措辞）**：「与 §0-1 逐字节同构」过强——Eax/Ecx/Esp 等寄存器逐跑必异（原现场 Eax=0x1498EC08 本身就是崩溃语料环境偶发值，骨架 §3 自认）。改为「**结构同构 + 毒值字段逐字段相等**」，口径见 §D1 D-1（r1–r8）。
- **勘-5（§3「写什么」；v1 新增=R7）**：骨架称 0xFE00FFFF 为「MSVC6 SBH『无节点』哨兵」并挂 #14 名义——**误称**：空表「无节点」形态的哨兵是 **head 自环值**（OFFLINE_BATCH_VERDICT.md:66-67），`0xFE00FFFF` 是**与业务数据同值分布的腐化产物值**（RC_SPEC_V4.md:113-114 判别式 `&3==3`、映像 imm32 0 命中=非代码常量）。追加层 §B1/§A1.3/§E1-7 的语义一直按后者使用（「哨兵短路不误伤毒值」的论证正建立在毒值≠自环哨兵上），此处补显式勘误以对齐「方向性分歧显式标注」自律；骨架原文不动。
- **勘-6（§3「时机」观察端；v1 新增=R2）**：勘-1 换闸门时未点破的第二重事实：**原唯一用图 U0400（93c2974b）存在 ~24 游戏秒确定性提前终局**（卡 §T32 :552-553：738 帧÷30fps≈24.6s≡计分板 時口 00:00:24，每趟同值域；§T34 :570 根因=出生点元数据损坏→`HouseClass::AI` 逐帧判败→frame≈738 记分板）⇒ 骨架「帧钟>600」（≈20 游戏秒）距终局仅 ~4 秒即触线，且**观察端**的「≤60 游戏秒观察窗 / 60 游戏秒未消费再注」预算在计分板态**不可达**（游戏秒随计分板冻结、「稳定窗→注入窗」挤占 24s 大半）。处置=主用图换 spawnfix8 长战局语料+计时基准改墙钟+计分板态=观察窗合法终态（§C1/§F1 修订）。

## §A1 注入机制深水（骨架案 A 完整展开：独立宿主非调试 VM_WRITE 写 4B）

**选型裁定：维持案 A 不变**。本节仅补实施细节。宿主=独立 Python/ctypes 工具（建议名 `qc_poison_gen.py`，与 qc134/qc135 同级独立进程，骨架 §6 口径），进程权限面**仅** `OpenProcess(PROCESS_VM_READ|PROCESS_VM_WRITE|PROCESS_VM_QUERY|PROCESS_VM_OPERATION)` + `ReadProcessMemory`/`WriteProcessMemory`/`VirtualQueryEx`——零调试端口、零线程控制、零远程代码。

### A1.1 为何不 DebugActiveProcess（异常直达面论证）

1. **异常直达面**：裸奔臂（守卫关）的验收件就是 `except.txt`——游戏自带 SEH 对普通 AV 会写 except.txt 且不落 WER（RC_SPEC_V4.md:147，双样本实证）。调试器附加后 AV 以 debug event 形式**先于 SEH** 送达调试器（first-chance 直达面被劫持），除非调试器显式向被调试者转交，否则 except.txt 根本不会产生 ⇒ 裸奔臂验收自动失败。非调试 WPM 完全不动异常分发链。
2. **端口独占**：每进程仅一个调试端口；P05/A4 的附加面已归属 qc134（`qc134_attach.json` `DebugActiveProcess_ok=True`，SPEC_TRIAGE:25）。发生器若也附加即与 P05 互斥——非调试 WPM 与附加态 P05 可共存（§E1-4）。
3. **纪律面先例**：P1 仪器（qc135_objloc.py）自身 AST 级禁用 DebugActiveProcess 等 19 名 API（QC205_VERIFY:267）；发生器作为同级外部工具遵循同一禁用面，且不触碰 qc135 已放行锚（`1355dead…e77e`，QC205_VERIFY:73）。
4. **探针件反证**：E1-11 两枚探针 except（INT3/非法指令，RC_SPEC_V4.md:153）证明**带内异常注入会留下仪器自身签名**、污染崩溃样本口径；带外 WPM 使异常面保持原版纯净。

### A1.2 `__sbh_heap_info` 发现：签名扫算法（伪码）

布局依据 [事实]：`head = heap_info + group*0x204 + 0x144`、`head(class)=head数组基+class*8`（RC_SPEC_V4.md:103，指令自证 `imul 0x204`/`lea +0x144`）；节点布局 `[node]=size,[node+4]=next,[node+8]=prev`（:92）；空表自环 `head->next==head`（:104，建堆对 64 槽自链实证；recommit 重建全部 64 head，:125）；头槽 8B 对齐（head(7,4) mod 16=8，:103）。**禁止硬编码 0x1498FB8C/0x1498EC08**（骨架 §3 自律，该值=崩溃语料偶发基址）。

```text
DISCOVER(pid) -> (H, evidence) | DISCOVERY_FAILED
  regions := [R for R in VirtualQueryEx(pid) 若
              R.State==MEM_COMMIT and R.Type==MEM_PRIVATE
              and R.Protect==PAGE_READWRITE]                    # SBH 堆=私有可读写
  cands := []
  for R in regions:
    for off in range(0, R.RegionSize - SCAN_SPAN, 4):           # 4B 对齐步进
      C := R.BaseAddress + off
      ok_groups := 0; saw_selfloop := False; saw_nonempty := False
      for g in 0 .. GROUPS_MAX-1:            # GROUPS_MAX=32 [推断]（I-4：上界无实证）
        HA := C + g*0x204 + 0x144                                 # :103
        ok_classes := 0
        for c in 0 .. 63:                                         # 64 类（:91、:104）
          h   := HA + c*8
          nxt := rd32(h+4); prv := rd32(h+8)
          if nxt==h and prv==h:                                   # 空表自环（:104）
            ok_classes+=1; saw_selfloop=True; continue
          if not in_region(nxt,R) or not in_region(prv,R): break  # 越域即否决本组
          if rd32(nxt+8) != h: break                              # 首节点->prev==head 配对
          n:=nxt; steps:=0
          while n != h and steps < 256:                           # WALK_MAX=256
            nn:=rd32(n+4); np:=rd32(n+8)
            if nn!=h and not in_region(nn,R): goto g_fail
            if rd32(np+4) != n: goto g_fail                       # next->prev==n（:99 配对写维持）
            n:=nn; steps+=1
          if steps>=256: goto g_fail                              # 链中毒/超长=否决本组
          ok_classes+=1; saw_nonempty=True
        if ok_classes>=2:                                         # 骨架验收口径 ≥2 类链一致
          ok_groups+=1
        g_fail:
      if ok_groups>=2 and saw_selfloop and saw_nonempty:
        cands.append((C, ok_groups))
  if len(cands)==1: return cands[0]
  if len(cands)>1:  # 歧义：交叉验证 region 描述符计数/数组（[0xB78B94]/[0xB78B98]，:109）
                    #   仍歧义 => DISCOVERY_FAILED（绝不盲写，见 §H1-R8）
  return DISCOVERY_FAILED
```

工程注记：(a) 任一 class 链被自然毒化时该候选组 walk 断链被否决——若全部候选因此失败，返回 DISCOVERY_FAILED 并记 `chain_walk_broken`（**其本身即 P1 相关信号**：说明堆内已有自然腐化，升级上报）；(b) SCAN_SPAN 建议 0x100000（region 描述符步长口径 :109）为扫描窗上限，纯速率参数不判语义；(c) 发现阶段全程只读，零写入。

### A1.3 选槽（写哪个 head；v1 修订=R4）

触发时在已确认 H 上枚举 `g × class 4`（class 4=80B/req 57–72，:91；业务压力面=49 处分配点+`AddCapacity 0x510860` 首要 free 站，:122-123）：**只允许取「当前非空」class-4 freelist 的 head(g,4)**（非空=消费快+与原现场「位图置位而链损」同族，OFFLINE_BATCH_VERDICT:68）。**空表 fallback 删除（R4）**：原「全空则任取一空 head(g,4)，写入后该表位图置位+链非空形态仍成立」的断言**不成立**——SBH 类位图与链表的一致性**仅由 alloc/free 两侧配对维护点维持**（置位指令 0x7CFD84/0x7CFD92/0x7CF9C4/0x7CF9D3 等，OFFLINE_BATCH_VERDICT.md:60-63「读点 0x7CFC9B 处无任何强制」），对 head->next 的一次裸写**不会置位**；而 `0x7CFC9B` 的执行以位图扫描命中为唯一前驱（OFFLINE_BATCH :57 第 1 条；RC_SPEC_V4.md:74「EDI=4 ⇒ 位图命中 class 4」）⇒ 向空链注入的毒值大概率**永不被读**（假阴、白烧重试预算）。**全空处置=NOT_ATTEMPTED（原因码 `no-nonempty-c4`）换局，不写任何字节**。守卫拦截面论证（毒值 ≠ head 自环值，`test edx,0x0F` 得 0xF≠0 ⇒ trip，RC_SPEC_V4.md:525）**仅对非空链成立**，随非空选槽保留。不固定 g=7（运行时发现制）。

### A1.4 写前快照 / 写后校验环

```text
INJECT(H, g, c=4):
  W0 pre-flight:  sha256(磁盘 gamemd.exe) == 73201cc0…（:419，不符→NOT_ATTEMPTED）
  S0 pre:  win_old  := RPM(head(g,4), 64B)                  # 64B 窗（骨架验收 1 口径）
           chain    := walk_chain(h, poison_terminator=off)  # 节点地址+首 dword 有序表
           ledger_pre(pid,H,g,c,head_addr,old_dword=rd32(head+4),ts_qpc)  # 先写后写（勘-3）
  W  write: WriteProcessMemory(pid, head_addr+4, 0xFE00FFFF, 4)   # 4B 对齐单写
  S1 post: win_new := RPM(head_addr, 64B)
           diff(win_old, win_new) 必须恰 = {偏移 +4: old_dword → 0xFE00FFFF}
           多一字节变化 ⇒ RESTORE + FAIL(diff-not-minimal)
  S2 chain: walk_chain(h, poison_terminator=on)
           首跳即毒值 ⇒ 记 POISON_VISIBLE_AT_HEAD（不 deref，只读停）
           形态不符 ⇒ RESTORE + FAIL(chain-shape)
  S3 restore（仅失败路径）: cur := rd32(head_addr+4)             # 回写前复读（v1=R5）
           若 cur == 0xFE00FFFF：WriteProcessMemory(old_dword,4) → RPM 复核 diff 清零
           否则（游戏在 S0–S3 间已合法改写该槽，如 0x7CFD30 unlink 配对写，:99）：
                **不回写**——陈旧 old_dword 会压掉游戏新写入的节点指针（=非毒值形态链损）
                ⇒ 记 stale-restore-aborted，按 foreign 路径隔离处置（§H1-R9）
           ⇒ 三值 FAIL(restored)，注入计数仍入台账（供互扰关联，§E1）
```

原子性：4B 对齐写相对目标线程读取不撕裂 [推断：x86 对齐 ≤4B 访问原子性的体系结构通识，无项目内直接证据]；写入瞬间恰逢游戏读该槽的最坏交错=游戏读到新旧二值之一，二者分别为「正常值/毒值」——后者正是注入意图本身，无半写态。**（v1 补 · R5）**：上段只覆盖「游戏读我方写」的单向交错；**反向交错（我方 S3 回写压过游戏写）**由 S3 前置复读条款排除——仅当槽现值仍==毒值才回写旧值，否则视为游戏已合法接管该槽、放弃还原；对应风险条目=§H1-R9。

### A1.5 失败回写与重试预算

- 任一校验失败 ⇒ S3 回写，**前置复读条款（v1=R5）**：仅当现值==0xFE00FFFF 才回写 ledger_pre 落盘的旧值（不依赖易失内存）⇒ 复核 ⇒ 三值化收口；现值已变（游戏合法改写该槽）⇒ **不回写**，记 `stale-restore-aborted` 按 foreign 隔离（§H1-R9）。
- 重试预算 **≤3 次**（骨架验收 5 口径）：仅允许两种重试原因——毒值 60 游戏秒未消费（换新分配 freelist head 再注）与写后链校验失败（同 head 复验后放弃换选）。原因码入台账。
- 全部失败 ⇒ NOT_ATTEMPTED/FAIL 三值上报，主会话裁决是否续批（§G1-G7）。

## §B1 毒值模式扩展（≥2 种可区分模式 + 取舍）

**模式 S（主案；v1 更名注记=R7：原称「哨兵模式」沿骨架误称——0xFE00FFFF 实非 SBH 哨兵而是腐化产物值，见勘-5）**：`DWORD 0xFE00FFFF` 固定值（骨架 §3 原案）。性质：判别式 `&3==3` ⇒ 非对齐、必为业务数据（:114）；映像 imm32 0 命中（:113、:85 `recompute_poison.txt`）⇒ 无代码常量混淆面；裸奔崩溃签名与原现场**逐字段同构**（Edx=FE00FFFF/Access address=FE00FFFF/Edi=4，:60-62、:74）⇒ J 判据直接复用（E1-8，:137）。

**模式 P（调用站/会话编码模式，备选）**：`DWORD 0xFE00_0000 | (session_id << 2) | 0b11`，`session_id ∈ [1, 0x3FFF]`（高 16 位保持 0xFE00，低 2 位钉死 11 保持判别式 :114）。崩溃现场自证归因：`Edx & 3 == 3` 且 `(Edx >> 2) & 0x3FFF == session_id` ——**产物级**区分「我注入的」与「自然的 0xFE00FFFF」，无需事后台账关联即可在 except.txt/寄存器转储里读出注入者身份；并支持未来多点注入实验（每点独立 session_id）。前置门禁：任一具体模式 P 值使用前必须离线 imm32 普查 gamemd/ra2render 映像 0 命中（方法先例 `recompute_poison.txt`，:85/:113）——0xFE00FFFF 的 0 命中结论**不外推**到族内其它值。

| 维度 | 模式 S | 模式 P |
|---|---|---|
| 与原崩溃签名可比性 | 逐字段全等（J1–J6 直用，:137） | EIP/字节/Edi 相等，Edx/Access address 为族值 ⇒ 判据需双档（§D1 D-1 附则） |
| 归因能力 | 仅靠台账地址关联（事后） | 产物级自证（现场即读） |
| 误认自然事件风险 | 值相同，只能靠地址+时序关联排除（§E1） | 值域天然排除自然命中（前提=族值普查 0 命中） |
| 证据先例 | 强（:60-62、:74、:113-114 全套） | 弱（无先例，新增判据面） |
| 用途 | 首批 A/B（签名保真优先） | 写点断点轮/P1 逐站试验（归因优先） |

**裁定**：首批 A/B 全部用模式 S；模式 P 仅登记预留，启用须经主会话批（新增判据面+普查门禁两成本）。

## §C1 A/B 协议（毒值开/关 · 两态交叉四批）

**臂定义**（任务口径 A=毒值开/B=毒值关；与 E1-8 的 A/B/C 三臂不同名同构，:137——E1-8 臂 C `EnableLFH=0` 本设计不启用，LFH 面归 #5 不混线，SPEC_TRIAGE:33）：

| 批 | 守卫态 | 臂 | 趟数 | 宿主动作 | 预期结局 |
|---|---|---|---|---|---|
| 1 | ON（`EnableSbhGuard=1`，默认 0 需显式开，:588） | A1 | 5 | 完整注入（模式 S） | 守卫拦截降级、游戏存活（D1-D2） |
| 2 | ON | B1 | 5 | **安慰剂**：完成发现/快照/链验证，**跳过 WPM** | 全阴（D1-D5） |
| 3 | OFF（裸奔，缺省态） | A2 | 5 | 完整注入（模式 S） | `0x7CFC9F` 崩溃、except.txt 中靶（D1-D1） |
| 4 | OFF | B2 | 5 | 安慰剂（同 B1） | 全阴（D1-D5） |

- **★批 1/2 前置门=守卫在场证据面（v1 新增=R1）**：「守卫在场」本身是**未交付件**——RC-1 守卫补丁（cave/安装器/`EnableSbhGuard` 开关）全链无实现证据（I-8：OFFLINE_BATCH_VERDICT.md:212 find 0 命中；设计自认 I-3「M 轨未建」）。前置门三证据：① RC-1 安装器/产物存在且过 G-0a 同款镜像指纹复验；② 安装自检产出 install 族 tag 证据（`SbhGuard=install(ok)` 形态，RC_SPEC_V4.md:389/:589）；③ `EnableSbhGuard=1` 生效证明（安装器自检或守卫自检日志；开关默认 0 需显式开，:588）。**三者缺一 ⇒ 批 1/2 = NOT_RUNNABLE（§G1 G-0e 门），不存在降级判定态（DEGRADED-GATE 已弃用，D-2/R6）**。

- **B 臂=安慰剂而非纯不注入**：B1/B2 走完 DISCOVER+S0+ledger_pre(仅发现面) 全流程但不 WPM——把宿主自身的 RPM/遍历扰动也纳入对照（骨架验收 4「空跑零命中」的可执行化）。
- **趟长与计时基准（v1 重写=R2）**：导航进目标图战术面（**主用图=spawnfix8 `0add791d`**，沿 T50 已验证导航链，卡 §T53；U0400 原图降为可选短局快筛臂、沿 T32 链，见 §F1）→ 稳定窗（对齐 W0 活跃段 15.42s 量级口径）→ 注入窗（勘-1 双条件）→ 观察窗 ≤60 **墙钟秒**（原「≤60 游戏秒」口径废止——U0400 原图 ~24 游戏秒确定性终局且游戏秒随计分板冻结，勘-6；换算依据=活跃段 fps p50≈31 ⇒ 墙钟秒≈游戏秒，只封顶不放大）；A2 预期秒级内消费（class 4 压力面 49 分配点，:122）；「未消费再注」预算同步改墙钟口径（骨架验收 5、§A1.5）。**观察窗终态定义（两图通用，R2）**：帧钟持续推进至窗末=正常收口；**计分板检出（或帧钟冻结+窗满）=观察窗合法终态**——D-2 的「存活至收口」=「检出计分板前无 fresh except 且非本注入所致崩溃」；A2 的崩溃判读只认 except.txt fresh 新增+r1–r8，与计分板态互斥不冲突。全程受 `SINGLE_TRIP_BUDGET_S` 框约束（qc135 :241 族，qc135 锚零改动）。
- **样本量依据（一句话）**：单趟事件概率按保守 p≥0.5 计（毒值植入后由 class-4 高压面消费，:122-123），N=5 给出单侧二项检出力 1−(1−0.5)^5=96.9%≥95%；B 臂「零事件」按 rule-of-three 3/N=0.6 仅作粗筛——判读以 **§D1 确定性签名匹配为主、不依赖率差**，与 E1-8「判据 J1–J6」的率型口径并存但本设计签名面优先。
- **次序（v1 修订=R1）**：理想序=批 1/2（守卫 ON）先行——游戏存活、证据便宜；批 3（裸奔 A2）其后——每趟终结该局（骨架 §7-3 已登记待批，**真机批 3 发射前须主会话显式授权**，§G1-G3 门禁位）；批 4 收尾。**守卫件未交付时的降序执行（R1 许可路径）**：批 3/4（裸奔+安慰剂）单态先行开跑，批 1/2 待 M 轨交付后补跑（各趟均为独立局，批序不破判读面）；此序下须在汇总报告**显式声明单臂局限**——A2 的「5/5 PASS_BARE」判读价值依赖 A1 臂对照存在（评审批点 1 口径）。
- **停止规则**：任一趟崩溃 EIP 落 `0x54D3xxxx`/`0x01B00000` ⇒ 全批停（E1-8 红线，:137、:143 分区口径）；注入尝试 ×3 失败 ⇒ 该局 NOT_ATTEMPTED；守卫批单局 trip 计数风暴（阈值 10，[推断] 无实证）⇒ 人工停局（§H1-R2）。

## §D1 检出判据可执行化（每条给可脚本化匹配规则）

行式依据 [事实]：`ra2youli/except.txt` 实件行式 `Error code: …`/`Access address:00000250 was read from.`/`Exception occurred at 00724737`/制表寄存器块 `Edx:00000000	…`/`Bytes at CS:EIP (…)  : 8B 0A …`；RC-1 原现场毒值字段（RC_SPEC_V4.md:60-62、:74）。

**D-1 裸奔臂阳性判据（A2 批；勘-4「结构同构」口径）**——解析 except.txt，8 规则全中=PASS：
```python
r1: any(line == "Error code: EXCEPTION_ACCESS_VIOLATION")
r2: any(line == "Access address:FE00FFFF was read from.")          # 精确行等值
r3: any(line == "Exception occurred at 007CFC9F")                   # ★崩溃点（:95、:62）
r4: regs["Edx"] == "FE00FFFF"                                       # :61
r5: regs["Edi"] == "00000004"                                       # class 4 位图命中（:74）
r6: (int(regs["Ecx"],16) - int(regs["Eax"],16) - 0x144) % 0x204 == 0   # 组算式（:103）
r7: eip_bytes.split(" ")[:2] == ["8B","0A"] 且
    32 token == gamemd.exe 文件偏移 0x3CFC9F 起 32B                  # VA−IB=0x3CFC9F；
                                                                    # 先例 identical=True（:74、:83）
r8: 台账闭环：r6 解出的 Eax == ledger.heap_info 且 group == ledger.g
    且 ledger.class == 4                                            # 注入→现场全链闭合
r9（软检查，不判门）: Eip 落 0x00400000–0x008A0000 gamemd 主区（:143）且
    栈顶近旁含 Ecx 值（原现场 00F9D15C 样式，:64）
```
模式 P 附则（若启用，§B1）：r2/r4 改 `(Edx>>16)==0xFE00 且 (Edx&3)==3 且 ((Edx>>2)&0x3FFF)==session_id`，其余不变。

**D-2 守卫臂阳性判据（A1 批；v1 修订=R6：DEGRADED-GATE 显式弃用）**——主判据=遥测计数器：`s_sbhGuardTrips` 相对趟前基线 **Δ≥1**（trip 路径 `lock inc`，RC_SPEC_V4.md:511、:546、:592；读接口须只读，:399）。辅助判据：except.txt **无** fresh 新增（except_gate 严格态语义：fresh 才 FAIL，:141）+ 该局存活至观察窗收口（收口定义见 §C1 趟长条，R2）。`"SbhGuard=poison-hit"` 字符串**不作门禁**（I-2：日志行格式未定稿）。**DEGRADED-GATE 弃用裁定（R6）**：原降级判据仍要求「守卫日志件出现任一 trip 计数非零快照」，而 I-3 已承认计数器**如何被外部读到无证据**（:399 独立遥测接口未落地、槽址须构建后反汇编钉死，:592）——「降级」名不副实（把读不到换成还是读）。**故 D-2 只认主判据；遥测读取通道或守卫本体任一未交付 ⇒ 批 1/2 = NOT_RUNNABLE（§C1 前置门、§G1 G-0e），协议以批 3/4 单态先行（§C1 次序）**；若 M 轨未来交付真实遥测产物（如 flush 件），降级变体须挂该产物另提案重议，不在本版预设。

**D-3 P1 捕获判据（v1 重写=R3：观测腿重定义，两臂通用）**——**必在腿=发生器内建只读观测器 `pg_poison_poll`**：发生器/趟脚本在注入后以 RPM 只读轮询台账注入地址集（head(g,4)+4 及链首 N 节点，N≤8），等价复刻 qc135 `l3_poison_poll` 的 `BAD_VALUE=0xFE00FFFF` 比对判据（qc135_objloc.py:190、:3704）并记**同构 event**（`slot`(十六进制槽地址)/`k`(组号)/`c`(槽序)/`ts`）+ verdict `pg_poison_poll:BAD_VALUE_seen`（对齐 qc135 :4191 f-string 口径）——判读规则与 qc135 逐字同构：
- 解出槽地址 ∈ 台账注入地址集 ⇒ 记 `POSITIVE-CONTROL(injector=self)`（毒值可见=观测器活体正控）；
- ∉ 台账 ⇒ 记 `NATURAL-EVENT`（即自然毒值——I-7 基线事件，**升级上报主会话**，进 #1 证据面）。

**跨实例腿降为旁证（R3）**：qc135 本体的 P1 腿直启**自实例**并以 `--max-stage L3` 菜单相 15s 窗轮询（qc135_objloc.py:68-70、:7、:245）——跨实例+跨相位，原则上看不见本趟另一实例战术面的注入（卡 §T28 :516 实证该相 class4 dword9 零命中），故**不判门**；同机并行 A5 趟的 readings 若恰现命中，作旁证升级件记录。**不装 `pg_poison_poll` 的发生器构建不得发射**（§G1 G-0d 自检项）。

**D-4 P2/P05 判据（P05 链；v1 修订=R3：在场性与候选 k 产出方钉死）**——**在场性**：P05（qc134 附加态）仅守卫批在场（E1-4 时序）；裸奔批 P05 不在场 ⇒ 本判据记 `leg-absent`（不判门、不算缺口）。**候选 k 集产出方（R3 钉死）=发生器**：DISCOVER 确认的堆基址组号集（台账 g 集）于注入前落盘为 P05 输入 JSON（QC209_VERIFY:70 外部 JSON 通道的供给方由此唯一化；A5 菜单相 12 组候选**不适用**战斗相，不作来源）。判读：P05 报告 `c4_active_set`（`_cells={_j//2}`、`P05_CLASS4_CELL`，QC209_VERIFY:118-119）：
- 含 `ledger.g`（窗 dword9=entry+0x24 变化→cell 4，QC209_VERIFY:83、:119）⇒ `POSITIVE-CONTROL(injector=self)`（兼作 P05 真机活体正控，QC209 离线直证的活体版）；
- 含其它组 ⇒ 自然 churn=P2 科学产出，照常入 #1 缩域面（SPEC_TRIAGE:76）。

**D-5 阴性判据（B1/B2 批；v1 修订=R3 按在场腿限定）**——全中=NEGATIVE-CLEAN：(a) 无 fresh except.txt（except_gate 严格态 exit 语义，:141）；(b) `pg_poison_poll`（必在腿，D-3）零 `BAD_VALUE_seen`；(c) P05 腿（仅守卫批 B1 在场）：零未知毒值窗、`c4_active_set` 无 ledger 外组；裸奔批 B2 记 `leg-absent` 跳过；(d) （仅 B1，且以遥测可读为前提——R6 门）`s_sbhGuardTrips` Δ=0。任一自然毒值命中 ⇒ 不是 FAIL，是 `NATURAL-EVENT` 升级件。

**D-6 匹配器骨架**（离线纯解析，零真机）：
```python
def judge(except_path, readings_dir, ledger, telemetry=None, p05_present=False):
    if except_fresh(except_path):            # mtime/sha256 四要素先例 :141
        x = parse_except(except_path)        # 按上述行式取 token
        return "PASS_BARE" if all([r1..r7, r8(x, ledger)]) else "FAIL_FOREIGN_CRASH"
    if telemetry and telemetry.trips_delta() >= 1:      # D-2 主判据唯一（R6：无降级分支；
        return "PASS_GUARD" if survived_window() else "FAIL_GUARD_THEN_CRASH"  # 守卫批 telemetry 缺席=NOT_RUNNABLE，G-0e）
    p1 = scan_readings(readings_dir, "pg_poison_poll:BAD_VALUE_seen")  # D-3 必在腿（R3）
    p2 = p05_c4_active(readings_dir) if p05_present else None          # D-4 仅守卫批在场（R3）
    classify(p1, p2, ledger)   # POSITIVE-CONTROL(self) / NATURAL-EVENT / NEGATIVE-CLEAN
```

## §E1 与 P1/P2 衔接（互扰分析：注入 4B 本身是否触发捕获？如何标记「注入者=自己」）

**结论先行**：注入 4B **会**被 P1（被动轮询）与 P2（双快照差分）以**值级/差分级**看见——这不是要消除的污染，而是要**标记后利用**的活体正控；处置统一靠「注入台账先写后写 + 地址集关联」。

| # | 仪器 | 注入是否触发 | 机理（证据） | 处置 |
|---|---|---|---|---|
| E1-1 | P1 跨实例腿 qc135 `l3_poison_poll`（被动 RPM 轮询，QC205 形态；v1 重定界=R3） | **原则上不会**：qc135 直启自实例、默认 `--max-stage L3` 菜单相 15s 窗（qc135_objloc.py:68-70、:7、:245），与 #4 注入实例（另一进程的战术面）无进程关系；跨实例+跨相位 ⇒ 不可依赖（卡 §T28 :516 该相 class4 dword9 零命中实证） | 轮询判据本身=逐 hop 比对 `BAD_VALUE=0xFE00FFFF`（qc135_objloc.py:190、:3704），命中记 event（:3721、:4191）——#4 趟内由 **`pg_poison_poll` 必在观测器**等价复刻该判据（D-3），机制不变、宿主换为发生器自身 | 台账地址集关联：解出槽地址 ∈ 注入地址集 ⇒ `POSITIVE-CONTROL(injector=self)`，**不进自然事件计数**（D-3）；反之= `NATURAL-EVENT` 升级。qc135 本体若同机在场且恰现命中 ⇒ 旁证升级件，不判门 |
| E1-2 | P2/P05 双快照差分（qc134，6378b538） | **会**（T0/T1 夹住注入时） | 窗 dword9（=entry+0x24）变化→`_cells={_j//2}`→cell 4→`c4_active_set` 纳入（QC209_VERIFY:83、:118-119）——注入恰落在 P05 的 class-4 监视坐标正中 | 同一关联规则（D-4）；且**升格为活体正控**：QC209 的 128/128 in_domain 直证是合成离线版（:84），注入后 P05 首次在真机看见「已知来源的已知坐标变化」=P05 端到端活体验证件（v1 注=R3：候选 k 集供给方=发生器 DISCOVER 组号集，D-4；P05 仅守卫批在场，裸奔批 leg-absent） |
| E1-3 | P1 写点断点形态（`0x7CFD30` HW brk / 守卫页，未实施） | HW brk：**不会**；守卫页：**会** | WPM 由内核态写入目标地址，不执行游戏 unlink 指令流、不在游戏线程上下文 ⇒ 不命中 DR 断点 [推断：体系结构通识]；守卫页形态则页上任意下次访问皆触发 | 该形态未实施（骨架 §7-1、勘-2）；启用前必须重评本节——若届时启用，发生器注入台账须同时登记「写点仪器是否在场」，防自触自指 |
| E1-4 | 调试端口 | **不冲突** | 发生器非调试（§A1.1）；P05 附加（qc134）独立持端口，二者可共存 | 时序规则（守卫批 A1）：`qc134 附着 → P05 T0 快照 → 注入 → T1 快照`——注入被夹进差分窗内，正控语义成立；裸奔批无 qc134，无此问题 |
| E1-5 | 台账（两仪器的共同排除键） | —— | —— | **先写后写**（勘-3）：`ledger_pre`（pid/heap_info/g/class/head_addr/old_dword/ts_qpc）在 WPM 前 fsync 落盘，`write_ok/ts` 事后补写；关联键=**地址 + 值双键**（E1-1 靠地址，E1-2 靠坐标），时序作第三佐证 |
| E1-6 | 崩溃时刻收尾 | 部分未知 | **[INSUFFICIENT→I-5]**：QC205_VERIFY 未覆盖「目标进程死亡瞬间 qc135 readings 落盘完整性」（其清单全为离线静态/内存核验，:292-297 自报）；QC209 同（:150-151） | 缓解：except.txt 与 readings 均为文件面产物，进程死亡不清失；裸奔批首趟增加核对项「崩溃前最后 N 条 readings 是否完整落盘」（§G1-G6） |
| E1-7 | 守卫（若 ON） | **会——这正是验收 2 本体** | 毒值 `0xFE00FFFF ≥ USER_ADDR_CEIL 0xBFFF0000` ⇒ `jae trip`（RC_SPEC_V4.md:525 拦截面明示毒值 ✔）；≠head ⇒ 哨兵短路不误放（OFFLINE_BATCH_VERDICT:67-68） | 非互扰，是 A1 批预期信号（D-2） |

**红线重申**：注入事件的写者=发生器本人，**公理级**不可作为 #1「谁写了 0x1498FB8C」的写者指认证据；#4 的产出=捕获链端到端验证 + 复现率知识（骨架 §1、SPEC_TRIAGE:32「P1 的弹药库」）。台账关联失败（有 BAD_VALUE_seen 但既不在台账也判不出自然性）⇒ 证据件标 `AMBIGUOUS` 隔离，不入任何计数。

## §F1 安全边界与回退

- **语料落实（v1 重写=R2：主用图换已验证长战局语料）**：主用图=**spawnfix8 `0add791d`**（归档件 `_maps_fixed\XMP29U2.MAP.spawnfix8_0add791d`；卡 §T53 :746-753 全链实证：units0=971、三窗全活跃（帧 886→1667→2449 推进）、harness 主动终断非游戏终局、导航链与载体链同 T50 已验证趟）——观察窗 ≤60 墙钟秒与重注预算由此可达。**路线分歧显式声明（R2）**：GOAL :36 记录的 #4 判别升级前提原是「高负载臂+长战局」（卡 §T33 :564 同判），本设计换用 spawnfix8 即**回归该前提**；骨架 §1「低负载语料」措辞废止，重述为「**语料选择准则=已验证导航链+战局寿命满足观察窗，负载档不设限**」——事件由发生器制造、不靠负载逼自然毒值（#4 存在理由不变，SPEC_TRIAGE:32、:78）；自然毒值基线（I-7）由 B 臂同时长对照承担。**可选短局快筛臂（非缺省）**=U0400 原图 93c2974b（T32 链真进图实证 units0=241，GOAL :42、:65）：其 ~24 游戏秒确定性终局（勘-6）下计时基准必须用墙钟、计分板态=观察窗合法终态（§C1 趟长条）。**禁入官方 MP29U2**（T24/T25/T27 误进教训，GOAL :42）。局定义=1 趟=1 进图=1 份注入预算（≤3 attempts）+ 观察窗；四批合计 20 趟（§C1）。
- **镜像 sha 前置校验（G0.1 同款）**：每批首趟前 `Get-FileHash`/sha256 目标 gamemd.exe 必须== `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` 且 size==4,825,360 B（RC_SPEC_V4.md:7、:419）；不符 ⇒ 全批 NOT_ATTEMPTED，**不写任何字节**（与 `SbhGuard=identity-unknown` 同款拒绝语义，:420；诊断授权≠补丁授权口径对发生器同样适用）。
- **单字节回写回退**：唯一写入面=1 个 4B 对齐 dword（§A1.4 W 步）；旧值随 ledger_pre 落盘，任何校验失败 ⇒ S3 单 dword WPM 还原 + RPM 复核 diff 清零（§A1.5）——最坏残留=0 字节。
- **失败三值化**：`PASS`（该臂 D-1/D-2 判据全中）／`FAIL`（注入已发生但判据未中，或还原成功收口；附原因码 `diff-not-minimal`/`chain-shape`/`foreign-crash`/`degrade-storm`）／`NOT_ATTEMPTED`（前置校验失败、DISCOVERY_FAILED、链验证 ×3 失败——**未写任何字节**）。三值与原因码全部入台账与 evidence 报告，禁止二值压缩。
- **AV/HIPS 与环境前置（I-6/I-9；v1 扩=R1 外部依赖注记）**：运行窗口须确认火绒内存防护已按用户侧安排处理（GOAL :97 既有线）；被拦 ⇒ NOT_ATTEMPTED（进程外可检测：WPM 返回 FALSE+GetLastError 记录）。**全部真机批的共同前置=boot hang 环境解锁**（卡 §T55 :726 定谳、:733 复跑条件=1 次独立 boot 探针通过）；环境未解锁期间仅离线项（G-0a–G-0d、D-6 匹配器、§A1.2 伪码评审）可推进。
- **磁盘税**：EVID move-out 1.8GB/趟既有行为（GOAL :87）×20 趟 ⇒ 批前磁盘余量门禁（≥60GB）+ 批后跑既有 dedup 纪律（GOAL :87 §128 两遍法）。
- **发生器写域**：crashspec 写域（本设计件+evidence 证据件）；不动锚定脚本（骨架 §6 维持）、不写 qc134/qc135 现件（两锚 `1355dead…`/`6378b538…` 前后必须零改动，批前批后各测一次哈希入证据件）。

## §G1 验收清单（主会话可直接执行的逐项检查）

> 每项含门禁命令形态与读数判据；全部命令为离线可执行或标注「真机批内」；零真机项先行。

| # | 检查项 | 门禁命令/动作 | 读数判据 | 状态位 |
|---|---|---|---|---|
| G-0a | 镜像指纹 | `Get-FileHash gamemd.exe -Algorithm SHA256` | `73201cc0…fcf67476` 且 4,825,360 B（:419） | 不符=NOT_ATTEMPTED |
| G-0b | 发生器禁用面 AST 审计 | 对 `qc_poison_gen.py` 跑 QC205 同款 19 名扫描（QC205_VERIFY:267 口径） | 禁用 API 调用=0；白名单仅 OpenProcess(VM_*)+RPM/WPM/VirtualQueryEx | 任一命中=拒绝放行 |
| G-0c | 仪器锚零改动基线 | 批前 sha256 qc135_objloc.py / qc134_attach.py | `1355dead…e77e` / `6378b538…5810`（QC205_VERIFY:73、QC209_VERIFY:8） | 漂移=停 |
| G-0d | 台账 schema 自检（v1 扩=R3） | `qc_poison_gen.py --selftest`（桩 pid=0xFFFFFFF0 必失败路径，QC209_VERIFY:151 同款手法） | exit 三值可辨、ledger_pre 文件生成且字段齐、`pg_poison_poll` 观测器自检（只读轮询+同构 event 落盘路径）在位 | 缺字段或缺观测器=停 |
| G-0e | **守卫在场门（v1 新增=R1）** | 核验 RC-1 安装器/产物存在 + G-0a 同款指纹复验 + install 族 tag 证据面（`SbhGuard=install(ok)` 形态，RC_SPEC_V4.md:389/:589）+ `EnableSbhGuard=1` 生效自检（:588） | 三证据齐 ⇒ 批 1/2 可排程 | 缺一 ⇒ 批 1/2 = NOT_RUNNABLE（I-8；批 3/4 不受此门） |
| G-0f | **真机环境门（v1 新增=I-9）** | boot hang 解锁探针 1 次通过（卡 §T55 :733 复跑条件）+ 火绒内存防护确认（GOAL :97） | 两项 ok ⇒ 真机批可排程 | 缺 ⇒ 全部「真机批内」项停，离线项照常 |
| G-1 | 批1 A1×5 判读（真机；前置=G-0e/G-0f，v1 修订=R1/R6） | 每趟跑 D-2 匹配器（仅主判据；DEGRADED 变体已弃用，无降级判读面） | `PASS_GUARD` 5/5 ⇒ 骨架验收 2 达成 | 前置不齐=NOT_RUNNABLE（非 FAIL）；<5 ⇒ FAIL 收口上报 |
| G-2 | 批2 B1×5 判读（真机；前置=G-0e/G-0f，v1 修订=R1） | 每趟跑 D-5 匹配器 | `NEGATIVE-CLEAN` 5/5 ⇒ 骨架验收 4 达成 | 前置不齐=NOT_RUNNABLE；任一 NATURAL-EVENT=升级件 |
| G-3 | 批3 A2×5 判读（真机；**须主会话显式授权发射**，骨架 §7-3；若批 1 未跑须声明单臂局限，§C1 次序 v1 注=R1） | 每趟跑 D-1 匹配器（r1–r8） | `PASS_BARE` 5/5 ⇒ 骨架验收 3（勘-4 口径）达成；EIP 出界即全批停（:137） | <5 ⇒ 隔离 AMBIGUOUS/FOREIGN |
| G-4 | 批4 B2×5 判读（真机） | D-5 | `NEGATIVE-CLEAN` 5/5 | 同 G-2 |
| G-5 | 注入完整性（每趟） | 差分器输出入 evidence | 64B 窗 diff 恰=目标 4B（骨架验收 1）；`diff-not-minimal` 计数=0 或已还原 | 任一未还原=FAIL |
| G-6 | 台账-判据闭环率（v1 修订=R3） | D-3/D-4 关联器 | **A 臂趟（A1/A2）按在场腿计关联率 100%**（必在腿=`pg_poison_poll`；守卫批加 P05；qc135 跨实例腿不参与计算）；B 臂趟改判 D-5 全阴（无注入无从关联）；AMBIGUOUS=0；裸奔首趟加验 readings 崩前落盘完整性（E1-6） | AMBIGUOUS>0 ⇒ 停批复勘 |
| G-7 | 三值台账完备 | 汇总台账 | 20 趟每趟有唯一终态+原因码；NOT_ATTEMPTED/FAIL 附因 | 缺失=账面 FAIL |
| G-8 | 批后锚复测 | 批后 sha256 两仪器件 | 与 G-0c 逐字节同 | 漂移=立即上报 |
| G-9 | 账面包 | 依本表产出汇总 + SPEC #4 行（:698）更新提案 | 「A/B 协议已备未执行」可否改写，由主会话裁 | 提案级 |

## §H1 风险登记（≥5 条）

| # | 风险 | 机理/证据 | 缓解 | 最坏后果预案 |
|---|---|---|---|---|
| R1 | **毒值自身诱发假阳性**：把注入事件当自然毒值事件归因，污染 P1/P2 产出乃至 #1 证据面 | 注入值与 BAD_VALUE 逐字相同（qc135 :190 vs 骨架 §3），值级不可分 | **对照排除法四层**：① 地址集关联（台账先写后写，E1-5，地址+值双键）；② 模式 S 下地址唯一指向台账 head_addr，自然毒值落点必异（原现场毒址算式唯一解 (g,c)=(7,4)，:102——若发现「自然」毒值恰落台账地址则只能是我方残留，AMBIGUOUS 隔离）；③ B 臂同时长安慰剂零命中（骨架验收 4，§C1-B1/B2）；④ **公理级**：注入事件写者=发生器本人，永久排除于 #1 写者指认证据面（§E1 红线） | 关联器失灵（AMBIGUOUS>0）⇒ 停批复勘（G-6）；必要时改模式 P 值族产物级自证（§B1，须主会话批） |
| R2 | **写错堆/写错地址**：签名扫误判基址或选错 head，腐化无关内存 | 现场基址为语料偶发值（骨架 §3 自律禁硬编码）；扫描歧义无先验 | 链一致性 ≥2 类 × ≥2 组 + 空表自环与非空链双形态验证（§A1.2）；64B 差分恰 4B + 链形态复核（§A1.4 S1/S2）；歧义绝不盲写（A1.2 注 c） | 非期望崩溃=`FAIL_FOREIGN_CRASH`，证据隔离**不入 J1–J6 计数**（E1-8 判据面，:137）；趟为一次性、进程死亡可接受；守卫态 trips 风暴 ⇒ 人工停局（§C1 停止规则）；若疑似写坏 P1/P2 仪器数据面 ⇒ 两仪器件哈希复测（G-0c/G-8） |
| R3 | **帧钟停摆挂起**：以帧钟为注入闸门则在停摆现场永久等待 | W1/W2 停摆实证（GOAL :65）、W0 窗尾冻结 31.245fps 恒值（:66） | 勘-1：战术面标志+墙钟稳定窗主条件，帧钟降辅证；120s 墙钟硬超时 | 超时 ⇒ NOT_ATTEMPTED，趟照常收口，不拖垮批调度 |
| R4 | **降级风暴**（守卫态）：毒值被反复消费、NULL→Win32 兜底反复触发 | 兜底路径实证（:106 `0x7C949D`）；class 4 高压面（:122-123）使毒值消费快 | 单局 trip 阈值 10（[推断]，无实证）人工停局；D2 判读区分「一次拦截+存活」与「风暴」 | 风暴局=FAIL(`degrade-storm`)，该局不入 PASS 统计；若怀疑兜底面本身被毒值旁态打崩（如 next->prev 同槽未同步毒化）⇒ 该局升级分析，不续注 |
| R5 | **AV/HIPS 拦截 WPM**：火绒内存防护拦无签名宿主写 gamemd | GOAL :97 既有火绒内存防护线；I-6 无历史处置证据 | 运行窗前置确认用户侧安排；WPM FALSE+GetLastError 可检 | NOT_ATTEMPTED 收口，登记待环境解锁后重排；**禁止**绕过尝试（与 E1-8 红线同级的纪律面） |
| R6 | **磁盘税**：20 趟 × move-out 1.8GB ≈ 36GB | GOAL :87 实测每趟全量拷贝行为 | 批前余量门禁 ≥60GB；批后两遍 dedup（GOAL :87 §128 法）；发生器自有证据件（台账/差分/判读 JSON）控制在 MB 级 | 余量不足 ⇒ 缩批（先批 1/2），不冒盘 |
| R7 | **模式 P 值族撞形**（若启用）：编码值与真实业务数据撞形造成误判 | 0xFE00FFFF 的 imm32 零命中**不外推**族内其它值（:113 结论范围） | 启用前离线 imm32 全映像普查门禁（§B1）+ 判别式 `&3==3` 保持（:114） | 撞形实证 ⇒ 该值作废回退模式 S |
| R8 | **发现歧义多候选**：≥2 个结构合法堆候选 | 进程可能持多堆（`HeapAlloc(0x41C4)` 之外，:102） | region 描述符交叉验证（:109 `[0xB78B94]/[0xB78B98]`）；仍歧义 ⇒ DISCOVERY_FAILED | 三值化收口，绝不盲写（§A1.2） |
| R9 | **S3 回写陈旧值（v1 新增=R5；骨架风险表第 4 条「写时机撞上游戏正在操作该链」PGD:42 曾在本表遗漏，一并回收）**：校验失败回写把 S0 读出的旧值压过游戏在 S0–S3 间合法写入的新节点指针 | unlink 摘链/入链写点 0x7CFD30 正是该槽（RC_SPEC_V4.md:99）；PGD 原原子性论证只覆盖「游戏读我方写」单向交错 | S3 前置复读（§A1.4 v1）：仅当现值==0xFE00FFFF 才回写，否则不回写、记 `stale-restore-aborted` 按 foreign 隔离；64B 窗差分与链形态复核照旧 | 误回写已发生 ⇒ 该局 FAIL(`stale-restore-aborted`)、证据隔离不入 J1–J6 计数；守卫批同时复核 trips 序列甄别降级风暴假象（与 §H1-R4 联判）；裸奔批产出不可控崩溃则按 FAIL_FOREIGN_CRASH 隔离 |

## §H2 交付自查（分析员署名面；v1 修订=R8 更正两处）

- 骨架 §1–§7 原文零改动（可由追加边界 `# 深水补章节` 验证）；勘误 v1 起共 6 条全部显式（勘-1 时机、勘-2 P1 形态过时、勘-3 集成点+台账纪律、勘-4 验收 3 措辞、**勘-5「无节点哨兵」误称（R7）、勘-6 U0400 终局/观察端计时基准（R2）**）。
- 证据指针全覆盖本文 [事实] 断言；I-1…I-9 九项 INSUFFICIENT 已点名缺什么（**I-1 已于 v1 撤销改记**，I-8/I-9 为 v1 新增）；[推断] 共 5 处（原子性、GROUPS_MAX、trip 风暴阈值、HW brk 不命中内核写、EIP 栈顶软检查）均已标注。
- 本件撰写与修订全程零真机动作；唯一写入=本文件+同目录 `REVISION_RECEIPT.md`；未触碰 QC161 签署块（**v1 更正（R8）：卡片实为 `lead\cards\QC161.md` 可达（808 行），原「该件不存在」系起草代理路径错误**；卡 §7 签署栏仍未读）、未写 ra2bench/ra2youli/qc124_observe_chain 母本。
- 遗留给主会话的批点（v1 修订）：① 批 3（裸奔）发射授权（骨架 §7-3、§G1-G3；评审批点 1=有条件放行，条件=R2/R5 修订落件——**已落**，是否发射由主会话裁）；② 模式 P 启用权（§B1；评审批点 2=暂缓，同设计自身裁定）；③ ~~DEGRADED-GATE 接受度~~ **已撤销（R6）**——替代批点=「批 1/2 NOT_RUNNABLE 期间协议以批 3/4 单态先行」是否接受（§C1 次序、§D1）。
- **修订层自查**：R1–R8 八条全部就地落实，逐条位置见文末 §R 修订对照表；处置回执=`REVISION_RECEIPT.md`（8/8 RESOLVED · 0 DEFERRED）。

---

## §R 修订对照表（v1 · 2026-10-19 · 独立修订者；依据=`DESIGN_REVIEW.md` R1–R8）

| R# | 修订点 | 修订位置 | 一句话 |
|---|---|---|---|
| R1 | 守卫态批前置件缺位 | §0 I-8（新增）、§C1「批 1/2 前置门」（新增）、§C1 次序、§F1 环境前置、§G1 G-0e（新增）/G-1/G-2、§H2 批点③ | 守卫本体登记为前置依赖并给存在性检验：I-8 登记全链无实现证据（OFFLINE_BATCH_VERDICT.md:212 find 0 命中+自认 I-3）；批 1/2 三证据「守卫在场门」（安装器产物+install 族 tag 证据面 RC_SPEC_V4.md:389/:589+`EnableSbhGuard=1` 生效自检），缺=NOT_RUNNABLE；批 3/4 单态先行路径与单臂局限声明入次序条款。 |
| R2 | U0400 ~24 游戏秒确定性提前终局未消化 | §0-bis 勘-6（新增）、勘-1 措辞、§C1 趟长与计时基准（重写）、§F1 语料落实（重写）、D-2 收口交叉引用、I-7 措辞 | 观察窗/时序重设计：主用图换 T50 全链实证的 spawnfix8 `0add791d` 长战局语料（回归 GOAL :36 前提并显式声明路线关系），计时基准改墙钟（游戏秒随计分板冻结）、计分板检出=观察窗合法终态；U0400 原图降为可选短局快筛臂（勘-6 登记 ~24 游戏秒确定性终局与「帧钟>600」的第二重荒谬）。 |
| R3 | P1/P05 观测腿跨实例跨相位不可达 | §D1 D-3（重写：`pg_poison_poll` 必在腿）、D-4（候选 k 产出方钉死）、D-5（按在场腿限定）、D-6、§E1 E1-1（重定界）/E1-2（注）、§G1 G-0d/G-6（限定在场腿） | 集成条款规范化：定义发生器内建只读观测器 `pg_poison_poll`（等价复刻 qc135 `BAD_VALUE` 判据+同构 event）为 #4 趟必在 P1 腿，qc135 跨实例腿降为不判门旁证；P05 候选 k 集产出方钉死=发生器 DISCOVER 组号集（QC209_VERIFY:70 JSON 通道供给方唯一化）且仅守卫批在场；G-6 关联率限定 A 臂趟×在场腿。 |
| R4 | 空表 fallback「位图置位」断言不成立 | §A1.3（重写） | 删除空表 fallback：位图仅由 alloc/free 配对维护点置位（OFFLINE_BATCH_VERDICT.md:60-63）、裸写 head->next 不置位、`0x7CFC9B` 以位图扫描命中为唯一前驱（:57）⇒ 全空=NOT_ATTEMPTED(`no-nonempty-c4`) 换局零写入；守卫拦截面论证限定非空链保留。 |
| R5 | S3 回写陈旧值风险漏登记 | §A1.4 S3 步与原子性注（前置复读）、§A1.5 首条、§H1 R9（新增） | 登记风险 R9（游戏可在 S0–S3 间经 0x7CFD30 合法改写同槽；骨架 PGD:42 被遗漏的第 4 条风险一并回收），S3 改为回写前复读、仅现值==毒值才回写旧值，否则不回写、记 `stale-restore-aborted` 按 foreign 隔离。 |
| R6 | DEGRADED-GATE 不可执行 | §D1 D-2（重写：显式弃用）、§G1 G-1、§H2 批点③ | 选「显式弃用」路径：D-2 只认遥测计数器主判据；读取通道（I-3）或守卫本体（I-8）任一未交付 ⇒ 批 1/2 如实标 NOT_RUNNABLE；「守卫日志件出现非零计数快照」式降级判据废除；未来降级变体须挂 M 轨真实产物另提案。 |
| R7 | 骨架「无节点哨兵」误称漏勘 | §0-bis 勘-5（新增）、§B1 模式 S 更名注记 | 补勘-5：0xFE00FFFF 非 MSVC6 SBH「无节点」哨兵（哨兵=head 自环值，OFFLINE_BATCH_VERDICT.md:66-67），系与业务数据同值分布的腐化产物值（RC_SPEC_V4.md:113-114）；骨架原文不动、追加层 §B1 同步更名注记。 |
| R8 | 小修包+I-1 撤销确认 | §0 I-1（撤销改记）、§0 P1 验件指针（:307→:292-297）、§0-bis 勘-1（「根因=」→「停摆位置=」+卡 §T32/§T34 定谳回填）、勘-2（QC205_VERIFY :25→:33）、§G1 G-1（DEGRADED 注记，随 R6 落实）、§H2 自查行更正 | I-1 撤销改记（卡实为 `lead\cards\QC161.md` 808 行可达，起草代理读件路径错误已定谳；卡 §7 签署栏仍未读）、勘-1 停摆归因措辞更正、两处行号指针修正、§H2 同步更正。 |

> 修订纪律自查：骨架 §1–§7 :1-:56 零改动（R7/R8 对骨架面的修正以勘-5/勘-6 勘误条目呈现，未改骨架原文）；本层其余修订全部就地改写并逐一登记于本表；全程零真机动作；唯一写入=本文件+`REVISION_RECEIPT.md`；未触碰 QC161 §7 签署块与任何母本。
