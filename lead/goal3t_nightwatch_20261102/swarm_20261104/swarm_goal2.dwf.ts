interface Goal2Finding {
  /** 子任务编号。 */
  id: string;
  /** 一句话结论。 */
  headline: string;
  /** 证据级别。 */
  level: "byte" | "derived" | "speculation";
  /** 关键 VA / 字节 / 数字。 */
  keyFacts: string[];
  /** 对 RC-4「正常退出硬门槛」的影响：SUPPORTS / UNDERMINES / NEUTRAL。 */
  rc4Impact: "SUPPORTS" | "UNDERMINES" | "NEUTRAL";
  /** 对「c″ 候选（EnableRC4ExitBail 开关默认关）」的设计影响。 */
  cprimeImpact: string;
  /** 诚实账。 */
  caveat: string;
}

interface VerifyOut {
  id: string;
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
  detail: string;
  recomputed: string;
}

const ABS = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104";
const ROOT = "lead/goal3t_nightwatch_20261102/swarm_20261104";

const RULES = [
  "## 铁律（本批尤严——涉及目标②退出线）",
  "1. 零真机：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. 零改动母本与冻结件：ra2youli/gamemd.exe、" ,
  "   lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py（6afe2711）、",
  "   _drive_c2_x_earlyclose.py（2e970eec）、harness7（d019e8be）、harness8_v4（38244d29）等",
  "   全部只读，一个字节都不许改。",
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
  "## 函数边界纪律（G-83）",
  "不许用 ±0x200 线性窗口定函数尾。用 ret 扫描 + E8 头集，或分支图闭包。",
  "",
  "## 证据分级",
  "[字节] / [推导] / [推测]。",
  "",
  "## 必写诚实账",
  "没做的、样本薄的、可能出错的、与既有台账冲突的。",
].join("\n");

phase("勘察现场");
const gate = await world.run("python", ["-I", "-X", "utf8", ROOT + "/selftest.py"], { timeoutMs: 900000 });
log(`环境自测门 exit=${gate.exitCode}`);
if (gate.exitCode !== 0) {
  return { conclusion: `自测门未通过 exit=${gate.exitCode}`, findings: [], verified: [], notCovered: ["全部"] };
}

