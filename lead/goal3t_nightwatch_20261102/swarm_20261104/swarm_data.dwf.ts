interface MiningResult {
  /** 子任务标识。 */
  id: string;
  /** 一句话结论。 */
  headline: string;
  /** 证据级别。 */
  level: "byte" | "derived" | "speculation";
  /** 关键数字清单。 */
  numbers: string[];
  /** 这个结论能否证伪 A02（焦点旗标假说）：CAN_CONFIRM / CAN_REFUTE / CANNOT_DECIDE / DATA_INSUFFICIENT。 */
  a02Impact: "CAN_CONFIRM" | "CAN_REFUTE" | "CANNOT_DECIDE" | "DATA_INSUFFICIENT";
  /** 理由。 */
  a02Reason: string;
  /** 冲突与局限。 */
  caveat: string;
}

interface DocConflict {
  /** 冲突主题。 */
  topic: string;
  /** 文档甲：路径 + 原文摘录。 */
  sideA: string;
  /** 文档乙：路径 + 原文摘录。 */
  sideB: string;
  /** 字节裁决：谁对，或都不对。 */
  byteVerdict: "A_CORRECT" | "B_CORRECT" | "BOTH_WRONG" | "BOTH_PARTIALLY_CORRECT" | "UNDECIDABLE_FROM_BYTES";
  /** 裁决依据（VA + 字节）。 */
  evidence: string;
}

const ABS = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104";
const ROOT = "lead/goal3t_nightwatch_20261102/swarm_20261104";

const RULES = [
  "## 铁律",
  "1. 零真机：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill。",
  "2. 零改动母本：ra2youli/gamemd.exe 只读。真机数据文件（json）也只读，不得改写。",
  "3. 写域仅限分配给你的目录。不改台账、不写 re_atlas/。",
  "4. 不 commit / 不 push。",
  "5. python 一律 python -I -X utf8。",
  "",
  "## 解码口径",
  "禁止 for ins in md.disasm(blob, va) 扫全镜像（capstone 静默停止，本仓 G-23）。",
  "用共享引擎：",
  "    import sys",
  "    sys.path.insert(0, r\"" + ABS + "\")",
  "    from ra2tool import Engine",
  "    eng = Engine(); print(eng.coverage)   # 必须打印自证",
  "",
  "## 证据分级",
  "[字节] / [推导] / [推测]。",
  "",
  "## 必写诚实账",
  "没做的、样本薄的、可能出错的、与既有台账冲突的。",
].join("\n");

phase("勘察现场：确认工具链可用");
const gate = await world.run("python", ["-I", "-X", "utf8", ROOT + "/selftest.py"], { timeoutMs: 900000 });
log(`环境自测门 exit=${gate.exitCode}`);
if (gate.exitCode !== 0) {
  return { conclusion: `自测门未通过 exit=${gate.exitCode}`, findings: [], verified: [], notCovered: ["全部"] };
}

