# -*- coding: utf-8 -*-
"""载体隔离检测器：从 WER Report.wer 判断哪些模块来自载体外。

用途：趟收尾后对 WER 记录做一次只读审计，把「哪些模块来自载体目录外」
变成可观测事实。零改动、零注入、只读。

背景：gamemd 通过注册表
  HKLM\\SOFTWARE\\WOW6432Node\\Westwood\\Yuri's Revenge\\InstallPath
解析绝对路径。凡走该路径的加载都绕开载体目录，直接取安装目录里的副本。
2026-10-16 的 QC111 现场已实证 LoadedModule[58] 落在载体外。

★ Sig[] 必须按 .Name= 配对取值，不能按 Sig[N] 的索引硬编码：
  本机 25 份 AppCrash 里「异常代码/异常偏移」有 [7]/[6]（17 份）、
  [6]/[7]（6 份）、以及两项都无（2 份）三种布局。

用法：
    python wer_module_isolation_audit.py <Report.wer 路径> --carrier <载体目录>
    python wer_module_isolation_audit.py --scan-archive --carrier <载体目录>
    python wer_module_isolation_audit.py --scan-archive --all --carrier <载体目录>
"""
import argparse
import glob
import os
import re
import sys

SYSTEM_PREFIXES = (
    "c:\\windows\\",
    "c:\\program files\\",
    "c:\\program files (x86)\\",
    "c:\\programdata\\",
)

# Sig 名称的中英文两套写法
NAME_EXC_CODE = ("异常代码", "Exception Code")
NAME_EXC_OFFSET = ("异常偏移", "Fault offset")
NAME_FAULT_MODULE = ("故障模块名称", "Fault Module Name")
NAME_APP_VERSION = ("应用程序版本", "Application Version")
NAME_APP_TIMESTAMP = ("应用程序时间戳", "Application Timestamp")
NAME_HANG_SIG = ("Hang Signature",)
NAME_HANG_TYPE = ("Hang Type",)


def _first(d, keys):
    for k in keys:
        if k in d and d[k]:
            return d[k]
    return None


def read_wer(path):
    """WER 的 Report.wer 是 UTF-16LE（带 BOM），也有纯 ASCII 的变体。"""
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16-le" if raw[:2] == b"\xff\xfe" else "utf-16-be",
                          errors="replace")
    else:
        text = raw.decode("utf-8", errors="replace")
    return text


def parse_report(text):
    """抽出事件类型、时间、签名字段、模块表。"""
    info = {
        "event_type": None,
        "event_time_ft": None,
        "is_fatal": None,
        "app_path": None,
        "ns_app_name": None,
        "hang_signature": None,
        "hang_type": None,
        "exception_code": None,
        "exception_offset": None,
        "fault_module": None,
        "app_version": None,
        "app_timestamp": None,
        "sig": {},
        "modules": [],
    }
    for line in text.splitlines():
        s = line.strip()
        if not s or "=" not in s:
            continue
        key, _, val = s.partition("=")
        key, val = key.strip(), val.strip()
        if key == "EventType":
            info["event_type"] = val
        elif key == "EventTime":
            info["event_time_ft"] = val
        elif key == "IsFatal":
            info["is_fatal"] = val
        elif key == "AppPath":
            info["app_path"] = val
        elif key == "NsAppName":
            info["ns_app_name"] = val
        elif key.startswith("LoadedModule["):
            idx = int(re.search(r"\[(\d+)\]", key).group(1))
            info["modules"].append((idx, val))

    # 按 Name 配对抓 Sig 值（不按索引，见模块 docstring）
    sig = {}
    cur = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("Sig[") and ".Name=" in s:
            cur = s.split(".Name=", 1)[1].strip()
        elif s.startswith("Sig[") and ".Value=" in s:
            val = s.split(".Value=", 1)[1].strip()
            if cur and cur not in sig:
                sig[cur] = val
            cur = None
    info["sig"] = sig
    info["hang_signature"] = _first(sig, NAME_HANG_SIG)
    info["hang_type"] = _first(sig, NAME_HANG_TYPE)
    info["exception_code"] = _first(sig, NAME_EXC_CODE)
    info["exception_offset"] = _first(sig, NAME_EXC_OFFSET)
    info["fault_module"] = _first(sig, NAME_FAULT_MODULE)
    info["app_version"] = _first(sig, NAME_APP_VERSION)
    info["app_timestamp"] = _first(sig, NAME_APP_TIMESTAMP)
    info["modules"].sort()
    return info


def is_system_path(p):
    low = p.lower()
    return any(low.startswith(pre) for pre in SYSTEM_PREFIXES)


def classify(modules, carrier_dir):
    """把模块分成：载体 / 系统 / 越界。"""
    carrier_abs = os.path.normcase(os.path.abspath(carrier_dir)).rstrip("\\") + "\\"
    inside, system, outside = [], [], []
    for idx, p in modules:
        if not os.path.isabs(p):
            outside.append((idx, p))
            continue
        pc = os.path.normcase(os.path.abspath(p))
        if pc.startswith(carrier_abs):
            inside.append((idx, p))
        elif is_system_path(p):
            system.append((idx, p))
        else:
            outside.append((idx, p))
    return inside, system, outside