const TASKS2: { id: string; title: string; brief: string }[] = [
  {
    id: "G01",
    title: "exitstate 0xA8EDD8 全生命周期：6 个写点的精确语义",
    brief: [
      "R-063a 已钉 exitstate 0xA8EDD8 的 raw abs32 命中恰 6 处：",
      "  0x6BE0B6 / 0x6BE0E1 / 0x6BEC72 / 0x6BEC8C / 0x777809 / 0x777818",
      "",
      "要做：",
      "1. 逐点解：是读还是写？写什么值（0/1/2/其它）？在什么条件分支下执行？",
      "2. 0x6BE0B6 / 0x6BE0E1 在宿主 0x6BE000 内（本仓记 0x6BE0E1 是 BAIL_SITE）。",
      "   解出这两点的完整上下文：什么事件触发、写入后发生什么。",
      "3. 0x777809 / 0x777818 在 WndProc 0x7775C0 内（WM_CLOSE / WM_DESTROY 链）。",
      "   解出这两点：哪个消息触发、写什么值、之后是否 PostQuitMessage。",
      "4. ★ 关键判定：exitstate 的值域语义。",
      "   本仓 D-12 记「观测到 1→2」（RC-4 相关）。请从字节判定：",
      "   - 值 0 / 1 / 2 各代表什么状态？",
      "   - 有没有代码**读** exitstate 并据此改变行为（例如见到 1 就挂住）？",
      "   若有，那才是「1→2 观测」能作为判据的前提。",
      "5. 判定：exitstate 是「状态标志」还是「控制开关」？这个区别决定 c″ 候选的设计。",
    ].join("\n"),
  },
  {
    id: "G02",
    title: "WndProc 关闭链：WM_CLOSE / WM_DESTROY / PostQuitMessage 完整路径",
    brief: [
      "主窗 WndProc = 0x7775C0（\"Yuri's Revenge\"，R-063a 已定名）。",
      "",
      "要做：",
      "1. 从 0x7775C0 的 uMsg 跳转表（0x777A80，槽 0..0x18）解出每个消息分支的职责。",
      "   特别关注：WM_CLOSE(0x10) / WM_DESTROY(0x2) / WM_QUIT / WM_SYSCOMMAND(0x112)。",
      "2. 解出完整的关闭链：谁发 WM_CLOSE（游戏自己还是用户点 X）？",
      "   WndProc 收到后做什么？是否 PostQuitMessage？退出码是什么？",
      "3. ★ 关键：正常退出（rc=0）时，这条链走的是哪条？",
      "   本仓 D-12 记 v4-e 趟 rc=0 / 168.6s / 清场干净。",
      "   请从字节给出「正常退出」的完整控制流。",
      "4. 异常退出（RC-4 现象的「未退出」）走的是哪条？哪一步没走到？",
      "5. 判定：WndProc 关闭链上有没有可能「收到 WM_CLOSE 但不退」的分支？",
      "   若有，它的条件是什么？这直接是 RC-4 的候选机制。",
    ].join("\n"),
  },
  {
    id: "G03",
    title: "宿主 A 0x6BB9A0：自旋等待环与退出 bail",
    brief: [
      "本仓记：宿主 A = 0x6BB9A0，含自旋等待环 0x6BDD03 / 0x6BDD2E：",
      "  call 0x5D4D50(泵); mov al,[0xA8ED80]; test al,al; je 自身",
      "即：A 轮询焦点旗标等「焦点恢复」。",
      "R-063a 判定：hwnd==0 后 WM_ACTIVATEAPP 永不被取用 ⇒ 旗标永不可置 1 ⇒ 两自旋环静态完备不可出。",
      "",
      "要做：",
      "1. 复核这两条自旋环的字节（0x6BDD03 / 0x6BDD2E），确认循环条件与退出条件。",
      "2. 解出宿主 A 的完整职责：它在游戏生命周期里处于什么阶段（启动？退出？）",
      "3. ★ 关键判定：A 的这两条自旋环，会不会就是 RC-4「未退出」的机制？",
      "   （进程卡在等焦点，永远不退）",
      "   若成立，给出：什么情况下会进入 A 的自旋环、什么情况下能出来。",
      "4. 判定：A 的自旋环与目标①的帧冻结（MainLogicFrame 的睡眠自旋）是**两个不同机制**还是同一个？",
      "   给出判据（两者都在等 0xA8ED80，但宿主不同、阶段不同）。",
      "5. 这个判定直接决定：①和②是否可能同源。",
    ].join("\n"),
  },
  {
    id: "G04",
    title: "RC-4 门槛的字节基础：「正常退出」到底需要什么",
    brief: [
      "本仓的 RC-4 硬门槛 = 「正常退出」。D-09 裁决要求确认：",
      "「c″ 不主动写退出状态值 ⇒『正常退出』与『观测到 1→2』不能未经核对视作同一判据，",
      "须确认补丁后自然退出路径是否仍经过写 2 点」。",
      "",
      "要做：",
      "1. 先定位「写 2 点」：exitstate 6 个写点里哪个写值 2？给出字节。",
      "2. 解出「自然退出路径」的完整控制流：从玩家点退出 -> ... -> 写 2 -> 进程结束。",
      "   逐跳给 VA。",
      "3. ★ 关键：这条路径上，写 2 之后还有几步？中间有没有可能卡住（即：写了 2 但没退出）？",
      "   若有，说明「写 2」不等于「正常退出」——这正是 D-09 要求核对的那一点。",
      "4. 判定：「正常退出」的充分条件是什么？必要条件是什么？",
      "   给出可判定的字节级定义（例如：进程 exit code 0 且 exitstate 最终值==2 且 ...）。",
      "5. 给出建议：若要做 c″，应该在哪里下开关、怎么保证「不主动写退出状态」。",
    ].join("\n"),
  },
  {
    id: "G05",
    title: "目标①与目标②是否同一根因：结构级判定",
    brief: [
      "★ 这是本批最重要的判定，直接决定三目标的工作是否需要合并。",
      "",
      "已知：",
      "  ① = 帧号冻结（CurrentFrame 不推进）2.56-24.73s，进程活着，**正常退出 rc=0**",
      "  ② = 主崩溃 / 异常退出（RC-4），进程**未退出**或崩溃",
      "",
      "本轮已解出：",
      "  - MainLogicFrame 有 2 条不经 inc 的 ret（0x55D877 / 0x55DEDB）",
      "  - MainLogicFrame 头部有睡眠自旋（等 0xA8ED80）",
      "  - 宿主 A 0x6BB9A0 有两条自旋环也等 0xA8ED80",
      "",
      "要做：",
      "1. 把「等 0xA8ED80」的全部等待点列全（全镜像搜 0xA8ED80 的 45 个读点，",
      "   按「是否在循环内」分类）。",
      "2. 判定这些等待点分几族：",
      "   - 帧内自旋（MainLogicFrame 内的）",
      "   - 退出前自旋（宿主 A 内的）",
      "   - 渲染/绘制门（WM_PAINT 等）",
      "   - 其它",
      "3. ★ 核心判定：同一个旗标 `0xA8ED80` 被「帧推进」和「退出流程」两处同时等待，",
      "   这意味着什么？",
      "   - 若旗标=1 是常态：那两处都不会卡；①的冻结就不是这个机制。",
      "   - 若旗标=0 是常态：那帧和退出都会卡，①和②同源。",
      "   请从字节判定：正常情况下（局内前台对战中），旗标应为什么值？",
      "4. 给出「①与②同源 / 不同源 / 部分重叠」的判定，附完整判据链。",
      "5. 若同源，指出这对三目标工作组织的影响（一句话，不要展开）。",
    ].join("\n"),
  },
  {
    id: "G06",
    title: "全镜像 [0xA8ED80] 45 个读点的功能分类",
    brief: [
      "R-063a 已做初步分类，但本任务要**独立重做**并给出更细的判定。",
      "",
      "要做：",
      "1. 用 eng.disp_hits(0xA8ED80) 拿全部 46 处（45 读 + 1 写）。",
      "2. 逐个判定它所属的函数（用 E8 头集 + ret 扫描定界，不许线性窗）。",
      "3. 按「读法」分类：",
      "   - `test al,al` + `je/jne` 紧跟（条件门）",
      "   - 在循环体内（自旋等待）",
      "   - 只是读到寄存器后传参/存储（传值）",
      "   - 比较具体值（cmp al,1 等）",
      "4. 按「函数职责」分类：帧推进 / 退出流程 / 渲染绘制 / 焦点处理 / 其它。",
      "5. ★ 输出一张表：VA × 宿主函数 × 读法 × 职责 × 是否在循环内。",
      "   这张表是「旗标语义」的最终依据。",
      "6. 判定：45 个读点里，有几个真的会把程序**卡住**（在循环里等它变）？",
    ].join("\n"),
  },
  {
    id: "G07",
    title: "c″ 候选（EnableRC4ExitBail）的字节级设计依据",
    brief: [
      "D-09 裁决：允许制作 c″ 独立候选副本（保留母本），",
      "独立 `EnableRC4ExitBail` 开关默认关，便于隔离对照与回退。",
      "",
      "要做（纯设计，不实现、不改任何文件）：",
      "1. 先读本仓已有的 candidate 件（只读）找设计先例：",
      "   lead/qc161_u0400_trip/codex_e12_e5_20261030/candidate/_drive_c2_x_e12.py",
      "   （看它的开关设计、自验、回退方式）",
      "2. 分析：如果要加一个「退出 bail」开关，最有字节依据的插入点在哪？",
      "   - 宿主 A 0x6BB9A0 的自旋环（0x6BDD03 / 0x6BDD2E）？",
      "   - WndProc 关闭链？",
      "   - exitstate 写点？",
      "   逐个评估：侵入性、可回退性、是否改变语义。",
      "3. ★ 关键约束（D-09 原文）：c″ **不主动写退出状态值**。",
      "   所以任何「替游戏写 exitstate」的方案都不合格。请据此筛选。",
      "4. 给出 2-3 个候选插入点，每个附：",
      "   - 精确 VA 与预期字节改动（只描述，不实施）",
      "   - 需要的开关形态（INI 键？内存 patch？）",
      "   - 回退方式",
      "   - 风险（会不会引入新死锁 / 会不会掩盖真实崩溃）",
      "5. 明确写出：这些方案**都未经验证**，只是设计候选。",
    ].join("\n"),
  },
  {
    id: "G08",
    title: "冻结与崩溃的时序区分：哪些观测能分开两者",
    brief: [
      "目标①的冻结趟**正常退出**（rc=0），目标②的挂死趟**未退出**。",
      "但本仓记录过「C/L3 先停摆后消失」（H-5），形态介于两者之间。",
      "",
      "要做：",
      "1. 读本仓相关记载：",
      "   lead/GOAL_THREE_TARGETS_20261018.md 的 401/402 节（H-5/H-6 定谳）",
      "   lead/qc161_u0400_trip/S401_H5_VERDICT.md、S402_H6_VERDICT.md",
      "2. 梳理已有的观测通道与它们能区分什么：",
      "   - 帧号（冻结 vs 推进）",
      "   - exitstate（0/1/2）",
      "   - 进程存活 + 退出码",
      "   - WER / 事件日志",
      "   - 泵计数 0xAA0430",
      "   - CPU 占用",
      "   - 窗口响应性",
      "3. ★ 给出**判别矩阵**：每种现象组合对应哪种结局（冻结后恢复 / 冻结后正常退出 / " +
      "挂死不退 / 崩溃）。",
      "4. 判定：本仓已有的「C/L3 先停摆后消失」属于哪一格？现有数据够判吗？",
      "5. 给出：要唯一确定结局，最少需要采哪几个量。",
    ].join("\n"),
  },
];

