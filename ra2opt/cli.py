"""命令行入口。

    python -m ra2opt audit   [--game DIR] [--online] [--out out/optimize]
    python -m ra2opt apply   [--game DIR] [--profile safe|perf] [--dry-run]
    python -m ra2opt verify  [--game DIR] [--seconds 8]
    python -m ra2opt status  [--game DIR]
    python -m ra2opt laa     on|off [--game DIR]
    python -m ra2opt restore [--game DIR] [--run RUN_ID]
    python -m ra2opt clean   [--game DIR]
    python -m ra2opt play    [--game DIR] [--exe gamemd.exe] [--priority high]
    python -m ra2opt budget  <设计.json> [...]
    python -m ra2opt selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, audit, backup, budget, safewrite
from . import game as gamemod, launcher, optimize, pe

DEFAULT_GAME_CANDIDATES = ("ra2youli", "RedAlert2", "RA2", "YR", "Yuri's Revenge")
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def default_game_dir() -> Path | None:
    """按项目内的常见目录名猜游戏目录（本仓库里就叫 ra2youli）。"""
    for name in DEFAULT_GAME_CANDIDATES:
        cand = PROJECT_ROOT / name
        if (cand / gamemod.GAMEMD_EXE).is_file():
            return cand
    return None


def resolve_game(args) -> gamemod.GameDir:
    path = args.game or default_game_dir()
    if path is None:
        raise SystemExit(
            "没有指定游戏目录，也没在项目里找到含 gamemd.exe 的目录。\n"
            "请用 --game <目录> 指定，例如 --game ra2youli"
        )
    g = gamemod.GameDir(path)
    if not g.valid:
        raise SystemExit(f"{g.path} 里没有 {gamemod.GAMEMD_EXE}，这不像是一个尤复游戏目录。")
    return g


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ra2opt",
        description="红警2 / 尤里的复仇：减少闪退与多单位卡顿的优化工具",
    )
    p.add_argument("--version", action="version", version=f"ra2opt {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_game(sp, help_text="游戏目录（含 gamemd.exe）"):
        sp.add_argument("--game", help=help_text)

    sp = sub.add_parser("audit", help="只读体检，输出待办清单与报告")
    add_game(sp)
    sp.add_argument("--online", action="store_true", help="联网查询 cnc-ddraw 最新版")
    sp.add_argument("--out", default="out/optimize", help="报告输出目录（默认 out/optimize）")
    sp.add_argument("--json", action="store_true", help="只打印 JSON")

    sp = sub.add_parser("apply", help="应用优化（自动备份，可一键回滚）")
    add_game(sp)
    sp.add_argument("--profile", choices=sorted(optimize.PROFILES), default="safe",
                    help="safe=不动 exe 二进制（默认）；perf=额外置 COFF 头 LAA 位并降渲染细节")
    sp.add_argument("--detail", type=int, choices=[0, 1, 2], default=None,
                    help="覆盖 DetailLevel（仅 perf 档默认设为 1）")
    sp.add_argument("--laa", dest="laa", action="store_true", default=None,
                    help="强制打开 Large Address Aware")
    sp.add_argument("--no-laa", dest="laa", action="store_false",
                    help="强制不开 Large Address Aware")
    sp.add_argument("--exe", action="append", default=None,
                    help="只对指定 exe 做 PE 修改，可重复（默认全部）")
    sp.add_argument("--ddraw-zip", default=None, help="离线指定 cnc-ddraw 的 zip 包")
    sp.add_argument("--offline", action="store_true", help="不联网（必须已有本地缓存）")
    sp.add_argument("--no-cddraw", action="store_true", help="跳过 cnc-ddraw 升级")
    sp.add_argument("--no-registry", action="store_true", help="跳过兼容性标记修改")
    sp.add_argument("--keep-display", action="store_true",
                    help="保留现有的分辨率/缩放偏好（不动 ddraw.ini 的显示相关键）")
    sp.add_argument("--multi-cpu", action="store_true",
                    help="关闭 cnc-ddraw 的单核绑定（换吞吐，稳定性风险自担）")
    sp.add_argument("--dry-run", action="store_true", help="只报告将要做的改动")
    sp.add_argument("--verify", action="store_true", help="改完后自动跑一次启动冒烟测试")

    sp = sub.add_parser("verify", help="启动冒烟测试：确认游戏能起来")
    add_game(sp)
    sp.add_argument("--exe", default=gamemod.GAMEMD_EXE)
    sp.add_argument("--seconds", type=float, default=8.0)

    sp = sub.add_parser("status", help="查看当前状态与可回滚内容")
    add_game(sp)

    sp = sub.add_parser("laa", help="单独开关 Large Address Aware")
    sp.add_argument("state", choices=["on", "off"])
    add_game(sp)
    sp.add_argument("--exe", action="append", default=None)

    sp = sub.add_parser("restore", help="从原始快照回滚")
    add_game(sp)
    sp.add_argument("--run", default=None, help="只回滚某一次 apply（run_id）")
    sp.add_argument("--dry-run", action="store_true")

    sp = sub.add_parser("clean", help="删除全部快照（放弃回滚能力）")
    add_game(sp)

    sp = sub.add_parser("seed", help="从另一份未改动的同版本安装补回原始快照")
    add_game(sp)
    sp.add_argument("--from", dest="source", required=True,
                    help="原始安装目录（须含同版本 gamemd.exe）")
    sp.add_argument("--verify", action="store_true",
                    help="逐个核对 SHA-256 是否与已知官方版本一致，不一致就拒绝")
    sp.add_argument("--include-ini", action="store_true",
                    help="连同 ra2md.ini / ra2.ini 一起补（会覆盖玩家的速度/难度等设置，慎用）")
    sp.add_argument("--dry-run", action="store_true")

    sp = sub.add_parser("play", help="以高优先级启动游戏")
    add_game(sp)
    sp.add_argument("--exe", default=gamemod.GAMEMD_EXE)
    sp.add_argument("--priority", choices=sorted(winprio()), default="high")
    sp.add_argument("--cpu", default=None, help="绑定 CPU 序号，如 0 或 0,1")
    sp.add_argument("--wait", action="store_true", help="等到游戏退出再返回")

    sp = sub.add_parser("budget", help="检查战役设计 JSON 的单位预算")
    sp.add_argument("designs", nargs="+", help="设计 JSON 路径")

    sub.add_parser("selftest", help="跑内置自检")
    return p


def winprio():
    from . import winproc

    return winproc.PRIORITY_CLASSES


# ---------------------------------------------------------------------------
# 各子命令
# ---------------------------------------------------------------------------

def cmd_audit(args) -> int:
    g = resolve_game(args)
    out = Path(args.out)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    report = audit.run(g.path, out_dir=out, online=args.online)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    findings = audit.sort_findings([audit.Finding(**f) for f in report["findings"]])
    print(f"== ra2opt 体检：{g.path}")
    print()
    audit.print_findings(findings)
    summary = report["summary"]
    print()
    print(f"严重 {summary['critical']} / 警告 {summary['warn']} / "
          f"建议 {summary['info']} / 已达标 {summary['ok']}")
    print(f"完整报告：{report.get('report_dir')}\\report.md")
    return 1 if summary["critical"] else 0


def cmd_apply(args) -> int:
    g = resolve_game(args)
    report = optimize.apply(
        g.path, profile=args.profile, online=not args.offline,
        ddraw_zip=args.ddraw_zip, detail=args.detail, laa=args.laa,
        exes=args.exe, dry_run=args.dry_run, multi_cpu=args.multi_cpu,
        skip_cddraw=args.no_cddraw, skip_registry=args.no_registry,
        keep_display=args.keep_display,
    )
    print(f"== ra2opt apply --profile {args.profile}"
          + ("（dry-run）" if args.dry_run else ""))
    print(f"游戏目录：{report.game_dir}")
    print()
    for step in report.steps:
        print(f"  · {step}")
    if report.pe_changes:
        print()
        print("PE 头改动：")
        for c in report.pe_changes:
            print(f"  · {c}")
    if report.ini_changes:
        print()
        print("配置改动：")
        for c in report.ini_changes:
            print(f"  · {c}")
    if report.registry_changes:
        print()
        print("兼容性标记：")
        for c in report.registry_changes:
            print(f"  · {c}")
    if report.warnings:
        print()
        print("需要注意：")
        for w in report.warnings:
            print(f"  ! {w}")
    if not args.dry_run:
        print()
        print(f"原始快照：{g.path}\\.ra2opt\\orig\\（回滚：python -m ra2opt restore --game \"{g.path}\"）")
        if report.backup_run:
            print(f"本次记录：run_id = {report.backup_run}")

    if args.verify and not args.dry_run:
        print()
        print("== 启动冒烟测试")
        result = optimize.verify(g.path, seconds=8.0)
        print(f"  {result['verdict']}")
        return 0 if result["started"] else 2
    return 0


def cmd_verify(args) -> int:
    g = resolve_game(args)
    result = optimize.verify(g.path, exe=args.exe, seconds=args.seconds)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    logs = launcher.tail_log(g, lines=15)
    if logs:
        print()
        print("ddraw.log 尾部：")
        for line in logs:
            print(f"  {line}")
    return 0 if result["started"] else 2


def cmd_status(args) -> int:
    g = resolve_game(args)
    st = optimize.status(g.path)
    print(f"游戏目录：{st['game_dir']}")
    print(f"cnc-ddraw：{st['ddraw_version'] or '未安装'}")
    print(f"启动器：{'已生成' if st['launcher_present'] else '未生成'}")
    print()
    print("可执行文件：")
    for name, info in st["exes"].items():
        print(f"  {name:<12} LAA={'开' if info['laa'] else '关'}  "
              f"栈={info['stack_reserve_mb']:.0f}MB")
    print()
    if st["backup_runs"]:
        print("apply 记录（可用 restore --run 精确回滚）：")
        for run in st["backup_runs"]:
            print(f"  {run['run_id']}  {run.get('profile') or '-':<5} "
                  f"{run.get('created')}  改动 {len(run.get('files', []))} 个文件")
        print()
        print(f"原始快照：{', '.join(st['pristine_files']) or '（无）'}")
    else:
        print("还没有 apply 记录，也没有快照。")
    return 0


def cmd_laa(args) -> int:
    g = resolve_game(args)
    targets = args.exe or list(g.present_exes())
    enable = args.state == "on"
    if enable and not pe.is_64bit_host():
        print("提示：当前是 32 位 Windows，LAA 不会带来额外地址空间。")
    bk = backup.BackupSet(g.path, note=f"laa {args.state}")
    bk.ensure_area()
    for name in targets:
        try:
            path = g.resolve_exe(name)
        except (ValueError, safewrite.UnsafePathError) as exc:
            print(f"  {name}: 跳过（{exc}）")
            continue
        before = pe.read(path)
        if before.laa == enable:
            print(f"  {name}: 已经是 {'开' if enable else '关'}，跳过")
            continue
        bk.snapshot(name)
        pe.set_laa(path, enable)
        after = pe.read(path)
        bk.record_file(name)
        # LAA 在 COFF Characteristics（e_lfanew+0x16），不在 DllCharacteristics
        print(f"  {name}: LAA {args.state} 完成"
              f"（COFF Characteristics {before.characteristics:04X} → "
              f"{after.characteristics:04X}）")
    bk.commit()
    if bk.run.files:
        print(f"原始快照已保存，回滚：python -m ra2opt restore --game \"{g.path}\"")
    return 0


def cmd_restore(args) -> int:
    g = resolve_game(args)
    if not backup.has_backup(g.path):
        print("没有找到原始快照，无需回滚。")
        return 0
    done = optimize.restore(g.path, run_id=args.run, dry_run=args.dry_run)
    if not done:
        print("没有需要回滚的内容。")
        return 0
    print("将还原：" if args.dry_run else "已还原：")
    for name, wrote in done:
        print(f"  {name}{'' if wrote or args.dry_run else '（跳过）'}")
    if not args.dry_run:
        print()
        print("兼容性标记与配置文件都已回到 apply 之前的状态。")
    return 0


def cmd_seed(args) -> int:
    g = resolve_game(args)
    expected = None
    if args.verify:
        from . import KNOWN_GAMEMD

        entry = next(iter(KNOWN_GAMEMD.values()))
        expected = {"gamemd.exe": entry["full_sha256"]}
    result = backup.seed(g.path, args.source, expected=expected,
                         include_ini=args.include_ini, dry_run=args.dry_run)
    seeded = sum(1 for _, st in result if st == "seeded")
    for name, status in result:
        mark = {"seeded": "已补回", "missing": "来源里没有",
                "hash-mismatch": "哈希不符，拒绝", "dry-run": "将要补回"}.get(status, status)
        print(f"  {name:<16} {mark}")
    print()
    if args.dry_run:
        print("（dry-run，未写入）")
    elif seeded:
        print(f"已补回 {seeded} 个文件的原始快照，restore 重新可用。")
    else:
        print("没有补回任何文件。")
    return 0


def cmd_clean(args) -> int:
    g = resolve_game(args)
    removed = backup.BackupSet.clean(g.path)
    if removed:
        print(f"已删除快照：{', '.join(removed)}")
        print("注意：删除后无法再回滚到原始状态。")
    else:
        print("没有快照需要删除。")
    return 0


def cmd_play(args) -> int:
    g = resolve_game(args)
    affinity = None
    if args.cpu:
        from . import winproc

        try:
            cpus = [int(x) for x in args.cpu.split(",") if x.strip() != ""]
        except ValueError:
            raise SystemExit("--cpu 只接受逗号分隔的整数，如 0 或 0,1")
        affinity = winproc.cpu_mask(cpus)
    result = launcher.play(g, exe=args.exe, priority=args.priority,
                           affinity=affinity, wait=args.wait)
    print(f"已启动 {result.exe}（PID {result.pid}，优先级 {result.priority}"
          f"{'，已生效' if result.priority_applied else '，未生效'}）")
    for note in result.notes:
        print(f"  ! {note}")
    return 0


def cmd_budget(args) -> int:
    worst = 0
    for design in args.designs:
        path = Path(design)
        if not path.is_file():
            print(f"跳过（文件不存在）：{path}")
            continue
        doc = budget.load_design(path)
        budgets = budget.analyze_design(doc)
        name = (doc.get("campaign") or {}).get("name") or path.stem
        print(f"== {name}（{path}）")
        print(budget.render(budgets))
        print()
        for b in budgets:
            worst = max(worst, {"ok": 0, "warn": 1, "heavy": 2}[b.verdict])
    return 1 if worst >= 2 else 0


def cmd_selftest(_args) -> int:
    from . import tests

    return tests.main()


def main(argv=None) -> int:
    # 输出被管道/重定向接走时，Python 会用系统 ANSI 码页编码，中文到 UTF-8 终端
    # 里就成了乱码。这里只在非交互场景强制 UTF-8，控制台输出交给 Python 原生处理。
    for stream in (sys.stdout, sys.stderr):
        try:
            if not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass

    args = build_parser().parse_args(argv)
    handlers = {
        "audit": cmd_audit,
        "apply": cmd_apply,
        "verify": cmd_verify,
        "status": cmd_status,
        "laa": cmd_laa,
        "restore": cmd_restore,
        "clean": cmd_clean,
        "seed": cmd_seed,
        "play": cmd_play,
        "budget": cmd_budget,
        "selftest": cmd_selftest,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
