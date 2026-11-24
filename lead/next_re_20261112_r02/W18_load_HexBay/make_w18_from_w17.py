# -*- coding: utf-8 -*-
"""一次性转换：由 W17_load_B 的三份已验证脚本生成 W18_load_HexBay 版本。

只读 W17_load_B/，只写 W18_load_HexBay/（写域合规）。
转换是有序字符串替换（先长串后短串），probe 的 docstring 整块重写。
生成后 py_compile 语法自检。
"""
from __future__ import annotations

import py_compile
import sys
from pathlib import Path

W17 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W17_load_B")
W18 = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W18_load_HexBay")

PROBE_DOCSTRING = '''"""NEXT_RE_20261112_R02 / W18 —— RE-N04g 高建筑载体 B′（HexBay）负载对照（单变量：只换地图）。

★ B′ 臂载体（开工前钉定，开工实算核对）：[8]黑心湾_HexBay.yrm，355,713 B。
  权威 [Basic].Name = "Hex Bay (2-8)"（离线实读；Official=no / MaxPlayer=8 /
  MinPlayer=2 / GameMode=standard / MultiplayerOnly=1 / 含 [Triggers]）。
  ★ 选图纪律：地图列表按显示名（=[Basic].Name）匹配，禁文件名匹配（文件名含
  [ ] 与中文，PowerShell 需 -LiteralPath）。W17 实测该显示名在 268 条
  skirmish 列表条目中唯一命中（索引 267）；本卡仍实测确认，命中数 >1 时
  如实记录并说明取舍，无法区分则停手上报。

★ 背景（W17 结论）：A 臂（W15）"无退化"读数来自 52 建筑的近空图 [8] Proving
  Grounds；B′ = 144 建筑（W17 实测可达集合内建筑声明量最高，可达上限=144）。
  声明量 ≠ 运行实例数（LoadBench 教训）⇒ 负载只以实测 CPU 为准。

★ 单变量纪律：与 A 臂（W15，[8] Proving Grounds）仅地图不同；配置基线
  baseline_pre_launch/ 逐字节一致；启动/导航/采样协议与 W15/W17 相同。
  A 臂基线（W15 实测，对照锚点）：cycle 通道每拍中位 1.691 ms；FILETIME 均值
  1.725 ms；窗口线程占用率 5.39% 单核；拍率 31.2492 计数/s；拍间隔均值 32.000 ms、
  ≥64 ms 间隔 0；有效段 240.006 s。
  ★ 判据（预设，不得事后改）：[成功造出压力] = B′ 每拍 CPU 中位 > 2.54 ms（A×1.5）
  或占用率 > 10%；[无显著差异] = 相对 A 差 < 20%；[中间地带] = 20%–50%；
  [B′ 不可用] = 未进图或有效段 < 90 s（如实记录，不重启凑时长）。

★ 三个必须避开的坑（本会话实测教训，已内建）：
  1) mode[0xA8B238] 不能判进图（加载/局内/退出后闲置全为 5）⇒ 进图判据 =
     frame 以 ≈29–32 计数/s 持续 ≥60 s。
  2) GetThreadTimes 记账量子 15.625 ms（本机 828 个非零 Δ 全为该值）⇒ FILETIME
     通道只作交叉核对；主判读通道 = cycle（QueryThreadCycleTime，≈3.104e9 cyc/ms）。
  3) 声明量 ≠ 运行实例数（LoadBench U800 实测无负载）⇒ 负载只以实测 CPU 为准。

★ 沿用 W15/W17 的仪器（源：W15_tick_cpu/tick_cpu_probe.py，仅换载体/判据/文案）：
  FILETIME 交叉核对 + cycle 主判读 + 观察者独立进程（1Hz UI 扫 +
  NtQuerySystemInformation 线程表 + 全线程 GetThreadTimes 求和）。
  逐拍字段：win_cyc_delta（相邻采样 cycle Δ）、cyc_est_ms（Δ/3.104e9，
  离线用 B 自标定系数重算）、ctx（NtQuery ContextSwitches）。
  A8ED50（候选 BulletCnt）逐拍记录，首次 0→非零记事件（交战旁证）。

★ 本卡能测 / 测不到（必须写进报告 §0）：
  能测：B′ 臂每拍 CPU 消耗分布、占用率、趋势；与 A 臂的单变量对照。
  测不到：阻塞类等待（Sleep/Present/vsync/等消息）——CPU 时间不含等待，
          「一拍 CPU 很低」≠「这一拍很快」；「一拍 CPU 很高」才是可靠的重活信号。
  也测不到：GPU 侧耗时、画面掉帧；8 席位实例化无已解码地址（如实报告）。

★ 仪器通道（开工前固定）：
  主判读：窗口线程 QueryThreadCycleTime 累计，每拍采样取 Δ（周期计数，上下文
          切换粒度，细于时钟节拍记账；W15 实测 ≈3.104e9 cyc/ms）。
  交叉核对：窗口线程 GetThreadTimes kernel/user（FILETIME→ms，记账量子
          15.625 ms，只作交叉核对，不得把 0 读作「拍快」）。
  进程级：全线程扫放观察者进程 1Hz（OpenThread+GetThreadTimes 求和+CycleTime；
          NtQuerySystemInformation 另给 ContextSwitches）。不留在采样循环内的原因：
          本机 Toolhelp 全系统线程迭代 ~7600 条 ≈5ms，会周期性污染 6ms 采样间隔
          （bindtest 实测）。线程退出时其最后累计值并入 retired，避免漏计。
          GetProcessTimes 在 Lead 自测中同权限返回 False（原因未明）——本探针只
          用它做一次性探测并如实记录结果，进程级 CPU 不依赖它。

★ 归属方式（predeclared）：每拍成本 = 相邻两次 frame 递增采样之间
  Δ(win_kernel+win_user) 与 Δ(win_cycle)。递增事件只能以采样粒度观测 ⇒ 归属窗口
  = 1 拍 ± 采样量化（±~6 ms），且窗口线程 CPU 含渲染+消息泵+逻辑（非纯逻辑）。
  GetThreadTimes 记账受系统时钟节拍粒度约束 ⇒ 每拍值可能出现台阶量子；
  本次实测量子在分析中如实报告（不预设具体值）。

★ 预设判据（开工前固定，不得事后改）：
  * 采样 6 ms 目标间隔（W14 已验证可达），实测间隔如实报告。
  * 分布主表用 df=1（Δframe=1）的递增事件；df≥2 的全额记单行并标注，不摊分。
  * 热点候选：每拍 CPU ≥ 3×中位 且 ≥ 1.0 ms ⇒ 列前 20（t_rel、CPU ms、frame、
    mode、fg）。cycle 通道同判据表为主（FILETIME 表仅量子复核）。
  * 趋势：10 s 窗 median(每拍CPU)；末 1/3 窗中位 > 首 1/3 窗中位 × 1.2 ⇒ 上升候选。
  * CPU 占用率 = ΔCPU/有效墙钟（窗口线程与进程级各一）；单位=单核百分比。
  * read_status=fail 拍保留不填补；跨 fail 拍的递增不计算（如实计数）。
  * 采样段零输入、零切窗、不进菜单；对局自然结束如实记录、不重启补测；
    有效段 <90 s 判 [B′ 不可用]。
  * 不得把 CPU 时间当帧时间/耗时；不得由「CPU 低」推断「拍快」。

★ 结构（attempt2/W14 教训）：本探针由代理经 WMI Win32_Process.Create 独立启动
  （脱离代理进程树）；观察者另起独立 WMI 进程（load_hexbay_ui_watch.py）。本探针
  finally 自愈收尾：停观察者 → 关游戏 → 核对残留 → 逐字节还原
  RA2MD.INI/ddraw.ini/benchbak 并实算自证 → 写 kind=meta_end → 恢复锁 owner=lead。

授权：启动 ra2youli/gamemd.exe、只读 ReadProcessMemory、OpenThread+GetThreadTimes、
枚举窗口/线程、发消息/点控件（仅导航/选图/开局阶段）。禁止：SuspendThread/
StackWalk64/MiniDump/断点/注入/写目标进程内存/改 exe/dll/hook；禁止增删改
ra2youli 文件（配置还原除外，为卡面要求）。只处理自己启动的 pid；启动前有
gamemd 残留 ⇒ 停手报告。

写域：仅 lead/next_re_20261112_r02/W18_load_HexBay/（本文件、load_hexbay_ui_watch.py、
analyze_hexbay.py、out/）+ 实例锁（授权例外：开工 owner=本代理，收尾恢复 owner=lead）。

用法：
  python -X utf8 load_hexbay_probe.py                       # 单趟 240 s @ 6 ms
  python -X utf8 load_hexbay_probe.py --interval-ms 6 --target-seconds 240
"""'''

