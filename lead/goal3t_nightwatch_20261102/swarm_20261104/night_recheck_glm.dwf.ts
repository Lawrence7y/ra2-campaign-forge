/** 一条复核判定。 */
interface Check {
  /** 判据编号，如 EX1-R1、EX1-COUNT、EX2-SCOPE。 */
  id: string;
  /** PASS / FAIL / PARTIAL。 */
  verdict: "PASS" | "FAIL" | "PARTIAL";
  /** 你自己算/查得到的证据；FAIL 时必须写正确值应是什么。 */
  evidence: string;
  /** 证据位置：文件与行号，或命令与输出片段。 */
  where: string;
}

/** 一个发现的问题。 */
interface Problem {
  /** 问题在哪：文件:行号或表名。 */
  where: string;
  /** 问题是什么，一句话。 */
  what: string;
  /** 正确值应是什么，或该怎么改。 */
  correct: string;
  /** 严重度。 */
  severity: "low" | "medium" | "high";
}

/** 需要用户裁决的新事项（若没有就返回空数组）。 */
interface NewDecision {
  /** 一句话标题。 */
  title: string;
  /** 背景与为什么必须由用户裁。 */
  why: string;
  /** 可选项，至少两个。 */
  options: string[];
}

interface NightReport {
  /** 总结论：两份候选件能不能接收。 */
  verdict: "PASS" | "FAIL" | "PARTIAL";
  /** 三到五句总纲。 */
  summary: string;
  /** 逐条判据。 */
  checks: Check[];
  /** 发现的问题。 */
  problems: Problem[];
  /** 需用户新裁的事项。 */
  newDecisions: NewDecision[];
  /** 你没查的部分，如实写。 */
  notCovered: string[];
}

const ROOT = "D:/Project/ra2-campaign-forge";
const ADJ = ROOT + "/lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5";
const TRIPS = ROOT + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip";
const LEDGER = ROOT + "/lead/GOAL_THREE_TARGETS_20261018.md";
const D15 = ADJ + "/D15_IMPLEMENTATION_CANDIDATE.md";
const D13 = ADJ + "/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md";

const RULES = [
  "## 铁律（违反即作废）",
  "1. **零真机**：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. **只读**：母本、真机 json/png、`RULING.md` / `RECHECK.md` / `FACTBASE.md`、",
  "   两份候选件、台账 `" + LEDGER + "`、`lead/PENDING_DECISIONS.md` —— **全部不得修改**。",
  "3. **写域仅限** `" + ADJ + "/`（唯一新文件是本报告 `D15_D13_NIGHT_RECHECK_GLM.md`），",
  "   中间脚本也写在 " + ADJ + "/night_" + String(run.id).slice(-8) + "/ 下。不 commit。",
  "4. python 一律 `python -I -X utf8`，路径一律**绝对路径**，不用 `..` 相对跳转。",
  "5. **不写任何采样代码**（无 MiniDump / SuspendThread / StackWalk / 注入 / 探针）。",
  "6. **独立复算**：候选件里的数字一律自己从原始 json 重算，不许抄。",
].join("\n");

const reviewer = agent("复核基准员", {
  system:
    "你是数据复核员。你只相信你自己从原始文件读到的值。候选件写什么，你都当作待验证的主张。" +
    "如果一条判据你无法验证，写 UNVERIFIABLE 并说明卡在哪，不要猜。",
});

phase("读裁决与候选件，建立复核基准");

