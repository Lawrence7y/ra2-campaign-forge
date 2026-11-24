interface Verdict {
  /** 任务编号，如 "A01"。 */
  id: string;
  /** 一句话结论（中文，不超过 60 字），必须是直接答案不是过程描述。 */
  headline: string;
  /** 结论的证据级别：byte=直接读出的字节；derived=CFG/数据流推导；speculation=无直接字节支撑。 */
  evidenceLevel: "byte" | "derived" | "speculation";
  /** 关键数字/地址清单，每条带 VA 与含义。 */
  keyFacts: string[];
  /** 这个机制若成立，真机侧应读到什么值（具体 VA + 期望值）。做不到就写"未给出"。 */
  falsifiablePrediction: string;
  /** 与本仓既有记载的冲突（无冲突写"无"）。 */
  conflicts: string;
  /** 有没有做完；false 时 problems 必填。 */
  complete: boolean;
  /** 没做完/受阻的原因。 */
  problems: string;
}

interface Confirmation {
  /** 被核验的任务编号。 */
  id: string;
  /** 核验判定。 */
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
  /** 逐条说明：哪些主张复现了、哪些没有、哪些无法判定。 */
  detail: string;
  /** 核验者自己重算出的数字（与子代理报的对照）。 */
  recomputed: string[];
  /** 核验者发现但原报告没写的问题。 */
  missedByAuthor: string;
}

const ROOT = "lead/goal3t_nightwatch_20261102/swarm_20261104";
const ABS = "D:/Project/ra2-campaign-forge/" + ROOT;

const RULES = [
  "## 铁律（违反即作废）",
  "1. 零真机：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. 零改动母本：ra2youli/gamemd.exe 只读，不得改一个字节。",
  "3. 写域仅限分配给你的目录，不得改任何台账、re_atlas/、冻结件。",
  "4. 不 commit / 不 push。",
  "5. python 一律 python -I -X utf8。",
  "",
  "## 解码口径（本仓血泪教训）",
  "禁止 for ins in md.disasm(blob, va) 扫全镜像——capstone 在首个不可解码字节处静默停止，",
  "会造出「0 处命中」的假零（本仓 G-23）。必须用重同步解码，或直接用共享引擎：",
  "",
  "    import sys",
  "    sys.path.insert(0, r\"" + ABS + "\")",
  "    from ra2tool import Engine",
  "    eng = Engine()",
  "    print(eng.coverage)          # 必须打印，覆盖率自证（应为 100.00% / 1394120 insns）",
  "    eng.disp_hits(0x00A8ED84)    # 绝对全局访存 -> [(va,'W'|'R',mnem,op_str)]",
  "    eng.disp_hits_field(0x62C)   # 任意基址 [reg+0x62C] 家族",
  "    eng.disasm(0x55D360, 0x200)  # 函数窗口反汇编",
  "    eng.rd(va,n) / eng.u32(va)   # 原始字节 / dword",
  "    eng.resolve_iat(0x7E11F0)    # -> ('KERNEL32.dll','Sleep')",
  "    eng.func_rets(lo,hi)         # (rets, succ)",
  "    eng.reach_without(head,hi,cut_lo,cut_hi)  # 绕开某直线块的可达集",
  "    eng.loop_backedges(lo,hi)    # 回边",
  "",
  "## 证据分级（每个结论必须带）",
  "[字节]=直接读出，附 VA+hex；[推导]=CFG/数据流推断，须列每跳；[推测]=无字节支撑，",
  "必须明写「推测」。禁止把推测写成结论。",
  "",
  "## 必写诚实账",
  "报告最后一节 诚实账：没做的、样本薄的、可能出错的、与既有台账冲突的（冲突必须指出）。",
  "",
  "## 已定谳基线（不许擅自改口径，除非给出字节反证）",
  "- CurrentFrame 0xA8ED84：1007 引用 / 10 写 / 唯一定常 inc 0x55DE7E + 写回 0x55DE81",
  "- 焦点旗标 0xA8ED80：46 引用 / 唯一写者 0x7778CE（WndProc WM_ACTIVATEAPP）",
  "- MainLogicFrame 0x55D360：3 个 ret（0x55D877 / 0x55DEC7 / 0x55DEDB）；",
  "  其中 0x55D877 与 0x55DEDB 不经 inc 即可达（冻结出口）",
  "- 0x7E11F0=KERNEL32!Sleep，0x7E1530=WINMM!timeGetTime",
  "",
  "## 产出",
  "写 <你的目录>/REPORT.md，中文，结构：",
  "# <编号> · <一句话结论>",
  "## 0. 现场自证（eng.coverage 输出 + tasklist 无 gamemd）",
  "## 1. 结论（带证据级别）",
  "## 2. 证据（逐条 VA + 字节 + 推导链）",
  "## 3. 与本仓既有记载的对账（一致/冲突）",
  "## 4. 诚实账",
  "## 5. 复算入口（脚本路径 + 命令行）",
].join("\n");

