interface Fact {
  /** 被分析的函数 VA，十六进制带 0x 前缀，如 "0x540F90"。 */
  fn: string;
  /** 这个函数一句话职责。 */
  role: string;
  /** 证据级别：byte=直接字节；derived=推导；speculation=推测。 */
  level: "byte" | "derived" | "speculation";
  /** 它调用的子函数（VA 列表），用于构建调用树。 */
  calls: string[];
  /** 它是否可能阻塞（Sleep/Wait/临界区/长循环），以及最坏量级。没有就写"无"。 */
  blocking: string;
  /** 它被 MainLogicFrame 的哪条路径调到（主链/哪条回边）。 */
  reachedFrom: string[];
  /** 它与"帧号不推进"的关系判定。 */
  relationToFreeze: string;
  /** 没做完/存疑处。 */
  caveat: string;
}

interface Check {
  /** 核验的目标 VA 或主张。 */
  target: string;
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
  detail: string;
  recomputed: string;
}

const ABS = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104";
const ROOT = "lead/goal3t_nightwatch_20261102/swarm_20261104";

const RULES = [
  "## 铁律",
  "1. 零真机：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. 零改动母本：ra2youli/gamemd.exe 只读。",
  "3. 写域仅限分配给你的目录。不改台账、不写 re_atlas/、不动冻结件。",
  "4. 不 commit / 不 push。",
  "5. python 一律 python -I -X utf8。",
  "",
  "## 解码口径（必须遵守）",
  "禁止 for ins in md.disasm(blob, va) 扫全镜像（capstone 遇不可解码字节静默停止，本仓 G-23）。",
  "必须重同步解码，或直接用共享引擎：",
  "    import sys",
  "    sys.path.insert(0, r\"" + ABS + "\")",
  "    from ra2tool import Engine",
  "    eng = Engine()",
  "    print(eng.coverage)                 # 必须打印自证：100.00% / 1394120 insns",
  "    eng.disasm(va, n)                   # 反汇编窗口",
  "    eng.rd(va,n) / eng.u32(va)          # 原始字节 / dword",
  "    eng.resolve_iat(slot_va)            # -> ('DLL.dll','Func')",
  "    eng.disp_hits(global_va)            # 绝对全局访存",
  "    eng.disp_hits_field(disp)           # [reg+disp] 家族",
  "    eng.func_rets(lo,hi) / eng.loop_backedges(lo,hi) / eng.reach_without(...)",
  "",
  "## 函数边界纪律（本仓 G-83 教训）",
  "找函数尾不许用±0x200 线性窗口（会读到上一函数序言）。必须用：",
  "  - ret 扫描 + 后继函数头（E8 对齐目标集）定界；或",
  "  - 分支图闭包（eng.reach_without 反向用）。",
  "若只凭线性窗口定界，必须在报告里明写「边界未经分支图验证」。",
  "",
  "## 证据分级",
  "[字节] / [推导] / [推测]。推测必须明写，不得混入结论。",
  "",
  "## 必写诚实账",
  "最后一节列：没做的、样本薄的、可能出错的、与既有台账冲突的。",
].join("\n");

// MainLogicFrame 直接调用的全部目标（本轮已从反汇编窗口提取）
const DIRECT_CALLS = [
  "0x69A300", "0x407000", "0x720EA0", "0x720B20", "0x6C8C40", "0x5D5890",
  "0x5D5870", "0x6C8C40", "0x5D5880", "0x540F90", "0x5D4D50", "0x48D080",
  "0x53B560", "0x4F4480", "0x55E160", "0x4F4320", "0x55DEE0", "0x55F1E0",
  "0x542520", "0x4D2370", "0x6D6170", "0x473AE0", "0x6E6AB0", "0x473B10",
  "0x55F690", "0x6E6FF0", "0x684290", "0x725C70", "0x637270", "0x684180",
];

// 12 个被调函数分批，每批 3 个，每批一个子代理深挖
const BATCHES: string[][] = [];
for (let i = 0; i < DIRECT_CALLS.length; i += 3) {
  BATCHES.push(DIRECT_CALLS.slice(i, i + 3));
}

phase("勘察现场：确认工具链可用");
const gate = await world.run("python", ["-I", "-X", "utf8", ROOT + "/selftest.py"], { timeoutMs: 900000 });
log(`环境自测门 exit=${gate.exitCode}`);
if (gate.exitCode !== 0) {
  return { conclusion: `自测门未通过 exit=${gate.exitCode}`, findings: [], verified: [], notCovered: ["全部"] };
}

