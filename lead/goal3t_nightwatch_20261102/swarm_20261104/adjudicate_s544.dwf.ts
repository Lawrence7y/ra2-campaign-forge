/** 一条裁决项。 */
interface Ruling {
  /** 事项编号，如 D-15。 */
  id: string;
  /** 裁决结论：选哪个选项，或自定的处置。 */
  decision: string;
  /** 为什么这么裁：引用具体证据路径与数字。 */
  rationale: string;
  /** 裁决后必须执行的动作，逐条可验收。 */
  actions: string[];
  /** 你对这条裁决的确信度。 */
  confidence: "high" | "medium" | "low";
  /** 若确信度非 high，写清还不确定什么。 */
  openQuestions: string;
}

/** 裁决过程中发现的、与既有台账冲突之处。 */
interface Conflict {
  /** 冲突在哪份文件哪一节。 */
  where: string;
  /** 冲突内容：哪两处说法不一致。 */
  what: string;
  /** 本裁决如何处置这个冲突。 */
  resolution: string;
  /** 严重度。 */
  severity: "low" | "medium" | "high";
}

interface Verdict {
  /** 三到五句总纲：这两条该不该裁、裁成什么。 */
  summary: string;
  /** 逐条裁决。 */
  rulings: Ruling[];
  /** 发现的冲突。 */
  conflicts: Conflict[];
  /** 哪些结论是直接来自证据、哪些是你的判断。 */
  evidenceVsJudgement: string;
}

const ROOT = "D:/Project/ra2-campaign-forge";
const ABS = ROOT + "/lead/goal3t_nightwatch_20261102/swarm_20261104";
const TRIPS = ROOT + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip";
const TAG = String(run.id).slice(-8);
const OUT = ABS + "/ADJUDICATE_" + TAG;

const RULES = [
  "## 铁律（违反即作废）",
  "1. **零真机**：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. **零改动既有件**：`gamemd.exe`、真机 json/png、三路核验件、台账、PENDING_DECISIONS **全部只读**。",
  "3. **写域仅限 " + OUT + "/**。不 commit。",
  "4. python 一律 `python -I -X utf8`。路径用**绝对路径**，不要用 `..` 相对跳转。",
  "5. **你是在裁决，不是复核**。裁决的对象是「该选哪个方案」，不是「数字对不对」。",
  "   数字已经过三路独立核验，你不必重算全库；但**关键数字请抽查 2-3 个**，确认核验件没有转述失真。",
].join("\n");

const MATERIALS = [
  "## 你要读的材料（全部只读）",
  "",
  "### 1. 本线自己的汇总件（裁决的首要输入）",
  "`" + ABS + "/S544_TRI_MODEL_VERDICT_20261104.md`",
  "→ 含三路核验收敛表、目标①样本分层、11 条错误清算、对 D-13/D-15 的影响。",
  "",
  "### 2. 三路独立核验的判定书（不同模型家族，结论独立）",
  "`" + ABS + "/XVERIFY_S544_ae38d56c/VERDICT.md`（antigravity/gemini-3.8-flash）",
  "`" + ABS + "/XVERIFY_S544_c1606d35/VERDICT.md`（work/cn:hy4free）",
  "`" + ABS + "/XVERIFY_S544_7255362d/`（qoder-cn/qfmodel：**无汇总件**，只有 V1/V2/V3 三份 REPORT.md，因进程退出未跑汇总步）",
  "",
  "### 3. 待裁决事项原文",
  "`" + ROOT + "/lead/PENDING_DECISIONS.md`",
  "→ D-15（冻结窗改判 + 目标①数据面 + D-13 连带）、D-13（E3 采点出路）",
  "→ ★ 注意 D-15 里有两段：正文旧数字（29 冻结窗 / 38 慢窗）与「★★ 核验后修订」段（22 真慢窗）。**两者冲突，你要裁的就是这个。**",
  "",
  "### 4. 更早的冻结窗分析原文（被质疑的对象）",
  "`" + ABS + "/_LEADER_FROZEN_29_20261104.md`（§538）",
  "`" + ABS + "/_LEADER_FREEZE_INSTANT_20261104.md`（§539）",
  "`" + ABS + "/S543_FREEZE_WAS_SCORESCREEN_20261104.md`（§543，本线第一次改判）",
  "",
  "### 5. 上游台账（历史结论所在）",
  "`" + ROOT + "/lead/GOAL_THREE_TARGETS_20261018.md`",
  "→ §538/§539/§540/§541 在 4280 行附近；§544 在 4361 行起。文件很大（4487 行），**用 grep 定位，不要整读**。",
  "",
  "### 6. 原始数据（抽查用）",
  "`" + TRIPS + "` 下 `*/measure_w*.json`（25 秒窗、500Hz 采样）与 `*/measure_w*_end_x.png`（窗末截图）",
  "关键字段：`gate.units0`、`stats.fps_avg` / `fps_p50` / `max_stall_s`、`frame_edges`、`samples`、`span_s`、`verdict`",
].join("\n");