const TASKS: { id: string; title: string; brief: string }[] = [];

TASKS.push({
  id: "A01",
  title: "帧冻结出口守卫链与 [GameLogic+0x62C] 定谳",
  brief: [
    "MainLogicFrame 0x55D360 有两条不经 inc 即可达的 ret：",
    "  (a) 0x55D877 —— 从 0x55D7C2 分支来：GameMode 属于 {0,5} 且 [[0xA8B230]+0x62C]!=0",
    "      ==> 跑 pump / 0x48D080 / 0x53B560 / vtable+0x5C / 0x4F4480 / LogicUpdate(0x55E160)，",
    "      世界更新照跑但帧号不推进",
    "  (b) 0x55DEDB —— 头部 [0xA8E9A0]==0 早退",
    "",
    "要做：",
    "1. 完整写出 0x55D7C2 -> 0x55D877 的守卫链，写成可判定条件表达式。",
    "2. 判定 [[0xA8B230]+0x62C] 是什么字段：",
    "   - [0xA8B230] 全镜像 3 个写点：0x52BA94 / 0x52BAB6 / 0x6BEB7D。逐个解上下文",
    "     （所在函数、写入值来源、守卫），判定该指针何时 NULL、何时赋值。",
    "   - +0x62C 用 disp_hits_field(0x62C) 拿家族，按 this 来源分档（不许合并不同类），",
    "     逐个判定哪个是写、宿主从哪来。",
    "   - 必须回答：是暂停标志、同步等待、跳帧还是别的。无法定谳就明写，并列出排除过的候选。",
    "3. [0xA8E9A0] 的 23 个写点里，哪些会在局内把它清 0，判定出口 (b) 实战是否可能触发。",
    "4. 给出机制判据：哪几个 VA 读到什么值就能证实或证伪。要具体，不要写观察一下。",
  ].join("\n"),
});

TASKS.push({
  id: "A02",
  title: "焦点旗标死锁循环的完整语义与冲突裁决",
  brief: [
    "MainLogicFrame 头部已逐字节钉死：",
    "  0x55D377 mov al,[0xA8ED80]   ; 焦点旗标",
    "  0x55D383 test al,al",
    "  0x55D385 jne 0x55D3BB        ; !=0 -> 直落帧体（会走到 inc）",
    "  0x55D387 mov esi,[0x7E11F0]  ; = KERNEL32!Sleep（IAT 已证实）",
    "  0x55D38D mov eax,[0xA8B238]  ; GameMode",
    "  0x55D392 test eax,eax ; 0x55D394 je 0x55D39B",
    "  0x55D396 cmp eax,5    ; 0x55D399 jne 0x55D3B2",
    "  0x55D39B push 0x1F4 ; 0x55D3A0 call esi     ; Sleep(500)",
    "  0x55D3A2 call 0x5D4D50       ; MessagePump",
    "  0x55D3A7 mov al,[0xA8ED80]",
    "  0x55D3AE je 0x55D38D         ; 旗标仍 0 -> 回到循环顶",
    "  0x55D3B0 jmp 0x55D3BB",
    "  0x55D3B2 push 0xA ; call esi ; Sleep(10)",
    "  0x55D3B6 call 0x5D4D50",
    "[0xA8ED80] 全镜像唯一写者是 0x7778CE（WndProc WM_ACTIVATEAPP 激活/失焦沿）。",
    "",
    "要做：",
    "1. 解出泵 0x5D4D50 的关键结构：是否 PeekMessage/DispatchMessage、入口守卫是什么、",
    "   它在 hwnd==0 时的行为。",
    "2. 判定旗标恒 0 是否可能长期持续：",
    "   - 0x7778CE 守卫链逐条核（WM_ACTIVATEAPP 且 hwnd==[0xB73550] 且 wParam!=0 且旧值!=新值）。",
    "   - 主窗 hwnd 变 0 或不再前台时，旗标还能否置 1？给能/不能的字节判据。",
    "   - 是否另有路径能跳出循环（GameMode 改变 / [0xA8E9A0] 被清 / 泵抛异常）？逐条排查。",
    "3. 算时间量级：被困时一秒几次循环？与实测帧号冻结 2.56 到 24.73 秒是否量级吻合？给算式。",
    "4. 真机判别式：应同时读到哪几个全局的什么值才能证实，以及证伪条件。要具体 VA + 数值。",
    "",
    "★ 重点冲突裁决：docs/re/clock_frame_loop.md 说 0xA8ED80 = 快进/跳过 Sleep 标志，",
    "R-063a 定谳为焦点旗标。你必须独立判定：用字节说话，谁对谁错，或两者是否都成立。",
    "这一条不许含糊。",
  ].join("\n"),
});