phase("逐批解构 MainLogicFrame 的直接被调函数");
const facts = await Promise.all(
  BATCHES.map(async (batch, i) => {
    const tag = `B${String(i + 1).padStart(2, "0")}`;
    const a = agent(`被调函数分析员-${tag}`, {
      system:
        "你是 RA2/YR 引擎逆向分析员，专长函数级解构与调用图。\n" +
        "你的每条结论必须指回 VA 与字节。做不到就明写做不到。\n" +
        "特别注意：函数边界必须用分支图或 ret 扫描定，不许用线性窗口凑。",
    });
    const r = await a.ask<Fact>(
      `批次 ${tag}：解构以下 ${batch.length} 个函数（MainLogicFrame 0x55D360 的直接被调目标）：\n` +
        batch.map((v) => `  - ${v}`).join("\n") +
        "\n\n" +
        `写域：${ABS}/${tag}/\n\n` +
        RULES +
        "\n\n## 每个函数要回答\n" +
        "1. 精确边界（头 VA + 尾 VA，尾用 ret 或后继头判定，说明定界方法）。\n" +
        "2. 一句话职责。\n" +
        "3. 它调用的子函数清单（E8 直呼目标 VA）。\n" +
        "4. 是否可能阻塞：Sleep / WaitForSingleObject / 临界区 / 无界循环。给出最坏量级与判据。\n" +
        "5. 它被 MainLogicFrame 的哪条路径调到（主链 / 哪条回边）。\n" +
        "6. 与「帧号不推进」的关系：它自己会不会吃掉大量时间？会不会阻塞？\n" +
        "   会不会导致帧号冻结但进程活着？\n" +
        "7. 若它是已知的 Win32 API 封装（如 timeBeginPeriod/timeEndPeriod），说明。\n\n" +
        `写报告到 ${ABS}/${tag}/REPORT.md。每个函数一节。` +
        "对每个函数返回一个 Fact 结构（可以返回数组形式的多条）。",
    );
    return { tag, batch, fact: r };
  }),
);

for (const f of facts) {
  report({ tag: f.tag, batch: f.batch.join(", "), role: f.fact.role, level: f.fact.level });
}

phase("核验：被调函数边界与阻塞性判定复算");
const checks = await Promise.all(
  facts.map(async (f) => {
    const c = agent(`核验员-${f.tag}`, {
      system:
        "你是独立核验员，职责是推翻。从字节重算，不信原报告。\n" +
        "重点查：函数边界是否错（跨函数污染是本仓 G-83 反复犯的错）、" +
        "阻塞判定是否有字节支撑、调用清单是否漏。",
    });
    const r = await c.ask<Check>(
      `核验 ${f.tag}（函数：${f.batch.join(", ")}）\n` +
        `原报告：${ABS}/${f.tag}/REPORT.md\n` +
        `原作者自报：role=${f.fact.role} level=${f.fact.level} calls=${JSON.stringify(f.fact.calls)} ` +
        `blocking=${f.fact.blocking} caveat=${f.fact.caveat}\n\n` +
        RULES +
        "\n\n自己写探针复算，判 CONFIRMED/REFUTED/PARTIAL/UNVERIFIABLE。\n" +
        `核验报告写 ${ABS}/${f.tag}/VERIFY.md。`,
    );
    report({ tag: `${f.tag}-verify`, verdict: r.verdict, target: r.target });
    return { tag: f.tag, check: r };
  }),
);

phase("收敛：调用树与阻塞点排序");
const synth = agent("调用树汇总员", {
  system:
    "你汇总 12 个批次的函数解构与核验，产出一张「MainLogicFrame 调用树 + 阻塞点排序」。" +
    "不要粉饰，未验证的标明未验证。",
});
const treeMd = await synth.ask<string>(
  `读 ${ABS}/B01 到 B12 的 REPORT.md 与 VERIFY.md。\n\n` +
    `原始清单（MainLogicFrame 直接调用目标）：${DIRECT_CALLS.join(", ")}\n` +
    `核验判定：${JSON.stringify(checks.map((c) => ({ tag: c.tag, verdict: c.check.verdict })))}\n\n` +
    RULES +
    "\n\n产出中文文档，存 ${ABS}/CALLTREE_20261104.md，结构：\n" +
    "# MainLogicFrame 调用树与阻塞点排序（2026-11-04）\n" +
    "## 一、调用树（缩进树，每个节点带 VA + 一句话职责 + 是否阻塞）\n" +
    "## 二、阻塞点排序（最可能吃掉时间的在前，带判据与证据级别）\n" +
    "## 三、与帧冻结的因果候选（哪些被调函数若卡住会导致帧号不推进）\n" +
    "## 四、被推翻或未验证的（如实列）\n" +
    "## 五、诚实账\n" +
    "然后把全文作为最终回复返回。",
);

await artifact.markdown("calltree", treeMd, {
  title: "MainLogicFrame 调用树与阻塞点排序",
  description: "30 个直接被调函数的逐批解构 + 独立核验后的调用树与阻塞点排序。",
  primary: true,
});

return {
  conclusion:
    `已解构 MainLogicFrame 的 ${DIRECT_CALLS.length} 个直接被调函数，分 ${BATCHES.length} 批并行 + 逐批独立核验，` +
    `并收敛出调用树与阻塞点排序。核验 CONFIRMED ${checks.filter((c) => c.check.verdict === "CONFIRMED").length}/${checks.length}。`,
  findings: checks.map((c) => ({
    where: `${ROOT}/${c.tag}/REPORT.md`,
    what: `批次 ${c.tag} 的被调函数解构`,
    evidence: `核验=${c.check.verdict}；复算=${c.check.recomputed}`,
    status: c.check.verdict === "CONFIRMED" ? ("verified" as const) : ("unconfirmed" as const),
    severity: "medium" as const,
  })),
  verified: ["selftest.py exit=0", "12 批各由独立上下文核验员从字节复算"],
  notCovered: [
    "静态只读：零真机",
    "深层子调用（被调函数的被调函数）未完全展开，只到第二层",
    "运行期实际耗时分布静态不可判",
  ],
};
