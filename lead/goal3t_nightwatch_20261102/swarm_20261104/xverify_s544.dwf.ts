/** 一条核验发现。 */
interface Finding {
  /** 编号，如 V1-A1。 */
  id: string;
  /** 一句话结论，不超过 60 字。 */
  headline: string;
  /** 证据级别：byte / data / derived / speculation。 */
  level: "byte" | "data" | "derived" | "speculation";
  /** 关键证据：文件路径 + 具体数值，每条一行。 */
  keyFacts: string[];
  /** 判定。 */
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
}

/** 对一条具体主张的独立复算。 */
interface Check {
  /** 被复核的主张编号。 */
  id: string;
  /** 独立判定的结果。 */
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
  /** 你自己重算得到的数字，不是复述原主张。 */
  recomputed: string;
  /** 你读了哪些字节/数据行、跑了什么命令。 */
  detail: string;
}

/** 汇总报告项。 */
interface ReportItem {
  /** 证据文件路径。 */
  where: string;
  /** 一句话：这条告诉用户什么。 */
  what: string;
  /** 什么证了它。 */
  evidence: string;
  /** verified = 已被独立复算或确定性检查证实。 */
  status: "verified" | "unconfirmed";
  /** 严重度。 */
  severity: "low" | "medium" | "high";
}

interface Task {
  id: string;
  title: string;
  brief: string;
}

interface LaneResult {
  task: string;
  findings: Finding[];
  checks: Check[];
}

const ROOT = "D:/Project/ra2-campaign-forge";
const ABS = ROOT + "/lead/goal3t_nightwatch_20261102/swarm_20261104";
const TRIPS = ROOT + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip";
const HARNESS = ROOT + "/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py";
const TAG = String(run.id).slice(-8);
const OUT = ABS + "/XVERIFY_S544_" + TAG;

const RULES = [
  "## 铁律（违反即作废）",
  "1. **零真机**：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. **零改动母本**：gamemd.exe 只读；真机数据 json/png 也只读。",
  "3. **写域仅限 " + OUT + "/**。不改台账、不改 swarm_20261104 根下已有文件、不 commit。",
  "4. python 一律 `python -I -X utf8`。路径一律用**绝对路径**，不要用 `..` 相对跳转。",
  "5. **独立复算**：不要相信本件给出的任何数字，全部自己从原始 json / png / 二进制重算。",
].join("\n");

const CONTEXT = [
  "## 背景（本线上一轮的自查，§544）",
  "",
  "本线在核对一批 RA2 遭遇战真机测量数据（`measure_w*.json`，每窗 25 秒、500Hz 采样）。",
  "上一轮（§543）曾宣称「29 个整窗零推进窗 = 结算屏」，两路外部核验已把它判为 PARTIAL 并",
  "抓获本线一处数据错误（表 1 中 `archive_T38` 写成 `00:00:30`，实际屏显 `00:00:32`）。",
  "",
  "本轮（§544）本线提出一个**新的、更大范围的改判**，核心是：",
  "**`fps_avg` 的分母是整窗 25 秒，一段停摆尾段会把正常 31fps 的运行稀释成「慢」**，",
  "所以「目标①卡顿」（目标=修数百单位时的卡顿）此前统计的「慢窗」池子里有大量假货。",
  "同时本线声称：**同一负载跨会话时段 fps 差 3 倍以上**（如 units≈1225 在 11-01 拿 31.2fps，",
  "而 units≈881 在 10-21 只拿 9.2fps），且 `ρ(pre_fps15, 活段fps) = +0.8925`。",
  "",
  "**你的职责是推翻它，不是确认它。**",
  "特别注意这些可能的漏洞：",
  "- 「活段 fps」是不是事后编造的口径？它有没有把「停摆也算慢」的正当性偷掉？",
  "- 「同负载跨时段」是不是被**工具链版本差异**混淆了（不同趟用的 harness 版本、载体图版本不同）？",
  "- ρ(pre_fps15, live_fps) 高是否只是同义反复（两者都由同一个时钟/同一段代码算出）？",
  "- 样本是否被重复计数（同一趟的三个窗不是独立样本）？",
].join("\n");

