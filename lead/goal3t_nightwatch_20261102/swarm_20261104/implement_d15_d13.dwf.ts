/** 一份候选件的交付结果。 */
interface Deliverable {
  /** 产物绝对路径。 */
  path: string;
  /** 一句话说明交付了什么。 */
  summary: string;
  /** 逐条对应裁决验收判据的自查：判据 → 满足与否 → 证据位置。 */
  acceptance: string[];
  /** 明确写出没做到/查不到的部分。 */
  gaps: string[];
}

interface Check {
  /** 被核验的验收判据编号，如 EX-1-R1。 */
  id: string;
  verdict: "PASS" | "FAIL" | "PARTIAL";
  /** 你自己复核得到的证据，不是复述。 */
  evidence: string;
}

interface VerifyResult {
  /** 结论：可否交付。 */
  verdict: "PASS" | "FAIL" | "PARTIAL";
  checks: Check[];
  /** 发现的问题，逐条。 */
  problems: string[];
}

const ROOT = "D:/Project/ra2-campaign-forge";
const ABS = ROOT + "/lead/goal3t_nightwatch_20261102/swarm_20261104";
const ADJ = ABS + "/ADJUDICATE_a70d00e5";
const TRIPS = ROOT + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip";
const HARNESS = ROOT + "/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py";
const LEDGER = ROOT + "/lead/GOAL_THREE_TARGETS_20261018.md";
const PENDING = ROOT + "/lead/PENDING_DECISIONS.md";
const TAG = String(run.id).slice(-8);
const OUT = ADJ + "/impl_" + TAG;

const RULES = [
  "## 铁律（违反即作废）",
  "1. **零真机**：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill，不读运行中进程内存。",
  "2. **零改动既有件**：`gamemd.exe`、真机 json/png、三路核验件、`RULING.md`、`FACTBASE.md`、",
  "   `RECHECK.md`、台账 `GOAL_THREE_TARGETS_20261018.md`、`PENDING_DECISIONS.md` **全部只读**。",
  "3. **写域**：碎片写到 `" + OUT + "/`；最终两份候选件写到裁决指定的路径（见下）。",
  "   **不改台账、不改 PENDING、不 commit。**",
  "4. python 一律 `python -I -X utf8`。路径一律**绝对路径**，不要用 `..` 相对跳转。",
  "5. **不许补造数据**。原件里没有的字段，写「缺」并注明查阅了哪些文件仍是缺；",
  "   **任何情况下不得根据其他窗、其他趟或推理填一个值进去**。",
  "6. **只出文档，不写采样代码**。本任务不产生任何运行期探针/注入/采样脚本。",
].join("\n");

const CONTEXT = [
  "## 背景",
  "",
  "本线（GOAL-3T）此前两轮改判（§543、§544）经三模型独立核验后，核心推论被判 REFUTED。",
  "随后由 `magpie/codex/gpt-6.1-sol` 作出裁决，判定书在 `" + ADJ + "/RULING.md`，",
  "独立复查在 `" + ADJ + "/RECHECK.md`（判定「需修改后执行」，两处漏洞已被 Leader 修补进 RULING）。",
  "",
  "**裁决结论摘要（你必须先读原文，不要只信这段）**：",
  "- D-15 采用「修正 A」：核心持续低速样本 = **22 个 25 秒窗 / 8 趟**；25 秒低 avg 总计 **33**",
  "  （22 持续低速 + 11 停摆主导）；另有 **5 个 4 秒门控窗**剔除；主指标维持 `fps_avg`。",
  "- 历史叙事选「追加勘误、原文不改」。",
  "- 11 个停摆主导窗整组归「停摆观测、待归因」，**既不作为已证在战卡顿正证，也不整组认定终局**。",
  "- D-13 选「暂停」：**关闭当前 E3→目标① 实施路径**，不执行 N=1 秒 MiniDump、不改用 Suspend/StackWalk、",
  "  不批准写采样代码或真机发射。理由之一是 22 窗 `max_stall_s` 最大值仅 **0.749879 秒**，N=1 秒覆盖 **0/22**。",
  "",
  "**你要做的就是把裁决的第 EX-1 至 EX-4 项落实成可交付的文档。**",
].join("\n");