phase("真机数据穷尽挖矿与文档冲突裁决并行");
const MINES: { id: string; title: string; brief: string }[] = [
  {
    id: "M01",
    title: "全量冻结事件普查与口径 B 复算",
    brief: [
      "数据根（只读）：out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/",
      "  - 88 个趟目录，98 个 measure_w*.json",
      "  - measure_w*.json 结构：samples.t（时间数组）、frame_edges（[[frame, t], ...]）、",
      "    counters（每 1s 一条含 ws_kb）、stats、gate（units0 等）",
      "",
      "要做：",
      "1. 枚举全部 measure_w*.json，打印有效窗数并与目录实测对账（本仓纪律：枚举后必须对账）。",
      "2. 用口径 B（卡住帧值首末拍跨度 = t(段内末拍) - t(段内首拍)，>=100ms 计入，",
      "   占比除以战斗段跨度）重算每个窗的停滞段数与占比。",
      "3. 输出：全量段数、时长分布（分档）、占比分布、按趟汇总。",
      "4. 与台账已公布数字对账：",
      "   - 97 窗 / 1734 个 >0.1s 平台（本仓 531 节）",
      "   - 0.1-0.2s 占 87.7%",
      "   - 最长 25.000s",
      "   若你的数字与之不符，必须指出并给出差异来源。",
      "5. 特别统计：每个窗里「冻结段」的位置（窗内第几秒开始）。",
    ].join("\n"),
  },
  {
    id: "M02",
    title: "tick 字段覆盖度与帧冻结相关性（A02 假说的直接检验）",
    brief: [
      "★ 这是本轮最关键的数据检验。",
      "timeline.json 里每行含 {t, singleton, hwnd, exitstate, frame, tick, hook6, ws_kb}，",
      "其中 tick = [0xA8ED80] 的采样值（焦点/快进旗标）。",
      "",
      "数据位置：lead/qc161_u0400_trip/c2ab_x/*/timeline.json（23 份）",
      "",
      "要做：",
      "1. 全量枚举这 23 份 timeline，统计：",
      "   - 总行数、含 tick 的行数、tick 的取值分布（0 ？ 1 ？其它？）",
      "   - 每份文件覆盖的时间跨度、采样频率",
      "2. ★ 核心：对每份 timeline，按 t 排序后找「frame 不变」的相邻行对（Δf==0），",
      "   检查同一时刻的 tick 值。",
      "   - 若存在 Δf==0 且 tick==0 → A02 假说的直接证据（帧冻结时焦点旗标为 0）",
      "   - 若 Δf==0 却 tick==1 → A02 假说在这批数据上被证伪",
      "   - 若 Δf==0 的样本里 tick 全是 1，但采样间隔太粗（>1s）看不出冻结 → DATA_INSUFFICIENT",
      "3. 注意陷阱：battle_tl 采样可能只覆盖战斗段的一部分，且采样间隔可能远大于冻结时长。",
      "   必须先算出「采样间隔」与「冻结时长」的可比性，再下结论。",
      "   若采样间隔 >> 冻结时长，则这批数据**根本无法**检验 A02，必须明写 DATA_INSUFFICIENT。",
      "4. 如实报：这条数据能不能判定 A02。不要为了有结论而硬凑。",
      "5. 给出最小补充采样方案（哪几个 VA、多少 Hz、采多久），不要求执行。",
    ].join("\n"),
  },
  {
    id: "M03",
    title: "wait-trace 4 份的逐拍分解与帧冻结对照",
    brief: [
      "h8_wait_trace.json 结构：{n, verdict, wait_s, samples: [[t, frame], ...]}（采样 400Hz）。",
      "位置：out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4{b,c,d,e}/h8_wait_trace.json",
      "",
      "要做：",
      "1. 4 份逐份读，打印：样本数、时间跨度、帧号首尾、verdict、wait_s。",
      "2. 逐拍分析：找所有 Δf==0 的连续区段，统计其时长分布。",
      "   这是**最高时间分辨率**的数据（400Hz），最能看清冻结的真实形态。",
      "3. ★ 关键判定：冻结段内，帧号是「完全不动」还是「偶尔跳一下」？",
      "   - 完全不动 → 单段主导型（引擎停摆）",
      "   - 偶尔跳 → 多次型（慢爬）",
      "   给出每份的分型结论与判据。",
      "4. 与台账 507 节的逐拍分解对账（v4-b poll_count=9989 等）。",
      "5. 判定：这 4 份数据能否区分 A01 的 (a) 出口与 A02 的睡眠自旋？",
      "   （提示：睡眠自旋下帧号完全不动且约 2 次/秒的泵节奏；",
      "   (a) 出口下帧号不动但世界更新在跑）",
    ].join("\n"),
  },
  {
    id: "M04",
    title: "units0 与冻结强度的再检验（复核 521 节的反相关）",
    brief: [
      "本仓 521 节结论：r(units0, B%) = -0.2005，判定「units0 不驱动卡顿」。",
      "但该结论标记为「本线判定、未经异族核验」。",
      "",
      "要做：",
      "1. 从 measure_w*.json 提取每窗的 gate.units0 与按口径 B 算出的停滞占比 B%。",
      "2. 复算 Pearson r(units0, B%) 与 Spearman。",
      "3. 分层：按 units0 分档（<200 / 200-500 / 500-1000 / >=1000），各档的 B% 分布。",
      "4. 判定：-0.2005 能否复现？若不能，差异来自哪里（窗口集合？口径？）。",
      "5. ★ 关键：这个结论影响目标①的整个方向——若 units0 真不驱动，" +
      "那么「数百单位卡顿」这个用户原话所指的现象就不在 units0 上。",
      "   请给出你独立判断的结论，并明写证据强度。",
    ].join("\n"),
  },
  {
    id: "M05",
    title: "文档冲突裁决：0xA8ED80 语义（焦点旗标 vs 快进标志）",
    brief: [
      "★ 这是纯文档对账 + 字节裁决任务，不碰游戏数据。",
      "",
      "冲突：",
      "  A 方：docs/re/clock_frame_loop.md 称 0xA8ED80 = 「快进/跳过 Sleep 标志」",
      "       （=1 时 0x55D360 跳过 Sleep 块，CPU 全力运转加速推帧）",
      "  B 方：re_atlas/evidence/r063a_flag_writer_closure.md 定谳为「焦点旗标」",
      "       （唯一写者 0x7778CE 在 WndProc WM_ACTIVATEAPP 激活/失焦沿；",
      "        引擎内名 Focus_Loss/Focus_Restore，社区惯例名 GameInFocus）",
      "",
      "要做：",
      "1. 两篇原文都读。",
      "2. 用字节独立裁决：读 0x7778CE 的完整守卫链、读 0x55D377-0x55D3BB 的完整逻辑、",
      "   读 0xA8ED80 的 45 个读点里哪些像「快进门」哪些像「焦点门」。",
      "3. 判定：A 对 / B 对 / 都错 / 都对（同一字节真的是两种语义？）。",
      "4. 若 A 对：则 0x7778CE 的 WM_ACTIVATEAPP 语义如何与「快进」相容？给出解释或反驳。",
      "   若 B 对：则 clock_frame_loop.md 的「快进」说法从何而来（可能是把",
      "   「失焦时 Sleep 500ms / 前台 Sleep 10ms」误解成「快进」）？",
      "5. 给出裁决书，含 VA + 字节 + 引用原文。这一条会直接进台账，必须钉死。",
    ].join("\n"),
  },
  {
    id: "M06",
    title: "文档冲突裁决：CurrentFrame 写点数与「唯一 inc」",
    brief: [
      "多处文档对 CurrentFrame 0xA8ED84 的描述不一致，需要字节裁决。",
      "",
      "要做：",
      "1. 收集所有相关文档记载：",
      "   - docs/re/ARCHITECTURE_ATLAS.md 8.4 节：「全 PE 镜像仅有 10 处向 0xA8ED84 写入」",
      "     「全镜像唯一定常递增写入点位于 0x0055DE73」（注意：它写的是 0x55DE73，",
      "     但 0x55DE73 是 mov edx,[0xA8ED84] 读取，inc 在 0x55DE7E，写回在 0x55DE81）",
      "   - docs/re/clock_frame_loop.md：「全镜像仅 10 处写 0xA8ED84，唯一 inc 在 0x55DE73-0x55DE81」",
      "   - docs/re/anchor_claims.txt：0x55DE73=读 / 0x55DE7E=inc / 0x55DE81=写回",
      "   - REVERSE_ENGINEERING_AND_PATCHES.md:1407",
      "2. 用字节逐条验证每条记载。",
      "3. ★ 判定 ATLAS 8.4 的「唯一递增点位于 0x0055DE73」这个地址是否正确。",
      "   若把「递增点」定义为 inc 指令本身，正确地址应是 0x55DE7E。",
      "   这是一个**地址级勘误**，必须明确指出。",
      "4. 验证「10 处写」是否精确（本轮重同步扫描也是 10 处，请独立复算）。",
      "5. 输出勘误清单：哪份文档哪一行该改成什么。",
    ].join("\n"),
  },
  {
    id: "M07",
    title: "文档冲突裁决：Sleep 语义与帧率上限",
    brief: [
      "多份文档对「Sleep 与帧率」的表述需要字节裁决。",
      "",
      "要做：",
      "1. 读 docs/re/clock_frame_loop.md 关于 Sleep 的段落：",
      "   「处于游戏主菜单或后台失焦时：Sleep(500ms)；处于常规局内前台对战时：Sleep(10ms)」",
      "   「快进模式：当 [0xA8ED80]==1 时完全跳过 Sleep 块」",
      "2. 用字节验证：0x55D387-0x55D3B6 的实际逻辑是什么？",
      "   - Sleep 值在哪几条路径上？（probe 已钉：Mode in {0,5} -> 500ms；其它 -> 10ms；",
      "     且都在 !flag 分支内）",
      "   - 「跳过 Sleep 块」是否准确？还是「跳过整个 Sleep+泵循环」？",
      "   - 这两个表述有实质差别：跳过 Sleep 但仍泵 vs 连泵都跳过。",
      "3. 判定 docs 的表述是否需要修正，给出精确措辞。",
      "4. ★ 顺带判定：既然 Sleep(500) 只在 Mode in {0,5} 时走，",
      "   而遭遇战是 Mode=5，那么「局内对战时 Sleep(10ms)」这个说法成立吗？",
      "   这是本仓的一个潜在错误，必须查清。",
      "5. 给出勘误清单。",
    ].join("\n"),
  },
  {
    id: "M08",
    title: "RE-ATLAS 线既有结论与本节新发现的对账",
    brief: [
      "RE-ATLAS 线（re_atlas/）已有大量与帧循环相关的定谳。要做跨线对账。",
      "",
      "要做：",
      "1. 读 re_atlas/STATUS.md 与 re_atlas/LEDGER.md 尾部的 R-063a/R-063b/R-064 相关记载。",
      "2. 读 re_atlas/evidence/r063a_flag_writer_closure.md 全文。",
      "3. 与本轮新发现逐条对账：",
      "   - R-063a 记「0xA8ED80 唯一写式 0x7778CE」「46 处引用」→ 本轮重同步复算是否吻合",
      "   - R-063a 记「0x55D360 内 3 处读 0xA8ED80」「自旋等待族」→ 逐条核",
      "   - R-063a 的泵族普查（5 个 DispatchMessageA 宿主、7 组泵计数写者）→ 复核",
      "4. ★ 重点：R-063a 把 0x55D360 的 3 处 0xA8ED80 读归为「自旋等待族」，",
      "   但它没有指出「这 3 处读会导致帧号不推进」。",
      "   本轮的贡献是把这个联系建立起来。请判定这个联系是否成立。",
      "5. 输出：RE-ATLAS 线哪些结论可以直接引用、哪些需要补、哪些与本轮冲突。",
    ].join("\n"),
  },
  {
    id: "M09",
    title: "E3 栈采样判别力评估：能否区分各条冻结路径",
    brief: [
      "本仓 530-532 节在争论 E3 栈采样（MiniDump / SuspendThread）的可行性与阈值 N。",
      "本轮从字节解出了多条「帧不推进」路径。要判定 E3 能否区分它们。",
      "",
      "要做：",
      "1. 先读 lead/codex_round_20261030/LEADER_battle/E3_SAMPLING_PLAN_REVIEWABLE.md（原文）。",
      "2. 读 lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md",
      "   与 E3_TRIGGER_N_CORRECTION_20261103.md。",
      "3. 对每条冻结路径，判定 E3 采样落在其上时的**栈签名**：",
      "   - 路径 A：睡眠/泵自旋（0x55D3AE->0x55D38D）→ 栈顶应在 Sleep 或 MessagePump 内",
      "   - 路径 B：(a) 出口（0x55D877）→ 栈顶应在 0x48D080 / 0x53B560 / LogicUpdate 内",
      "   - 路径 C：头部早退（0x55DEDB）→ 根本不在函数内（函数已返回）",
      "   - 路径 D：体内长循环 → 栈顶在循环体调用内",
      "   逐条给出**镜像内最近返回地址**（call+6）的具体 VA。",
      "4. ★ 关键：如果采样落在路径 A，栈上能否看到 Sleep？",
      "   Sleep 是外部 API，栈帧在 KERNEL32 内，镜像我方只能看到返回地址 0x55D3A2+? 之类。",
      "   请精确算出：若采样在 Sleep 内，镜像内最近返回地址是哪个 VA。",
      "5. 判定 E3 的判别力：哪些路径能被栈签名唯一确定，哪些不能。",
      "6. 给出更省的替代方案（若纯被动读几个全局就能区分，就不必上 E3）。",
    ].join("\n"),
  },
  {
    id: "M10",
    title: "冻结时长分布与 A02 睡眠节奏的可判别性",
    brief: [
      "A02 假说预测：帧冻结时会以 Sleep(500) + 泵 的节奏循环（约 2 次/秒）。",
      "这个预测有可观测后果：若冻结期间进程被采样的 CPU 时间极低，且唤醒节奏约 500ms，",
      "则是 A02 的旁证。",
      "",
      "要做：",
      "1. 从全量 measure_w*.json 里提取所有冻结段（按口径 B），列出时长。",
      "2. 统计冻结时长的**分布形态**：",
      "   - 是否在 0.5s 的整数倍附近聚集？（A02 预测：每 500ms 一次机会退出循环，",
      "     所以冻结时长应近似为 0.5s 的整数倍 +/- 泵耗时）",
      "   - 还是连续分布（无 0.5s 周期性）？",
      "3. ★ 这是 A02 的一个**可证伪预测**，请严格执行这个检验。",
      "   若分布明显偏离 0.5s 整数倍，则 A02 的「睡眠节奏」预测被削弱。",
      "4. 注意：帧冻结的「退出」不是因为循环退出，而是因为旗标被置 1。",
      "   旗标由 WM_ACTIVATEAPP 置 1，这是异步的，所以冻结时长本就不该是 0.5s 整数倍。",
      "   请自行判断这个逻辑，若你认为该预测本身不成立，请明说并解释。",
      "5. 给出你认为最有判别力的统计量。",
    ].join("\n"),
  },
];

