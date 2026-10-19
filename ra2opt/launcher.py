"""启动器：生成 bat 快捷方式，以及从 Python 以指定优先级/亲和性启动游戏。

为什么需要它：RA2/YR 的引擎是 2001 年的单线程循环，被其他进程抢占时会明显抖动
（表现为"卡顿"）。给它较高的优先级能减少被调度器打断的次数，这是纯调度层面的
收益，不改动游戏任何逻辑。

进程创建一律走 `winproc.spawn()`（`CreateProcessW` + `lpApplicationName`，
不构造命令行），可执行文件名必须匹配白名单正则且必须存在于游戏目录内。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from . import safewrite, winproc
LAUNCHER_NAME = "ra2opt_play.bat"

LAUNCHER_TEMPLATE = """@echo off
rem ra2opt 启动器 - 由 `python -m ra2opt apply` 生成，可安全删除
rem 作用：以高优先级启动游戏，减少被其他进程抢占造成的卡顿。
rem 直接双击 %EXE% 也能玩，只是没有这个优先级提升。
cd /d "%~dp0"
start "" /%STARTFLAG% "%EXE%"
"""

_START_FLAG = {"high": "high", "realtime": "realtime",
               "above": "abovenormal", "normal": "normal"}


@dataclass
class LaunchResult:
    pid: int
    exe: str
    priority: str
    priority_applied: bool
    affinity: str | None
    affinity_applied: bool
    notes: list = field(default_factory=list)


def resolve_exe(game, exe: str) -> Path:
    """把 exe 名解析成游戏目录内的真实路径；名字非法或不存在即拒绝。

    统一走 `GameDir.resolve_exe()`（裸文件名校验 + 沙箱校验），
    这样"从名字到可写路径"只有一处实现，不会各写各的。
    """
    return game.resolve_exe(exe)


def write_launcher(game, exe: str = "gamemd.exe", priority: str = "high") -> str | None:
    """在游戏目录生成 `ra2opt_play.bat`。

    返回写入的文件名；内容与现有文件完全一致时返回 None（不重复写）。
    """
    resolve_exe(game, exe)
    text = (LAUNCHER_TEMPLATE
            .replace("%STARTFLAG%", _START_FLAG.get(priority, "normal"))
            .replace("%EXE%", exe))
    payload = text.encode("gbk", errors="replace")
    if game.has(LAUNCHER_NAME):
        try:
            if safewrite.read_bytes(game.path, LAUNCHER_NAME) == payload:
                return None
        except (OSError, ValueError):
            pass
    safewrite.write_bytes(game.path, LAUNCHER_NAME, payload, allow_create=True)
    return LAUNCHER_NAME


def play(game, *, exe: str = "gamemd.exe", priority: str = "high",
         affinity: int | None = None, wait: bool = False) -> LaunchResult:
    """启动游戏并可调优先级/亲和性。默认立即返回（游戏继续运行）。"""
    target = resolve_exe(game, exe)
    proc = winproc.spawn(target, cwd=str(game.path), priority=priority, affinity=affinity)
    result = LaunchResult(
        pid=proc.pid, exe=exe, priority=priority,
        priority_applied=proc.priority_applied,
        affinity=str(affinity) if affinity is not None else None,
        affinity_applied=proc.affinity_applied,
        notes=list(proc.notes),
    )
    if wait:
        code = proc.wait()
        result.notes.append(f"游戏进程已退出，返回码 {code}")
        proc.close()
    return result


def smoke_test(game, *, exe: str = "gamemd.exe", seconds: float = 8.0) -> dict:
    """启动游戏并观察 N 秒，然后结束进程。

    用途：确认"改过 PE 头 / 换了 ddraw.dll 之后游戏至少能起来"。
    这不是完整的功能验证——只证明加载器与初始化阶段没有立刻崩溃。
    """
    target = resolve_exe(game, exe)
    proc = winproc.spawn(target, cwd=str(game.path), priority="normal")
    try:
        code = proc.wait(timeout_ms=int(seconds * 1000))
        if code is None:
            return {"started": True, "exit_code": None, "alive_seconds": seconds,
                    "verdict": f"存活 {seconds:.0f} 秒未退出，启动阶段正常（已结束进程）"}
        return {"started": False, "exit_code": code, "alive_seconds": 0.0,
                "verdict": f"启动后 {seconds:.0f} 秒内已退出（返回码 {code}，疑似崩溃）"}
    finally:
        proc.terminate()
        proc.close()


def log_path(game) -> Path:
    return game.path / "ddraw.log"


def tail_log(game, lines: int = 40) -> list:
    """读 cnc-ddraw 的 ddraw.log 尾部（崩溃排查的第一手材料）。"""
    path = log_path(game)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="latin-1", errors="replace")
    except OSError:
        return []
    return text.splitlines()[-lines:]


def crash_dumps(names=("gamemd.exe", "ra2md.exe", "ra2.exe", "yuri.exe")) -> list:
    """列出 %LOCALAPPDATA%\\CrashDumps 下与游戏 exe 相关的转储文件。"""
    base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "CrashDumps")
    if not os.path.isdir(base):
        return []
    wanted = {n.lower() for n in names}
    out = []
    for entry in os.scandir(base):
        if not entry.is_file():
            continue
        stem = entry.name.split(".")[0].lower() + ".exe"
        if stem in wanted:
            stat = entry.stat()
            out.append({"path": entry.path, "size": stat.st_size, "mtime": stat.st_mtime})
    out.sort(key=lambda d: d["mtime"], reverse=True)
    return out