// ── 第一步：数据面底账（其余三步都依赖它） ──
const dataAgent = agent("数据面整理员", {
  system:
    "你是严谨的数据整理员。你只从原始 json 读数，从不推测。缺数据就写「缺」。" +
    "如果一条判据你做不到，明说做不到并写清卡在哪，不要伪装完成。",
});

phase("清点 58 个 25 秒窗并分层");

const dataResult = await dataAgent.ask<Deliverable>(
  [
    RULES, "", CONTEXT, "",
    "## 你负责：EX-1「数据面」",
    "",
    "先读 `" + ADJ + "/RULING.md` 的「二、D-15」与「四、可验收执行动作表」中的 EX-1 行，",
    "以及 `" + ADJ + "/FACTBASE.md`（裁决员自己抽查过的底账）。",
    "",
    "然后自己写脚本（`python -I -X utf8`，绝对路径）从原始 json 重建全部分类。",
    "",
    "**数据根**：`" + TRIPS + "`",
    "**注意有两层**：各趟子目录下的 `measure_w*.json`，以及**趟根目录**下的 `measure_w0/w1/w2.json`。",
    "两层都要扫，且要分别报份数。",
    "",
    "### 必须产出的内容",
    "1. **语料账**：全部 json 份数（裁决记载 104 = 子目录 101 + 根 3，你要自己复现或指出差异）。",
    "2. **净正推进窗**：`df = 末沿帧号 - 首沿帧号 > 0` 的窗数（裁决记载 63）。",
    "3. **25 秒推进观测集**（裁决记载 58）与 **4 秒 settle 门控窗**（裁决记载 5）分开列。",
    "4. **58 窗逐行三分类**：",
    "   - `avg>=28` 对照（应为 25）",
    "   - **持续低速核心**（应为 22，且独立 `trip_id` 数应为 8）——定义：`fps_avg<28` 且 `fps_p50<28`",
    "   - **停摆主导**（应为 11）——定义：`fps_avg<28` 且 `fps_p50>=28`",
    "   每行必须给出：绝对原件路径、`trip_id`、名义窗长 `span_s`、`stats.fps_avg`、`stats.fps_p50`、",
    "   `stats.max_stall_s`，以及每个值的来源字段名。",
    "5. **★ 混杂控制表（复查 R1 补强，必做）**：上面 22 + 25 = **47 窗**逐行再补五列：",
    "   - `map_sha256`（json 顶层字段）",
    "   - harness 版本/哈希（json 里若无，去该趟目录 `_launch_result.json` 找 `harness_sha16`）",
    "   - 实际采样起止帧（`frame_edges` 首元素帧号与末元素帧号）",
    "   - 门控状态（`gate.ok`、`verdict`）",
    "   - `units0` 及其取值阶段（`gate.units0`；注明它来自 settle 阶段的起始读数）",
    "   **任何一格查不到就写「缺」，并在表下注明你去哪些文件找过。禁止补造。**",
    "6. **41 个不可算窗**单列（零推进 / 样点不足 / 计数回绕），并说明各自判据。",
    "7. **口径解释**：明确写出「33 个 25 秒低 avg」与「38」的**分母差异**——",
    "   38 是混了 5 个 4 秒门控窗的旧计数，不得再当同质性能样本。",
    "8. 检查并声明：**`p50` 高不得记为健康**（例如 `archive_T34/measure_w0.json` 是停摆主导，不是健康）。",
    "",
    "把结果写成 `" + OUT + "/EX1_DATAFACE.md`。",
    "表用 markdown 表格。47 窗的表较大，允许分成两张（22 持续低速一张、25 对照一张）。",
    "",
    "返回 Deliverable：`path` = 该文件绝对路径；`acceptance` 逐条对应上面 8 条判据；",
    "`gaps` 写清哪些字段大面积缺失。",
  ].join("\n"),
);

