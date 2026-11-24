interface Finding {
  /** 子任务编号。 */
  id: string;
  /** 一句话结论，不超过 60 字。 */
  headline: string;
  /** 证据级别：byte / derived / speculation。 */
  level: "byte" | "derived" | "speculation";
  /** 关键 VA + 数值，每条一条。 */
  keyFacts: string[];
  /** 真机可判别的预测（VA + 期望值）。做不到写"未给出"。 */
  prediction: string;
  /** 与既有台账冲突处，无则写"无"。 */
  conflicts: string;
  /** 完成度。 */
  status: "full" | "partial" | "failed";
}

interface Check {
  id: string;
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
  detail: string;
  recomputed: string;
}

const ABS = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104";
const ROOT = "lead/goal3t_nightwatch_20261102/swarm_20261104";

const RULES = [
  "## 铁律",
  "1. 零真机：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. 零改动母本：ra2youli/gamemd.exe 只读。真机数据 json 也只读。",
  "3. 写域仅限分配给你的目录。不改台账、不写 re_atlas/、不动冻结件。",
  "4. 不 commit / 不 push。",
  "5. python 一律 python -I -X utf8。路径用**绝对路径**（会话 cwd 会漂移）。",
  "",
  "## 解码口径（本仓血泪教训，已犯多次）",
  "禁止 for ins in md.disasm(blob, va) 扫全镜像——capstone 遇不可解码字节静默停止，",
  "会造出「0 处命中」的假零（本仓 G-23）。必须重同步解码，或直接用共享引擎：",
  "    import sys",
  "    sys.path.insert(0, r\"" + ABS + "\")",
  "    from ra2tool import Engine",
  "    eng = Engine()",
  "    print(eng.coverage)             # 必须打印自证：99.998376% / 1394120 insns / 66 resync",
  "    eng.disasm(va, n) / eng.rd(va,n) / eng.u32(va)",
  "    eng.resolve_iat(slot_va)        # -> ('DLL.dll','Func')",
  "    eng.disp_hits(global_va)        # 绝对全局访存 -> [(va,'W'|'R',mnem,op_str)]",
  "    eng.disp_hits_field(disp)       # [reg+disp] 任意基址家族",
  "    eng.func_rets(lo,hi)            # (rets, succ)",
  "    eng.reach_without(head,hi,cut_lo,cut_hi)",
  "    eng.loop_backedges(lo,hi)",
  "",
  "## 函数边界纪律（G-83）",
  "找函数尾不许用 ±0x200 线性窗口。必须用 ret 扫描 + E8 对齐头集，或分支图闭包。",
  "若只凭线性窗定界，必须明写「边界未经分支图验证」。",
  "",
  "## 证据分级",
  "[字节] / [推导] / [推测]。推测必须明写，禁止混入结论。",
  "",
  "## 必写诚实账",
  "报告最后一节列：没做的、样本薄的、可能出错的、与既有台账冲突的。",
  "",
  "## 第一批已定谳（作为你的起点，不许擅自推翻，除非给出字节反证）",
  "- P01：0x55D877 出口 = 单机局挂起门；[GameLogic+0x62C] = ScenarioClass 挂起深度计数器",
  "  （inc 0x684174 / dec 0x684195 / 复位 0x6836D2），非暂停布尔/同步/跳帧",
  "- P02：焦点旗标等待环 = 失焦等待**非死锁**（泵内 0x5D4E47 call [0x7E14C0]=DispatchMessageA",
  "  可送达激活沿解环）；R-063a「焦点旗标」对，clock_frame_loop.md「快进」命名被字节否定",
  "- P03：CurrentFrame 10 写点全归因；唯一读改写=0x55DE7E->0x55DE81 成立；",
  "  **9/10 写点数据流恒 0**（字面 3 处 + xor 清零 6 处）；",
  "  另有第 11 条间接写路径（push 0xA8ED84 -> 存档序列化虚方法 0x67F819/0x67FA19）；",
  "  W10 宿主 0x7970D0 是死代码（全镜像零静态引用）；",
  "  ★ 发现 0x55CFD0 = 四旗标状态机（写块 0x55D123/0x55D1B1/0x55D219/0x55D25C），",
  "  MLF 里四旗标任一非零 -> jne 0x55DEC8 -> 跳过 inc -> ret 0x55DEDB",
  "- P04：A02 假说不能被既有数据判定（15229 个 tick 采样无一为 0；",
  "  Δf==0 的 11263 对全落在 menu_idle/zeroed 两类，活游戏停帧候选=0）；判定 DATA_INSUFFICIENT",
  "- P05：4 份 wait-trace 全是多次型慢爬，**无一处 >=2s 停摆**（最长静止窗 1.2387s）；",
  "  v4-b 深滞=2.6 帧/s 连续慢泵；单通道数据不能区分睡眠自旋与 (a) 出口",
  "",
  "## 已知的张力（第二批要处理）",
  "P01/P03 给出了「帧号可被跳过 inc」的静态路径，但 P05 的实测数据显示停滞是**慢爬**而非冻结。",
  "两者的张力是第二批的核心。不要假定哪一方对。",
  "",
  "## 产出",
  "写 <你的目录>/REPORT.md，中文，结构：",
  "# <编号> · <一句话结论>",
  "## 0. 现场自证（eng.coverage + tasklist 无 gamemd）",
  "## 1. 结论（每条带证据级别）",
  "## 2. 证据（逐条 VA + 字节 + 推导链）",
  "## 3. 与本仓既有记载的对账",
  "## 4. 诚实账",
  "## 5. 复算入口",
].join("\n");

