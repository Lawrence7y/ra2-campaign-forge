interface Finding {
  /** 编号，如 V1-A1。 */
  id: string;
  /** 一句话结论，不超过 60 字。 */
  headline: string;
  /** 证据级别：byte / data / derived / speculation。 */
  level: "byte" | "data" | "derived" | "speculation";
  /** 关键证据：文件路径 + 具体数值/像素坐标，每条一行。 */
  keyFacts: string[];
  /** 判定：CONFIRMED / REFUTED / PARTIAL / UNVERIFIABLE。 */
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
}

interface Check {
  id: string;
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
  /** 你自己重算得到的数字，不是复述原报告。 */
  recomputed: string;
  detail: string;
}

const ROOT = "D:/Project/ra2-campaign-forge";
const ABS = ROOT + "/lead/goal3t_nightwatch_20261102/swarm_20261104";
const TRIPS = ROOT + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip";
/** 本次 run 的写域：用 run.id 尾段保证两个模型的两趟互不覆盖。 */
const TAG = String(run.id).slice(-8);
const OUT = ABS + "/XVERIFY_S543_" + TAG;

const RULES = [
  "## 铁律（违反即作废）",
  "1. **零真机**：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. **零改动母本**：ra2youli/gamemd.exe 只读；真机数据 json/png 也只读。",
  "3. **写域仅限 " + OUT + "/**。不改台账、不改 swarm_20261104 根下已有文件、不 commit。",
  "4. python 一律 `python -I -X utf8`。路径一律用**绝对路径**（cwd 会漂移）。",
  "",
  "## 你要核验的对象",
  "本线（Leader）刚产出一份自我纠错件：`" + ABS + "/S543_FREEZE_WAS_SCORESCREEN_20261104.md`。",
  "它的核心主张是：此前 §538/§539/§540/§541 反复分析的「29 个战斗段完全冻结窗」，",
  "**其实是对局已经打完之后的「遭遇战得分」结算屏**，不是引擎停摆。",
  "",
  "**你的职责是推翻它，不是确认它。** 逐条自己复算，不要相信原件里的数字。",
  "复现不出来就判 REFUTED 或 UNVERIFIABLE，并写清你读了哪些字节/像素/数据行。",
  "特别检查：把「有推进窗」和「冻结窗」混谈、把像素判据当 OCR、样本当总体、",
  "截图时序错位、用同一张图重复计数当多个样本。",
].join("\n");