const baseline = await reviewer.ask<string>(
  [
    RULES, "",
    "## 第一步：建立基线（不要写结论，只写你确认了什么）",
    "",
    "读这几份（可先读结构再定位）：",
    "- `" + ADJ + "/RULING.md` 第四节「可验收执行动作表」（EX-1..EX-5 的判据，含 Leader 按 RECHECK 补的 R1/R2）",
    "- `" + ADJ + "/RECHECK.md`（两处补丁 R1/R2 的要求）",
    "- `" + D15 + "`（156KB，**分段读**，先看 `## ` 级标题再定点读）",
    "- `" + D13 + "`",
    "",
    "然后**自己写脚本**从 `" + TRIPS + "` 重建这八个数（`python -I -X utf8`，绝对路径）：",
    "`104 / 63 / 58 / 25 / 22 / 11 / 5 / 41`，以及 22 个持续低速窗的独立 `trip_id` 数（应为 8）。",
    "",
    "判据（写死在脚本里，不要引用候选件的分类）：",
    "- 全量 json：`" + TRIPS + "` 下 `*\\measure_w*.json`（子目录层）+ `measure_w*.json`（趟根层），两层都要",
    "- 可推进：`frame_edges` 长度 >= 2 且 `末沿帧号 - 首沿帧号 > 0`",
    "- 25 秒窗：`span_s == 25.0`；4 秒门控窗：`span_s == 4.0`",
    "- 对照：25 秒窗中 `stats.fps_avg >= 28`",
    "- 持续低速：25 秒窗中 `fps_avg < 28` 且 `stats.fps_p50 < 28`",
    "- 停摆主导：25 秒窗中 `fps_avg < 28` 且 `stats.fps_p50 >= 28`",
    "- 不可算：`frame_edges` 为空或不满足可推进",
    "",
    "把你算到的八个数与独立 trip_id 数写出来，**与候选件声明的值逐项对比**，列出一致/不一致。",
    "",
    "返回 500 字内：你的八个数、候选件的八个数、哪些对不上。",
  ].join("\n"),
);

phase("逐条核验 EX-1..EX-4 验收判据");