const found = await Promise.all(
  TASKS2.map(async (t) => {
    const a = agent(`退出线分析员-${t.id}`, {
      system:
        "你是 RA2/YR 引擎逆向分析员，专注退出流程与崩溃路径。\n" +
        "你的结论会用于决定是否给游戏打补丁，所以每条都必须有字节支撑。\n" +
        "做不到就明写做不到——错误的补丁方案比没有方案更危险。",
    });
    const r = await a.ask<Goal2Finding>(
      `任务 ${t.id}：${t.title}\n\n` + `写域：${ABS}/${t.id}/\n\n` + RULES + "\n\n## 具体任务\n" + t.brief,
    );
    report({ id: t.id, headline: r.headline, level: r.level, rc4: r.rc4Impact });
    return { t, r };
  }),
);

phase("逐份核验");
const vs = await Promise.all(
  found.map(async (x) => {
    const c = agent(`核验员-${x.t.id}`, {
      system:
        "你是独立核验员，职责是推翻。从字节重算，不信原报告。\n" +
        "特别查：exitstate 写点是否数对、写值是否读对、控制流是否漏分支。",
    });
    const r = await c.ask<VerifyOut>(
      `核验 ${x.t.id}：${x.t.title}\n` +
        `原报告：${ABS}/${x.t.id}/REPORT.md\n` +
        `自报：${x.r.headline} | level=${x.r.level} | rc4Impact=${x.r.rc4Impact}\n` +
        `keyFacts=${JSON.stringify(x.r.keyFacts)}\n` +
        `cprimeImpact=${x.r.cprimeImpact}\n\n` +
        RULES +
        "\n\n" +
        `写 ${ABS}/${x.t.id}/VERIFY.md。`,
    );
    report({ id: `${x.t.id}-verify`, verdict: r.verdict });
    return { id: x.t.id, check: r };
  }),
);