const TASKS: { id: string; title: string; brief: string }[] = [
  {
    id: "V1",
    title: "图像证据核验：那 25 张窗末截图到底是不是计分屏",
    brief: [
      "**这是核心。必须自己看图，不许信原件结论。**",
      "",
      "数据目录：" + TRIPS,
      "待核验文件：`*\\measure_w*_end_x.png`（共 25 张，800×600）。",
      "",
      "要做：",
      "1. 用 PIL 打开**每一张**，逐张判断画面类型：",
      "   - 是否出现「遭遇战得分」标题条（右上角）？",
      "   - 是否出现计分表（表头含 玩家/摧毁数/失败数/建造数/分数）？",
      "   - 还是纯战斗画面 / 菜单 / 桌面？",
      "   **必须写出你用什么像素/色块判据做的初筛，然后逐张目视确认**。",
      "   注意：蓝紫色加载/简报屏也会命中「蓝紫占比」这类粗糙判据——",
      "   本线已踩过这个坑，你不能再踩。",
      "2. **逐张读出「时间」字段**（右上，HH:MM:SS 黄色字）。写清你是靠放大图目视还是别的方法。",
      "3. 把每张的时间读数与同趟 `measure_w{k}.json` 的 `frame_edges` 末帧号对账：",
      "   算 隐含fps = 末帧号 / 屏显秒数。列出全表。",
      "   本线声称 12 趟里 11 趟落在 29.9–31.4，只有 l3_20261023r 是 24.81。**你独立算一遍**。",
      "4. **逐像素重复检验**：对 25 张算 sha256(RGB raw)。",
      "   本线称独立整幅仅 21/25，且 `archive_T33/w2`、`archive_T42/w1`、`archive_T42/w2`、",
      "   `archive_T45/w2` 四张完全相同，`archive_T36/w1` 与 `archive_T38/w1` 也相同。",
      "   **你独立算一遍，报出你自己的重复组**。",
      "5. **同趟 w1 vs w2 的「时间」字段逐像素差**（区域约 (430,118)-(640,150)）。",
      "   本线称 7/8 趟逐像素相同（maxdiff=0），唯一反例是 archive_T38（w1=00:00:10 → w2=00:00:32）。",
      "   **你独立算一遍**。",
      "6. 关键判据：**计分屏计时器在帧号冻结期间是否冻结？**",
      "   若冻结 ⇒ 屏幕是静态结算屏 ⇒ 支持「对局已结束」；",
      "   若继续走 ⇒ 反对。给出你的判定。",
      "",
      "产出：" + OUT + "/V1/REPORT.md，把脚本与输出存同目录（`V1_probe*.py` / `V1_probe*_out.txt`）。",
      "必写诚实账：哪些图你看得不确定、哪些读数靠猜。",
    ].join("\n"),
  },
  {
    id: "V2",
    title: "数据面核验：29 个 df==0 窗的性质与「可用样本」重算",
    brief: [
      "**这一路只看 json，不看图**（图由 V1 负责），两条独立通道互为对照。",
      "",
      "数据目录：" + TRIPS + "，文件 `*\\measure_w*.json`（schema MEASURE_V1）。",
      "",
      "要做：",
      "1. 全量重算窗分类（每份 json 的 `frame_edges`）：",
      "   - df>0（有推进）、df==0 且 f0!=0（本线称「冻结」）、df==0 且 f0==0（加载段）、df<0（回退）。",
      "   本线报的是 94 窗 / 36 趟，有推进 63、冻结 29、加载段 1、回退 1。**你独立算，报你自己的数**。",
      "2. 对 63 个有推进窗，按 `stats.fps_avg` 分档，报：",
      "   - fps_avg>=28 多少个？<28 多少个？（本线称 25 / 38）",
      "   - 列出 <28 的那些窗（趟 + 窗号 + fps_avg + df），这是「目标① 真正可用样本」的候选。",
      "3. **对账 §538 的分类表**：读 `" + ABS + "/_LEADER_FROZEN_29_20261104.md`。",
      "   它把 29 窗列为「战斗段完全冻结」并称「df==0 ⇒ 引擎停摆、永不恢复」。",
      "   **你要检查它有没有任何一处读过截图**。若没有，明确写「纯 JSON 口径，无图像佐证」。",
      "4. **反证检查（最重要）**：如果那 29 窗真是「对局已结束」，则这些趟应该显示：",
      "   - `gate.pre_fps15` 高（开局满速）而 `logic_frames==0`（窗口期零推进）——检查是否如此；",
      "   - `counters` 里 `units`/`g`/`b` 在冻结窗内**完全不变**；",
      "   - 冻结窗的 `max_stall_s ≈ span_s`（整窗停）。",
      "   逐条核对并报出反例（若有）。",
      "5. **T42 与 l1_20261023e4 是反例候选**：本线称这两趟的 df==0 窗**没有**计分屏证据，",
      "   仍未解释。你去查这两趟的 json，看有没有别的解释（加载失败？进程退出？），给出你的判断。",
      "6. **边界检查**：帧号回退的那 1 窗（l1_20261023e4 w1，df=-3557）到底是什么？",
      "   本线没解释它。给出你的分析。",
      "",
      "产出：" + OUT + "/V2/REPORT.md + 脚本/输出同目录。",
    ].join("\n"),
  },
  {
    id: "V3",
    title: "主张审计：§538/§539/§540/§541 哪些结论必须撤回、哪些不受影响",
    brief: [
      "**这一路做文书审计，但每条都必须落到可复算的证据上。**",
      "",
      "读这五份（只读）：",
      "  1. `" + ABS + "/_LEADER_FROZEN_29_20261104.md`（§538）",
      "  2. `" + ABS + "/_LEADER_FREEZE_INSTANT_20261104.md`（§539）",
      "  3. `" + ABS + "/_LEADER_FRAME_COST_20261104.md`（§536）",
      "  4. `" + ABS + "/BATCH1_VERDICT.md`（§541 转录来源）",
      "  5. `" + ABS + "/S543_FREEZE_WAS_SCORESCREEN_20261104.md`（本线自我纠错件，**你要审计的是它**）",
      "",
      "要做：",
      "1. 把 §538/§539 里**每一条**关于「引擎停摆 / 冻结 / 断崖 / 永不恢复」的断言列成表，",
      "   逐条判：若「29 窗是对局结束」成立，该条是 (a) 必须撤回 (b) 需改口径 (c) 不受影响。",
      "   给出理由必须指回原文行号 + 该条依赖的数据。",
      "2. **重点核对一处自相矛盾**：§539 说「进程仍活着、采样通道正常、状态永久保持」并用它论证",
      "   「引擎停摆而非崩溃」。若实为对局结束，这句话是否仍成立？（进程确实还活着——但对局已完）",
      "   给出精确改写措辞。",
      "3. **重点核对 §536（单帧耗时结构，5 条容器遍历回边）**：",
      "   本线声它「不受影响，因为那是静态反汇编」。**你判断这个说法站不站得住**。",
      "   §536 §四 自己承认「9.22 倍是否真由这些循环造成，本件未证明」。",
      "   那么「不受影响」到底指什么不受影响？给出你的结论。",
      "4. **重点核对 §541 / BATCH1_VERDICT 的那张「真机判别表」（P-A…P-G）**：",
      "   它把 P-B「挂起冻结」列为一个需要真机判别的路径。若 29 窗是对局结束，",
      "   那张表的 P-B 行是否仍然可用？「D-13 的采点时机=停滞段内」是否还成立？",
      "   **这一条直接关系待裁项 D-13，必须给明确结论**。",
      "5. **检查 S543 自身有没有过度声称**：",
      "   - 它说「20/25 判为计分屏」——这个数你接受吗？",
      "   - 它说「4 张不是独立采集」——你接受吗？",
      "   - 它说「§533 假说被弱化仍成立」——有没有逻辑跳跃？",
      "   - 它把目标①可用样本从 29 窗改判为 38 慢窗——这个改判有没有洞？",
      "   逐条给 CONFIRMED / PARTIAL / REFUTED。",
      "6. **必须写**：如果 S543 是错的（即那些窗真是引擎停摆而非对局结束），",
      "   什么证据能证明它错？列出 3 条可判别的检验。",
      "",
      "产出：" + OUT + "/V3/REPORT.md。",
    ].join("\n"),
  },
];