phase("勘察现场：确认工具链与冻结基线可用");
const gate = await world.run("python", ["-I", "-X", "utf8", ABS + "/selftest.py"], { timeoutMs: 900000 });
log(`环境自测门 exit=${gate.exitCode}`);
if (gate.exitCode !== 0) {
  return {
    conclusion: `环境自测门未通过（exit=${gate.exitCode}），未派发任何分析任务。`,
    findings: [],
    verified: [`selftest.py exit=${gate.exitCode}`],
    notCovered: ["全部——工具链未就绪"],
  };
}

phase("第二批 5 个方向并行取证");
const BATCH2: { id: string; title: string; brief: string }[] = [
  {
    id: "Q01",
    title: "四旗标状态机 0x55CFD0 全解：谁是冻结的真正扳机",
    brief: [
      "P03 发现 MLF 有一道**四旗标门**，并且发现 0x55CFD0 是旗标状态机。",
      "本任务要把它彻底解透——这可能是帧号不推进的**主要**机制（比睡眠自旋更符合实测）。",
      "",
      "已知字节（Leader 已亲验）：",
      "  0x55CFD0  mov eax,[0xA8ED84]     ; CurrentFrame",
      "  0x55CFD5  sub esp,0x7C",
      "  0x55CFD8  test eax,0x3FF         ; ★ 帧号低 10 位（每 1024 帧一次）",
      "  0x55CFDF  jmp 0x55D059",
      "  四个「清零三旗标」块（Leader 已亲验字节）：",
      "    0x55D123 mov [0xA8ECD0],bl / [0xA83D49],bl / [0x8B41C0],bl",
      "    0x55D1B1 同上（写序不同）",
      "    0x55D219 同上",
      "    0x55D25C 同上",
      "",
      "要做：",
      "1. 完整解出 0x55CFD0 的函数边界（头/尾，用 ret 扫描 + E8 头集）与全部输入。",
      "2. ★ 解出四旗标门：MLF 里读 [0xA8ECD0]/[0xA83D49]/[0x8B41C0]/[0xA83D48] 的位置，",
      "   以及「任一非零 -> 跳过 inc」的确切字节。给出全部 4 个读点与判定指令。",
      "3. 答：这四个旗标各是什么语义？谁写它们（除 0x55CFD0 的清零块外）？",
      "   用 eng.disp_hits 逐个查写点，逐个解上下文。",
      "4. ★ 核心判定：这条门若为真，则「帧号不推进」不需要睡眠自旋或 (a) 出口——",
      "   只要任一旗标非零就会跳过 inc。那么：",
      "   - 这些旗标在什么条件下非零？（正常战斗中会吗？）",
      "   - 非零持续多久？（一帧？多帧？直到某个事件？）",
      "   这直接决定它能否解释「冻结 2.56-24.73s」。",
      "5. 给出真机判别式：读哪几个 VA 的什么值能判定这条门是否被触发。",
    ].join("\n"),
  },
  {
    id: "Q02",
    title: "慢爬 vs 冻结的调和：P05 实测与 P01/P03 静态路径的张力",
    brief: [
      "★ 这是第二批最重要的任务。第一批留下了一个未解张力：",
      "  - P01/P03 给出了「帧号可被跳过 inc」的静态路径（0x55D877 / 0x55DEDB / 四旗标门）",
      "  - P05 的实测（400Hz wait-trace）显示停滞是**多次型慢爬**，无一处 >=2s 停摆",
      "  两者若都对，则「跳过 inc」的路径实际很少触发，或触发但持续时间极短。",
      "",
      "要做：",
      "1. 先读 ${ABS}/P05/REPORT.md 与 ${ABS}/P01/REPORT.md、${ABS}/P03/REPORT.md。",
      "2. ★ 从字节判定：「跳过 inc」的每条路径，其**单次跳过的持续代价**是多少？",
      "   - 0x55DEDB 早退：跳过一次 inc = 少推 1 帧。持续多久取决于调用者多久再调一次。",
      "   - 0x55D877 挂起门：不推帧，但世界更新照跑。持续多久取决于 +0x62C 何时归零。",
      "   - 四旗标门：跳过 inc 后置 [0xABCD58]=0 然后 ret。下次调用仍可能再跳。",
      "   逐条算：单次跳过 = 丢几帧？若连续 N 次 = 丢 N 帧？",
      "3. ★ 关键换算：把「丢帧」换算成「观测到的停滞时长」。",
      "   - 若正常帧率 31fps，丢 1 帧 = 32ms 停滞。",
      "   - P05 观测到的最长静止窗 1.2387s ⇒ 约 38 帧连续丢失？还是慢爬（每帧间隔变长）？",
      "   请用 P05 的原始数据（poll_count / 帧号序列）算出：**v4-b 的深滞段到底是丢帧还是变慢**。",
      "   判据：若帧号增量均匀分布在长间隔上（Δf 小但非零且持续推进）⇒ 变慢；",
      "   若帧号长时间完全不变后突然跳 ⇒ 丢帧。",
      "4. ★ 给出结论：P05 的「慢爬」能否被「频繁短暂跳过 inc」解释？",
      "   若能，说明这是同一机制的不同时间尺度表现；若不能，说明还有未知机制。",
      "5. 这个判定直接决定目标①的下一步方向。",
    ].join("\n"),
  },
  {
    id: "Q03",
    title: "第 11 条间接写路径：存档序列化与帧号跳变",
    brief: [
      "P03 发现：除 10 个 disp 写点外，还有一条**间接写**路径——",
      "  0x67F819 push 0xA8ED84（槽 +0x10）",
      "  0x67FA19 push 0xA8ED84（槽 +0xC）",
      "把 CurrentFrame 当 4 字节缓冲交给流对象虚方法，属存/读档字段序列化。",
      "读档侧会把存档中的帧值写进 CurrentFrame（帧号跳变为存档值）。",
      "两宿主 0x67F7E0 / 0x67F9C0 序列化同一组全局",
      "（[0xA8ED78]/[0xA83D4C]/[0xA8ED84]/[0x89EA40]/[0x89EC28]/[0x89ECC0]/[0xA8E3A8]/[0xB07784]）。",
      "",
      "要做：",
      "1. 独立复核这两个 push 站点与宿主函数，确认槽方向（读还是写 CurrentFrame）。",
      "   P03 自报「槽方向映射为推测」，这一点必须钉实——它决定「跳变」还是「快照」。",
      "2. 解出流对象虚方法的实现（槽 +0xC / +0x10 指向哪个函数）。",
      "3. ★ 判定：读档时 CurrentFrame 被写成存档值，会造成：",
      "   - 帧号**回退**（存档帧号 < 当前）⇒ 观测上看到 Δf<0",
      "   - 帧号**前跳**（存档帧号 > 当前）⇒ 观测上看到 Δf 大正跳",
      "   本仓 P04 记过 Δf<0 有 4 例（-3798/-3613/-4019/-5700）。",
      "   这些负跳变能否被这条路径解释？请对账。",
      "4. 判定：这条路径能否解释「f[0]==0 加载段型」窗（本仓 §525 的判别规则）？",
      "5. 给出真机判别式。",
    ].join("\n"),
  },
  {
    id: "Q04",
    title: "最小补充采样方案设计：要判定机制还缺什么数据",
    brief: [
      "P04 判 DATA_INSUFFICIENT。本任务设计**最小**补充采样方案（不执行，只设计）。",
      "",
      "要做到「能判定」而非「多采点」：先想清楚要判别什么，再倒推需要什么量。",
      "",
      "要做：",
      "1. 先读 ${ABS}/P04/REPORT.md 与 ${ABS}/P05/REPORT.md，理解现有数据的缺口。",
      "2. ★ 列出**全部待判别的假设**（第二批的 Q01/Q02/Q03 各自需要什么判据）。",
      "3. 对每个假设，给出「能证实的最小读数集」与「能证伪的最小读数集」。",
      "   每个读数写明：VA、数据类型（u32/byte）、期望值范围、采样率要求。",
      "4. ★ 关键约束：",
      "   - 采样必须是被动只读（ReadProcessMemory），不得注入/挂 Hook/改内存。",
      "   - 现有 harness 已采的量：frame(0xA8ED84)、tick(0xA8ED80)、exitstate(0xA8EDD8)、",
      "     hwnd(0xB73550)、pump 计数(0xAA0430)、ws_kb、hook6 字节。",
      "   - 若要新增读数，必须说明是**新增 VA** 还是**提高采样率**。",
      "5. 给出方案 A（最小：只加 VA 不加率）与方案 B（加率）的对比：",
      "   各自能判定什么、不能判定什么、代价（趟时长、风险）。",
      "6. ★ 明确写出：这些方案**都未执行**，只是设计。不要写代码，不要跑真机。",
    ].join("\n"),
  },
  {
    id: "Q05",
    title: "ATLAS 与 clock_frame_loop 的完整勘误清单（可直接施用）",
    brief: [
      "第一批已确认两处必改勘误，本任务盘点**全部**需要改的地方，产出可直接施用的清单。",
      "",
      "已确认：",
      "  勘误1：docs/re/ARCHITECTURE_ATLAS.md §8.4 散文「全镜像唯一定常递增写入点位于 0x0055DE73」",
      "         → 0x55DE73 是 mov edx,[0xA8ED84]（读）；正确应为 inc 0x55DE7E + 写回 0x55DE81。",
      "         同节代码块标注的就是 0x55DE7E，散文与代码自相矛盾。",
      "  勘误2：docs/re/clock_frame_loop.md 称 0xA8ED80 = 「快进/跳过 Sleep 标志」",
      "         → 字节显示旗标=1 时跳过**整个 Sleep+泵循环**（0x55D385 jne 0x55D3BB），",
      "           且唯一写者是 WndProc 的 WM_ACTIVATEAPP（焦点语义）。R-063a 已定谳为焦点旗标。",
      "",
      "要做：",
      "1. 逐份读这三份文档的帧循环相关章节，与字节对照，找出**所有**不符处：",
      "   docs/re/ARCHITECTURE_ATLAS.md（§8.4 / §8.5 / §9 相关）",
      "   docs/re/clock_frame_loop.md（全文）",
      "   REVERSE_ENGINEERING_AND_PATCHES.md（帧号相关行，如 :497、:1407）",
      "2. ★ 特别注意 clock_frame_loop.md 的 §3.2 伪码，逐条核：",
      "   - 「if (![0xA8E9A0]) return」→ 字节是 0x55D371 je 0x55DECF（早退到函数尾）",
      "   - 「if (![0xA8ED80]) { Sleep... }」→ 需确认是循环而非单次",
      "   - 「if (CurrentFrame >= [0xA8E2E4]) 0x69A300(state)」→ 核 0x55D3C0 附近",
      "   - 伪码是否漏了 0x55D877 挂起门与四旗标门？",
      "3. 产出清单，每条形如：",
      "   文件 | 行号或章节 | 现文（原文摘录） | 应改为（精确措辞） | 依据（VA + 字节）",
      "4. ★ 只产出清单，**不要改任何文档**（写域限制）。",
      "5. 对每条判定严重度：会误导读者做错实验的=高；只是措辞不精确=低。",
    ].join("\n"),
  },
];

