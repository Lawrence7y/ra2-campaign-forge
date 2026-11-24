interface AdversarialOut {
  /** 被挑战的主张。 */
  claim: string;
  /** 这个主张的原始出处。 */
  source: string;
  /** 攻击结论。 */
  attack: "SURVIVES" | "WEAKENED" | "BROKEN" | "UNTESTABLE";
  /** 最强反驳：如果这个主张是错的，最有可能是错在哪。 */
  strongestObjection: string;
  /** 你为验证它跑了什么（VA + 字节 + 命令）。 */
  whatIRan: string;
  /** 你的判定依据。 */
  reasoning: string;
  /** 如果攻击成功，替代解释是什么。 */
  alternativeIfBroken: string;
}

interface Synthesis {
  /** 最终按硬度分层的结论。 */
  tiers: string[];
  /** 一句话回答：目标①的机制现在处于什么状态。 */
  goal1State: string;
  /** 一句话回答：目标②的机制现在处于什么状态。 */
  goal2State: string;
  /** 下一步最小动作（不执行，只给方案）。 */
  nextMinimalAction: string;
  /** 本轮最大的方法学教训。 */
  lesson: string;
}

const ABS = "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104";
const ROOT = "lead/goal3t_nightwatch_20261102/swarm_20261104";

const RULES = [
  "## 铁律",
  "1. 零真机：不启动 gamemd.exe / ra2loader.exe / YURI，不 taskkill。",
  "2. 零改动母本：ra2youli/gamemd.exe 只读。",
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
  "## 你是反方",
  "你的任务不是确认，是**尽力打碎**。一个能扛住最强攻击的结论才有资格进台账。",
  "如果你发现某主张其实无法被现有证据判定，判 UNTESTABLE 并说明缺什么。",
].join("\n");