const mines = await Promise.all(
  MINES.map(async (m) => {
    const a = agent(`数据矿工-${m.id}`, {
      system:
        "你是数据分析师 + 逆向分析员。你擅长从既有测量数据里挖出结构性结论。\n" +
        "你的第一职责是**如实**：样本不足就说样本不足，不要为了有结论而硬凑。\n" +
        "本仓多次因「看起来合理的量」犯错，请特别警惕循环定义与分母错位。",
    });
    const r = await a.ask<MiningResult>(
      `任务 ${m.id}：${m.title}\n\n` + `写域：${ABS}/${m.id}/\n\n` + RULES + "\n\n## 具体任务\n" + m.brief,
    );
    report({ id: m.id, headline: r.headline, level: r.level, a02: r.a02Impact });
    return { m, r };
  }),
);

phase("交叉核对：矿工结论之间是否一致");
const audit = agent("数据交叉核对员", {
  system:
    "你是交叉核对员。检查多位矿工的结论是否互相矛盾，特别是同一数字的不同算法。\n" +
    "不要调和，矛盾本身就是发现。",
});
const auditResult = await audit.ask<DocConflict[]>(
  `读 ${ABS}/M01 到 M10 的全部 REPORT.md。\n\n` +
    "## 你要做的\n" +
    "1. 找出所有数字不一致的地方（同一个量，不同矿工算出不同值）。\n" +
    "2. 对每处不一致，判定哪个正确、或两者口径不同（若口径不同，说明各自口径）。\n" +
    "3. 找出所有被标为 DATA_INSUFFICIENT 的，汇总成「还缺什么数据」。\n" +
    "4. 特别核对 M01 的冻结段数与台账 531 节的 1734 段是否吻合。\n" +
    `写进 ${ABS}/_DATA_AUDIT.md。`,
);