const b2 = await Promise.all(
  BATCH2.map(async (t) => {
    const a = agent(`分析员-${t.id}`, {
      system:
        "你是 RA2/YR 引擎逆向分析员，擅长 x86 反汇编、CFG 分析、数据流追踪。\n" +
        "你的每条结论都必须指回具体 VA 与十六进制字节，或指回具体数据行。\n" +
        "禁止把猜测写成结论。做不到就明写做不到。\n" +
        "发现与既有文档冲突必须指出，不得沉默迁就。\n" +
        "所有文件写入只允许在分配给你的目录内。",
    });
    const v = await a.ask<Finding>(
      `任务 ${t.id}：${t.title}\n\n` + `你的写域：${ABS}/${t.id}/\n\n` + RULES + "\n\n## 具体任务\n" + t.brief,
    );
    return { task: t, r: v };
  }),
);

for (const x of b2) report({ id: x.task.id, headline: x.r.headline, level: x.r.level, status: x.r.status });

phase("第二批逐份独立核验");
const b2c = await Promise.all(
  b2.map(async (x) => {
    const c = agent(`核验员-${x.task.id}`, {
      system:
        "你是独立核验员。你的职责是推翻，不是确认。\n" +
        "从字节/数据重新复算，不要相信原报告的结论。\n" +
        "复现不出来就判 REFUTED 或 UNVERIFIABLE，并说明你读了哪些字节/数据。\n" +
        "特别检查：地址读错、字节数数错、CFG 漏分支、口径偷换、样本当总体、循环定义。",
    });
    const r = await c.ask<Check>(
      `核验 ${x.task.id}：${x.task.title}\n\n` +
        `原报告：${ABS}/${x.task.id}/REPORT.md\n` +
        `自报：headline=${x.r.headline}\nlevel=${x.r.level}\n` +
        `keyFacts=${JSON.stringify(x.r.keyFacts)}\n` +
        `prediction=${x.r.prediction}\nconflicts=${x.r.conflicts}\nstatus=${x.r.status}\n\n` +
        RULES +
        "\n\n自己写探针复算每个 keyFact，判 CONFIRMED/REFUTED/PARTIAL/UNVERIFIABLE。" +
        `核验报告写 ${ABS}/${x.task.id}/VERIFY.md。`,
    );
    return { id: x.task.id, c: r };
  }),
);