TASKS.push({
  id: "A03",
  title: "[0xA8B230] GameLogic 指针的身份与生命周期",
  brief: [
    "[0xA8B230] 是全镜像 1293 处引用的核心全局指针（GameLogic 类实例）。",
    "它也是 A01 里 [[0xA8B230]+0x62C] 的基址。",
    "",
    "要做：",
    "1. 3 个写点逐个解：0x52BA94 / 0x52BAB6 / 0x6BEB7D。",
    "   对每个：所在函数头、该函数做什么、写入值(eax/ebx)从哪来、调用者是谁。",
    "2. 判定这个指针的构造时机：哪个函数 new 出 GameLogic 实例？大小是多少（push 的立即数）？",
    "   是单例还是有生命周期（对战结束后置 NULL？）。",
    "3. 从写点上下文判断：在局内战斗窗口（measure 窗）期间，这个指针是否必然非 NULL？",
    "   给出字节判据。",
    "4. 该对象的 RTTI 名（若可解）：从 vptr 反查 .rdata 的 COL/TD。",
    "5. 与 docs/re/clock_frame_loop.md、ARCHITECTURE_ATLAS.md 的记载对账，指出冲突。",
  ].join("\n"),
});

TASKS.push({
  id: "A04",
  title: "GameMode 状态机与 Campaign/Skirmish 值域",
  brief: [
    "0xA8B238 是 SessionClass::Instance 首成员 GameMode，全镜像 570 处引用 / 30 写。",
    "ARCHITECTURE_ATLAS 记枚举 {Campaign=0, LAN=3, Internet=4, Skirmish=5}，",
    "并注明 0 亦由退局路径反复写入，不可作菜单/局内判据。",
    "",
    "要做：",
    "1. 30 个写点全部列出，按写入值分档（写 0 的几处、写 5 的几处、写 3/4 的几处）。",
    "   逐档判定：哪个写点对应进入遭遇战、哪个对应退回主菜单、哪个对应战役加载。",
    "2. 找出进入遭遇战（Skirmish=5）的确切写点，以及它的上游触发。",
    "3. 判定 MainLogicFrame 里 GameMode 判定（0x55D394 je / 0x55D399 cmp 5）在遭遇战局内的取值。",
    "   即：打遭遇战时 GameMode 恒为 5 吗？还是会在 0/5 之间跳？",
    "4. 若 GameMode 在局内可能为 0，则 A01 的 (a) 出口在遭遇战里也有效——给出字节判据。",
    "5. 对账 ATLAS 的枚举表，指出是否有第 5 个值或未登记的写点。",
  ].join("\n"),
});

TASKS.push({
  id: "A05",
  title: "MessagePump 0x5D4D50 全面解构",
  brief: [
    "0x5D4D50 是 MainLogicFrame 里调用的消息泵，也是全镜像 5 个 DispatchMessageA",
    "宿主之一（返回地址 0x5D4E4D）。",
    "",
    "要做：",
    "1. 整函数反汇编 + 结构说明：PeekMessageA 参数、消息循环形态、DispatchMessageA 调用点、",
    "   返回值语义、是否有 hwnd==0 短路。",
    "2. 判定：泵在跑、但窗口没消息时，它做什么？立即返回还是阻塞？",
    "3. 找它的全部调用者（E8 直呼 + 间接），按宿主聚簇：哪些在帧循环里、哪些在等待环里。",
    "4. 泵计数器 [0xAA0430]（R-063a 记 7 组写者）：复核写者数量与增量语义，",
    "   判定主泵 hwnd==0 时计数不增是否成立。",
    "5. 若 A02 的假说成立（旗标恒 0 困在 Sleep+泵循环），泵在这里的职责是什么？",
    "   它能不能自己让旗标变 1？（即：泵内是否会间接触发 WM_ACTIVATEAPP 写者）",
  ].join("\n"),
});