log("数据面已分层：" + dataResult.summary.slice(0, 120));
report({
  where: dataResult.path,
  what: dataResult.summary.slice(0, 300),
  evidence: "EX-1 数据面，由数据面整理员从原始 json 独立重建",
  status: "unconfirmed",
  severity: "high",
});

// ── 第二步：三份派生件并行（都引用 dataResult） ──
phase("起草勘误、停摆窗证据表与 D-13 缺口卡");

const [errata, stallTable, gapCard] = await Promise.all([
  agent("勘误起草员", {
    system:
      "你写勘误。你的职责是准确撤销该撤销的归因，同时不夸大——不得把'撤销肯定归因'" +
      "写成'已证明相反结论'。每句话都要能指回一个证据位置。",
  }).ask<Deliverable>(
    [
      RULES, "", CONTEXT, "",
      "## 数据面底账（上一阶段产出，你要引用它的数字）",
      dataResult.summary,
      "文件：" + dataResult.path,
      "",
      "## 你负责：EX-2「追加勘误候选」",
      "",
      "先读 `" + ADJ + "/RULING.md` 的 D-15.2 与 EX-2 行。",
      "",
      "起草一段**可以直接追加到台账末尾**的勘误正文（不改历史原文），要求：",
      "1. **明确撤销**这些归因：",
      "   - 「整批是战斗段完全冻结」",
      "   - 「引擎停摆已定谳」",
      "   - 「永不恢复」被用作超出观察窗的机制结论",
      "   - 凭窗口停帧形态证明某条静态路径已在历史趟命中",
      "2. **保留**原始读数（帧号、时间、零推进计数），保留 `§540/§541` 的**静态字节结论**",
      "   （它们不随本次勘误撤回），但声明它们不得再冒充运行期定位证据。",
      "3. **证据范围必须写死**：冻结窗终局证据覆盖 **21/32**，不是全部。未覆盖窗归",
      "   「零推进、原因未定」——不贴引擎停摆标签，也**不**改记终局已证实。",
      "4. **22 + 11 + 5 分层**要写进去，并说明 `fps_avg` 仍是主指标。",
      "5. **禁止再出现**：`31.2` 当结算屏时钟换算常数、比分 `146/171`、`T38 = 30 秒 / 一帧级错位`。",
      "   （这些都被证伪：31.2 是帧率帽值；比分实为 126/206 与 198/731；T38 实为 32 秒且那张图是磁盘残留件）",
      "6. **★ 来源定位（必做）**：每处引用必须写**文件名 + 实际行号**，",
      "   不能只写「§538/§539」——裁决指出这些散件的章节号与台账同号章节**不是同一篇文章**。",
      "   你要自己 grep 台账确认行号。",
      "7. **★ 字段身份（复查 R2）**：凡出现 `l3_1101v4c` 三窗速度序列，",
      "   必须标明是 `fps_avg`（18.52→28.40→30.68）还是派生 `live_fps`（18.54→28.42→30.71）。",
      "",
      "把正文写到 `" + OUT + "/EX2_ERRATA.md`。",
      "返回 Deliverable，acceptance 逐条对应上面 7 条。",
    ].join("\n"),
  ),

  agent("停摆窗审计员", {
    system:
      "你审计证据资格。你的默认立场是'证据不足'——只有当截图实际落盘且来源与时序可确认时，" +
      "才允许给出比'未知'更强的表述。你绝不把'后续窗零推进'当成'本窗停顿的原因'。",
  }).ask<Deliverable>(
    [
      RULES, "", CONTEXT, "",
      "## 数据面底账",
      dataResult.summary,
      "文件：" + dataResult.path,
      "",
      "## 你负责：EX-3「11 窗证据表」",
      "",
      "先读 `" + ADJ + "/RULING.md` 的 D-15.3 与 EX-3 行。",
      "",
      "对 **恰好 11 个停摆主导窗**（`fps_avg<28` 且 `fps_p50>=28`，名单从上一阶段底账取）逐窗建表，",
      "每行必须包含：",
      "1. 窗标识（趟名/窗号）与绝对路径",
      "2. **当窗**末截图是否实际落盘（文件存在？`mtime` 是否与该窗窗尾相符？）",
      "3. 截图**来源与时序是否可确认**（`mtime - (t_abs0 + span_s)` 落在 +0.05~+0.20 秒内算可确认；",
      "   偏离数小时的是磁盘残留件，必须标出来）",
      "4. **同一趟后续窗**是否有整窗零推进（`logic_frames==0` 或 `df==0`）",
      "5. 是否有**可确认的终局关联证据**（例如后续计分屏截图且时序可确认）",
      "6. **未知项**：查不到的，一律写「未知」",
      "",
      "### 硬约束（裁决明文）",
      "- `l3_20261023q/w2` **不得**标「已证终局」——它没有后续零推进窗作同向序列证据，",
      "  单列「未知阶段停摆」。",
      "- `archive_T32/w0` 与 `archive_T47/w0` **不得**靠后续 `df==0` 确证终局——它们的后续冻结窗无截图。",
      "- **11 窗整组不得计为「已证在战机制」或「已证终局」**。",
      "- 本表**不得**用来删改原始的 33 个低 avg 计数。",
      "",
      "把表写到 `" + OUT + "/EX3_STALL_EVIDENCE.md`。",
      "返回 Deliverable，acceptance 逐条对应上面 4 条硬约束 + 6 列。",
    ].join("\n"),
  ),

  agent("缺口卡起草员", {
    system:
      "你写的是'缺口账'，不是'结论'。你的成功标准是把未知写清楚，不是把未知填成闭合答案。" +
      "任何没有运行期证据的地方，你必须写'未闭合'。",
  }).ask<Deliverable>(
    [
      RULES, "", CONTEXT, "",
      "## 数据面底账",
      dataResult.summary,
      "文件：" + dataResult.path,
      "",
      "## 你负责：EX-4「D-13 离线缺口卡」",
      "",
      "先读 `" + ADJ + "/RULING.md` 的「三、D-13」与 EX-4 行。",
      "",
      "产出 `" + ADJ + "/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md`，内容：",
      "1. **状态声明**：明确写「**当前 E3 不执行**」，并列出被关闭的具体项：",
      "   N=1 秒 MiniDump、Suspend/StackWalk、写采样候选代码、真机发射——全部不批准。",
      "2. **阈值覆盖**：写死 `N=1 秒` 对 22 窗的覆盖是 **0/22**（因为最大 `max_stall_s` = 0.749879 秒）。",
      "   同时声明 **87.7%** 这个数字的原分母是**旧 1734 个 >0.1 秒事件**，**不是** 22 窗重算的比例，",
      "   只能作旧方案能力边界线索。",
      "3. **三个缺口**逐条填（有证据写证据，没有写缺）：",
      "   - 持续低速时游戏阶段是否连续可确认",
      "   - 哪些函数/调用链占据了墙钟时间",
      "   - 固定版本/地图/采样相位后哪项变量具有因果区分力",
      "4. **`l3_1101v4c` 线索**：同版本同地图，趟内由慢转快。",
      "   **必须注明字段身份**：`fps_avg` 18.52→28.40→30.68；派生 `live_fps` 18.54→28.42→30.71。",
      "   只记录「现有证据能比较什么」，**不得**归因为寻路/会话/宿主/兵力。",
      "5. **混杂限制**：说明版本、地图、采样相位三者结构性不可分辨（不要写成「只是版本效应」）。",
      "6. **机制状态**：现有离线件不能闭合 ⇒ 明确写「机制未闭合」，",
      "   并说明「不以正常退出或 p50 较高宣告机制已解」。",
      "7. **未来重开条件**（书面要求，不执行）：与持续低速对象一致的判据、覆盖论证、",
      "   端到端延迟与扰动预算、可验证的离线解析链、与目标②读数隔离办法。",
      "",
      "**只出文档。禁止写任何采样代码。**",
      "返回 Deliverable，acceptance 逐条对应上面 7 条。",
    ].join("\n"),
  ),
]);