phase("第二批收敛");
const s2 = agent("第二批汇总员", {
  system:
    "你是汇总员。把 5 个方向的结论与核验收敛成判定。不粉饰：硬的是硬的，破的是破的。\n" +
    "特别要回答：第一批留下的「慢爬 vs 冻结」张力，这一批解决了没有。",
});
const sum2 = await s2.ask<string>(
  `读 ${ABS}/Q01..Q05 的 REPORT.md 与 VERIFY.md。\n\n` +
    `自报：${JSON.stringify(b2.map((x) => ({ id: x.task.id, headline: x.r.headline, level: x.r.level, status: x.r.status })))}\n` +
    `核验：${JSON.stringify(b2c.map((c) => ({ id: c.id, verdict: c.c.verdict })))}\n\n` +
    `写 ${ABS}/BATCH2_VERDICT.md，结构：\n` +
    "# 第二批判定（Q01-Q05）\n" +
    "## 一、一句话结论\n" +
    "## 二、★ 「慢爬 vs 冻结」张力：解决了 / 部分解决 / 仍未解\n" +
    "## 三、四旗标门是否为主要机制（判定 + 判据）\n" +
    "## 四、已证实（含 VA 与字节）\n" +
    "## 五、被推翻/降级\n" +
    "## 六、最小补充采样方案（Q04 摘要）\n" +
    "## 七、文档勘误清单（Q05 摘要，可直接施用）\n" +
    "## 八、诚实账\n全文返回。",
);