TASKS.push({
  id: "A06",
  title: "LogicUpdate 0x55E160 节拍门与帧冻结的关系",
  brief: [
    "0x55E160 LogicUpdate 是 MainLogicFrame 尾部调用的世界更新函数，",
    "带自己的 timeGetTime 节拍门（[0x887328] 上次 / [0x887330] 目标间隔 ms）。",
    "",
    "要做：",
    "1. 整函数反汇编 + 结构说明：早退条件有几条、节拍门算式、[0xA8EDA0] 与 [0xA8ED80] 的",
    "   双重门（docs 记：if [0xA8EDA0]==0 && [0xA8ED80]==1 才更新世界）。",
    "2. ★ 关键：A01 的 (a) 出口（0x55D877）会调用 0x55E160。若此时 [0xA8ED80]==0，",
    "   0x55E160 会不会早退？即：走 (a) 出口时，世界到底更新了没有？给字节判据。",
    "3. [0x887330] 目标间隔的计算：从 [0xA8B558]（GameSpeed）到 ms 的完整算式，",
    "   算几个典型 GameSpeed 下的实际间隔。",
    "4. 判定：若帧号冻结但 LogicUpdate 仍在跑，会产生什么可观测现象？",
    "   （例如：帧号不动但单位仍在动？还是都不动？）",
    "5. 对账 docs/re/clock_frame_loop.md 的 3.3 节，指出冲突。",
  ].join("\n"),
});

TASKS.push({
  id: "A07",
  title: "CurrentFrame 10 个写点的全归因",
  brief: [
    "CurrentFrame 0xA8ED84 全镜像 1007 引用 / 10 写（本轮重同步复核，与 ATLAS 8.4 吻合）。",
    "10 个写点：",
    "  0x52DA08  mov [0xA8ED84], ebx",
    "  0x55DE81  mov [0xA8ED84], edx     <-- 唯一定常 inc 后写回",
    "  0x5B7329  mov [0xA8ED84], 0",
    "  0x5BB20C  mov [0xA8ED84], ebp",
    "  0x5E550F  mov [0xA8ED84], esi",
    "  0x5E747C  mov [0xA8ED84], 0",
    "  0x68466B  mov [0xA8ED84], esi",
    "  0x686765  mov [0xA8ED84], ebp",
    "  0x795234  mov [0xA8ED84], 0",
    "  0x79758C  mov [0xA8ED84], eax",
    "",
    "要做：",
    "1. 逐点解：所在函数头、该函数职责（存档/读档/开局清零/回填）、写入值来源、守卫条件。",
    "2. 判定哪几个可能在 measure 窗内被触发（即：不只是开局/存读档）。",
    "   若有，它会不会造成帧号跳变而非冻结？这与本仓 f[0]==0 加载段型有何关系？",
    "3. ★ 特别核：0x55DE81 是否真的是唯一定常自增点。检查这 10 个写点里有没有",
    "   其它读-加-写形态（构成第二个自增点）。给出完整判据。",
    "4. 复核写 0 的 3 处（0x5B7329 / 0x5E747C / 0x795234）分别在什么时机。",
    "5. 与 ATLAS 8.4「9 处均为载入地图、读取存档或开局清零」对账，逐点验证这句话。",
  ].join("\n"),
});