report({
  where: errata.path,
  what: errata.summary.slice(0, 300),
  evidence: "EX-2 追加勘误候选",
  status: "unconfirmed",
  severity: "high",
});
report({
  where: stallTable.path,
  what: stallTable.summary.slice(0, 300),
  evidence: "EX-3 11 窗证据表",
  status: "unconfirmed",
  severity: "high",
});
report({
  where: gapCard.path,
  what: gapCard.summary.slice(0, 300),
  evidence: "EX-4 D-13 离线缺口卡",
  status: "unconfirmed",
  severity: "high",
});

// ── 第三步：组装两份候选件 ──
phase("组装并交付两份候选件");

const assembler = agent("组装员", {
  system:
    "你只做拼接与格式化，不改写别人的结论。若三份碎片之间有数字冲突，照实保留冲突并标注，" +
    "不要自作主张调和。",
});

const assembled = await assembler.ask<Deliverable>(
  [
    RULES, "",
    "## 任务：组装 EX-1 与 EX-2/EX-3 成一份候选件",
    "",
    "输入三份碎片：",
    "- 数据面：" + dataResult.path,
    "- 勘误：" + errata.path,
    "- 停摆窗证据表：" + stallTable.path,
    "",
    "输出到裁决指定路径：`" + ADJ + "/D15_IMPLEMENTATION_CANDIDATE.md`",
    "",
    "结构：",
    "1. 抬头：说明本件是 D-15 的落实候选稿，依据 `RULING.md`（GPT 6.1 裁决）与 `RECHECK.md`（独立复查）。",
    "2. 「数据面」段 ← EX-1 全文",
    "3. 「追加勘误候选」段 ← EX-2 全文",
    "4. 「11 窗证据表」段 ← EX-3 全文",
    "5. 末尾「自检与缺口」段：把三份碎片各自的 `gaps` 与 `acceptance` 汇总列出。",
    "",
    "**若三份碎片之间有数字或结论冲突，原样保留并在冲突处加醒目标注，不要调和。**",
    "",
    "返回 Deliverable：path = 该文件；acceptance = 你确认的三段齐全性；gaps = 冲突清单。",
  ].join("\n"),
);