PROBE_SUBS = [
    # --- 载体钉定 ---
    ('BG_FILENAME = "[8]音速公路_SonicHighways.yrm"',
     'BG_FILENAME = "[8]黑心湾_HexBay.yrm"'),
    ('BG_SHA256 = "0805e637d3ac14bd8c68ab2acac92b157514f8472c819bbbfecee9c00da712f3"',
     'BG_SHA256 = "cb6c5224efcdfc9a79455f5b95cd4aeb8b6efbb655fc99ede104aadfd536529d"'),
    ('BG_BYTES = 252270', 'BG_BYTES = 355713'),
    ('# B 臂载体钉定（开工实算 0805e637…712f3 / 252,270 B；[Basic].Name=[8] Sonic Highways）',
     '# B′ 臂载体钉定（开工实算 cb6c5224…529d / 355,713 B；[Basic].Name=Hex Bay (2-8)，'
     'Official=no，W17 实测列表索引 267 唯一命中）'),
    # --- 选图模式与关键词 ---
    ('''default=["[8] Sonic Highways", "Sonic Highways",
                             "音速公路", "音速"],
                    help="按显示名选图的模式序列（依次尝试，禁固定索引/文件名）。"
                         "attempt1 实测：'Invisible Light Post' 与 '[8] Sonic "
                         "Highways' 在 268 条列表中均 0 命中 ⇒ 显示名来源待 "
                         "maplist_names.json 实测定")''',
     '''default=["Hex Bay (2-8)", "Hex Bay", "黑心湾", "黑心"],
                    help="按显示名选图的模式序列（依次尝试，禁固定索引/文件名）。"
                         "W17 实测：'Hex Bay (2-8)' 在 268 条列表中唯一命中"
                         "（索引 267）；本卡仍实测确认，命中 >1 时说明取舍")'''),
    ('''("sonic", "highway", "音速", "invisible",
                                    "light"))]''',
     '''("hex bay", "hexbay", "黑心湾", "hex"))]'''),
    # --- 卡片/判据文案（此时 RE-N04f 已换 RE-N04g，W17 尚未换 W18） ---
    ('"RE-N04g W17 load-B arm: single-variable map swap load-pressure test (external read-only, single run)"',
     '"RE-N04g W18 load-B\' arm (HexBay): single-variable map swap load-pressure test (external read-only, single run)"'),
    ('[B 不可用]', '[B′ 不可用]'),
    ('B 臂', 'B′ 臂'),
]

