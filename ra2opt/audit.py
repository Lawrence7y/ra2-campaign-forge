"""只读体检：把游戏目录扫一遍，输出"按严重度排序的待办清单 + 证据"。

audit 不改任何文件，也不联网（除非显式 `--online`），因此可以随时随便跑。
报告同时落 `out/optimize/report.md`（人看）与 `report.json`（机器看）。
"""

from __future__ import annotations

import ctypes
import json
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import CNCDDRAW_RA2_FIXES, __version__, appcompat, backup, game as gamemod
from . import pe

SEVERITY_ORDER = {"critical": 0, "warn": 1, "info": 2, "ok": 3}
SEVERITY_LABEL = {"critical": "严重", "warn": "警告", "info": "建议", "ok": "已达标"}

# 认为"值得开 LAA"的物理内存门槛（MB）
LAA_RAM_THRESHOLD_MB = 3500


@dataclass
class Finding:
    id: str
    severity: str
    title: str
    detail: str
    evidence: list = field(default_factory=list)
    fix: str = ""


# ---------------------------------------------------------------------------
# 环境
# ---------------------------------------------------------------------------

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _total_ram_mb() -> int:
    try:
        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys // (1024 * 1024))
    except (AttributeError, OSError):
        pass
    return 0


def _cpu_name() -> str:
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
        ) as key:
            return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    except (ImportError, OSError):
        return platform.processor() or "unknown"


def environment() -> dict:
    return {
        "os": platform.platform(),
        "os_version": "%d.%d.%d" % sys.getwindowsversion()[:3] if sys.platform.startswith("win") else "",
        "python": platform.python_version(),
        "cpu": _cpu_name(),
        "cpu_count": os.cpu_count(),
        "ram_mb": _total_ram_mb(),
        "is_64bit_host": pe.is_64bit_host(),
        "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ra2opt_version": __version__,
    }


# ---------------------------------------------------------------------------
# 事实采集
# ---------------------------------------------------------------------------

def collect(game_path) -> dict:
    g = gamemod.GameDir(game_path)
    facts: dict = {"game_dir": str(g.path), "valid": g.valid, "env": environment()}

    if not g.valid:
        facts["missing_gamemd"] = str(g.gamemd)
        return facts

    # exe
    exes = {}
    for name in g.present_exes():
        ident = g.identity(name)
        if ident is not None:
            exes[name] = ident.as_dict()
    facts["exes"] = exes
    facts["gamemd"] = exes.get("gamemd.exe", {})

    # wrappers
    facts["components"] = g.components()
    facts["ddraw_version"] = g.ddraw_version()

    # ddraw.ini
    ini_facts: dict = {}
    if g.has("ddraw.ini"):
        try:
            doc = _load_ini(g, "ddraw.ini")
            ini_facts["global"] = {k.lower(): v for k, v in doc.keys("ddraw").items()}
            for section in ("gamemd", "ra2md", "gamemd-spawn", "ra2", "Red Alert 2", "Yuri's Revenge"):
                if doc.has_section(section):
                    ini_facts[section] = {k.lower(): v for k, v in doc.keys(section).items()}
            ini_facts["raw_size"] = (g.path / "ddraw.ini").stat().st_size
        except (OSError, ValueError) as exc:
            ini_facts["error"] = str(exc)
    facts["ddraw_ini"] = ini_facts

    # ra2md.ini / ra2.ini
    for name in ("ra2md.ini", "ra2.ini"):
        key = name.replace(".", "_")
        if not g.has(name):
            facts[key] = {"present": False}
            continue
        try:
            doc = _load_ini(g, name)
            facts[key] = {
                "present": True,
                "options": {k.lower(): v for k, v in doc.keys("Options").items()},
                "video": {k.lower(): v for k, v in doc.keys("Video").items()},
                "audio": {k.lower(): v for k, v in doc.keys("Audio").items()},
                "sections": doc.sections(),
                "size": (g.path / name).stat().st_size,
            }
        except (OSError, ValueError) as exc:
            facts[key] = {"present": True, "error": str(exc)}

    # 兼容性标记
    layers = {}
    for name in g.present_exes():
        layers[name] = appcompat.analyze(g.exe(name), name)
    facts["appcompat"] = layers

    # 回滚信息
    facts["backup"] = {
        "has_backup": backup.has_backup(g.path),
        "pristine_files": backup.pristine_files(g.path),
        "runs": [r.get("run_id") for r in backup.manifest(g.path).get("runs", [])],
    }

    # 崩溃证据
    from . import launcher

    dumps = launcher.crash_dumps()
    facts["crash_dumps"] = dumps
    log_tail = launcher.tail_log(g, lines=200)
    facts["ddraw_log_tail"] = log_tail[-40:]
    facts["ddraw_log_exists"] = bool(launcher.log_path(g).is_file())

    # 战役安装状态（由 ra2forge 装入，仅作记录，不参与优化决策）
    # 新版 ra2forge（FORGE-1 方案 B 起）的注册文件是**散装 BATTLEMD98.INI**
    # （只追加自有条目 [Battles] 15=RA2F1），官方 BATTLEMD.INI 不再被改写；
    # 旧版安装留下的才是散装 BATTLEMD.INI 覆盖件 —— 两种形态都要认。
    campaign = {"expandmd98": g.has("expandmd98.mix")}
    for flag, head_key, file_name in (
        ("battlemd_ini", "battlemd_head", "BATTLEMD.INI"),
        ("battlemd98_ini", "battlemd98_head", "BATTLEMD98.INI"),
    ):
        path = g.path / file_name
        campaign[flag] = path.is_file()
        if not campaign[flag]:
            continue
        try:
            text = path.read_bytes().decode("gbk", errors="replace")
        except OSError:
            continue
        campaign[head_key] = text.splitlines()[:12]
    facts["campaign"] = campaign

    facts["disk_free_mb"] = _disk_free_mb(g.path)
    return facts