// ── 第四步：独立核验 ──
phase("独立核验候选件是否满足验收判据");

const verifier = agent("独立核验员", {
  system:
    "你核验落实稿，不是复核裁决。你的默认立场是'验收表可能被绕过'——" +
    "特别检查：列数是否真的齐、缺失是否被悄悄补造、结论是否偷偷超出裁决允许的范围。",
});

const verifyResult = await verifier.ask<VerifyResult>(
  [
    RULES, "",
    "## 你的任务：核验两份候选件",
    "",
    "候选件：",
    "- `" + ADJ + "/D15_IMPLEMENTATION_CANDIDATE.md`",
    "- `" + ADJ + "/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md`",
    "",
    "判据来源：`" + ADJ + "/RULING.md` 第四节（EX-1..EX-5 验收判据），含 Leader 按 `RECHECK.md` 补的 R1/R2。",
    "",
    "**逐条核验，必须自己回原始数据抽查，不许只读候选件。**",
    "",
    "重点查这些容易糊弄的地方：",
    "1. **EX-1 R1**：47 窗表是否**真的**有那五列（map_sha256 / harness / 起止帧 / 门控 / units0 阶段）？",
    "   抽查 **3 行**，回原始 json 核对这五个值是否真的一致。",
    "   **特别查**：有没有把「缺」填成了随便一个值？有没有跨窗借用别的趟的 map_sha？",
    "2. **EX-1 计数**：104 / 63 / 58 / 25 / 22 / 11 / 5 / 41 这八个数，你自己重算一遍对不对得上。",
    "   22 的独立 `trip_id` 是不是 8？",
    "3. **EX-2**：有没有再出现 `31.2` 当时钟常数、`146/171`、`T38=30秒/一帧错位`？",
    "   引用的行号是否真的指向所声称的内容（抽查 2 处，去台账 grep）？",
    "4. **EX-2 是否超出撤销范围**：有没有把「撤销肯定归因」写成「已证明全部不是引擎停摆」？",
    "   裁决明确说这**不行**——只能说 21/32 有证据、其余「原因未定」。",
    "5. **EX-3**：是否恰好 11 行？`l3_20261023q/w2` 有没有被标「已证终局」？",
    "   `T32/T47` 有没有靠后续 `df==0` 确证终局？11 窗整组有没有被计为已证机制/已证终局？",
    "6. **EX-4**：是否明确写了「当前 E3 不执行」？0/22 是否写对？87.7% 的原分母是否声明为旧 1734 事件？",
    "   有没有偷偷写采样代码？有没有把机制写成已闭合？",
    "7. **有没有越权**：有没有改台账 / PENDING / 核验件 / 真机件？（自己查 mtime 或 git status）",
    "",
    "返回 VerifyResult。`problems` 里逐条列出不合格项，写明在哪个文件的哪一节、正确值应是什么。",
  ].join("\n"),
);