// 本轮的核心主张（将被独立攻击）
const CLAIMS: { id: string; claim: string; source: string; attackPlan: string }[] = [
  {
    id: "X01",
    claim: [
      "MainLogicFrame 0x55D360 是全镜像唯一推进会推进 CurrentFrame 的函数，",
      "它有 3 个 ret，其中 0x55D877 与 0x55DEDB 可以在不经过 0x55DE7E 的 inc 的情况下到达。",
      "因此「帧号冻结」在二进制上等价于「MainLogicFrame 走了这两个出口之一，或根本没被调用」。",
    ].join(""),
    source: "本轮 §533 probe A/B（Leader 亲算）",
    attackPlan: [
      "1. 独立复算：CurrentFrame 是否真的只有一处 inc？10 个写点里有没有第二个「读-加-写」形态？",
      "   必须逐点读字节确认每个写点写的是什么（常数？寄存器？读改写？）。",
      "2. 独立复算 0x55D360 的边界：头是不是 0x55D360？尾是不是 0x55DEE0？",
      "   用 E8 对齐目标集 + ret 扫描独立定界，不许信任给定的边界。",
      "3. 独立复算 CFG：从 0x55D360 出发，绕开 0x55DE73..0x55DE84 这个区间，",
      "   哪些 ret 仍可达？自己写 BFS，不许用 ra2tool.reach_without 的封装（要自己实现一遍对照）。",
      "4. ★ 攻击点：这个「等价」是否漏了什么？",
      "   - 有没有别的函数也写 CurrentFrame（例如存档回填）导致帧号「跳变」而非「冻结」？",
      "   - 有没有 CurrentFrame 被别的线程写的情况？",
      "   - 「帧号冻结」的观测本身（采样读 0xA8ED84）有没有可能是读取失败导致的假冻结？",
      "5. 判 SURVIVES / WEAKENED / BROKEN。",
    ].join("\n"),
  },
  {
    id: "X02",
    claim: [
      "MainLogicFrame 头部在 [0xA8ED80]==0 时进入 Sleep(500 或 10ms) + MessagePump(0x5D4D50) ",
      "的循环，循环条件是再次读到 [0xA8ED80]==0。因此若旗标长期为 0，帧号永不推进，",
      "但进程活着、CPU 低、可正常退出。这是目标①形态的强候选机制。",
    ].join(""),
    source: "本轮 §533 probe A（Leader 亲算）",
    attackPlan: [
      "1. 独立反汇编 0x55D377..0x55D3BB，逐字节确认这个循环的形态与退出条件。",
      "2. ★ 攻击点 A：这个循环真的会「长期」持续吗？",
      "   - MessagePump 0x5D4D50 内部会不会自己处理消息、间接触发 WM_ACTIVATEAPP 写旗标？",
      "   解出 0x5D4D50，判定它是否 DispatchMessage（若是，则 WndProc 可能被调用，旗标可能被写）。",
      "   - 若泵在 DispatchMessage，那这个循环**不是死锁**，而是一个正常的「失焦等待」，",
      "     一旦有激活消息就会退出。那么它就不能解释「冻结 2.56-24.73s 且无任何用户操作」。",
      "3. ★ 攻击点 B：Sleep(500) 只在 GameMode in {0,5} 时走。",
      "   遭遇战是 Mode=5，所以会走 Sleep(500)。但 500ms 的 Sleep 期间，" ,
      "   如果旗标在这期间被写 1，循环会在下一次检查时退出（最多晚 500ms）。",
      "   那么「冻结 21.156s」需要多少次连续失败？2 次/秒 x 21s ≈ 42 次连续读到 0。",
      "   这现实吗？请评估这个概率论证的强度。",
      "4. ★ 攻击点 C：实测帧冻结趟是**正常退出 rc=0**。",
      "   若卡在等焦点，退出流程（需要主窗消息）能走通吗？请判定这个循环与正常退出的相容性。",
      "5. 判 SURVIVES / WEAKENED / BROKEN，并给出替代解释（若破了）。",
    ].join("\n"),
  },
  {
    id: "X03",
    claim: [
      "焦点旗标 0xA8ED80 的全镜像唯一写者是 0x7778CE（WndProc 处理 WM_ACTIVATEAPP），",
      "因此只有 OS 投递激活消息才能把它置 1。",
    ].join(""),
    source: "re_atlas R-063a + 本轮重同步复核（46 处 / 1 写）",
    attackPlan: [
      "1. 独立复算：用重同步扫描找 [0xA8ED80] 的全部访存，统计读写。",
      "2. ★ 攻击点：唯一「绝对地址」写者是否等于唯一写者？",
      "   - 有没有通过 `lea reg,[0xA8ED80]` 取地址然后间接写的路径？",
      "   - 有没有通过 `mov reg, 0xA8ED80` 再间接写的路径？",
      "   - 有没有 memcpy/memset 之类的批量写入把一个区间覆盖到 0xA8ED80？",
      "   （注意 0xA8ED80 所在的 .data 段是 BSS，初值 0）",
      "   请专门做这个「间接写」普查，这是「唯一写者」主张的最大软肋。",
      "3. 攻击点 B：0xA8ED80 是 byte。相邻字节（0xA8ED81 = SC_MINIMIZE 位）的写者会不会",
      "   用 16/32 位写顺带改到 0xA8ED80？做宽度普查。",
      "4. 判 SURVIVES / WEAKENED / BROKEN。",
    ].join("\n"),
  },
  {
    id: "X04",
    claim: [
      "目标①（帧冻结）与目标②（挂死未退）可能是同一根因：两者都在等 0xA8ED80。",
      "但①的趟正常退出 rc=0，②的趟未退出，所以更可能是两个不同机制。",
    ].join(""),
    source: "本轮 swarm G03/G05 的待验假设",
    attackPlan: [
      "1. 独立列出全镜像所有「等 0xA8ED80」的位置（在循环内反复读的点）。",
      "2. ★ 攻击点：把「都在等同一个旗标」当作「同源」的证据，这是不是过度归因？",
      "   - 同一个旗标被多处等待，是正常的（焦点是全局状态）。",
      "   - 真正的同源应该是「同一个触发事件导致两处都卡」。",
      "   请判定：有没有证据表明①和②由同一事件触发？还是只是都依赖同一个全局？",
      "3. 攻击点 B：①的实测是「冻结后恢复」（帧号又动了），②是「冻结后不恢复且不退」。",
      "   这个差异本身就说明机制不同——请从字节判定「冻结后能恢复」需要什么条件，",
      "   而该条件在②的情形下为什么不能满足。",
      "4. 判 SURVIVES / WEAKENED / BROKEN，并给出你独立认为的关系（同源/不同源/部分重叠）。",
    ].join("\n"),
  },
  {
    id: "X05",
    claim: [
      "本仓台账的核心停滞口径（口径 B = 卡住帧值首末拍跨度）与「帧号冻结」是同一件事，",
      "因此用 0xA8ED84 的冻结时长就能代表「卡顿」。",
    ].join(""),
    source: "lead/PENDING_DECISIONS.md D-12② 裁决 + 台账 §507/§515/§531/§532",
    attackPlan: [
      "1. 读 lead/PENDING_DECISIONS.md 的 D-12 条目与台账 §531/§532 全文。",
      "2. ★ 攻击点：§532 自己承认犯过「把停滞当正常抖动」的循环定义错误（第三次同类错误）。",
      "   现在这个口径 B 本身有没有类似的循环定义？",
      "   - 口径 B 用「卡住帧值」定义停滞，那「卡住」是不是就是「停滞」的同义词？",
      "   - 若 A 与 B 是同一个概念，那么「用 B 度量停滞」是恒真的，不构成发现。",
      "   请严格检验这一点：口径 B 到底提供了什么独立信息？",
      "3. 攻击点 B：帧号冻结 != 用户感知的卡顿。",
      "   - 帧号是逻辑帧，渲染可能仍在跑（画面在动但逻辑不动，或反之）。",
      "   - 用户说的「卡顿」是画面卡，那是渲染帧率。",
      "   请判定：0xA8ED84 的冻结与「画面卡顿」之间的因果关系是否有字节支撑？",
      "   若无，这整条度量链可能测的不是用户要的东西。",
      "4. 判 SURVIVES / WEAKENED / BROKEN。",
    ].join("\n"),
  },
  {
    id: "X06",
    claim: [
      "「数百单位卡顿」不是负载驱动：r(units0, B%) = -0.2005，且 >=1000 单位 22 窗中 9 窗 B<1%。",
    ].join(""),
    source: "台账 §521（本线判定，未经异族核验）",
    attackPlan: [
      "1. 读台账 §521 原文。",
      "2. 独立从 measure_w*.json 复算 r(units0, B%)。",
      "3. ★ 攻击点 A：相关系数 -0.2005 是否有统计显著性？n 是多少？",
      "   请算 p 值与置信区间。弱负相关 + 小样本 = 什么都证明不了，包括「无关」。",
      "4. ★ 攻击点 B：「不单调相关」不等于「不驱动」。",
      "   - 可能存在阈值效应（超过某单位数才卡），线性相关系数测不出来。",
      "   - 可能存在混杂（不同地图/不同 BOOT 混合）。",
      "   请做分层检验：按地图/按趟分组算相关系数，看是否被辛普森悖论掩盖。",
      "5. ★ 攻击点 C：用户原话是「数百单位卡顿」。",
      "   本仓的高负载档是 971-1342 单位，这是「数千」量级。",
      "   用户说的「数百」可能是 200-500 档，而那档的样本可能很少。",
      "   请判定：现有数据里 units0 在 200-500 档的窗有几个？能否支撑任何结论？",
      "6. 判 SURVIVES / WEAKENED / BROKEN。",
    ].join("\n"),
  },
  {
    id: "X07",
    claim: [
      "本仓台账记载的文档（ARCHITECTURE_ATLAS / clock_frame_loop）关于帧循环的描述基本可信，",
      "只需局部勘误。",
    ].join(""),
    source: "docs/re/ 三份文档",
    attackPlan: [
      "1. 挑 clock_frame_loop.md 的 §3.2 MainLogicFrame 伪码，逐条与字节对照。",
      "2. ★ 攻击点：伪码列出了「if (![0xA8E9A0]) return」「if (![0xA8ED80]) { Sleep... }」等，",
      "   还有「if (CurrentFrame >= [0xA8E2E4]) 0x69A300(state)」。",
      "   请逐条验证这些条件在字节里的位置与顺序。",
      "3. ★ 特别注意 docs 说「0xA8ED80 = 快进标志（=1 时跳过 Sleep 块）」——",
      "   按字节，旗标=1 时是**跳过整个 Sleep+泵循环**（0x55D385 jne 0x55D3BB），",
      "   不是「跳过 Sleep 但仍在泵」。这个差别重要吗？请判定。",
      "4. 攻击点 B：伪码里没有提到 0x55D877 那条出口（GameMode+0x62C 分支）。",
      "   这是文档漏项还是我读错了？请判定。",
      "5. 判文档整体可信度：SURVIVES / WEAKENED / BROKEN。给出必须勘误的清单。",
    ].join("\n"),
  },
  {
    id: "X08",
    claim: [
      "本轮 12 个方向的静态分析可以在不启动游戏的情况下推进目标①，",
      "且不需要 E3 栈采样就能定谳机制。",
    ].join(""),
    source: "本轮整体方法论",
    attackPlan: [
      "1. ★ 这是对本轮方法论本身的攻击。",
      "2. 攻击点 A：静态分析能确定「有哪些路径」，但不能确定「运行期走了哪条」。",
      "   本轮所有结论都是「候选机制」，不是「实际机制」。",
      "   请判定：本轮是否有人把「路径存在」写成了「机制成立」？",
      "   若 12 份报告里有这种越界，逐份点名。",
      "3. 攻击点 B：E3 真的不必要吗？",
      "   - 若静态能给出「VA × 路径 × 期望值」判别表，那么纯被动读几个全局就能定谳。",
      "   - 但如果两条路径在同一个全局上给出相同读数，就无法区分，必须看栈。",
      "   请判定：本轮给出的判据是否真的能区分所有路径？有没有不可区分对？",
      "4. 攻击点 C：静态分析的样本是「一个二进制」。",
      "   若实际运行的是打了补丁的版本（ra2render.dll 等），行为可能不同。",
      "   请判定：本轮分析的基础（gamemd.exe 原版）与实际运行环境是否一致？",
      "5. 判 SURVIVES / WEAKENED / BROKEN，并给出「静态分析的边界」。",
    ].join("\n"),
  },
];