WATCHER_SUBS = [
    ('RE-N04g B 臂（[8] Sonic Highways）专用观察者；源：W15_tick_cpu/tick_ui_watch.py，\n'
     '仅改模块导入（ThreadTable 来自 load_hexbay_probe）与卡名，行为与 W15 一致：',
     'RE-N04g B′ 臂（[8]黑心湾_HexBay.yrm / Hex Bay (2-8)）专用观察者；'
     '源：W15_tick_cpu/tick_ui_watch.py，\n'
     '仅改模块导入（ThreadTable 来自 load_hexbay_probe）与卡名，行为与 W15/W17 一致：'),
]

ANALYZE_SUBS = [
    ('"""NEXT_RE_20261112_R02 / W17 —— RE-N04g B 臂负载对照离线重算。',
     '"""NEXT_RE_20261112_R02 / W18 —— RE-N04g 高建筑载体 B′（HexBay）负载对照离线重算。'),
    ('"card": "RE-N04g W17 load-B arm (single-variable map swap)"',
     '"card": "RE-N04g W18 load-B\' arm (HexBay, single-variable map swap)"'),
    ('[B 不可用]', '[B′ 不可用]'),
]


def apply_subs(text, subs):
    for old, new in subs:
        if old not in text:
            raise SystemExit("!! 替换目标未找到: %r" % old[:80])
        text = text.replace(old, new)
    return text


def replace_docstring(text, new_doc):
    start = text.find('"""')
    end = text.find('"""', start + 3)
    if start < 0 or end < 0:
        raise SystemExit("!! docstring 边界未找到")
    return text[:start] + new_doc + text[end + 3:]


def main():
    # ---- probe ----
    src = (W17 / "load_b_probe.py").read_text(encoding="utf-8")
    src = replace_docstring(src, PROBE_DOCSTRING)
    # 有序：先长串/具体串，后通用串
    src = src.replace("W17_load_B", "W18_load_HexBay")
    src = src.replace("W17-load-B-subagent", "W18-load-HexBay-subagent")
    src = src.replace("load_b_ui_watch", "load_hexbay_ui_watch")
    src = src.replace("RE-N04f", "RE-N04g")
    src = apply_subs(src, PROBE_SUBS)
    src = src.replace("W17", "W18")
    (W18 / "load_hexbay_probe.py").write_text(src, encoding="utf-8")

    # ---- watcher ----
    wsrc = (W17 / "load_b_ui_watch.py").read_text(encoding="utf-8")
    wsrc = wsrc.replace("W17_load_B", "W18_load_HexBay")
    wsrc = wsrc.replace("load_b_probe", "load_hexbay_probe")
    wsrc = wsrc.replace("load_b_ui_watch", "load_hexbay_ui_watch")
    wsrc = wsrc.replace("RE-N04f", "RE-N04g")
    wsrc = apply_subs(wsrc, WATCHER_SUBS)
    wsrc = wsrc.replace("W17", "W18")
    (W18 / "load_hexbay_ui_watch.py").write_text(wsrc, encoding="utf-8")

    # ---- analyzer ----
    asrc = (W17 / "analyze_load_b.py").read_text(encoding="utf-8")
    asrc = asrc.replace("W17_load_B", "W18_load_HexBay")
    asrc = asrc.replace("RE-N04f", "RE-N04g")
    asrc = apply_subs(asrc, ANALYZE_SUBS)
    asrc = asrc.replace("analyze_load_b.py", "analyze_hexbay.py")
    asrc = asrc.replace("W17", "W18")
    (W18 / "analyze_hexbay.py").write_text(asrc, encoding="utf-8")

    # ---- 语法自检 ----
    for name in ("load_hexbay_probe.py", "load_hexbay_ui_watch.py",
                 "analyze_hexbay.py"):
        py_compile.compile(str(W18 / name), doraise=True)
        print("compile ok:", name)
    print("ALL DONE")


if __name__ == "__main__":
    sys.exit(main())
