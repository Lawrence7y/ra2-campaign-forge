"""命令行入口。

    python -m ra2re rtti <gamemd.exe> [--out out/reverse] [--no-vfuncs]

`rtti` 解析 MSVC RTTI，产出：
    out/reverse/symbols.json   类名 / 继承链 / vtable 地址 / 各虚函数地址
    out/reverse/hierarchy.txt  继承树（人看）

只读原版二进制，不修改任何文件。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, rtti

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# M1（渲染接管）与 M2（oracle）最关心的一批类：
# 渲染层（blit 接管点）+ 模拟主干（继承链验证 + 后续对拍目标）
FOCUS_CLASSES = (
    "Blitter", "BSurface", "BitFont", "BitText", "BinkMovieHandle",
    "AbstractClass", "ObjectClass", "MissionClass", "RadioClass",
    "TechnoClass", "FootClass", "UnitClass", "InfantryClass",
    "AircraftClass", "BuildingClass", "AnimClass", "BulletClass",
    "HouseClass", "CellClass", "MapClass", "TeamClass", "TeamTypeClass",
)

DEFAULT_GAME_EXES = ("ra2youli/gamemd.exe", "gamemd.exe")


def default_exe() -> Path | None:
    for cand in DEFAULT_GAME_EXES:
        p = PROJECT_ROOT / cand
        if p.is_file():
            return p
    return None


def cmd_rtti(args) -> int:
    exe = Path(args.exe) if args.exe else default_exe()
    if exe is None or not Path(exe).is_file():
        print("找不到 gamemd.exe，请用 <路径> 指定", file=sys.stderr)
        return 2

    print(f"== ra2re rtti　{exe}")
    img = rtti.Image.load(exe)
    print(f"镜像基址 {img.image_base:#x}，大小 {len(img.data) / 1048576:.2f} MB")
    print(f"代码段指纹 {rtti.pe.text_section_sha256(exe)}")
    print()

    result = rtti.dump(img, args.out, with_vfuncs=not args.no_vfuncs)
    diag = result["diagnostics"]

    print("— 头部宽度自洽性检验（选中的那个是自洽的）—")
    for k, v in sorted(diag["header_hypotheses"].items(), key=lambda x: int(x[0])):
        mark = " ←选中" if int(k) == diag["header_delta"] else ""
        print(f"  头部 = {k:>2} 字节: 有效描述符 {v['valid']:>4}，"
              f"共享 type_info vtable 占比 {v.get('top_share', 0):.1%}"
              f"（{v.get('distinct', 0)} 个不同值）{mark}")
    print()

    print("— 解析统计 —")
    print(f"  装饰名 {diag['raw_names']} 个 → 类描述符 {diag['classes']} 个")
    print(f"  拿到 CompleteObjectLocator: {diag['with_col']}")
    print(f"  拿到 vtable 地址:           {diag['with_vtable']}")
    print(f"  拿到完整基类链（>1 层）:    {diag['with_bases']}")
    print()

    print("— 重点类：vtable 地址与继承链（M1 的接管点就在这张表里）—")
    print(rtti.render_focus_table(result["classes"], FOCUS_CLASSES))
    print()

    print("— 类名片（重点类的细节）—")
    for name in ("Blitter", "BSurface", "TechnoClass", "FootClass"):
        print(rtti.render_class_card(result["classes"], name))
        print()

    print(f"产出：{result['out_dir']}\\symbols.json　{result['out_dir']}\\hierarchy.txt")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ra2re",
                                description="RA2/尤复 底层现代化的逆向工具集（只读原版二进制）")
    p.add_argument("--version", action="version", version=f"ra2re {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("rtti", help="解析 MSVC RTTI → 继承图 + vtable 地址表")
    sp.add_argument("exe", nargs="?", help="gamemd.exe 路径（默认找项目内的 ra2youli/gamemd.exe）")
    sp.add_argument("--out", default=str(PROJECT_ROOT / "out" / "reverse"),
                    help="输出目录（默认 out/reverse）")
    sp.add_argument("--no-vfuncs", action="store_true",
                    help="symbols.json 里不写每个虚函数地址（文件更小）")

    sp = sub.add_parser("perf", help="采样剖析正在运行的原版游戏（只读 EIP，不改代码）")
    sp.add_argument("--process", default="gamemd.exe", help="目标进程名（默认 gamemd.exe）")
    sp.add_argument("--seconds", type=float, default=30.0, help="采样时长（秒）")
    sp.add_argument("--hz", type=float, default=500.0, help="采样频率（默认 500 Hz）")
    sp.add_argument("--scenario", default="", help="场景描述，写进报告")
    sp.add_argument("--out", default=str(PROJECT_ROOT / "out" / "reverse"),
                    help="输出目录（默认 out/reverse）")

    sp = sub.add_parser("selftest", help="RTTI 解析器自检（需要原版 gamemd.exe）")
    sp.add_argument("exe", nargs="?", help="gamemd.exe 路径")

    sp = sub.add_parser("loadbench", help="生成预置 N 单位的遭遇战基准图（.yrm）")
    sp.add_argument("units", nargs="*", type=int, default=[50, 100, 200, 400],
                    help="每档双方合计单位数（默认 50 100 200 400）")
    sp.add_argument("--size", type=int, default=100, help="地图边长（偶数）")
    sp.add_argument("--dest", default="", help="输出目录（默认游戏目录）")
    sp.add_argument("--out", default="", help="只写到该目录，不装进游戏")

    sp = sub.add_parser("loadrun", help="跑重载基准：开局 → 采样 → 汇总")
    sp.add_argument("units", nargs="*", type=int, default=[50, 200, 400])
    sp.add_argument("--seconds", type=float, default=45.0)
    sp.add_argument("--skip-nav", action="store_true", help="不自动点菜单")
    sp.add_argument("--summarize-only", action="store_true")
    return p


def cmd_perf(args) -> int:
    from . import perf

    out_dir = Path(args.out)
    symbols = out_dir / "symbols.json"
    blit = out_dir / "m1_blit_targets.txt"
    if not symbols.is_file():
        print(f"缺少 {symbols}，先跑 `python -m ra2re rtti`", file=sys.stderr)
        return 2

    print(f"== ra2re perf　目标 {args.process}　{args.seconds:.0f}s @ {args.hz:.0f}Hz")
    try:
        res = perf.profile(args.process, seconds=args.seconds, hz=args.hz,
                           symbols_json=symbols, blit_file=blit)
    except RuntimeError as exc:
        print(f"采样失败：{exc}", file=sys.stderr)
        return 2

    files = perf.dump(res, out_dir, scenario=args.scenario)
    total = max(res.samples, 1)
    print(f"样本 {res.samples}（{res.hz:.0f} Hz）")
    print()
    print("按模块：")
    for mod, n in sorted(res.by_module.items(), key=lambda x: -x[1]):
        print(f"  {mod:<20} {100.0*n/total:>6.2f}%  {n}")
    print()
    print("按类别：")
    for kind, n in sorted(res.by_class.items(), key=lambda x: -x[1]):
        print(f"  {kind:<16} {100.0*n/total:>6.2f}%  {n}")
    if res.top_symbols:
        print()
        print("热点函数 Top 8：")
        for name, n in sorted(res.top_symbols.items(), key=lambda x: -x[1])[:8]:
            print(f"  {name:<44} {100.0*n/total:>6.2f}%")
    print()
    print(f"产出：{files['md']}")
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            if not stream.isatty():
                stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    if args.cmd == "selftest":
        from . import tests

        return tests.main(args.exe)
    if args.cmd == "loadbench":
        from . import loadbench

        return loadbench.main([
            *[str(u) for u in (args.units or [50, 100, 200, 400])],
            "--size", str(args.size),
            *(["--dest", args.dest] if args.dest else []),
            *(["--out", args.out] if args.out else []),
        ])
    if args.cmd == "loadrun":
        from . import loadrun

        argv = [*map(str, args.units or [50, 200, 400]),
                "--seconds", str(args.seconds)]
        if args.skip_nav:
            argv.append("--skip-nav")
        if args.summarize_only:
            argv.append("--summarize-only")
        return loadrun.main(argv)
    return {"rtti": cmd_rtti, "perf": cmd_perf}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