phase("汇总判定书");
const synth = agent("判定书撰写人", {
  system:
    "你是汇总员。把 10 个数据方向 + 交叉核对收敛成判定书。\n" +
    "不粉饰：能判定的写能判定，不能判定的明写不能。",
});
const md = await synth.ask<string>(
  `读 ${ABS}/M01..M10 的 REPORT.md 与 ${ABS}/_DATA_AUDIT.md。\n\n` +
    `各矿工自报：${JSON.stringify(
      mines.map((x) => ({ id: x.m.id, headline: x.r.headline, a02: x.r.a02Impact, level: x.r.level })),
    )}\n` +
    `交叉核对：${JSON.stringify(auditResult)}\n\n` +
    `写 ${ABS}/DATA_VERDICT_20261104.md，结构：\n` +
    "# 真机数据穷尽挖矿 · 判定书（2026-11-04）\n" +
    "## 一、一句话结论：A02 假说被数据支持、被证伪，还是数据不足以判定？\n" +
    "## 二、已复现的既有数字（与台账对账）\n" +
    "## 三、新发现\n" +
    "## 四、数据不足的部分与最小补充方案\n" +
    "## 五、文档勘误清单（逐条：文件 × 行 × 现文 × 应改为）\n" +
    "## 六、诚实账\n" +
    "然后全文返回。",
);