phase("三路独立核验 §543 的「冻结窗其实是结算屏」主张");
const found = await Promise.all(
  TASKS.map(async (t) => {
    const a = agent(`核验员-${t.id}`, {
      system:
        "你是 RA2/尤复仇引擎逆向项目的独立核验员，专长是把别人的结论推倒。\n" +
        "你的每条结论都必须指回具体文件路径、具体像素坐标或具体数据行号。\n" +
        "禁止把猜测写成结论；做不到就明写做不到。\n" +
        "发现与原件冲突必须指出，不得沉默迁就。\n" +
        "所有写入只允许在分配给你的目录内。",
    });
    const r = await a.ask<Finding>(
      `任务 ${t.id}：${t.title}\n\n你的写域：${OUT}/${t.id}/\n\n` + RULES + "\n\n## 具体任务\n" + t.brief,
    );
    return { task: t, r };
  }),
);
for (const x of found) report({ id: x.task.id, verdict: x.r.verdict, headline: x.r.headline });

phase("逐份独立复核三份核验件");
const checked = await Promise.all(
  found.map(async (x) => {
    const c = agent(`复核员-${x.task.id}`, {
      system:
        "你是第二道核验。你的任务是检查上一道核验员有没有偷懒、有没有把像素判据当 OCR、\n" +
        "有没有拿重复样本充数、有没有把「有推进窗」和「冻结窗」混谈。\n" +
        "你自己重新抽 3 个具体样本复算（自己选），复现不出就判 REFUTED。",
    });
    const r = await c.ask<Check>(
      `复核 ${x.task.id}：${x.task.title}\n\n` +
        `核验员报告：${OUT}/${x.task.id}/REPORT.md\n` +
        `自报：verdict=${x.r.verdict}\nheadline=${x.r.headline}\n` +
        `keyFacts=${JSON.stringify(x.r.keyFacts)}\n\n` +
        RULES +
        "\n\n自己抽 3 个样本独立复算（不许照抄它的数字），判 CONFIRMED/REFUTED/PARTIAL/UNVERIFIABLE。" +
        `复核报告写 ${OUT}/${x.task.id}/RECHECK.md。`,
    );
    return { id: x.task.id, c: r };
  }),
);