const report = await reviewer.ask<NightReport>(
  [
    RULES, "",
    "## 你已建立的基线",
    baseline, "",
    "## 现在逐条核验，并写报告",
    "",
    "### A. EX-1 数据面",
    "1. **八项计数**：用你基线里算的八个数，逐项判 PASS/FAIL。",
    "2. **★ R1 混杂控制表**：47 窗（22 持续低速 + 25 对照）是否**真的**有五列：",
    "   `map_sha256` / harness 版本或 sha16 / 实际起止帧 / 门控状态 / `units0` 及取值阶段。",
    "   **抽查 3 行**（至少含 1 个持续低速窗、1 个对照窗），回原始 json 核对这五个值。",
    "   **重点查造假**：",
    "   - 有没有把「缺」填成了值？",
    "   - `map_sha256` 有没有跨趟借用（同一趟不同窗必须同值，不同地图的趟必须不同值）？",
    "   - harness sha16 是否与该趟 `_launch_result.json` 一致？",
    "   - 起止帧是否与 `frame_edges` 首末元素一致？",
    "3. **缺格统计**：候选件 4.3 节声称的缺格数与查阅来源，抽查 2 项是否属实。",
    "4. **`p50` 高不得记为健康**：确认 `archive_T34/measure_w0.json` 被归入停摆主导而非健康。",
    "5. **33 与 38 的分母解释**：候选件是否说清「38 混了 5 个 4 秒窗」？",
    "",
    "### B. EX-2 勘误",
    "6. **禁用表述**：全文 grep，是否仍出现 `31.2` 当作时钟换算常数、比分 `146/171`、",
    "   `T38 = 30 秒` 或「一帧级错位」？逐处列出（注意：把它作为**被推翻的旧说法**引用是允许的，",
    "   但要能看出是在撤销而非复述）。",
    "7. **证据范围**：是否写死 **21/32**，且未覆盖窗归「原因未定」？",
    "   有没有把「撤销肯定归因」偷写成「已证明全部不是引擎停摆」？**这是 high 级错误。**",
    "8. **来源定位**：抽查 2 处「文件名:行号」引用，去台账 `" + LEDGER + "` grep 该行，",
    "   确认内容与被引用句相符。裁决特别警告过：散件的 §538/§539 与台账同号章节**不是同一篇**。",
    "9. **R2 字段身份**：凡出现 `l3_1101v4c` 三窗序列，是否标明 `fps_avg`（18.52→28.40→30.68）",
    "   还是派生 `live_fps`（18.54→28.42→30.71）？有没有混用？",
    "",
    "### C. EX-3 11 窗证据表",
    "10. **恰好 11 行**？逐窗数。",
    "11. **`l3_20261023q/w2` 有没有被标「已证终局」**？（不得，它无后续零推进作同向证据）",
    "12. **`archive_T32/w0` 与 `archive_T47/w0` 有没有靠后续 `df==0` 确证终局**？（不得，其后续冻结窗无截图）",
    "13. **11 窗整组**有没有被计为「已证在战机制」或「已证终局」？（都不得）",
    "14. 抽查 2 窗的截图落盘判定：回 `" + TRIPS + "` 看该趟是否有 `measure_w*_end_x.png`、",
    "    `mtime` 是否与该窗窗尾（`t_abs0 + span_s`）相差在 +0.05~+0.20 秒内。",
    "",
    "### D. EX-4 D-13 缺口卡",
    "15. 是否明确写「**当前 E3 不执行**」，且列出被关闭的具体项（N=1秒 MiniDump / Suspend-StackWalk /",
    "    写采样代码 / 真机发射）？",
    "16. **0/22 覆盖**是否写对？（22 窗 `max_stall_s` 最大值应为 0.749879 秒）自己抽查该最大值。",
    "17. **87.7%** 是否声明原分母为**旧 1734 个 >0.1 秒事件**、而非 22 窗重算比例？",
    "18. 三个缺口是否逐条填（阶段可确认性 / 耗时函数与调用链 / 固定条件下因果区分力）？",
    "    没有证据的地方是否写「缺」/「未闭合」而非编造？",
    "19. 是否**未**出现任何采样代码？全文 grep `MiniDump` / `SuspendThread` / `StackWalk` 看是否只有说明性提及。",
    "20. 是否守住「不以正常退出或 p50 较高宣告机制已解」？",
    "",
    "### E. 越权检查",
    "21. 用 `git status --short` 与文件 `mtime` 确认：台账、PENDING、RULING、RECHECK、",
    "    三路核验件、真机 json/png **均未被本轮改动**。",
    "",
    "## 输出",
    "写报告到 `" + ADJ + "/D15_D13_NIGHT_RECHECK_GLM.md`，包含：",
    "- 总结论（PASS/FAIL/PARTIAL）与三到五句总纲",
    "- 21 条判据的逐条 PASS/FAIL/PARTIAL 表，每条给证据位置（文件:行号 或 命令输出）",
    "- 问题清单（每条写：在哪、是什么、正确值应是什么）",
    "- 需用户新裁的事项（没有就空数组）",
    "- 你没查的部分（如实）",
    "",
    "返回 NightReport。",
  ].join("\n"),
);

const item = {
  where: ADJ + "/D15_D13_NIGHT_RECHECK_GLM.md",
  what: report.summary.slice(0, 400),
  evidence: "21 条判据逐条复核；问题 " + report.problems.length + " 条",
  status: "verified" as const,
  severity: "high" as const,
};

return {
  conclusion: report.summary,
  findings: [
    item,
    ...report.problems.slice(0, 8).map((p) => ({
      where: p.where,
      what: p.what.slice(0, 200),
      evidence: ("正确值：" + p.correct).slice(0, 400),
      status: "unconfirmed" as const,
      severity: p.severity,
    })),
    ...report.newDecisions.map((d) => ({
      where: ADJ + "/D15_D13_NIGHT_RECHECK_GLM.md",
      what: "需新裁：" + d.title.slice(0, 150),
      evidence: d.why.slice(0, 400),
      status: "unconfirmed" as const,
      severity: "high" as const,
    })),
  ],
  verified: [
    "八项计数由复核员独立从原始 json 重算，非采信候选件",
    "47 窗五列抽 3 行回原始 json 核对",
    "21 条判据逐条给 PASS/FAIL 与证据位置",
    "零真机、零改动台账/PENDING/核验件（git status 与 mtime 双向确认）",
  ],
  notCovered: report.notCovered,
};