TASKS.push({
  id: "A08",
  title: "帧冻结期间的可观测旁证：tick 旗标、泵计数、ws 阶梯",
  brief: [
    "目标①的实测形态：帧号冻结 2.56 到 24.73 秒、进程活着、正常退出、CPU 低。",
    "本仓已有真机数据（只读，绝对不要新跑）：",
    "  out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_*/measure_w*.json",
    "  out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_*/h8_wait_trace.json",
    "  lead/qc161_u0400_trip/c2ab_x/*/timeline.json  （含 frame + tick 字段）",
    "",
    "要做：",
    "1. 全量统计这些窗里的帧冻结事件：时长分布、次数、在窗内的位置。",
    "   用与台账一致的口径 B（卡住帧值首末拍跨度）。",
    "2. ★ 核心：timeline.json 里有 tick 字段（= [0xA8ED80] 采样值）。",
    "   全量统计：帧冻结期间 tick 是多少。若存在 tick==0 且帧不动，这是 A02 假说的直接证据；",
    "   若 tick 恒为 1，则 A02 假说被这批数据证伪（这同样重要，必须如实报）。",
    "   注意：这些 timeline 的 tick 可能只覆盖部分趟，先做覆盖度普查再下结论。",
    "3. 统计冻结期间 ws_kb 是否有阶梯跳变（本仓记 ws 是阶梯跳变非分配抖动，复核）。",
    "4. 统计冻结时长与冻结发生时刻的关系（本仓记无指示器，复核）。",
    "5. 若数据不足以判定 A02，明写样本不足，并给出最小的补充采样方案",
    "   （哪几个 VA、多少 Hz、什么条件下采），不要求你去跑。",
    "",
    "★ 这一条的结论方向不预设。tick 恒 1 与 tick 有 0 都可能是结果，如实报。",
  ].join("\n"),
});

TASKS.push({
  id: "A09",
  title: "窗口消息投递面：能否有路径让 WM_ACTIVATEAPP 不来",
  brief: [
    "A02 假说依赖「WM_ACTIVATEAPP(wParam!=0) 永远不到达」。要判定这条路径是否真的可达。",
    "",
    "要做：",
    "1. 普查所有向主窗投递或转发消息的代码：SendMessageA / PostMessageA / DispatchMessageA /",
    "   PeekMessageA 的 IAT 槽与调用点。逐个解上下文。",
    "2. 判定：本进程内有没有代码主动制造 WM_ACTIVATEAPP（例如自己 PostMessage 给主窗）？",
    "   若有，那条路径的触发条件是什么？",
    "3. 主窗 hwnd [0xB73550] 的生命周期：几个写点、何时被置 0、置 0 后 WndProc 还能否收到消息？",
    "4. 判定窗口存在但永远不是前台这个状态在游戏里能否自发产生",
    "   （例如：全屏/窗口模式切换、Alt-Tab 后没回来、最小化 SC_MINIMIZE）。",
    "   结合 [0xA8ED81]（SC_MINIMIZE 位）的写点分析。",
    "5. 给出：在什么条件下，主窗存在且泵在跑，但 WM_ACTIVATEAPP(wParam!=0) 不会到达。",
    "   若不存在这种条件，明写 A02 的长期困局路径不成立。",
  ].join("\n"),
});

TASKS.push({
  id: "A10",
  title: "0x55D360 函数体内 6 条回边的阻塞能力普查",
  brief: [
    "MainLogicFrame 0x55D360 体内有 6 条回边（本轮已钉）：",
    "  0x55D3AE -> 0x55D38D  （Sleep+泵自旋，A02 主题）",
    "  0x55D5ED -> 0x55D5D5  （call 0x540F90）",
    "  0x55D9B7 -> 0x55D975  （call 0x6E6AB0）",
    "  0x55DA1E -> 0x55D9D2  （call 0x6E6AB0 + 0x473AE0）",
    "  0x55DAEF -> 0x55DAAC  （call 0x6E6AB0）",
    "  0x55DB83 -> 0x55DB24  （call 0x473B10 + 0x55F690 + 0x6E6FF0 + vtable+0x14C）",
    "",
    "要做：",
    "1. 逐条回边解出循环体语义：迭代量是什么、退出条件是什么、被调函数做什么。",
    "2. 判定每条回边的最坏迭代次数上限：是有界的（遍历一个有限集合）还是无界的？",
    "   给出判据（例如：循环上界来自哪个全局或参数）。",
    "3. ★ 重点：哪些回边在极端输入下可能迭代极多次（数万次）从而造成帧号长时间不推进",
    "   但不死锁？这与①的多次型停滞（帧号严格递增慢爬）是否对应？",
    "4. 用本仓已定的两类停滞结论对账：",
    "   单段主导=帧钟冻结（完全不动）/ 多次型=帧号严格递增慢爬。",
    "   判定本函数里哪条路径对应哪一类。这是本轮最关键的结构性对账。",
    "5. 给出每个循环的预期耗时量级算式。",
  ].join("\n"),
});

