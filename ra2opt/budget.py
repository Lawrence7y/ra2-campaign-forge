"""战役单位预算检查：给"多单位卡顿"一个可量化的门槛。

RA2/YR 的卡顿本质是**单线程模拟 + 软件渲染**：场面上活着的物件（建筑/车辆/步兵，
再加上动画与弹道）越多，每帧要跑的逻辑与要 blit 的精灵就越多。引擎没有硬件加速的
精灵渲染，所以单位数量是最硬的变量。

所以"减少多单位卡顿"最有效的一招其实是**设计期就控制同屏物件总数**——这个模块
把那条经验线量出来，让 ra2forge 生成的战役在设计阶段就能看到自己有没有超标。

阈值来自社区经验（原版任务的平均规模远低于此），只做提示，不影响构建。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

# 每关物件总数（建筑+车辆+步兵）的经验门槛
BUDGET_OK = 300        # 以内：基本感觉不到掉速
BUDGET_WARN = 600      # 以内：后期大规模交战会明显掉速
                       # 超过：模拟速度会明显下降，建议拆分或用增援代替初始铺满

VERDICT_LABEL = {
    "ok": "轻松",
    "warn": "偏多",
    "heavy": "超载",
}


@dataclass
class MissionBudget:
    name: str
    title: str = ""
    structures: int = 0
    units: int = 0
    infantry: int = 0
    waypoints: int = 0
    reinforcements: int = 0
    objectives: int = 0
    size: tuple = (0, 0)

    @property
    def initial_objects(self) -> int:
        return self.structures + self.units + self.infantry

    @property
    def peak_objects(self) -> int:
        """峰值估算：初始物件 + 增援带来的单位。"""
        return self.initial_objects + self.reinforcements

    @property
    def verdict(self) -> str:
        peak = self.peak_objects
        if peak <= BUDGET_OK:
            return "ok"
        if peak <= BUDGET_WARN:
            return "warn"
        return "heavy"

    @property
    def cells(self) -> int:
        return self.size[0] * self.size[1]

    @property
    def density(self) -> float:
        """每千格物件数——衡量"拥挤度"，拥挤会放大寻路开销。"""
        return (self.peak_objects / self.cells * 1000) if self.cells else 0.0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "structures": self.structures,
            "units": self.units,
            "infantry": self.infantry,
            "initial_objects": self.initial_objects,
            "reinforcements": self.reinforcements,
            "peak_objects": self.peak_objects,
            "size": list(self.size),
            "cells": self.cells,
            "density_per_1k_cells": round(self.density, 2),
            "verdict": self.verdict,
            "verdict_label": VERDICT_LABEL[self.verdict],
        }


def _count(seq) -> int:
    return len(seq) if isinstance(seq, list) else 0


def _reinforcement_units(objectives) -> int:
    total = 0
    if not isinstance(objectives, list):
        return 0
    for obj in objectives:
        if not isinstance(obj, dict) or obj.get("type") != "reinforce":
            continue
        team = obj.get("team") or {}
        for unit in team.get("units") or []:
            if isinstance(unit, dict):
                total += int(unit.get("count") or 1)
    return total


def analyze_design(doc) -> list:
    """分析一份设计 JSON，返回每关的预算结果。"""
    missions = doc.get("missions") or []
    out = []
    for mission in missions:
        if not isinstance(mission, dict):
            continue
        size = mission.get("size") or [0, 0]
        try:
            size_pair = (int(size[0]), int(size[1]))
        except (TypeError, ValueError, IndexError):
            size_pair = (0, 0)
        out.append(MissionBudget(
            name=str(mission.get("name", "?")),
            title=str(mission.get("title", "")),
            structures=_count(mission.get("structures")),
            units=_count(mission.get("units")),
            infantry=_count(mission.get("infantry")),
            waypoints=len(mission.get("waypoints") or {}),
            reinforcements=_reinforcement_units(mission.get("objectives")),
            objectives=_count(mission.get("objectives")),
            size=size_pair,
        ))
    return out


def load_design(path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def render(budgets: list) -> str:
    if not budgets:
        return "没有可分析的关卡。"
    lines = [
        f"{'关卡':<10} {'标题':<16} {'建筑':>4} {'车辆':>4} {'步兵':>4} "
        f"{'增援':>4} {'峰值':>5} {'密度/千格':>10}  评级",
        "-" * 78,
    ]
    for b in budgets:
        title = b.title[:14] + "…" if len(b.title) > 15 else b.title
        lines.append(
            f"{b.name:<10} {title:<16} {b.structures:>4} {b.units:>4} {b.infantry:>4} "
            f"{b.reinforcements:>4} {b.peak_objects:>5} {b.density:>10.2f}  "
            f"{VERDICT_LABEL[b.verdict]}"
        )
    heavy = [b for b in budgets if b.verdict != "ok"]
    lines.append("")
    if heavy:
        lines.append("偏多/超载的关卡（多单位时模拟速度会下降）：")
        for b in heavy:
            lines.append(
                f"  - {b.name}（{b.title}）：峰值 {b.peak_objects} 个物件"
                f"（门槛 {BUDGET_OK} 轻松 / {BUDGET_WARN} 偏多）"
            )
        lines.append("")
        lines.append("建议：把「开局铺满」改成「开局少量 + 定时增援」（objectives 里的 "
                     "reinforce 事件），峰值不变但同屏压力会小很多；"
                     "或者把一张大地图拆成两关。")
    else:
        lines.append(f"所有关卡都在轻松区间（≤ {BUDGET_OK} 个物件）。")
    return "\n".join(lines)