phase("收敛目标②判定书");
const synth = agent("退出线汇总员", {
  system:
    "你是汇总员。把目标②（退出/崩溃）这条线的 8 个方向收敛成判定书。\n" +
    "记住：RC-4 是硬门槛，「正常退出」的判定口径不能放松。\n" +
    "任何「让程序看起来退出了」的方案都必须被明确标注为「不满足硬门槛」。",
});
const md = await synth.ask<string>(
  `读 ${ABS}/G01..G08 的 REPORT.md 与 VERIFY.md。\n\n` +
    `自报：${JSON.stringify(found.map((x) => ({ id: x.t.id, headline: x.r.headline, rc4: x.r.rc4Impact, level: x.r.level })))}\n` +
    `核验：${JSON.stringify(vs.map((v) => ({ id: v.id, verdict: v.check.verdict })))}\n\n` +
    `写 ${ABS}/GOAL2_VERDICT_20261104.md，结构：\n` +
    "# 目标②（退出/崩溃）判定书（2026-11-04）\n" +
    "## 一、一句话结论\n" +
    "## 二、exitstate 与退出链的字节事实（含全部 VA 与写值）\n" +
    "## 三、「正常退出」的可判定定义\n" +
    "## 四、RC-4 现象的机制候选与排序\n" +
    "## 五、①与②是否同源（判定 + 判据链）\n" +
    "## 六、c″ 候选的设计依据与红线（不实施）\n" +
    "## 七、诚实账：本判决未改变 RC-4 门槛、未做任何真机验证\n" +
    "然后全文返回。",
);

await artifact.markdown("goal2-verdict", md, {
  title: "目标② 退出/崩溃判定书",
  description: "exitstate 全生命周期、WndProc 关闭链、宿主 A 自旋环、①与②同源性判定、c″ 设计红线。",
  primary: true,
});

return {
  conclusion: `目标② 8 个方向跑完并核验：${vs.filter((v) => v.check.verdict === "CONFIRMED").length}/8 CONFIRMED。RC-4 门槛未变，未做真机验证。`,
  findings: found.map((x) => ({
    where: `${ROOT}/${x.t.id}/REPORT.md`,
    what: `${x.t.id} ${x.t.title}：${x.r.headline}`,
    evidence: `级别=${x.r.level}；RC-4 影响=${x.r.rc4Impact}；核验=${vs.find((v) => v.id === x.t.id)?.check.verdict}`,
    status: (x.r.level === "byte" ? "verified" : "unconfirmed") as "verified" | "unconfirmed",
    severity: "high" as const,
  })),
  verified: ["selftest.py exit=0", "8 份各由独立上下文核验员复算"],
  notCovered: ["零真机验证", "c″ 候选仅为设计，未实施未验证", "RC-4 门槛不受本判决影响"],
};