phase("勘察现场");
const gate = await world.run("python", ["-I", "-X", "utf8", ROOT + "/selftest.py"], { timeoutMs: 900000 });
log(`环境自测门 exit=${gate.exitCode}`);
if (gate.exitCode !== 0) {
  return { conclusion: `自测门未通过 exit=${gate.exitCode}`, findings: [], verified: [], notCovered: ["全部"] };
}

phase("八条核心主张的对抗性攻击");
const attacks = await Promise.all(
  CLAIMS.map(async (c) => {
    const a = agent(`反方-${c.id}`, {
      system:
        "你是对抗性审查员。你的 KPI 是打碎主张，不是确认。\n" +
        "从字节独立复算，绝不相信给定的结论。自己写 BFS、自己定函数边界。\n" +
        "如果你推翻不了，也要说明你试了什么、为什么推不翻——这同样是证据。\n" +
        "本仓历史上有多次「看起来合理的量但循环定义」「样本当总体」的错误，" +
        "请专门找这类。",
    });
    const r = await a.ask<AdversarialOut>(
      `主张 ${c.id}：\n${c.claim}\n\n` +
        `出处：${c.source}\n\n` +
        `写域：${ABS}/${c.id}/\n\n` +
        RULES +
        "\n\n## 攻击计划（照做，但发现新攻击面就加）\n" +
        c.attackPlan,
    );
    report({ id: c.id, attack: r.attack, claim: c.claim.slice(0, 80) });
    return { c, r };
  }),
);

