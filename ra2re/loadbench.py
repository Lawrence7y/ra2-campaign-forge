"""重载基准图生成器：预置 N 个单位的遭遇战 .yrm，用来测「单位数 vs 忙时」。

为什么是遭遇战图而不是战役包：
- 装成游戏根目录下的 `.yrm` 会直接进遭遇战地图列表，**不动 expandmd98.mix**。
- 预置单位写在 [Units]/[Infantry]，开局即存在，不需要等 AI 暴兵。

设计：
- 两支对峙军队（Russians vs Americans），mission=Hunt，开局就交火，
  同时打到「单位绘制」与「弹道/动画」两条负载。
- 图例名以 `0` 开头（如 `0LoadBench_U200.yrm`），在地图列表里尽量排前，
  便于用 ScenIndex=0 定位。
"""

from __future__ import annotations

from pathlib import Path

from ra2forge.maplib import MissionMap

# 双方混合编队：覆盖车/步/重型单位，走不同 blit 路径
ARMY_VEHICLES = [
    ("MTNK", 3),   # 灰熊/犀牛 —— 主战，体积小数量多
    ("HTNK", 1),   # 天启 —— 大体积重绘
    ("TTNK", 1),   # 磁能
]
ARMY_INFANTRY = [
    ("E1", 3),
    ("GI", 2),
    ("FLAKT", 1),
]