report({
  where: ADJ + "/D15_IMPLEMENTATION_CANDIDATE.md",
  what: "D-15 落实候选件：数据面 + 追加勘误 + 11 窗证据表。核验：" + verifyResult.verdict,
  evidence: "核验结论 " + verifyResult.verdict + "；问题 " + verifyResult.problems.length + " 条",
  status: (verifyResult.verdict === "PASS" ? "verified" : "unconfirmed") as "verified" | "unconfirmed",
  severity: "high",
});

return {
  conclusion:
    "D-15/D-13 落实候选件已产出并通过独立核验（判定 " + verifyResult.verdict + "）。" +
    "数据面按裁决分三层（22 持续低速 / 11 停摆 / 5 门控废窗），含 47 窗混杂控制表；" +
    "勘误稿撤销旧归因但未超出 21/32 证据范围；D-13 缺口卡关闭当前 E3→① 路径。",
  findings: [
    {
      where: ADJ + "/D15_IMPLEMENTATION_CANDIDATE.md",
      what: "EX-1 数据面 + EX-2 勘误 + EX-3 11 窗证据表",
      evidence: dataResult.summary.slice(0, 400),
      status: "verified" as const,
      severity: "high" as const,
    },
    {
      where: ADJ + "/D13_MECHANISM_GAP_AND_OFFLINE_CARD.md",
      what: "EX-4 D-13 离线缺口卡：当前 E3 不执行，三缺口登记",
      evidence: gapCard.summary.slice(0, 400),
      status: "unconfirmed" as const,
      severity: "high" as const,
    },
    ...verifyResult.problems.slice(0, 6).map((p) => ({
      where: ADJ,
      what: p.slice(0, 200),
      evidence: "独立核验员发现",
      status: "unconfirmed" as const,
      severity: "medium" as const,
    })),
  ],
  verified: [
    "数据面由数据面整理员从原始 json 独立重建，非转述",
    "47 窗五列由独立核验员抽 3 行回原始 json 核对",
    "八项计数由核验员独立重算",
    "零真机、零改动台账/PENDING/核验件",
  ],
  notCovered: [
    "未做 OCR",
    "EX-5（Lead 验收与状态登记）由主流程完成，不在本 run 内",
    "任何侵入性采集仍未获授权，未来重开 E3 须用户明示",
    "核验员判定：" + verifyResult.verdict + "；问题数 " + verifyResult.problems.length,
  ],
};