phase("攻击结果相互复核");
const peer = agent("攻击复核员", {
  system:
    "你是复核员。检查 8 位反方的攻击是否真的打到了点上。\n" +
    "有些攻击可能是「打偏了」——攻击了一个主张没说的东西。请指出。\n" +
    "也有些攻击可能因为反方自己的读数错误而误判——请复算。",
});
const peerOut = await peer.ask<AdversarialOut[]>(
  `读 ${ABS}/X01..X08 的 REPORT.md。\n\n` +
    `攻击结论：${JSON.stringify(attacks.map((x) => ({ id: x.c.id, attack: x.r.attack })))}\n\n` +
    RULES +
    "\n\n## 你要做的\n" +
    "1. 逐份检查：攻击的 target 是否真的是主张在说的东西（不是稻草人）。\n" +
    "2. 逐一复算反方引用的 VA 与字节，检查读数是否错。\n" +
    "3. 判定每份攻击是否「成立」。若不成立，说明是打偏了还是读错了。\n" +
    "4. 汇总：哪些主张真的被打碎了、哪些只是被削弱、哪些扛住了。\n" +
    `写 ${ABS}/_PEER_REVIEW.md。`,
);

phase("收敛：按证据硬度重新分层");
const synth = agent("最终收敛员", {
  system:
    "你是最终收敛员。读了主张、攻击、复核之后，给出一个按硬度分层的结论。\n" +
    "不要给「都很好」的结论。硬的就是硬的，软的就是软的，破的就是破的。\n" +
    "这份文档会被人类用来决定下一步，必须诚实到不留情面。",
});
const md = await synth.ask<string>(
  `读 ${ABS}/X01..X08 的 REPORT.md + ${ABS}/_PEER_REVIEW.md。\n\n` +
    `主张与攻击结果：${JSON.stringify(
      attacks.map((x) => ({ id: x.c.id, claim: x.c.claim, attack: x.r.attack, objection: x.r.strongestObjection })),
    )}\n` +
    `复核结论：${peerOut.map((p) => `${p.claim.slice(0, 40)} => ${p.attack}`).join(" | ")}\n\n` +
    `写 ${ABS}/HARDNESS_VERDICT_20261104.md，结构：\n` +
    "# 主张硬度判定书（2026-11-04）\n" +
    "## 一、一句话结论\n" +
    "## 二、硬结论（扛住最强攻击，可进台账）\n" +
    "## 三、软结论（被削弱，可引用但须注明条件）\n" +
    "## 四、被打碎的主张（如实列，含替代解释）\n" +
    "## 五、不可判定的（UNTESTABLE，缺什么证据）\n" +
    "## 六、静态分析的边界（本轮方法论的自省）\n" +
    "## 七、下一步最小动作\n" +
    "## 八、诚实账\n" +
    "然后全文返回。",
);