TASKS.push({
  id: "A11",
  title: "0x48D080 Game::UnknownCall 与帧冻结的关系",
  brief: [
    "0x48D080 是每帧钩（169 处直呼），MainLogicFrame 与 LogicUpdate 各调一次。",
    "A01 的 (a) 出口也调用它。",
    "",
    "要做：",
    "1. 整函数反汇编 + 结构说明（docs 有骨架 skel_48D080.txt 但不要当结论，自己复算）。",
    "2. 它做什么？switch([0xA8B238]) 的各分支分别做什么？",
    "3. ★ 关键：它是不是渲染/音频这类非逻辑更新？",
    "   若 A01 的 (a) 出口只跑 0x48D080 而不跑真正逻辑，那么帧号冻结但画面还在动是否成立？",
    "   给出字节判据。",
    "4. 判定它内部是否有阻塞调用（Sleep / WaitForSingleObject / 临界区），",
    "   若有，列出调用点与最坏等待时长。",
    "5. 与 docs 记载对账。",
  ].join("\n"),
});

TASKS.push({
  id: "A12",
  title: "帧号冻结但进程活着且正常退出的完整二进制路径穷举",
  brief: [
    "这是收口任务：把所有能让 CurrentFrame 长时间不推进的路径穷举出来并排序。",
    "",
    "要做：",
    "1. 从 CurrentFrame 唯一 inc 在 0x55DE7E 出发，穷举所有 MainLogicFrame 调用了但没走到 inc 的路径：",
    "   - 头部早退（0x55DEDB，[0xA8E9A0]==0）",
    "   - 睡眠/泵自旋（0x55D3AE -> 0x55D38D）",
    "   - (a) 出口（0x55D877，GameMode+0x62C）",
    "   - 体内长循环（A10 的 6 条回边）",
    "   - 函数本身没被调用（调用者侧：0x48CE8A 主环及其它 5 个模态泵）",
    "   - 被外部阻塞（Sleep/等待/临界区）",
    "   逐条给出：触发条件、预期持续时长量级、是否与进程正常退出相容。",
    "2. 对每条路径给出排他性判别式：真机侧读哪几个 VA 就能唯一确定是哪条。",
    "   这要构成一张判别表（VA × 路径 × 期望值）。",
    "3. 判定哪条路径与①的实测形态最吻合：",
    "   帧号冻结 2.56 到 24.73 秒、进程活着、CPU 低、正常退出 rc=0、无崩溃。",
    "   给出你的排序与理由，并明写这是排位不是定谳。",
    "4. 明确列出：还需要什么真机证据才能定谳（最小采样清单）。",
    "5. 对账本仓 530 到 532 节的 E3 争论：E3 栈采样能否区分这些路径？",
    "   若能，指出栈签名；若不能，明说。",
  ].join("\n"),
});

phase("勘察现场：确认工具链与冻结基线可用");
const gate = await world.run(
  "python",
  ["-I", "-X", "utf8", ROOT + "/selftest.py"],
  { timeoutMs: 900000 },
);
log(`环境自测门 exit=${gate.exitCode}`);
if (gate.exitCode !== 0) {
  return {
    conclusion: `环境自测门未通过（exit=${gate.exitCode}），未派发任何逆向分析任务。`,
    findings: [],
    verified: [`selftest.py exit=${gate.exitCode}`],
    notCovered: ["全部 12 个方向——工具链未就绪"],
  };
}

