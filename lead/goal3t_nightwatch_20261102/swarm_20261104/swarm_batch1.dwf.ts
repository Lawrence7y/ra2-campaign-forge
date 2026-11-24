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
  /** 完成度：full / partial / failed。 */
  status: "full" | "partial" | "failed";
}

interface Check {
  /** 被核验的编号。 */
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
  "2. 零改动母本：ra2youli/gamemd.exe 只读，一个字节都不许改。",
  "3. 写域仅限分配给你的目录。不改台账、不写 re_atlas/、不动冻结件。",
  "4. 不 commit / 不 push。",
  "5. python 一律 python -I -X utf8。",
  "",
  "## 解码口径（本仓血泪教训）",
  "禁止 for ins in md.disasm(blob, va) 扫全镜像——capstone 遇不可解码字节静默停止，",
  "会造出「0 处命中」的假零（本仓 G-23，已犯过多次）。必须重同步解码，或直接用共享引擎：",
  "    import sys",
  "    sys.path.insert(0, r\"" + ABS + "\")",
  "    from ra2tool import Engine",
  "    eng = Engine()",
  "    print(eng.coverage)             # 必须打印自证：100.00% / 1394120 insns",
  "    eng.disasm(va, n)               # 反汇编窗口",
  "    eng.rd(va,n) / eng.u32(va)      # 原始字节 / dword",
  "    eng.resolve_iat(slot_va)        # -> ('DLL.dll','Func')",
  "    eng.disp_hits(global_va)        # 绝对全局访存 -> [(va,'W'|'R',mnem,op_str)]",
  "    eng.disp_hits_field(disp)       # [reg+disp] 任意基址家族",
  "    eng.func_rets(lo,hi)            # (rets, succ)",
  "    eng.reach_without(head,hi,cut_lo,cut_hi)  # 绕开某直线块的可达集",
  "    eng.loop_backedges(lo,hi)       # 回边",
  "",
  "## 函数边界纪律（G-83）",
  "找函数尾不许用 ±0x200 线性窗口（会读到上一函数序言）。必须用 ret 扫描 + E8 对齐头集，",
  "或分支图闭包。若只凭线性窗，必须明写「边界未经分支图验证」。",
  "",
  "## 证据分级",
  "[字节] / [推导] / [推测]。推测必须明写，禁止混入结论。",
  "",
  "## 必写诚实账",
  "报告最后一节列：没做的、样本薄的、可能出错的、与既有台账冲突的。",
  "",
  "## 已定谳基线（不许擅自改口径，除非给出字节反证）",
  "- CurrentFrame 0xA8ED84：1007 引用 / 10 写 / 唯一定常 inc 0x55DE7E + 写回 0x55DE81",
  "- 焦点旗标 0xA8ED80：46 引用 / 唯一写者 0x7778CE（WndProc WM_ACTIVATEAPP）",
  "- MainLogicFrame 0x55D360：3 个 ret（0x55D877 / 0x55DEC7 / 0x55DEDB）；",
  "  其中 0x55D877 与 0x55DEDB 不经 inc 即可达（冻结出口）",
  "- 0x7E11F0=KERNEL32!Sleep，0x7E1530=WINMM!timeGetTime",
  "- [0xA8B230] GameLogic 指针：1293 引用 / 3 写（0x52BA94 / 0x52BAB6 / 0x6BEB7D）",
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

// ===== 第一批：5 个方向（并发上限 5） =====
phase("第一批 5 个方向并行取证");
const BATCH1: { id: string; title: string; brief: string }[] = [
  {
    id: "P01",
    title: "帧冻结出口 (a) 0x55D877 守卫链与 [GameLogic+0x62C] 定谳",
    brief: [
      "MainLogicFrame 0x55D360 有一条不经 0x55DE7E inc 即可达的 ret：0x55D877。",
      "路径（probe 已初步钉）：",
      "  0x55D7C2 mov eax,[0xA8B238]     ; GameMode",
      "  0x55D7C7 test eax,eax ; 0x55D7C9 je 0x55D7D4     ; Mode==0",
      "  0x55D7CB cmp eax,5    ; 0x55D7CE jne 0x55D878    ; Mode!=5 走正常帧体",
      "  0x55D7D4 mov edi,[0xA8B230]     ; GameLogic 指针",
      "  ... 0x55D821 mov eax,[0xA8B230]",
      "  0x55D826 mov ecx,[eax+0x62C]",
      "  0x55D82C test ecx,ecx",
      "  0x55D82E je 0x55D878            ; ==0 -> 正常帧体（会走 inc）",
      "  0x55D830 call 0x5D4D50 (泵) / 0x55D835 call 0x48D080 / 0x55D83A call 0x53B560",
      "  0x55D83F.. vtable+0x5C / 0x55D84A call 0x4F4480 / 0x55D854 call 0x55E160 (LogicUpdate)",
      "  0x55D877 ret                    ; ★ 帧号不推进，但世界更新照跑",
      "",
      "要做：",
      "1. 逐字节复核上述 0x55D7C2..0x55D877 全段，确认每条分支的 VA 与条件。",
      "2. 判定 [[0xA8B230]+0x62C] 到底是什么字段：",
      "   - 用 eng.disp_hits_field(0x62C) 拿全家族（注意会混入不同类的同偏移字段），",
      "     按 this 来源分档，不许合并。",
      "   - 找出该字段的**写点**（可能是通过别的基址寄存器写的），判定写入值语义。",
      "   - [0xA8B230] 3 个写点（0x52BA94 / 0x52BAB6 / 0x6BEB7D）逐个解上下文。",
      "3. 必须回答：+0x62C 是「暂停标志」「同步等待」「跳帧」还是别的？",
      "   无法定谳就明写，并列出所有排除过的候选与排除依据。",
      "4. 给出机制判据：真机侧读哪几个 VA 的什么值就能证实/证伪这条路径。",
    ].join("\n"),
  },
  {
    id: "P02",
    title: "焦点旗标睡眠自旋：循环能否长期困住 + 与文档冲突裁决",
    brief: [
      "MainLogicFrame 头部逐字节钉死：",
      "  0x55D377 mov al,[0xA8ED80]      ; 焦点旗标",
      "  0x55D383 test al,al",
      "  0x55D385 jne 0x55D3BB           ; !=0 -> 直落帧体（会走 inc）",
      "  0x55D387 mov esi,[0x7E11F0]     ; = KERNEL32!Sleep（IAT 已证实）",
      "  0x55D38D mov eax,[0xA8B238]     ; GameMode",
      "  0x55D394 je 0x55D39B ; 0x55D399 jne 0x55D3B2",
      "  0x55D39B push 0x1F4 / call esi  ; Sleep(500)  <- Mode in {0,5}",
      "  0x55D3A2 call 0x5D4D50          ; MessagePump",
      "  0x55D3A7 mov al,[0xA8ED80]",
      "  0x55D3AE je 0x55D38D            ; ★ 旗标仍 0 -> 回循环顶",
      "  0x55D3B0 jmp 0x55D3BB",
      "  0x55D3B2 push 0xA / call esi / call 0x5D4D50  ; 其它 Mode 走 Sleep(10)",
      "旗标全镜像唯一写者 = 0x7778CE（WndProc WM_ACTIVATEAPP 激活沿）。",
      "",
      "要做：",
      "1. ★ 攻击本循环的「长期困住」能力：解出泵 0x5D4D50，判定它是否 DispatchMessageA。",
      "   若是，则 WndProc 可能被调用、旗标可能被写 1 ⇒ 这个循环不是死锁而是「失焦等待」，",
      "   有激活消息就会退出。这直接决定它能否解释「冻结 2.56-24.73s 且无用户操作」。",
      "2. 解出主窗 hwnd [0xB73550] 的写点与生命周期，判定 hwnd==0 时泵的行为。",
      "3. 算时间量级：若被困，一秒几次循环？冻结 21.156s 需要多少次连续读到 0？",
      "   给出算式与概率评估。",
      "4. ★ 文档冲突裁决（重点，不许含糊）：",
      "   docs/re/clock_frame_loop.md 称 0xA8ED80 = 「快进/跳过 Sleep 标志」",
      "   re_atlas/evidence/r063a_flag_writer_closure.md 定谳为「焦点旗标」",
      "   用字节独立判定：谁对、都对、还是都错？注意差别：",
      "   旗标=1 时是**跳过整个 Sleep+泵循环**（0x55D385 jne 0x55D3BB），",
      "   而不是「跳过 Sleep 但仍在泵」。这个差别是否使「快进」说法错误？",
      "5. 给出真机判别式：读哪几个 VA 的什么值能证实/证伪这条路径。",
    ].join("\n"),
  },
  {
    id: "P03",
    title: "CurrentFrame 10 个写点全归因 + 「唯一 inc」的独立复核",
    brief: [
      "CurrentFrame 0xA8ED84 全镜像 1007 引用 / 10 写（本轮重同步复核）。",
      "10 个写点：",
      "  0x52DA08  mov [0xA8ED84], ebx",
      "  0x55DE81  mov [0xA8ED84], edx     <-- 唯一定常 inc 后写回（0x55DE7E inc edx）",
      "  0x5B7329  mov [0xA8ED84], 0",
      "  0x5BB20C  mov [0xA8ED84], ebp",
      "  0x5E550F  mov [0xA8ED84], esi",
      "  0x5E747C  mov [0xA8ED84], 0",
      "  0x68466B  mov [0xA8ED84], esi",
      "  0x686765  mov [0xA8ED84], ebp",
      "  0x795234  mov [0xA8ED84], 0",
      "  0x79758C  mov [0xA8ED84], eax",
      "",
      "要做：",
      "1. 逐点解：所在函数头（用 E8 头集 + ret 扫描定界，不许线性窗）、",
      "   该函数职责、写入值来源（常数？寄存器？读改写？）、守卫条件。",
      "2. ★ 核心攻击：0x55DE81 是否真的是**唯一**定常自增点？",
      "   逐点检查这 10 个写点里有没有第二个「读-加-写」形态：",
      "   即在写点之前不远处有 mov reg,[0xA8ED84] 然后再写回 reg+常数。",
      "   若有，那「唯一 inc」的主张破。",
      "3. 判定哪几个写点可能在 measure 窗内（局内战斗）被触发，而不只是开局/存读档。",
      "   若有，它会造成帧号「跳变」而非「冻结」——与「f[0]==0 加载段型」有何关系？",
      "4. 复核 3 处写 0（0x5B7329 / 0x5E747C / 0x795234）分别在什么时机。",
      "5. 对账 docs/re/ARCHITECTURE_ATLAS.md §8.4「9 处均为载入地图、读取存档或开局清零」：",
      "   逐点验证这句话是否成立。",
      "6. ★ 顺带勘误：ATLAS §8.4 写「全镜像唯一定常递增写入点位于 0x0055DE73」，",
      "   但 0x55DE73 是 mov edx,[0xA8ED84]（读），inc 在 0x55DE7E。",
      "   这是地址级勘误，必须明确指出正确地址。",
    ].join("\n"),
  },
  {
    id: "P04",
    title: "tick 字段数据检验：A02 焦点旗标假说能否被既有真机数据判定",
    brief: [
      "★ 纯数据分析任务，只读既有真机数据，绝对不新跑游戏。",
      "",
      "数据：lead/qc161_u0400_trip/c2ab_x/*/timeline.json（23 份）",
      "每行含 {t, singleton, hwnd, exitstate, frame, tick, hook6, ws_kb}，",
      "其中 tick = [0xA8ED80] 的采样值（焦点旗标）。",
      "另有 battle_tl / pre5 / close_rows 三个字段，battle_tl 是战斗段轨迹。",
      "",
      "要做：",
      "1. 全量枚举 23 份 timeline，打印覆盖度自证：",
      "   总文件数、含 tick 行数、每份的时间跨度与采样间隔中位数。",
      "2. 统计 tick 取值分布（0 / 1 / 其它），逐份列出。",
      "3. ★ 核心检验：对每份按 t 排序后找 frame 不变的相邻行对（Δf==0），",
      "   对照同一时刻的 tick 值。",
      "   - Δf==0 且 tick==0 → A02 假说的直接证据",
      "   - Δf==0 却 tick==1 → A02 假说在这批数据上被证伪",
      "4. ★ 关键陷阱（必须处理）：采样间隔 vs 冻结时长的可比性。",
      "   若采样间隔（可能 1s 以上）远大于典型冻结时长，则这批数据**无法**检验 A02，",
      "   必须明写 DATA_INSUFFICIENT，不许硬凑结论。",
      "5. 统计 Δf==0 的相邻对有多少、其中 tick 分布如何。",
      "6. 结论必须明确落入四选一：CAN_CONFIRM / CAN_REFUTE / CANNOT_DECIDE / DATA_INSUFFICIENT。",
      "7. 若 DATA_INSUFFICIENT，给出最小补充采样方案（哪几个 VA、多少 Hz、多久），不执行。",
    ].join("\n"),
  },
  {
    id: "P05",
    title: "wait-trace 4 份逐拍分解：冻结段是「完全不动」还是「慢爬」",
    brief: [
      "这是本仓**时间分辨率最高**的数据（400Hz），最能看清冻结的真实形态。",
      "",
      "数据（只读）：",
      "  out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l3_1101v4{b,c,d,e}/h8_wait_trace.json",
      "结构：{n, verdict, wait_s, samples: [[t, frame], ...]}",
      "",
      "要做：",
      "1. 4 份逐份读，打印：样本数、时间跨度、帧号首尾、verdict、wait_s。",
      "2. 逐拍分析：找所有 Δf==0 的连续区段，统计时长分布（分档：<0.1s / 0.1-0.5 / 0.5-1 / 1-5 / >5）。",
      "3. ★ 关键分型判定：冻结段内帧号是「完全不动」还是「偶尔跳一下」？",
      "   - 完全不动 → 单段主导型（引擎停摆）",
      "   - 偶尔跳（Δf 很小但非零）→ 多次型（慢爬）",
      "   给出每份的分型结论与判据。",
      "4. 与之对账本仓台账 §507 的逐拍分解（记 v4-b poll_count=9989 等）。",
      "   若数字不符，指出差异来源。",
      "5. ★ 判定：这 4 份数据能否区分「睡眠自旋」（帧完全不动）与",
      "   「(a) 出口」（帧不动但世界更新在跑）？说明能/不能的判据。",
      "6. 统计每份的「帧号推进速率」时间序列，找出速率突变的时刻。",
    ].join("\n"),
  },
];

const b1 = await Promise.all(
  BATCH1.map(async (t) => {
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

for (const x of b1) report({ id: x.task.id, headline: x.r.headline, level: x.r.level, status: x.r.status });

phase("第一批逐份独立核验");
const b1c = await Promise.all(
  b1.map(async (x) => {
    const c = agent(`核验员-${x.task.id}`, {
      system:
        "你是独立核验员。你的职责是推翻，不是确认。\n" +
        "从字节/数据重新复算，不要相信原报告的结论。\n" +
        "复现不出来就判 REFUTED 或 UNVERIFIABLE，并说明你读了哪些字节/数据。\n" +
        "特别检查：地址读错、字节数数错、CFG 漏分支、口径偷换、样本当总体。",
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

phase("第一批收敛");
const s1 = agent("第一批汇总员", {
  system:
    "你是汇总员。把 5 个方向的结论与核验收敛成判定。不粉饰：硬的是硬的，破的是破的。",
});
const sum1 = await s1.ask<string>(
  `读 ${ABS}/P01..P05 的 REPORT.md 与 VERIFY.md。\n\n` +
    `自报：${JSON.stringify(b1.map((x) => ({ id: x.task.id, headline: x.r.headline, level: x.r.level, status: x.r.status })))}\n` +
    `核验：${JSON.stringify(b1c.map((c) => ({ id: c.id, verdict: c.c.verdict })))}\n\n` +
    `写 ${ABS}/BATCH1_VERDICT.md，结构：\n` +
    "# 第一批判定（P01-P05）\n" +
    "## 一、一句话结论\n" +
    "## 二、已证实（含 VA 与字节）\n" +
    "## 三、被推翻/降级\n" +
    "## 四、仍未定谳与缺什么\n" +
    "## 五、真机判别表（VA × 路径 × 期望值）\n" +
    "## 六、诚实账\n全文返回。",
);

await artifact.markdown("batch1", sum1, {
  title: "第一批判定（P01-P05）",
  description: "帧冻结出口、焦点旗标自旋、CurrentFrame 写点、tick 数据检验、wait-trace 逐拍分型。",
  primary: true,
});

return {
  conclusion:
    `第一批 5 个方向完成并逐份核验：` +
    `${b1c.filter((c) => c.c.verdict === "CONFIRMED").length}/5 CONFIRMED。判定书见 artifact。`,
  findings: b1.map((x) => ({
    where: `${ROOT}/${x.task.id}/REPORT.md`,
    what: `${x.task.id} ${x.task.title}：${x.r.headline}`,
    evidence: `级别=${x.r.level}；核验=${b1c.find((c) => c.id === x.task.id)?.c.verdict}；复算=${b1c.find((c) => c.id === x.task.id)?.c.recomputed}`,
    status: (b1c.find((c) => c.id === x.task.id)?.c.verdict === "CONFIRMED"
      ? "verified"
      : "unconfirmed") as "verified" | "unconfirmed",
    severity: "medium" as const,
  })),
  verified: ["selftest.py exit=0", "5 份各由独立上下文核验员从字节复算"],
  notCovered: [
    "静态只读：零真机、零母本改动",
    "运行期哪条路径真实触发，需真机采样",
    "P04 若判 DATA_INSUFFICIENT，A02 假说仍未被数据判定",
  ],
};