def _load_ini(g, name):
    from . import inifile

    return inifile.IniFile.load(g.path, name)


def _disk_free_mb(path) -> int:
    try:
        usage = os.statvfs(path)
        return int(usage.f_bavail * usage.f_frsize // (1024 * 1024)) if hasattr(os, "statvfs") else 0
    except (OSError, AttributeError):
        try:
            import shutil

            return shutil.disk_usage(path).free // (1024 * 1024)
        except OSError:
            return 0


# ---------------------------------------------------------------------------
# 分析
# ---------------------------------------------------------------------------

def _as_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def analyze(facts: dict) -> list:
    """基于事实产出待办清单。"""
    out: list = []
    add = out.append

    if not facts.get("valid"):
        add(Finding(
            "dir.invalid", "critical", "这里不像是一个尤复游戏目录",
            f"没有找到 `{gamemod.GAMEMD_EXE}`。",
            [f"检查路径：{facts.get('missing_gamemd')}"],
            "用 --game 指定含 gamemd.exe 的游戏目录，例如 --game ra2youli",
        ))
        return out

    env = facts["env"]
    gamemd = facts.get("gamemd", {})
    components = facts.get("components", {})

    # --- 引擎与内存 ---
    if gamemd.get("known_as"):
        add(Finding("exe.identity", "ok", "已识别引擎版本",
                    f"`gamemd.exe` = {gamemd['known_as']}。",
                    [f"代码段指纹：{(gamemd.get('text_sha256') or '')[:16]}…",
                     f"整文件 SHA-256：{gamemd.get('sha256', '')[:16]}…"
                     + ("（与我们记录的原始版本不同 = 已被本工具改过头部，属预期）"
                        if gamemd.get("patched_by_ra2opt") else "")]))

    laa = bool(gamemd.get("laa"))
    if not laa and env["is_64bit_host"] and env["ram_mb"] >= LAA_RAM_THRESHOLD_MB:
        add(Finding(
            "exe.laa", "warn", "引擎没有开 Large Address Aware（4GB 内存寻址）",
            "gamemd.exe 是 32 位程序且未声明 LAA，用户态地址空间被卡在 2GB。"
            "大地图 + 多单位/多 AI 时内存很容易撞到这个上限，表现就是"
            "“玩着玩着突然闪退”或弹出内存不足。开 LAA 后在 64 位系统上可用 4GB，"
            "这类崩溃会大幅减少。",
            [f"PE COFF Characteristics = {gamemd.get('characteristics')}（LAA bit 0x0020 未置位）",
             f"宿主：64 位 = {env['is_64bit_host']}，物理内存 {env['ram_mb']} MB"],
            "python -m ra2opt laa on --game <游戏目录>",
        ))
    elif laa:
        add(Finding("exe.laa", "ok", "已开启 Large Address Aware",
                    "32 位进程可用到 4GB 地址空间，大地图/多单位时不易触发内存崩溃。", []))

    stack_mb = (gamemd.get("stack_reserve") or 0) / pe.MB
    if 0 < stack_mb <= 1.0:
        add(Finding(
            "exe.stack", "info", f"主线程栈只有 {stack_mb:.0f}MB",
            "MSVC6 的默认值。引擎的寻路/AI 递归在大地图 + 大量单位时会吃栈，"
            "栈溢出表现为毫无征兆的闪退。提到 4MB 只多占地址空间（提交仍按需），"
            "不改变任何指针运算，属于低风险改动。",
            [f"SizeOfStackReserve = {gamemd.get('stack_reserve')} 字节"],
            "python -m ra2opt apply --profile safe --game <游戏目录>",
        ))

    wx = gamemd.get("writable_executable_sections") or []
    if wx:
        add(Finding("exe.wx_sections", "info", "存在可写可执行的段",
                    "该段同时可写可执行，是 DEP 崩溃与内存破坏类问题的常见来源"
                    "（老引擎为性能这么设计）。仅作提示，本工具不修改代码段。",
                    [f"可写可执行段：{', '.join(wx)}"]))

    # --- 渲染代理 ---
    version = facts.get("ddraw_version")
    latest_version = facts.get("ddraw_latest")
    if not components.get("cnc_ddraw"):
        add(Finding(
            "ddraw.missing", "critical", "没有安装 cnc-ddraw（DirectDraw 代理）",
            "现代 Windows 上原版 DirectDraw 早已被阉割，直接跑会出现黑屏、花屏、"
            "Alt+Tab 后退不回画面、切分辨率崩溃等现象。cnc-ddraw 是目前 RA2 玩家的标准方案。",
            [], "python -m ra2opt apply --profile safe --game <游戏目录>",
        ))
    else:
        evidence = [f"ddraw.dll FileVersion = {version or '无法读取'}"]
        outdated = False
        if version and latest_version:
            from . import cddraw

            outdated = cddraw_facts_outdated(version, latest_version)
            evidence.append(f"官方最新 = {latest_version}")
        if outdated:
            add(Finding(
                "ddraw.outdated", "warn", f"cnc-ddraw 版本偏旧（{version} < {latest_version}）",
                "2021→2024 之间官方发布了多条与 RA2 直接相关的崩溃修复，"
                "升级只需替换一个 dll，是本项目性价比最高的一项。",
                evidence + [f"{tag}：{text}" for tag, text in CNCDDRAW_RA2_FIXES],
                "python -m ra2opt apply --profile safe --game <游戏目录>",
            ))
        elif version:
            add(Finding("ddraw.version", "ok", f"cnc-ddraw 版本 {version}（已是最新或无法确认）",
                        "", evidence))

    # --- ddraw.ini ---
    ddraw_ini = facts.get("ddraw_ini", {})
    gset = ddraw_ini.get("global", {})
    gamemd_section = ddraw_ini.get("gamemd", {})
    if components.get("ddraw_ini") and "error" not in ddraw_ini:
        if (gamemd_section.get("tshack", "").lower() not in ("true", "yes", "1")):
            add(Finding(
                "ddraw.ini.tshack", "warn", "ddraw.ini 没有为 gamemd 打开 tshack",
                "`tshack` 是 cnc-ddraw 针对 TS/RA2 引擎的兼容开关，不开会导致渲染异常。",
                [f"[gamemd] tshack = {gamemd_section.get('tshack', '<缺失>')}"],
                "python -m ra2opt apply --profile safe --game <游戏目录>",
            ))
        if gset.get("singlecpu", "").lower() in ("false", "no", "0"):
            add(Finding(
                "ddraw.ini.singlecpu", "info", "cnc-ddraw 未绑定单核（singlecpu=false）",
                "RA2/YR 的时序假设与多核调度不完全兼容，绑定 CPU0 能规避一类崩溃/卡死；"
                "代价是极端情况下略微损失吞吐。",
                ["[ddraw] singlecpu = false"], ""))

        # 分辨率 / 拉伸一致性
        ra2md = facts.get("ra2md_ini", {})
        sw = _as_int(ra2md.get("video", {}).get("screenwidth"))
        sh = _as_int(ra2md.get("video", {}).get("screenheight"))
        dw = _as_int(gset.get("width"))
        dh = _as_int(gset.get("height"))
        maintas = gset.get("maintas", "").lower() in ("true", "yes", "1")
        if sw and sh and dw and dh and (dw, dh) != (sw, sh) and not maintas:
            add(Finding(
                "ddraw.ini.stretch", "warn",
                f"窗口 {dw}x{dh} 与游戏分辨率 {sw}x{sh} 不一致，且未保持宽高比",
                "画面会被非等比拉伸：既模糊又变形（这是当前这台机器的实际情况）。"
                "要么让窗口跟随游戏分辨率做 1:1 输出，要么打开 maintas 保持比例。",
                [f"[ddraw] width/height = {dw}x{dh}，maintas = {gset.get('maintas')}",
                 f"ra2md.ini [Video] {sw}x{sh}"],
                "python -m ra2opt apply --profile safe --game <游戏目录>",
            ))

    # --- ra2md.ini / ra2.ini ---
    for name, label in (("ra2md_ini", "ra2md.ini（尤复）"), ("ra2_ini", "ra2.ini（原版红警2）")):
        doc = facts.get(name, {})
        if not doc.get("present"):
            continue
        video = doc.get("video", {})
        options = doc.get("options", {})
        if video.get("videobackbuffer", "").lower() not in ("no", "false", "0"):
            add(Finding(
                f"ini.videobackbuffer.{name}", "warn",
                f"{label} 未关闭 VideoBackBuffer",
                "后台缓冲会让部分显卡驱动在切换分辨率/Alt+Tab 时崩溃或黑屏，"
                "RA2 社区的标准做法是关掉它。",
                [f"[Video] VideoBackBuffer = {video.get('videobackbuffer', '<缺失>')}"],
                "python -m ra2opt apply --profile safe --game <游戏目录>",
            ))
        if video.get("allowvramsidebar", "").lower() in ("yes", "true", "1"):
            add(Finding(
                f"ini.vramsidebar.{name}", "warn",
                f"{label} 打开了 AllowVRAMSidebar",
                "把侧边栏放到显存里在新驱动上容易出现黑块/闪屏，建议关闭。",
                ["[Video] AllowVRAMSidebar = yes"],
                "python -m ra2opt apply --profile safe --game <游戏目录>",
            ))
        detail = _as_int(options.get("detaillevel"), -1)
        if detail == 2:
            add(Finding(
                f"ini.detail.{name}", "info",
                f"{label} 渲染细节为最高档（DetailLevel=2）",
                "多单位场景下渲染是主要瓶颈之一：细节档位越高，要绘制的动画/装饰层越多。"
                "降到 1 只影响画面细节，不改动任何游戏规则与胜负判定，是「不换硬件」的"
                "最直接手段。",
                ["[Options] DetailLevel = 2（最高）"],
                "python -m ra2opt apply --profile perf --game <游戏目录>（会设 DetailLevel=1）",
            ))
        speed = _as_int(options.get("gamespeed"), -1)
        if 0 <= speed <= 2:
            add(Finding(
                f"ini.gamespeed.{name}", "info", f"{label} 游戏速度偏低（GameSpeed={speed}）",
                "速度档位偏低时引擎每帧间隔更长，单位多时的掉速会更明显。"
                "这属于个人偏好，仅供参考。", [f"[Options] GameSpeed = {speed}"]))

    # --- 兼容性标记 ---
    for exe_name, info in (facts.get("appcompat") or {}).items():
        if info.get("problems"):
            add(Finding(
                f"appcompat.harmful.{exe_name}", "warn",
                f"{exe_name} 带有会引发问题的兼容性标记",
                "这些标记是老整合包为了让原版 DirectDraw 能跑而加的，"
                "在已经装了 cnc-ddraw 的前提下只会带来副作用。",
                info["problems"],
                "python -m ra2opt apply --profile safe --game <游戏目录>",
            ))
        elif info.get("recommended"):
            add(Finding(
                f"appcompat.missing.{exe_name}", "info",
                f"{exe_name} 可以补两个兼容性标记",
                "`DISABLEDXMAXIMIZEDWINDOWEDMODE` 让全屏走独占而不是 Win10+ 的"
                "“全屏优化”假全屏（后者有额外合成延迟）；`HIGHDPIAWARE` 避免 DPI 缩放"
                "导致的模糊。",
                [f"当前：{info.get('raw') or '<无>'}"],
                "python -m ra2opt apply --profile safe --game <游戏目录>",
            ))

    # --- 崩溃证据 ---
    dumps = facts.get("crash_dumps") or []
    if dumps:
        add(Finding(
            "crash.dumps", "warn", f"发现 {len(dumps)} 个与游戏相关的崩溃转储",
            "Windows 错误报告留下了 dump，说明确实崩过。可以配合 DbgHelp/WinDbg 用 "
            "`!analyze -v` 看崩溃模块，或先按本报告的建议逐项排除。",
            [f"{Path(d['path']).name}  {d['size'] // 1024} KB  "
             f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(d['mtime']))}" for d in dumps[:5]],
        ))
    log_tail = facts.get("ddraw_log_tail") or []
    if log_tail:
        bad = [ln for ln in log_tail if any(
            kw in ln.lower() for kw in
            ("error", "fail", "exception", "crash", "unsupported", "invalid", "cannot"))]
        if bad:
            add(Finding(
                "crash.ddraw_log", "warn", "ddraw.log 里有报错记录",
                "cnc-ddraw 会把初始化与致命错误写进 `ddraw.log`，这是排查崩溃的第一手材料。",
                bad[-6:],
            ))

    # --- 回滚能力 ---
    bk = facts.get("backup", {})
    if bk.get("has_backup"):
        add(Finding("backup.present", "ok", "存在原始快照，可随时回滚",
                    "", [f"已快照：{', '.join(bk.get('pristine_files', []))}"]))
    else:
        add(Finding(
            "backup.none", "info", "还没有原始快照",
            "第一次执行 apply 时会自动创建 `<游戏目录>/.ra2opt/orig/`，"
            "之后任何改动都能用 `restore` 一键撤销。", [],
            "python -m ra2opt apply --profile safe --game <游戏目录>",
        ))

    # --- 网络降级记录 ---------------------------------------------------
    for note in facts.get("net_notes") or []:
        add(Finding(
            "net.note", "info", "联网请求有一处降级放行",
            "本工具的下载只允许 https + 主机白名单 + 公网 IP。这里记录的是被放行的"
            "唯一例外，用来避免静默降级——看到它就说明本机 DNS 走了代理的 fake-IP。",
            [note]))

    # --- 战役安装记录 ---
    camp = facts.get("campaign", {})
    if camp.get("expandmd98") or camp.get("battlemd_ini") or camp.get("battlemd98_ini"):
        add(Finding(
            "campaign.installed", "info", "检测到已安装的 AI 战役（ra2forge 产物）",
            "expandmd98.mix + 散装 BATTLEMD98.INI（新版：自有条目 RA2F1 追加，"
            "BATTLEMD.INI 保持官方原样）或散装 BATTLEMD.INI（旧版：覆盖过官方列表）"
            "是 ra2forge 生成的战役包，本工具的优化不碰这些文件"
            "（改的是引擎/wrapper/配置层），可以共存。",
            [f"expandmd98.mix = {camp.get('expandmd98')}",
             f"BATTLEMD98.INI = {camp.get('battlemd98_ini')}",
             f"BATTLEMD.INI = {camp.get('battlemd_ini')}"],
        ))
    return out