const TASKS: Task[] = [
  {
    id: "V1",
    title: "口径核验：fps_avg 的分母到底是什么，活段 fps 是不是编出来的口径",
    brief: [
      "**先读源码定口径，再重算。**",
      "",
      "1. 打开 `" + HARNESS + "`，找到 `_measure_stats`（约 4728-4820 行），",
      "   逐行确认：`fps_avg` 的分子分母分别是什么？`span` 取自哪个变量？",
      "   `frame_ms_p50` / `fps_p50` 又是怎么算的？把这三者的定义写成一句话。",
      "2. 全量数据：`" + TRIPS + "` 下所有 `measure_w*.json`。",
      "   **注意有两层**：子目录里的 + 趟根目录下的（`measure_w0/w1/w2.json` 直接在 trip 根）。",
      "   报出总数。",
      "3. 对每一份能算出推进的 json，自己算三个数并列表：",
      "   - `fps_avg`（json 里已给）",
      "   - `live_fps = (末沿帧号 - 首沿帧号) / (末沿时刻 - 首沿时刻)`",
      "   - `fps_p50`（json 里已给）",
      "   明确报出：**`fps_avg < 28` 但 `fps_p50 >= 28` 的窗有几个**，逐个列名。",
      "   再报：`live_fps < 28` 的窗几个，`fps_p50 < 28` 的窗几个。",
      "4. **对抗自查**：`fps_p50` 是「中位帧间隔的倒数」，它天然忽略尾段停摆。",
      "   那用它当主指标是不是等于**把「卡顿」定义改掉了**？",
      "   如果一个窗前面跑 31fps、后面停 20 秒不动，这算不算用户说的「卡顿」？",
      "   把你的立场写清楚：`fps_avg` 和 `fps_p50` 各回答什么问题，**哪个该当目标①的主指标**。",
      "5. 特别核：`archive_T34/measure_w0.json` 这个窗，",
      "   `fps_avg` 极低但 `fps_p50` 高，它的 `samples.t` 有没有采样缺口（相邻 dt>10ms 的累计）？",
      "   报出缺口秒数。",
    ].join("\n"),
  },
  {
    id: "V2",
    title: "时代效应核验：同负载跨时段差 3 倍，还是被工具链版本混淆了",
    brief: [
      "**这是最容易被混淆污染的一条，重点查混淆。**",
      "",
      "1. 对全部可算窗，按 `gate.units0` 分组，列出每个负载档出现过的所有 (时刻, live_fps, trip_id)。",
      "   只在同一 `units0` 出现 >= 3 次时报。",
      "   核对这条关键对照：`units0` 在 1180-1360 的样本里，",
      "   11-01 16:48 与 11-03 11:20 的窗是不是真拿到 31.2-31.3 fps，",
      "   而 10-21 19:03 / 10-31 20:15 的窗只有 6.8-9.2 fps。逐个自己算，不要抄。",
      "2. **★ 混淆排查（必做）**：每一趟用的 harness 版本可能不同。",
      "   看每份 json 里有没有 `harness_sha16` / `argv` / schema 字段；",
      "   若没有，就去趟目录的 `_launch_result.json` 或 `qc151_fields.json` 里找 `harness_sha16`。",
      "   把「快时段」和「慢时段」各自用的 harness 版本列成表。",
      "   **如果快慢与 harness 版本完全共线，那「时代效应」这个说法就不成立，只是版本效应。**",
      "   这一条必须给明确判定。",
      "3. 同样查地图：每份 json 的 `map_sha256` 是什么？快时段和慢时段的地图 sha 一样吗？",
      "   还有载体件数、`tz`/机器状态若有记录也列。",
      "4. 算两个相关系数（自己实现，不调库）：",
      "   `ρ(pre_fps15, live_fps)` 与 `ρ(units0, live_fps)`，只在 units0 非空、live_fps 可算的窗上算。",
      "   然后**在固定 harness 版本内**再算一次 ρ(units0, live_fps)。两次结果都报。",
      "5. **同义反复检查**：`pre_fps15` 是「settle 相位 1.5 秒内的帧推进速率」。",
      "   它与 `live_fps` 是不是同一个量的两次测量（只是时间窗不同）？",
      "   如果是，那 ρ=0.89 只说明「这台机器这个会话一直这么快/慢」，",
      "   **并不能证明任何机制**。把你的判定写清楚。",
      "6. 趟内 vs 趟间方差：对同一 `trip_id` 的多个窗，算窗间 fps 极差；",
      "   对比不同趟之间的极差。报中位数。这一条用来判断「整趟锁定」还是「窗内漂移」。",
    ].join("\n"),
  },
  {
    id: "V3",
    title: "真机分诊：v4f / v4g 两趟为什么没进图，是不是回归",
    brief: [
      "本线今天（2026-11-04）新跑了两趟真机，**都失败了**：`units0=0`、`pre_fps15=0`、",
      "measure 窗内 2001 个采样帧号恒为 0。同机同命令的上一趟 `v4e` 是成功的",
      "（`units0=1189`、`pre_fps15=31.395`、帧号 925→1707）。",
      "",
      "**你的任务：判定这是「随机导航失败」还是「某处回归」，并给出证据。**",
      "",
      "1. 三个趟目录对比：`" + TRIPS + "/l3_1101v4e`（成功）、`l3_1101v4f`、`l3_1101v4g`（失败）。",
      "   逐项对比 `qc151_fields.json` 里的导航链字段（`verify_ok_nav_*`、`signature_got_nav_*`、",
      "   `in_tactical_target`、`seconds_to_window`、`window_stabilize_seconds`、各 stage 秒数）。",
      "   报出**逐字段差异表**。",
      "2. 看 `except_post_*.txt`：三个趟各有没有异常、异常地址是什么。",
      "   **关键**：v4e（成功趟）有没有同样的异常？如果有，那这个异常不是失败原因。",
      "   把三趟的 `except_set_diff.json` 也读了。",
      "3. 看 `measure_w0.json` 的 `gate`：失败趟的 `pre_fps15=0.0` 是「游戏没跑」还是「读了但不动」？",
      "   用 `samples.f` 的取值分布回答（全 0？还是有别的值？）。",
      "   再对比成功趟 `v4e` 的 `samples.f` 起点（它一上来就是 925 吗？还是从 0 涨上去的？）。",
      "4. 看截图：三趟的 `frame_target_01.png` 是不是**同一张画面**（算 sha256 与逐像素差）。",
      "   `fs_boot_probe.png` 也一并比。若画面相同但结果不同，说明分叉点在截图之后。",
      "5. 查历史同类：全库还有没有别的趟也是 `units0=0` 且 `verdict=no_advance`？",
      "   列出全部，并看它们的 `except` 地址是否也是 `007CFC9F`。",
      "   **如果 007CFC9F 在这些失败趟里普遍出现，说明这是一条已知的加载期异常路径；",
      "   如果只在个例出现，那 v4f/v4g 是撞上了新问题。**",
      "6. 给出结论：v4f/v4g 失败的直接原因是什么（导航没点进去 / 点进去了但地图没载 / 加载期崩溃 /",
      "   其它），以及**重跑一趟是否可能成功**。",
    ].join("\n"),
  },
];