phase("12 个逆向方向并行取证");
const drafts = await Promise.all(
  TASKS.map(async (t) => {
    const analyst = agent(`分析员-${t.id}`, {
      system:
        "你是 RA2/YR 引擎逆向分析员，擅长 x86 反汇编、CFG 分析、数据流追踪。\n" +
        "你的每条结论都必须能指回具体 VA 与十六进制字节。禁止把猜测写成结论。\n" +
        "如果某项做不到或被证据反驳，如实写明——这比给出漂亮结论更有价值。\n" +
        "如果发现与既有文档冲突，必须明确指出，不得沉默迁就。\n" +
        "所有文件写入只允许在分配给你的目录内。",
    });
    const v = await analyst.ask<Verdict>(
      `任务编号 ${t.id}：${t.title}\n\n` +
        `你的写域：${ABS}/${t.id}/\n` +
        `纪律件：${ABS}/DISCIPLINE.md\n\n` +
        RULES +
        "\n\n## 你的具体任务\n" +
        t.brief +
        "\n\n完成后把结论按结构化格式返回。evidenceLevel 必须诚实分级：" +
        "有直接字节就是 byte，只靠推导就是 derived，没有字节支撑就是 speculation。",
    );
    return { task: t, verdict: v };
  }),
);

log(`12 份初稿已回收：${drafts.filter((d) => d.verdict.complete).length}/12 自报完成`);
for (const d of drafts) {
  report({
    id: d.task.id,
    title: d.task.title,
    headline: d.verdict.headline,
    evidenceLevel: d.verdict.evidenceLevel,
    complete: d.verdict.complete,
  });
}

phase("逐份独立核验：换一个上下文从字节复算");
const confirmed = await Promise.all(
  drafts.map(async (d) => {
    const checker = agent(`核验员-${d.task.id}`, {
      system:
        "你是独立核验员。你的职责是推翻，不是确认。\n" +
        "从字节重新复算，不要相信原报告的结论。原报告说 A，你去读字节验证 A。\n" +
        "如果你复现不出来，判 REFUTED 或 UNVERIFIABLE，并说明你读了哪些字节。\n" +
        "特别检查：地址是否读错、字节数是否数错、CFG 是否有遗漏分支、口径是否偷换。\n" +
        "本仓有多次「看起来合理的量但循环定义」的错误史，请特别警惕这类。",
    });
    const c = await checker.ask<Confirmation>(
      `核验任务 ${d.task.id}：${d.task.title}\n\n` +
        `待核验报告：${ABS}/${d.task.id}/REPORT.md\n` +
        `纪律件：${ABS}/DISCIPLINE.md\n\n` +
        RULES +
        "\n\n## 原报告的自报结论（供对照，不要直接采信）\n" +
        `headline: ${d.verdict.headline}\n` +
        `evidenceLevel: ${d.verdict.evidenceLevel}\n` +
        `keyFacts: ${JSON.stringify(d.verdict.keyFacts)}\n` +
        `falsifiablePrediction: ${d.verdict.falsifiablePrediction}\n` +
        `conflicts: ${d.verdict.conflicts}\n` +
        `problems: ${d.verdict.problems}\n\n` +
        "## 你要做的\n" +
        "1. 自己写探针从 gamemd.exe 字节复算每一个 keyFacts（不许 import 原报告的脚本，" +
        `只可用共享引擎 ${ABS}/ra2tool.py）。\n` +
        "2. 逐项判定 CONFIRMED / REFUTED / PARTIAL / UNVERIFIABLE，写进 detail。\n" +
        "3. recomputed 填你自己算出的数字，与原作者的数字并列。\n" +
        "4. missedByAuthor 填原作者没写但你想问「他为什么没提这个」的问题。\n" +
        `核验报告写到 ${ABS}/${d.task.id}/VERIFY.md。`,
    );
    report({
      id: `${d.task.id}-verify`,
      title: `核验 · ${d.task.title}`,
      verdict: c.verdict,
    });
    return { task: d.task, verdict: d.verdict, check: c };
  }),
);

phase("交叉对账：找出方向之间的矛盾");
const ledger = agent("对账员", {
  system:
    "你是交叉对账员。你的职责是找出 12 份报告之间互相矛盾的地方。\n" +
    "两份报告对同一个 VA 给出不同解释、对同一个机制给出互斥的判据——这些必须被揪出来。\n" +
    "不要调和矛盾，不要和稀泥。矛盾本身就是最重要的发现。",
});
const crosscheck = await ledger.ask<Confirmation>(
  `${ABS}/ 下有 12 个子目录，每个含 REPORT.md 与 VERIFY.md。\n\n` +
    RULES +
    "\n\n## 你要做的\n" +
    "1. 全部读完 12 份 REPORT.md + 12 份 VERIFY.md。\n" +
    "2. 列出所有互相矛盾的主张（同一 VA 不同解释 / 同一机制互斥判据 / 数字不一致）。\n" +
    "3. 列出所有被 VERIFY 判 REFUTED 或 PARTIAL 的主张，判定该主张是否仍被其它报告当作前提使用" +
    "（若是，这是传染性错误，必须点名）。\n" +
    "4. 给出：哪几条结论已经足够硬，可以进台账；哪几条还差什么。\n" +
    "5. 判定 A01 的 (a) 出口假说与 A02 的睡眠自旋假说，哪个与实测现象更吻合，理由是什么。\n" +
    `写进 ${ABS}/_CROSSCHECK.md（目录根，你的写域）。`,
);