phase("汇总判定：§543 与 §538/§539 到底谁对");
const synth = agent("汇总员", {
  system:
    "你是汇总员。把三路核验与复核收敛成一份判定。不粉饰：硬的是硬的，破的是破的。\n" +
    "最要紧的是回答一句话：那 29 个「整窗零推进」窗，到底是对局已结束、还是引擎停摆？\n" +
    "若两路证据矛盾，明写矛盾，不要强行调和。",
});
const verdict = await synth.ask<string>(
  `读 ${OUT}/V1..V3 的 REPORT.md 与 RECHECK.md。\n\n` +
    `自报：${JSON.stringify(found.map((x) => ({ id: x.task.id, v: x.r.verdict, h: x.r.headline })))}\n` +
    `复核：${JSON.stringify(checked.map((c) => ({ id: c.id, v: c.c.verdict, re: c.c.recomputed })))}\n\n` +
    `写 ${OUT}/VERDICT.md，结构：\n` +
    "# §543 独立核验判定\n" +
    "## 一、一句话结论（29 窗到底是什么）\n" +
    "## 二、三路核验结果对照表\n" +
    "## 三、已证实（含具体文件/像素/数据）\n" +
    "## 四、被推翻或降级\n" +
    "## 五、★ 对 §538/§539/§540/§541 的逐条处置（撤回/改口径/不受影响）\n" +
    "## 六、★ 对目标①的影响：可用样本到底是多少\n" +
    "## 七、★ 对 D-13 的影响（E3 采点时机是否还成立）\n" +
    "## 八、仍未解释的（T42 / l1_20261023e4 / 帧号回退）\n" +
    "## 九、诚实账（本次核验没做到的）\n全文返回。",
);

await artifact.markdown("verdict", verdict, {
  title: "§543 独立核验判定",
  description: "三路核验 + 逐份复核：29 个「冻结窗」到底是对局已结束还是引擎停摆。",
  primary: true,
});

return {
  conclusion:
    `三路独立核验完成：${checked.filter((c) => c.c.verdict === "CONFIRMED").length}/3 复核 CONFIRMED。` +
    " 判定书见 artifact。",
  findings: found.map((x) => ({
    where: `${OUT}/${x.task.id}/REPORT.md`,
    what: `${x.task.id} ${x.task.title}：${x.r.headline}`,
    evidence: `级别=${x.r.level}；复核=${checked.find((c) => c.id === x.task.id)?.c.verdict}；复算=${checked.find((c) => c.id === x.task.id)?.c.recomputed}`,
    status: (checked.find((c) => c.id === x.task.id)?.c.verdict === "CONFIRMED"
      ? "verified"
      : "unconfirmed") as "verified" | "unconfirmed",
    severity: "high" as const,
  })),
  verified: [
    "三路各由独立上下文从原始 PNG / JSON 复算，未采信原件数字",
    "每个方向再由第二道复核员抽 3 个样本独立复算",
  ],
  notCovered: [
    "纯离线只读：零真机、零母本改动",
    "未做 OCR，屏显时间靠放大目视，有 1 秒量化误差",
    "T42 / l1_20261023e4 的 df==0 若仍无解释，属未闭合",
  ],
};