def ft_to_local(ft_str):
    """FILETIME(100ns since 1601) -> 本地时间字符串。"""
    try:
        ft = int(ft_str)
    except (TypeError, ValueError):
        return None
    import datetime
    unix = ft / 1e7 - 11644473600
    return datetime.datetime.fromtimestamp(unix).strftime("%Y-%m-%d %H:%M:%S")


def _hex_or_raw(v):
    if v is None:
        return None
    try:
        return "%s (hex %s)" % (v, hex(int(v)))
    except (TypeError, ValueError):
        return v


def audit_one(wer_path, carrier_dir, verbose=False):
    text = read_wer(wer_path)
    info = parse_report(text)
    inside, system, outside = classify(info["modules"], carrier_dir)

    print("=" * 74)
    print("报告: %s" % os.path.basename(os.path.dirname(wer_path)))
    print("=" * 74)
    print("  事件类型   : %s" % info["event_type"])
    print("  发生时刻   : %s" % (ft_to_local(info["event_time_ft"]) or "?"))
    print("  IsFatal    : %s" % info["is_fatal"])
    print("  进程路径   : %s" % info["app_path"])
    if info["hang_signature"] is not None:
        print("  Hang Sig   : %s" % _hex_or_raw(info["hang_signature"]))
    if info["hang_type"] is not None:
        print("  Hang Type  : %s" % _hex_or_raw(info["hang_type"]))
    if info["exception_code"]:
        print("  异常代码   : %s" % info["exception_code"])
    if info["exception_offset"]:
        print("  异常偏移   : %s" % info["exception_offset"])
    if info["fault_module"]:
        print("  故障模块   : %s" % info["fault_module"])
    print("  模块总数   : %d" % len(info["modules"]))
    print("    载体内   : %d" % len(inside))
    print("    系统     : %d" % len(system))
    print("    ★ 越界   : %d" % len(outside))

    if inside:
        print()
        print("  载体内模块（应含 exe + 注入目标）：")
        for idx, p in inside:
            print("    [%3d] %s" % (idx, p))

    if outside:
        print()
        print("  ★ 越界模块（来自载体目录之外）：")
        for idx, p in outside:
            exists = "存在" if os.path.exists(p) else "已不存在"
            print("    [%3d] %s  (%s)" % (idx, p, exists))
        print()
        print("  说明：越界不等于污染——若越界件与载体件 sha256 相同，")
        print("        则是同一二进制被按 InstallPath 绝对路径加载，")
        print("        问题在「隔离边界」而不在「代码来源」。")
    elif verbose:
        print()
        print("  ✅ 无越界模块")

    return {
        "wer": wer_path,
        "event_type": info["event_type"],
        "event_time": ft_to_local(info["event_time_ft"]),
        "exception_code": info["exception_code"],
        "exception_offset": info["exception_offset"],
        "fault_module": info["fault_module"],
        "n_modules": len(info["modules"]),
        "n_inside": len(inside),
        "n_system": len(system),
        "n_outside": len(outside),
        "outside": [p for _, p in outside],
        "inside": [p for _, p in inside],
    }


def main():
    ap = argparse.ArgumentParser(description="WER 模块表载体隔离审计（只读）")
    ap.add_argument("wer", nargs="?", help="Report.wer 路径")
    ap.add_argument("--scan-archive", action="store_true",
                    help="扫描 WER ReportArchive 里全部匹配记录")
    ap.add_argument("--app", default="gamemd",
                    help="--scan-archive 时的进程名过滤（默认 gamemd）")
    ap.add_argument("--all", action="store_true",
                    help="配合 --scan-archive，扫全部记录不过滤进程名")
    ap.add_argument("--archive-dir",
                    default=r"C:\ProgramData\Microsoft\Windows\WER\ReportArchive")
    ap.add_argument("--carrier", required=True, help="载体目录（隔离基准）")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(args.carrier):
        print("载体目录不存在: %s" % args.carrier)
        return 2

    targets = []
    if args.scan_archive:
        if args.all:
            pattern = os.path.join(args.archive_dir, "*", "Report.wer")
            label = "全部"
        else:
            pattern = os.path.join(args.archive_dir, "*%s*" % args.app, "Report.wer")
            label = args.app
        targets = sorted(glob.glob(pattern))
        if not targets:
            print("ReportArchive 里没有 *%s* 记录: %s" % (label, args.archive_dir))
            return 1
        print("找到 %d 份 %s WER 记录" % (len(targets), label))
        print()
    elif args.wer:
        if not os.path.isfile(args.wer):
            print("文件不存在: %s" % args.wer)
            return 2
        targets = [args.wer]
    else:
        ap.error("需要给出 Report.wer 路径，或用 --scan-archive")

    results = [audit_one(t, args.carrier, args.verbose) for t in targets]

    print()
    print("=" * 74)
    print("汇总")
    print("=" * 74)
    total_outside = 0
    for r in results:
        flag = "★越界%d" % r["n_outside"] if r["n_outside"] else "OK"
        print("  %-20s %-26s %s" % (r["event_time"] or "?", r["event_type"] or "?", flag))
        total_outside += r["n_outside"]
    print()
    print("  越界模块总数: %d" % total_outside)
    return 0 if total_outside == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