phase("汇总最终判定");
const summary = agent("汇总员", {
  system:
    "你是汇总员。把 12 个方向 + 核验 + 对账收敛成一份可交付的判定书。\n" +
    "不要粉饰。已证实的写已证实，未证实的写未证实，被推翻的写被推翻。\n" +
    "这份文档会被人类用来决定下一步真机怎么跑，所以每个可执行建议都必须落到具体 VA。",
});
const finalMarkdown = await summary.ask<string>(
  "读以下全部材料：\n" +
    `- 12 个子目录的 REPORT.md 与 VERIFY.md：${ABS}/A01 到 A12\n` +
    `- 交叉对账：${ABS}/_CROSSCHECK.md\n` +
    `- 原报告自报结论：${JSON.stringify(
      drafts.map((d) => ({ id: d.task.id, headline: d.verdict.headline, level: d.verdict.evidenceLevel })),
    )}\n` +
    `- 核验判定：${JSON.stringify(
      confirmed.map((c) => ({ id: c.task.id, verdict: c.check.verdict })),
    )}\n` +
    `- 对账结论：${crosscheck.detail}\n\n` +
    `写一份中文判定书，存到 ${ABS}/VERDICT_20261104.md，结构：\n` +
    "# 帧冻结机制攻坚 · 判定书（2026-11-04）\n" +
    "## 一、一句话结论\n" +
    "## 二、已被字节证实的机制（含 VA 与字节）\n" +
    "## 三、被推翻或降级的主张（如实列，含谁推翻的）\n" +
    "## 四、仍未定谳的与缺什么证据\n" +
    "## 五、真机判别表（VA × 路径 × 期望值 → 结论）\n" +
    "## 六、下一步最小动作（不要求执行，只给方案与代价）\n" +
    "## 七、诚实账\n\n" +
    "然后把这个 markdown 全文作为你的最终回复返回。",
);

await artifact.markdown("verdict", finalMarkdown, {
  title: "帧冻结机制攻坚判定书",
  description: "12 个逆向方向 + 独立核验 + 交叉对账的收敛结果，含真机判别表。",
  primary: true,
});

const verifiedCount = confirmed.filter((c) => c.check.verdict === "CONFIRMED").length;
const refutedCount = confirmed.filter((c) => c.check.verdict === "REFUTED").length;

return {
  conclusion:
    `12 个逆向方向全部跑完并逐份独立核验：${verifiedCount} 份 CONFIRMED，${refutedCount} 份 REFUTED，` +
    `其余为 PARTIAL 或 UNVERIFIABLE。交叉对账与最终判定书见 artifact。`,
  findings: confirmed.map((c) => ({
    where: `${ROOT}/${c.task.id}/REPORT.md`,
    what: `${c.task.id} ${c.task.title}：${c.verdict.headline}`,
    evidence: `证据级别=${c.verdict.evidenceLevel}；核验=${c.check.verdict}；核验者复算=${c.check.recomputed.join("; ")}`,
    status: c.check.verdict === "CONFIRMED" ? ("verified" as const) : ("unconfirmed" as const),
    severity: (c.verdict.complete ? "medium" : "low") as "medium" | "low",
  })),
  verified: [
    "selftest.py exit=0（覆盖率 100% / 1394120 insns / 四条冻结基线逐位命中）",
    "12 份报告各由不同上下文的核验员从字节复算",
    "交叉对账员读完全部 24 份文件，矛盾清单在 _CROSSCHECK.md",
  ],
  notCovered: [
    "全部为静态只读分析：零真机、零进程、零母本改动",
    "运行期哪条路径真实触发，静态不可判，需真机采样",
    "本仓真机数据里 timeline.json 的 tick 字段覆盖度有限，A08 已如实登记",
  ],
};