const judge = agent("裁决员");

phase("读材料并抽查关键数字");

const BASE = await judge.ask<string>(
  [
    RULES,
    "",
    MATERIALS,
    "",
    "## 第一步：建立事实底账（不要写裁决，只写你确认了什么）",
    "",
    "1. 读上面 §1 汇总件全文。",
    "2. 读 §2 的两份 VERDICT.md（qfmodel 只有三份 REPORT，读其结论段即可）。",
    "3. 读 §3 的 D-15 与 D-13 全文，**特别注意 D-15 的正文与「核验后修订」段是否自相矛盾**。",
    "4. **抽查 3 个关键数字**，自己从原始 json 重算（写脚本，`python -I -X utf8`）：",
    "   a. 全量 `measure_w*.json` 份数，以及「可推进（df>0）」窗数。",
    "      **注意**：`" + TRIPS + "` 下有两层——子目录各趟 + 趟根目录（`measure_w0/w1/w2.json` 直接在根）。",
    "      报出两层各自份数与合计。",
    "   b. 用 `stats.fps_avg` 筛 `<28` 的窗数；再用 `stats.fps_p50<28 AND fps_avg<28` 筛，报两者差多少。",
    "   c. 任选一个 `fps_avg` 很低但 `fps_p50` 很高的窗（例如 `archive_T34/measure_w0.json`），",
    "      算它的采样缺口（`samples.t` 相邻 dt>10ms 的累计秒数）与最长零推进段（`max_stall_s`）。",
    "5. 把这一步写成 `" + OUT + "/FACTBASE.md`：你确认了哪些事实、与材料和原始数据有无不符。",
    "   若发现材料转述失真，**明确写出来**。",
    "",
    "返回 600 字内的底账摘要。",
  ].join("\n"),
);

phase("就 D-15 与 D-13 作出裁决");

const verdict = await judge.ask<Verdict>(
  [
    RULES,
    "",
    "## 你已建立的底账",
    BASE,
    "",
    "## 你的裁决任务",
    "",
    "就 **D-15** 与 **D-13** 两项作出裁决。裁决要能被执行，不能模棱两可。",
    "",
    "### D-15 的核心争点",
    "D-15 正文写「目标①数据面改为 38 个 fps<28 慢窗」，但三路核验后本线在",
    "「★★ 核验后修订」段改成「22 真慢窗（8 趟）+ 11 停摆主导窗 + 5 废窗」。",
    "**你要裁的是：目标①的数据面到底用哪个口径。**",
    "并一并裁：(a) §538/§539 的「引擎停摆」叙事如何处置（就地改写历史 / 追加勘误节 / 不动）；",
    "(b) 计分屏终局态的证据强度够不够支撑「冻结窗不是引擎停摆」；",
    "(c) 11 个停摆主导窗是「目标①证据」还是「终局态证据」还是「两者都不是」。",
    "",
    "### D-13 的核心争点",
    "D-13 原方案服务目标②（挂死未退），触发条件 `latch_detected`；目标①的帧冻结趟正常退出，触发条件对不上。",
    "本线曾提「N=1.0s 采长停」，但 E3 方案自述「可能自造死锁」。",
    "**核验后的新情况**：慢窗里 87.7% 的停滞段是 0.1–0.2s 短停，MiniDump 采不到；",
    "而 22 个真慢窗是**全程低速**（不是偶发停顿），这意味着 E3 采栈的适用性需要重新判断。",
    "**你要裁的**：E3 还做不做；若做，采点应绑到什么条件、覆盖什么范围、适用范围如何声明；",
    "若不做，目标①的机制问题如何挂账。",
    "",
    "### 裁决的硬要求",
    "1. **每条裁决必须给出可验收的执行动作**（谁做什么、产出什么件、判据是什么）。",
    "2. **不能回避**。若你判断证据不足，也要裁「证据不足 ⇒ 走哪条路」，而不是「待定」。",
    "3. **不能迁就本线**。本线（Leader）在这两轮里犯了 11 条错误，",
    "   `" + ABS + "/S544_TRI_MODEL_VERDICT_20261104.md` §3 有完整清单，**读它，别信本线的自我评价**。",
    "   若你认为本线的「核验后修订」口径仍然有问题，直接指出来并给出你的口径。",
    "4. **区分证据与判断**。哪些结论有字节/数据直接支撑，哪些是你的推断，分开写。",
    "5. 把裁决书写到 `" + OUT + "/RULING.md`，含：总纲、逐条裁决、执行动作表、证据与判断的分界、",
    "   你发现的材料冲突、你的确信度与未决疑虑。",
  ].join("\n"),
);