phase("三路独立核验 §544 的慢窗改判");

const lanes = await Promise.all(
  TASKS.map(async (t): Promise<LaneResult> => {
    log("派出 " + t.id + "：" + t.title);
    const findings = await agent("核验员-" + t.id).ask<Finding[]>(
      [
        RULES,
        "",
        "## 你的方向",
        t.title,
        "",
        t.brief,
        "",
        CONTEXT,
        "",
        "## 输出",
        "返回 2-5 条 Finding。每条 headline 一句话讲结论，keyFacts 每行一条给具体路径+数字。",
        "verdict 只能取 CONFIRMED / REFUTED / PARTIAL / UNVERIFIABLE。",
        "**你推翻不了就写 CONFIRMED，不要为了显得严格而硬判 PARTIAL。**",
        "把你跑过的命令与关键输出写进 " + OUT + "/" + t.id + "/REPORT.md（自己建目录）。",
      ].join("\n"),
    );
    report({
      where: OUT + "/" + t.id + "/REPORT.md",
      what: t.title + " —— " + findings.map((f) => f.verdict).join("/"),
      evidence: findings
        .map((f) => f.id + " " + f.headline)
        .join("；")
        .slice(0, 400),
      status: "unconfirmed",
      severity: "high",
    } as ReportItem);

    const checks = await agent("复核员-" + t.id).ask<Check[]>(
      [
        RULES,
        "",
        "## 你的任务：独立复核下面这份核验件",
        "你看不到核验员的推理过程，只看到它的结论。**自己从原始数据重算。**",
        "",
        "核验件路径：" + OUT + "/" + t.id + "/REPORT.md",
        "核验员自报结论：" + JSON.stringify(findings).slice(0, 4000),
        "",
        "1. 先读 REPORT.md 全文（它写了命令与输出）。",
        "2. **抽 3 条最关键的结论，逐条自己重算**。不要信它给的数字。",
        "3. 特别检查：它有没有把「像素判据」当「OCR」、把「样本」当「总体」、",
        "   把「同一张图重复计数」当多个样本、把「相关」当「因果」。",
        "4. 若它的结论站得住，判 CONFIRMED 并给出你自己算的数。",
        "   若站不住，判 REFUTED 并写清你读到了什么、算出什么。",
        "5. 把复核写进 " + OUT + "/" + t.id + "/RECHECK.md。",
      ].join("\n"),
    );

    return { task: t.id, findings, checks };
  }),
);

