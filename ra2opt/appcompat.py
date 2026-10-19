"""Windows 兼容性标记（AppCompatFlags\\Layers）读写与体检。

位置（HKCU，不需要管理员权限）::

    HKCU\\Software\\Microsoft\\Windows NT\\CurrentVersion\\AppCompatFlags\\Layers

值名 = exe 完整路径，值 = 以 `~` 开头的空格分隔标记串，例如
`~ RUNASADMIN 16BITCOLOR WINXPSP2`。

本机整合版的 `0ne.bat` 就给 Ra2.exe / Ra2md.exe / 配置器.exe 打了
`RUNASADMIN 16BITCOLOR WINXPSP2`，其中两个标记在老游戏 + cnc-ddraw 的组合下
是**有害**的：

- `16BITCOLOR`：强制 16 位色深（桌面分辨率/色深被改），现代显卡驱动 +
  cnc-ddraw 已经在 32 位色下正确输出 16bpp 画面，这个标记只会引入
  模式切换失败、黑屏、颜色错乱。
- `RUNASADMIN`：每次启动弹 UAC；更麻烦的是提权进程与普通权限的 ddraw 代理/hook
  之间会出现跨完整性级别的问题（注入失败、文件虚拟化）。

有益的两个：

- `DISABLEDXMAXIMIZEDWINDOWEDMODE`：让全屏走独占而不是 Win10+ 的"全屏优化"
  假全屏（后者会带来额外合成延迟与偶发卡顿）。
- `HIGHDPIAWARE`：避免 DPI 缩放导致画面模糊。
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import winreg
except ImportError:  # 非 Windows 上仅用于测试导入
    winreg = None

LAYERS_SUBKEY = r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"

# 会带来兼容性收益的标记
HELPFUL_FLAGS = ("DISABLEDXMAXIMIZEDWINDOWEDMODE", "HIGHDPIAWARE")
# 老游戏 + wrappers 组合下通常有害的标记
HARMFUL_FLAGS = {
    "16BITCOLOR": "强制 16 位色，与 cnc-ddraw/现代驱动冲突（改桌面色深）",
    "256COLOR": "强制 256 色，与 cnc-ddraw 冲突",
    "640X480": "强制 640x480，缩放模糊且与高分辨率设置冲突",
    "RUNASADMIN": "每次启动弹 UAC；提权进程会破坏 ddraw 代理/hook",
}
# 影响不大但没必要保留的
LEGACY_FLAGS = {"WINXPSP2", "WINXPSP3", "WIN98", "WIN2000", "DISABLETHEMES"}

_VIEWS = []
if winreg is not None:
    _VIEWS = [
        ("64", winreg.KEY_WOW64_64KEY),
        ("32", winreg.KEY_WOW64_32KEY),
    ]


def _iter_keys(access=winreg.KEY_READ if winreg else 0):
    """遍历两个注册表视图（有的安装会把值写进 WOW6432Node 镜像）。"""
    for label, view in _VIEWS:
        try:
            yield label, winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, LAYERS_SUBKEY, 0, access | view
            )
        except OSError:
            continue


def read_layers() -> dict:
    """读取全部兼容性标记。键为 exe 路径原文（保留大小写），值为标记串。"""
    if winreg is None:
        return {}
    out = {}
    for _label, key in _iter_keys():
        with key:
            i = 0
            while True:
                try:
                    name, value, _type = winreg.EnumValue(key, i)
                except OSError:
                    break
                i += 1
                out[name] = value
    return out


def normalize(exe_path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(exe_path)))


def get_layer(exe_path) -> str | None:
    """取某个 exe 的兼容性标记串（原始文本），没有则 None。"""
    want = normalize(exe_path)
    for name, value in read_layers().items():
        if normalize(name) == want:
            return value
    return None


def parse_flags(value) -> list:
    """把 `~ A B` 解析成 ['A','B']（保序、去重）。"""
    if not value:
        return []
    text = str(value).strip()
    if text.startswith("~"):
        text = text[1:]
    seen, out = set(), []
    for token in text.split():
        up = token.upper()
        if up not in seen:
            seen.add(up)
            out.append(up)
    return out


def format_flags(flags) -> str:
    flags = list(flags)
    return "~" + (" " + " ".join(flags) if flags else "")


def _set_in_view(view, exe_path: str, value):
    """在单个注册表视图里写/删一个值。返回是否做了改动。"""
    access = winreg.KEY_ALL_ACCESS | view
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, LAYERS_SUBKEY, 0, access)
    except OSError:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, LAYERS_SUBKEY, 0, access)
    with key:
        if value is None:
            try:
                winreg.DeleteValue(key, exe_path)
                return True
            except OSError:
                return False
        winreg.SetValueEx(key, exe_path, 0, winreg.REG_SZ, value)
        return True


def set_layer(exe_path, value) -> bool:
    """写入（value 为标记串）或删除（value 为 None）兼容性标记。

    两个视图一起处理：镜像里残留的旧值同样会被系统读取，删干净才有效果。
    """
    if winreg is None:
        raise RuntimeError("当前环境不支持 winreg（非 Windows）")
    exe = os.path.abspath(os.fspath(exe_path))
    changed = False
    for _label, view in _VIEWS:
        try:
            changed |= _set_in_view(view, exe, value)
        except OSError:
            continue
    return changed


def merge_flags(existing, add=(), remove=()) -> str | None:
    """在现有标记基础上增删，返回新的标记串；结果为空则返回 None（表示删除该项）。"""
    flags = parse_flags(existing)
    drop = {f.upper() for f in remove}
    flags = [f for f in flags if f not in drop]
    for f in add:
        up = f.upper()
        if up not in flags:
            flags.append(up)
    return format_flags(flags) if flags else None


def analyze(exe_path, exe_name: str | None = None) -> dict:
    """体检单个 exe 的兼容性标记，返回问题与建议。"""
    raw = get_layer(exe_path)
    flags = parse_flags(raw)
    name = exe_name or Path(os.fspath(exe_path)).name
    problems, suggestions = [], []
    for f in flags:
        if f in HARMFUL_FLAGS:
            problems.append(f"{name}: 兼容性标记 {f} —— {HARMFUL_FLAGS[f]}")
            suggestions.append(f)
    for f in HELPFUL_FLAGS:
        if f not in flags:
            suggestions.append(f)
    return {
        "exe": str(exe_path),
        "name": name,
        "raw": raw,
        "flags": flags,
        "problems": problems,
        "recommended": suggestions,
        "recommended_value": merge_flags(raw, add=HELPFUL_FLAGS, remove=HARMFUL_FLAGS) if suggestions else raw,
    }