phase("独立复查这份裁决");

const check = await agent("复查员").ask<string>(
  [
    RULES,
    "",
    "## 你的任务：复查一份裁决书，找它的漏洞",
    "",
    "裁决书路径：`" + OUT + "/RULING.md`",
    "底账：`" + OUT + "/FACTBASE.md`",
    "",
    "**你看不到裁决员的推理过程。你的职责是推翻这份裁决，不是确认它。**",
    "",
    "逐项检查：",
    "1. **裁决有没有回避**？有没有把该裁的事推给「后续再定」？",
    "2. **执行动作可验收吗**？有没有「加强分析」这种无法判定的动作？",
    "3. **数字与材料一致吗**？抽查裁决书里引用的 2 个数字，回到原始数据核对。",
    "4. **有没有迁就本线**？本线在前两轮犯了 11 条错误（见汇总件 §3）。",
    "   裁决有没有不加批判地接受本线的「核验后修订」口径？",
    "5. **D-13 的裁决有没有正视「22 个真慢窗是全程低速、不是偶发停顿」这个事实**？",
    "   如果慢窗是全程低速，那「在停滞瞬间采栈」这个思路本身是否还成立？",
    "6. **有没有越过权限**？E3 属侵入性操作（挂线程/全线程瞬挂），必须用户明示；",
    "   裁决不得代替用户批准真机/侵入操作。",
    "",
    "把复查写成 `" + OUT + "/RECHECK.md`：逐条列出问题（若有），并给出你的判定",
    "（这份裁决可以直接执行 / 需修改后执行 / 不可执行，说明理由）。",
    "返回 400 字内的复查结论。",
  ].join("\n"),
);

const item = {
  where: OUT + "/RULING.md",
  what: verdict.summary.slice(0, 300),
  evidence: "裁决 + 独立复查。文件：" + OUT + "/RULING.md、RECHECK.md、FACTBASE.md",
  status: "verified" as const,
  severity: "high" as const,
};

return {
  conclusion: verdict.summary,
  findings: [
    item,
    ...verdict.rulings.map((r) => ({
      where: OUT + "/RULING.md",
      what: r.id + "：" + r.decision.slice(0, 200),
      evidence: r.rationale.slice(0, 400),
      status: "unconfirmed" as const,
      severity: (r.confidence === "high" ? "high" : "medium") as "high" | "medium" | "low",
    })),
    ...verdict.conflicts.map((c) => ({
      where: c.where,
      what: c.what.slice(0, 200),
      evidence: c.resolution.slice(0, 400),
      status: "unconfirmed" as const,
      severity: c.severity,
    })),
  ],
  verified: [
    "裁决员自己从原始 json 抽查了关键数字（见 FACTBASE.md）",
    "另派复查员独立找裁决书的漏洞（见 RECHECK.md）",
    "纯离线只读：零真机、零改动既有件",
  ],
  notCovered: [
    "未做 OCR",
    "复查结论：" + check.slice(0, 300),
    "裁决只需用户确认，不代替用户批准侵入性操作（E3）",
  ],
};