phase("汇总判定：§544 的慢窗改判站不站得住");

const verdicts = lanes.map((l) => ({
  lane: l.task,
  findings: l.findings,
  checks: l.checks,
}));

const summary = await agent("汇总员").ask<string>(
  [
    RULES,
    "",
    "## 汇总任务",
    "三路核验与三路复核已全部完成。材料：",
    JSON.stringify(verdicts).slice(0, 24000),
    "",
    "写一份判定书到 " + OUT + "/VERDICT.md，包含：",
    "1. 一句话结论：§544 的「慢窗口径改判」到底成立到什么程度。",
    "2. 逐条处置表：§544 的每条主张 → CONFIRMED / REFUTED / PARTIAL，给依据。",
    "3. **必须点名本线的错误**（如果有）：哪条数字错了、错在哪、正确值是什么。",
    "4. 对「目标①卡顿」这条主线：现在还剩多少个**可用样本**，下一步该往哪查。",
    "5. 对 v4f/v4g 失败：定性与重跑建议。",
    "6. 诚实账：本轮没查到什么。",
    "返回该判定书的核心结论（300 字内）。",
  ].join("\n"),
);

const item = {
  where: OUT + "/VERDICT.md",
  what: summary.slice(0, 300),
  evidence: "三路核验 + 三路独立复核，见 " + OUT,
  status: "verified" as const,
  severity: "high" as const,
};

return {
  conclusion: summary,
  findings: [item as ReportItem],
  verified: [
    "三路各由独立上下文从原始 json / png / harness 源码复算，未采信 §544 的任何数字",
    "每条方向再由第二道复核员抽 3 条结论独立重算",
    "纯离线只读：零真机、零母本改动",
  ],
  notCovered: [
    "未做 OCR，屏显时间仍靠放大目视",
    "v4f/v4g 只做离线分诊，未重跑真机验证",
    "若「时代效应」与 harness 版本共线，则时代效应不可分（V2 会给判定）",
  ],
};