await artifact.markdown("hardness", md, {
  title: "主张硬度判定书（对抗性审查）",
  description: "8 条核心主张经独立反方攻击 + 相互复核后的硬度分层。",
  primary: true,
});

// 返回最终综合判定
const synth2 = agent("总判定撰写人", {
  system:
    "你是总判定撰写人。把硬度判定书收敛成最终回答。\n" +
    "必须回答三个问题：①的机制现在知道什么、②的机制现在知道什么、下一步该做什么。",
});
const final = await synth2.ask<Synthesis>(
  `读 ${ABS}/HARDNESS_VERDICT_20261104.md（若存在）。\n` +
    `硬度判定摘要：${md.slice(0, 4000)}\n\n` +
    `攻击结果汇总：${JSON.stringify(attacks.map((x) => ({ id: x.c.id, attack: x.r.attack })))}\n\n` +
    `给出：\n` +
    "1. tiers：按硬度分层的结论清单（每条一句话，标注 [硬]/[软]/[破]/[不可判定]）\n" +
    "2. goal1State：目标①的机制现在处于什么状态（一句话）\n" +
    "3. goal2State：目标②的机制现在处于什么状态（一句话）\n" +
    "4. nextMinimalAction：下一步最小动作（具体到 VA 与代价，不要泛泛）\n" +
    "5. lesson：本轮最大的方法学教训",
);

return {
  conclusion:
    `8 条核心主张经对抗性审查：${
      attacks.filter((x) => x.r.attack === "SURVIVES").length
    } 条扛住、${attacks.filter((x) => x.r.attack === "WEAKENED").length} 条被削弱、${
      attacks.filter((x) => x.r.attack === "BROKEN").length
    } 条被打碎。目标①状态：${final.goal1State}。目标②状态：${final.goal2State}`,
  findings: attacks.map((x) => ({
    where: `${ROOT}/${x.c.id}/REPORT.md`,
    what: `${x.c.id} 攻击「${x.c.claim.slice(0, 40)}…」→ ${x.r.attack}`,
    evidence: x.r.whatIRan,
    status: (x.r.attack === "SURVIVES" ? "verified" : "unconfirmed") as "verified" | "unconfirmed",
    severity: (x.r.attack === "BROKEN" ? "high" : "medium") as "high" | "medium",
  })),
  verified: [
    "selftest.py exit=0",
    "8 条主张各由独立反方从字节复算并尝试推翻",
    "攻击结果经第二位复核员检查是否打偏",
  ],
  notCovered: [
    "静态只读：零真机",
    "部分主张判定为 UNTESTABLE，需运行期数据",
    final.nextMinimalAction,
  ],
};