await artifact.markdown("data-verdict", md, {
  title: "真机数据挖矿判定书",
  description: "98 窗 + 4 份 wait-trace + 23 份 timeline 的穷尽分析，含 A02 假说的数据检验与文档勘误清单。",
  primary: true,
});

const insufficient = mines.filter((x) => x.r.a02Impact === "DATA_INSUFFICIENT").length;
return {
  conclusion:
    `10 个数据方向跑完：A02 假说的数据检验结论已出（${insufficient} 个方向判定数据不足）。` +
    `文档勘误清单见 artifact。`,
  findings: mines.map((x) => ({
    where: `${ROOT}/${x.m.id}/REPORT.md`,
    what: `${x.m.id} ${x.m.title}：${x.r.headline}`,
    evidence: `证据级别=${x.r.level}；A02 影响=${x.r.a02Impact}；${x.r.a02Reason}`,
    status: (x.r.level === "byte" ? "verified" : "unconfirmed") as "verified" | "unconfirmed",
    severity: "medium" as const,
  })),
  verified: ["selftest.py exit=0", "M01 的段数已与台账 531 节对账", "交叉核对员比对全部 10 份报告的数字"],
  notCovered: ["静态数据只读：无新真机趟", "A02 的运行期判定若数据不足，需补采样"],
};