def cddraw_facts_outdated(version: str, latest: str) -> bool:
    from .game import compare_versions

    return compare_versions(version, latest) < 0


def sort_findings(findings) -> list:
    return sorted(findings, key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.id))


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------

def render_markdown(facts: dict, findings: list) -> str:
    env = facts.get("env", {})
    lines = [
        "# RA2 / 尤复 稳定性与性能体检报告",
        "",
        f"生成时间：{env.get('checked_at')}　工具版本：ra2opt {env.get('ra2opt_version')}",
        f"游戏目录：`{facts.get('game_dir')}`",
        "",
        "## 环境",
        "",
        f"- 系统：{env.get('os')}（64 位宿主 = {env.get('is_64bit_host')}）",
        f"- CPU：{env.get('cpu')}（{env.get('cpu_count')} 逻辑核）",
        f"- 内存：{env.get('ram_mb')} MB",
        f"- Python：{env.get('python')}",
        "",
    ]

    counts = {}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    summary = "，".join(f"{SEVERITY_LABEL[s]} {counts[s]}" for s in
                        ("critical", "warn", "info", "ok") if s in counts)
    lines += ["## 结论", "", f"共 {len(findings)} 项：{summary}。", ""]

    for severity in ("critical", "warn", "info"):
        group = [f for f in findings if f.severity == severity]
        if not group:
            continue
        lines += [f"### {SEVERITY_LABEL[severity]}（{len(group)}）", ""]
        for f in group:
            lines.append(f"**{f.title}**")
            lines.append("")
            if f.detail:
                lines.append(f.detail)
                lines.append("")
            for ev in f.evidence:
                lines.append(f"- `{ev}`")
            if f.evidence:
                lines.append("")
            if f.fix:
                lines.append(f"修：`{f.fix}`")
                lines.append("")

    ok = [f for f in findings if f.severity == "ok"]
    if ok:
        lines += ["### 已达标", ""]
        for f in ok:
            lines.append(f"- {f.title}")
        lines.append("")

    lines += [
        "## 附录：本工具会改什么、怎么撤销",
        "",
        "| 层 | 动作 | 可用性 |",
        "|---|---|---|",
        "| 渲染代理 | 升级/安装 cnc-ddraw，重写 `ddraw.ini` 调优项 | 覆盖前快照 `ddraw.dll`/`ddraw.ini` |",
        "| PE 头 | COFF 头 LAA 位、栈保留空间 | 只改 PE 头字段，代码段零改动 |",
        "| 配置 | `ra2md.ini` / `ra2.ini` 少量键 | 行级保留注释与顺序，只改指定键 |",
        "| 系统 | HKCU 兼容性标记 | 记录原值，restore 时还原 |",
        "| 启动 | 生成 `ra2opt_play.bat` | 直接删除即可 |",
        "",
        "撤销全部改动：`python -m ra2opt restore --game <游戏目录>`",
        "",
        "> 本工具**不改**：`.mix` 资源、地图、`BATTLEMD.INI`（战役内容），也不改游戏代码段。",
        "",
    ]
    return "\n".join(lines)