await artifact.markdown("batch2", sum2, {
  title: "第二批判定（Q01-Q05）",
  description: "四旗标状态机、慢爬 vs 冻结张力、存档间接写、最小采样方案、文档勘误清单。",
  primary: true,
});

return {
  conclusion:
    `第二批 5 个方向完成并逐份核验：` +
    `${b2c.filter((c) => c.c.verdict === "CONFIRMED").length}/5 CONFIRMED。判定书见 artifact。`,
  findings: b2.map((x) => ({
    where: `${ROOT}/${x.task.id}/REPORT.md`,
    what: `${x.task.id} ${x.task.title}：${x.r.headline}`,
    evidence: `级别=${x.r.level}；核验=${b2c.find((c) => c.id === x.task.id)?.c.verdict}；复算=${b2c.find((c) => c.id === x.task.id)?.c.recomputed}`,
    status: (b2c.find((c) => c.id === x.task.id)?.c.verdict === "CONFIRMED"
      ? "verified"
      : "unconfirmed") as "verified" | "unconfirmed",
    severity: "medium" as const,
  })),
  verified: ["selftest.py exit=0", "5 份各由独立上下文核验员从字节复算"],
  notCovered: [
    "静态只读：零真机、零母本改动",
    "Q04 的采样方案未执行",
    "Q05 的勘误清单未施用（写域限制）",
  ],
};