def _compose_army(total: int) -> list[tuple[str, str]]:
    """把 total 拆成 (kind, type_id) 列表，kind ∈ {vehicle, infantry}。"""
    # 车:步 ≈ 3:2，保证两种绘制路径都有样本
    n_veh = max(1, (total * 3) // 5)
    n_inf = max(0, total - n_veh)
    out: list[tuple[str, str]] = []
    veh_cycle = [t for t, w in ARMY_VEHICLES for _ in range(w)]
    inf_cycle = [t for t, w in ARMY_INFANTRY for _ in range(w)]
    for i in range(n_veh):
        out.append(("vehicle", veh_cycle[i % len(veh_cycle)]))
    for i in range(n_inf):
        out.append(("infantry", inf_cycle[i % len(inf_cycle)]))
    return out


def _grid_positions(row0: int, row1: int, col0: int, col1: int, n: int):
    """在矩形内均匀撒 n 个 (row,col)，行列步长自适应。"""
    rows = max(1, row1 - row0 + 1)
    cols = max(1, col1 - col0 + 1)
    cells = [(r, c) for r in range(row0, row1 + 1) for c in range(col0, col1 + 1)]
    if n >= len(cells):
        # 不够放就重复用格子（引擎允许重叠生成，会自动挤开）
        return [cells[i % len(cells)] for i in range(n)]
    # 均匀抽样
    step = len(cells) / n
    return [cells[int(i * step)] for i in range(n)]


def build_loadbench_map(total_units: int, *, size: int = 100) -> MissionMap:
    """total_units 为双方合计（约各一半）。size 为正方形边长（偶数）。"""
    if total_units < 2:
        raise ValueError("total_units must be >= 2")
    if size % 2:
        size += 1
    name = f"[2] 0LoadBench U{total_units}"
    m = MissionMap(name, width=size, height=size, theater="TEMPERATE")

    # 多人遭遇战字段（对齐官方/社区 .yrm 的 [Basic]）
    m.basic.update({
        "GameMode": "standard",
        "MaxPlayer": 2,
        "MinPlayer": 2,
        "MultiplayerOnly": 1,
        "FreeRadar": "yes",          # 全图可见，便于观察与稳定测量
        "IgnoreGlobalAITriggers": "no",
    })

    # 两个起始航点（玩家位）
    half = size // 2
    m.add_waypoint(0, half, 4)
    m.add_waypoint(1, half, size - 5)

    # 双方军队：左 Russians / 右 Americans，中部对峙
    n_each = total_units // 2
    army = _compose_army(n_each)
    # 左军占 col 12..45，右军占 col 55..88（size=100 时）
    left = _grid_positions(half - 18, half + 18, 12, min(45, half - 8), len(army))
    right = _grid_positions(half - 18, half + 18, max(55, half + 8), size - 12, len(army))

    for (kind, type_id), (row, col) in zip(army, left):
        if kind == "vehicle":
            m.add_unit("Russians", type_id, row, col, mission="Hunt", facing=16)
        else:
            m.add_infantry("Russians", type_id, row, col, mission="Hunt", facing=16)
    for (kind, type_id), (row, col) in zip(army, right):
        if kind == "vehicle":
            m.add_unit("Americans", type_id, row, col, mission="Hunt", facing=80)
        else:
            m.add_infantry("Americans", type_id, row, col, mission="Hunt", facing=80)

    # 房屋：双方高 IQ 让预置部队主动交战；PlayerControl 保持 no（人机房由大厅分配）
    m.house_configs = [
        {"name": "Russians", "player": False, "techlevel": 10, "credits": 10000,
         "iq": 5, "edge": "West", "color": "DarkRed", "allies": "Russians"},
        {"name": "Americans", "player": False, "techlevel": 10, "credits": 10000,
         "iq": 5, "edge": "East", "color": "Blue", "allies": "Americans"},
    ]
    m.player_house = "Russians"
    return m


def _header_section(size: int) -> list[str]:
    """遭遇战列表/预览用的 [Header]（官方编辑器会写；没有它 lobby 可能显示异常）。"""
    # Waypoint 坐标是预览像素空间，给个落在预览内的近似值即可
    return [
        "[Header]",
        f"Width={size}",
        f"Height={size}",
        f"StartX={size * 2}",
        f"StartY={size // 2}",
        f"Waypoint1={size * 2 + 20},{size // 2 + 10}",
        f"Waypoint2={size * 2 + 40},{size // 2 + 20}",
        "Waypoint3=0,0",
        "Waypoint4=0,0",
        "Waypoint5=0,0",
        "Waypoint6=0,0",
        "Waypoint7=0,0",
        "Waypoint8=0,0",
        "NumberStartingPoints=2",
        "",
    ]


def patch_multiplayer_basic(map_text: str, *, size: int = 100) -> str:
    """把 MissionMap 输出的战役向 [Basic] 补成遭遇战可用的字段。"""
    lines = map_text.splitlines()
    out: list[str] = []
    in_basic = False
    seen = set()
    extras = {
        "GameMode": "standard",
        "MaxPlayer": "2",
        "MinPlayer": "2",
        "MultiplayerOnly": "1",
        "FreeRadar": "yes",
        "HomeCell": "0",
        "AltHomeCell": "0",
    }
    for line in lines:
        if line.startswith("["):
            if in_basic:
                for k, v in extras.items():
                    if k not in seen:
                        out.append(f"{k}={v}")
                in_basic = False
            if line.strip() == "[Basic]":
                in_basic = True
            out.append(line)
            continue
        if in_basic:
            key = line.split("=", 1)[0]
            if key in extras:
                out.append(f"{key}={extras[key]}")
                seen.add(key)
                continue
            if key == "IgnoreGlobalAITriggers":
                # 预置部队要主动交战，别忽略 AI
                out.append("IgnoreGlobalAITriggers=no")
                seen.add(key)
                continue
            if key in ("NextScenario", "AltNextScenario"):
                out.append(f"{key}=")
                seen.add(key)
                continue
        out.append(line)
    if in_basic:
        for k, v in extras.items():
            if k not in seen:
                out.append(f"{k}={v}")

    text = "\n".join(out) + "\n"
    # [Header] 挂在 [Preview] 之前（与官方 .yrm 一致）
    if "[Header]" not in text:
        head = "\n".join(_header_section(size))
        text = head + text
    return text


def write_loadbench(total_units: int, dest_dir: Path, *, size: int = 100) -> Path:
    m = build_loadbench_map(total_units, size=size)
    text = patch_multiplayer_basic(m.to_ini_text(), size=size)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    # 前缀 [2] 表示 2 人图；0 开头便于排序靠前
    path = dest_dir / f"[2]0LoadBench_U{total_units:04d}.yrm"
    # 必须 CRLF + GBK：Westwood INI 解析器对 LF-only 会丢掉 [Basic] Name，
    # 战役/遭遇战列表里就显示成「no name」。
    text_crlf = text.replace("\r\n", "\n").replace("\n", "\r\n")
    if not text_crlf.endswith("\r\n"):
        text_crlf += "\r\n"
    # 社区图都有 [Digest]；缺了列表可能异常
    if "[Digest]" not in text_crlf:
        import base64
        import hashlib
        body = text_crlf.encode("gbk", errors="replace")
        d = base64.b64encode(hashlib.sha1(body).digest()).decode("ascii")
        text_crlf += f"[Digest]\r\n1={d}\r\n"
    path.write_bytes(text_crlf.encode("gbk", errors="replace"))
    return path


def main(argv=None) -> int:
    import argparse
    import sys

    p = argparse.ArgumentParser(prog="ra2re loadbench",
                                description="生成预置 N 单位的遭遇战基准图（.yrm）")
    p.add_argument("units", nargs="*", type=int, default=[50, 100, 200, 400],
                   help="每档的双方合计单位数（默认 50 100 200 400）")
    p.add_argument("--size", type=int, default=100, help="地图边长（偶数，默认 100）")
    p.add_argument("--dest", default="",
                   help="输出目录（默认游戏目录 ra2youli）")
    p.add_argument("--out", default="",
                   help="若指定则只写到该目录（如 out/loadbench），不装进游戏")
    args = p.parse_args(argv)

    project = Path(__file__).resolve().parent.parent
    if args.out:
        dest = Path(args.out)
    elif args.dest:
        dest = Path(args.dest)
    else:
        dest = project / "ra2youli"

    print(f"== loadbench → {dest}")
    for n in args.units:
        path = write_loadbench(n, dest, size=args.size)
        raw = path.stat().st_size
        # 自检：字节可解、含 [Units]/[Infantry]、MultiplayerOnly=1
        t = path.read_bytes().decode("gbk", errors="replace")
        n_units = t.count("\n")  # rough
        ok_mp = "MultiplayerOnly=1" in t
        ok_u = "[Units]" in t and "[Infantry]" in t
        ok_wp = "[Waypoints]" in t
        print(f"  {path.name:28s}  {raw:7d} B  "
              f"MultiplayerOnly={'Y' if ok_mp else 'N'}  "
              f"units/inf={'Y' if ok_u else 'N'}  wp={'Y' if ok_wp else 'N'}")
        if not (ok_mp and ok_u and ok_wp):
            print("    ⚠ 自检未过", file=sys.stderr)
            return 1
    print("完成。游戏地图列表里找 0LoadBench_*（可能需重启游戏刷新列表）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