def run(game_path, out_dir=None, *, online: bool = False) -> dict:
    """跑一次体检。`online=True` 时额外联网查询 cnc-ddraw 最新版本。"""
    from . import net

    net.clear_notes()
    facts = collect(game_path)
    if online and facts.get("valid"):
        try:
            from . import cddraw

            rel = cddraw.latest_release()
            facts["ddraw_latest"] = rel.version
            facts["ddraw_latest_published"] = rel.published
            facts["ddraw_latest_notes"] = rel.body[:2000]
            cached = cddraw.cached_zip()
            facts["ddraw_cached_zip"] = str(cached) if cached else None
        except Exception as exc:  # 网络问题不影响体检
            facts["ddraw_latest_error"] = f"{type(exc).__name__}: {exc}"
    facts["net_notes"] = net.notes()
    findings = sort_findings(analyze(facts))

    report = {
        "facts": facts,
        "findings": [asdict(f) for f in findings],
        "summary": {s: sum(1 for f in findings if f.severity == s)
                    for s in ("critical", "warn", "info", "ok")},
    }
    if out_dir:
        target = Path(out_dir)
        target.mkdir(parents=True, exist_ok=True)
        (target / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (target / "report.md").write_text(
            render_markdown(facts, findings), encoding="utf-8")
        report["report_dir"] = str(target)
    return report


def print_findings(findings, stream=sys.stdout) -> None:
    for f in findings:
        mark = {"critical": "[!]", "warn": "[*]", "info": "[-]", "ok": "[+]"}.get(f.severity, "[ ]")
        print(f"{mark} {f.title}", file=stream)
        if f.severity != "ok" and f.detail:
            print(f"      {f.detail}", file=stream)
        if f.fix:
            print(f"      → {f.fix}", file=stream)
