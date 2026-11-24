interface SubsysFinding {
  /** 子任务编号。 */
  id: string;
  /** 一句话结论。 */
  headline: string;
  /** 证据级别。 */
  level: "byte" | "derived" | "speculation";
  /** 关键 VA 与数字。 */
  keyFacts: string[];
  /** 这个子系统是否可能在局内吃掉时间/阻塞，导致帧号不推进。 */
  canStallFrame: "YES_STRONG" | "YES_WEAK" | "NO" | "UNKNOWN";
  /** 判据。 */
  stallEvidence: string;
  /** 与目标①实测形态（冻结 2.56-24.73s、CPU 低、正常退出）是否相容。 */
  compatibleWithObserved: "YES" | "NO" | "PARTIAL" | "UNKNOWN";
  /** 诚实账。 */
  caveat: string;
}

interface CrossVerdict {
  topic: string;
  verdict: "CONFIRMED" | "REFUTED" | "PARTIAL" | "UNVERIFIABLE";
  detail: string;
  evidence: string;
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
  "## 解码口径",
  "禁止 for ins in md.disasm(blob, va) 扫全镜像（capstone 遇不可解码字节静默停止，本仓 G-23）。",
  "用共享引擎：",
  "    import sys",
  "    sys.path.insert(0, r\"" + ABS + "\")",
  "    from ra2tool import Engine",
  "    eng = Engine()",
  "    print(eng.coverage)              # 必须打印自证：100.00% / 1394120 insns",
  "    eng.disasm(va, n) / eng.rd(va,n) / eng.u32(va)",
  "    eng.resolve_iat(slot_va)         # IAT 槽 -> (DLL, Func)",
  "    eng.disp_hits(global_va)         # 绝对全局访存",
  "    eng.func_rets(lo,hi) / eng.loop_backedges(lo,hi)",
  "",
  "## 函数边界纪律（G-83）",
  "不许用 ±0x200 线性窗口定函数尾（会读到上一函数序言）。用 ret 扫描 + E8 头集，或分支图闭包。",
  "若只凭线性窗口定界，必须明写「边界未经分支图验证」。",
  "",
  "## 证据分级",
  "[字节] / [推导] / [推测]。推测必须明写。",
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

const SUBS: { id: string; title: string; brief: string }[] = [
  {
    id: "S01",
    title: "渲染路径：TacticalClass::Render 与帧耗时的关系",
    brief: [
      "本仓记：渲染入口 0x6D4B50 在 TacticalClass::Render(0x6D3D10) 内，每渲染帧 2 次调用。",
      "",
      "要做：",
      "1. 定位 TacticalClass::Render 的确切头尾（用 E8 头集 + ret 扫描，不许线性窗）。",
      "2. 解出它的调用链：它调了哪些子函数、是否有 DDraw Blt / Lock / Flip 这类阻塞调用。",
      "3. 判定：若渲染卡住（DDraw 等待 vsync / 失去设备），会不会导致",
      "   MainLogicFrame 无法推进？（即：渲染是否在逻辑帧的调用栈内）",
      "4. 若渲染与逻辑帧是**不同线程**，说明线程结构并给出判据。",
      "5. 与目标①实测（帧冻结但游戏没崩、CPU 低）判定相容性。",
    ].join("\n"),
  },
  {
    id: "S02",
    title: "音频路径：AudioFrameUpdate 与阻塞",
    brief: [
      "本仓记：0x406F70 = AudioFrameUpdate（Clock::Now + 33ms 门），在 0x48D080 内首调。",
      "0x752760 = ThemeTick。",
      "",
      "要做：",
      "1. 解 0x406F70 的完整逻辑：它做什么、有哪些 Win32 调用（waveOut / DirectSound / " +
      "timeGetTime / Sleep）。",
      "2. 判定：音频路径会不会阻塞？若音频设备异常（无声卡/独占），会不会卡住整个逻辑帧？",
      "   给出字节判据。",
      "3. 解 0x752760 ThemeTick 同上。",
      "4. 判定：音频初始化/关闭时的等待是否可能造成长时间停顿。",
      "5. 与目标①判定相容性。",
    ].join("\n"),
  },
  {
    id: "S03",
    title: "输入路径：0x54F5C0 与键盘鼠标处理",
    brief: [
      "本仓记：MainLogicFrame 内有「输入检查 0x54F5C0 / 视口缩放 0x4A9840」。",
      "",
      "要做：",
      "1. 解 0x54F5C0 完整逻辑：它检查什么、有无 GetAsyncKeyState / GetKeyState / " +
      "GetCursorPos / 阻塞读。",
      "2. 解 0x4A9840（视口缩放）。",
      "3. 判定：输入路径有无可能阻塞或长循环（例如等待按键释放）。",
      "4. 特别查：是否有可能进入「等待用户输入」的模态状态，而在无人操作时永久等待。",
      "   这是「帧号冻结但进程活着」的一个强力候选。",
      "5. 若存在模态等待，给出它的触发条件与退出条件。",
    ].join("\n"),
  },
  {
    id: "S04",
    title: "网络/同步路径：0x647260 与确定性帧校验",
    brief: [
      "本仓记：0x647260 是「每帧同步入口」，MainLogicFrame 尾部 0x55DE40 唯一调用点。",
      "职责：收包 -> 校验 CRC -> 执行到期命令 -> 算帧 CRC -> 发包/补发 FrameSync。",
      "",
      "要做：",
      "1. 解 0x647260 完整逻辑：它做哪些网络操作？有无阻塞 recv / WaitForSingleObject / " +
      "超时等待？",
      "2. ★ 关键：单机遭遇战（非联机）时，这条路径会走吗？还是被 GameMode 门控掉？",
      "   给出确切判据（哪个分支、哪个全局）。",
      "3. 若单机也走：它会不会因「等所有玩家帧同步」而阻塞？哪怕只有一个本地玩家？",
      "4. 判定：这条路径是否是「帧号冻结」的候选。",
      "5. 与目标①判定相容性。",
    ].join("\n"),
  },
  {
    id: "S05",
    title: "主环调用者侧：0x48CE8A 与 5 个模态泵",
    brief: [
      "MainLogicFrame 的调用者：0x48CE8A（主环）+ 0x608206 / 0x60D407 / 0x62314E / " +
      "0x623D72 / 0x624271（模态/UI 内嵌泵）。",
      "",
      "要做：",
      "1. 逐个解这 6 个调用点的宿主函数与上下文：",
      "   - 主环 0x48CE8A 所在的完整循环（应有「call MainLogicFrame -> 检查退出 -> 回边」）",
      "   - 5 个模态泵分别在什么 UI 状态下被调用",
      "2. ★ 关键：如果主环本身卡住（不在 MainLogicFrame 内），帧号也会冻结。",
      "   解出主环 0x48CE8A 前后的完整结构，判定主环有哪些可能不回到 MainLogicFrame 的路径。",
      "3. 特别查：主环里是否有「等窗口消息」「等设备」「等用户确认」的阻塞点。",
      "4. 判定：这 6 个调用点里，哪些在「局内战斗」时是活跃的。",
      "5. 给出「主环侧卡住」的判据（区别于「MainLogicFrame 内部卡住」）。",
    ].join("\n"),
  },
  {
    id: "S06",
    title: "内存分配路径：是否有 GC 式停顿",
    brief: [
      "本仓 526 节结论：ws_kb 是阶梯跳变，非分配抖动，判定「内存/GC 型」被排除。",
      "但该结论标记为本线判定。",
      "",
      "要做：",
      "1. 找游戏的堆分配封装（operator new / malloc 包装）：",
      "   - 全镜像搜 HeapAlloc / HeapCreate / VirtualAlloc 的 IAT 槽与调用点",
      "   - 找集中封装的分配函数（被大量调用的那个）",
      "2. 判定：分配路径有无可能长时间阻塞（例如大块分配触发系统内存整理）。",
      "3. 特别查：是否存在「分配失败 -> 重试循环」或「内存不足 -> 等待」的路径。",
      "4. 判定：本仓「ws_kb 阶梯跳变」这个观测，与「分配路径造成停顿」是否矛盾？",
      "   （阶梯跳变说明有大块分配，大块分配可能带来停顿——这两者不矛盾）",
      "5. 给出这个方向的结论与证据强度。",
    ].join("\n"),
  },
  {
    id: "S07",
    title: "临界区与多线程：是否有锁竞争",
    brief: [
      "要做：",
      "1. 普查全镜像的线程原语：",
      "   - EnterCriticalSection / LeaveCriticalSection 的 IAT 槽与调用点",
      "   - WaitForSingleObject / WaitForMultipleObjects 的调用点",
      "   - CreateThread / _beginthreadex 的调用点（游戏开了几个线程？）",
      "2. 判定：游戏是否多线程？若是，线程各自的职责是什么？",
      "   主逻辑线程与渲染线程是否分离？",
      "3. ★ 关键：若多线程，是否存在「主线程等渲染线程/音频线程」或反之的同步点？",
      "   这些同步点若对方卡住，会造成帧号冻结而进程活着。",
      "4. 解出所有 WaitForSingleObject 的等待对象与超时值。",
      "5. 判定：锁竞争是否可能是帧冻结的候选。",
    ].join("\n"),
  },
  {
    id: "S08",
    title: "异常处理与 SEH：是否有静默捕获导致卡住",
    brief: [
      "本仓记：目标②是主崩溃，有 RC-4 退出线相关的大量工作（0x6BE0B6 等 exitstate 写点）。",
      "本任务只关注：异常处理是否可能让程序「活着但不动」。",
      "",
      "要做：",
      "1. 找全镜像的 SEH 安装点（SetUnhandledExceptionFilter / __try 的 FS:[0] 链操作）。",
      "2. 判定：游戏是否有顶层异常处理器？它捕获异常后做什么（记录+退出？还是继续？）",
      "3. ★ 关键：若某处异常被静默捕获并进入重试循环，会造成「进程活着但逻辑不推进」。",
      "   排查这种模式。",
      "4. 与目标②的 RC-4 关系：帧冻结与主崩溃是否可能是同一根因的两种表现？",
      "   给出你的判断（这直接关系到三目标是否该合并）。",
      "5. 诚实标级别。",
    ].join("\n"),
  },
];

const subs = await Promise.all(
  SUBS.map(async (s) => {
    const a = agent(`子系统分析员-${s.id}`, {
      system:
        "你是 RA2/YR 引擎逆向分析员，专长子系统解构。\n" +
        "每条结论必须指回 VA 与字节。做不到就明写做不到。\n" +
        "特别注意：不要为了让结论好看而把推测写成事实。",
    });
    const r = await a.ask<SubsysFinding>(
      `任务 ${s.id}：${s.title}\n\n` + `写域：${ABS}/${s.id}/\n\n` + RULES + "\n\n## 具体任务\n" + s.brief,
    );
    report({ id: s.id, headline: r.headline, level: r.level, stall: r.canStallFrame });
    return { s, r };
  }),
);

phase("逐个子系统核验");
const checks = await Promise.all(
  subs.map(async (x) => {
    const c = agent(`核验员-${x.s.id}`, {
      system:
        "你是独立核验员，职责是推翻。从字节重算，不信原报告。\n" +
        "重点查：IAT 槽是否解对、函数边界是否错、阻塞判定是否有字节支撑。",
    });
    const r = await c.ask<CrossVerdict>(
      `核验 ${x.s.id}：${x.s.title}\n` +
        `原报告：${ABS}/${x.s.id}/REPORT.md\n` +
        `自报：headline=${x.r.headline} level=${x.r.level} ` +
        `canStall=${x.r.canStallFrame} compatible=${x.r.compatibleWithObserved}\n` +
        `keyFacts=${JSON.stringify(x.r.keyFacts)}\n\n` +
        RULES +
        "\n\n" +
        `核验报告写 ${ABS}/${x.s.id}/VERIFY.md。`,
    );
    report({ id: `${x.s.id}-verify`, verdict: r.verdict, topic: r.topic });
    return { id: x.s.id, check: r };
  }),
);

phase("汇总：八子系统与帧冻结的因果排序");
const synth = agent("因果排序员", {
  system:
    "你是汇总员。把 8 个子系统的排查结果收敛成一张「谁最可能让帧号冻结」的排序表。\n" +
    "按证据强度排序，不按直觉。未验证的标未验证。",
});
const md = await synth.ask<string>(
  `读 ${ABS}/S01..S08 的 REPORT.md 与 VERIFY.md。\n\n` +
    `自报汇总：${JSON.stringify(
      subs.map((x) => ({
        id: x.s.id,
        headline: x.r.headline,
        canStall: x.r.canStallFrame,
        compatible: x.r.compatibleWithObserved,
      })),
    )}\n` +
    `核验判定：${JSON.stringify(checks.map((c) => ({ id: c.id, verdict: c.check.verdict })))}\n\n` +
    `写 ${ABS}/SUBSYS_VERDICT_20261104.md，结构：\n` +
    "# 子系统级帧冻结排查 · 判定书（2026-11-04）\n" +
    "## 一、一句话结论\n" +
    "## 二、按证据强度排序的候选（含 VA 与判据）\n" +
    "## 三、被排除的方向与排除依据\n" +
    "## 四、与「帧冻结 2.56-24.73s + CPU 低 + 正常退出」的相容性分析\n" +
    "## 五、目标①与目标②是否同一根因（判断 + 理由）\n" +
    "## 六、诚实账\n" +
    "然后全文返回。",
);

await artifact.markdown("subsys-verdict", md, {
  title: "子系统级帧冻结排查判定书",
  description: "渲染/音频/输入/网络/主环/内存/线程/异常 八个子系统逐项排查与核验。",
  primary: true,
});

return {
  conclusion: `8 个子系统全部排查并核验：${checks.filter((c) => c.check.verdict === "CONFIRMED").length}/8 CONFIRMED。判定书见 artifact。`,
  findings: subs.map((x) => ({
    where: `${ROOT}/${x.s.id}/REPORT.md`,
    what: `${x.s.id} ${x.s.title}：${x.r.headline}`,
    evidence: `级别=${x.r.level}；可致冻结=${x.r.canStallFrame}；与实测相容=${x.r.compatibleWithObserved}；核验=${checks.find((c) => c.id === x.s.id)?.check.verdict}`,
    status: (x.r.level === "byte" ? "verified" : "unconfirmed") as "verified" | "unconfirmed",
    severity: "medium" as const,
  })),
  verified: ["selftest.py exit=0", "8 个子系统各由独立上下文核验员从字节复算"],
  notCovered: ["静态只读：零真机", "线程结构与运行期同步行为静态只能部分推断"],
};
