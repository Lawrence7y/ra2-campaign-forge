#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_diff.py — 像素级对拍与视觉回归差分引擎（解决 Q5）。

核心功能：
1. 双图像素差分算法：
   - 比较基线帧图 (A) 与待测帧图 (B)。
   - 支持逐像素色彩容差参数化：max(|R_a - R_b|, |G_a - G_b|, |B_a - B_b|) > tol 判为有差异。
   - 允许对迷雾渐变、半透明 Alpha 混合的 16位色彩转换舍入抖动设置容差（默认 tol=8）。
2. 区域遮罩 (ROI Masking)：
   - 支持剔除动态非被测区域：
     * 侧边栏动态 UI（x >= 640, y >= 160）
     * 雷达/小地图扫描点（x >= 640, y < 160）
     * 顶部横幅文字（y <= 42）
     * 自定义屏蔽矩形列表 (x0, y0, x1, y1)
3. 差异热力图渲染：
   - 无差异区域：降饱和/半透明灰度底图显示，保留场景轮廓；
   - 差异区域：高亮荧光红/品红色强化标记，按差异幅度缩放 Alpha，直观展现错位/闪烁。
4. 定量判定标准：
   - 严格等价（如 EnableSIMD 向量化加速 Blit）：diff_pct 须为 0.000%，max_delta 须为 0。
   - 容差等价（如灰雾渐变/半透明渲染重构）：diff_pct <= 0.05%，max_delta <= 16。
5. 内置自检验证套件 (--selftest)：
   - 构造合成测试矩阵，验证同一图无差、容差吸纳、超差检出、区域遮罩剔除的确定性。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image
except ImportError:
    raise RuntimeError("bench_diff 依赖 Pillow 库，请先安装：pip install Pillow")

# 800x600 典型 UI 预置排除区域 (x0, y0, x1, y1)
DEFAULT_SIDEBAR_RECT = (640, 160, 800, 600)
DEFAULT_RADAR_RECT = (640, 0, 800, 160)
DEFAULT_BANNER_RECT = (0, 0, 800, 42)
# 遮罩矩形所属的基准坐标系（PROTOCOL §7 定死 800x600）
MASK_BASE = (800, 600)


def compute_image_diff(
    img_a_path: Path | str,
    img_b_path: Path | str,
    *,
    tol: int = 8,
    diff_pct_max: float = 0.05,
    max_delta_limit: int = 16,
    exclude_sidebar: bool = False,
    exclude_radar: bool = False,
    exclude_banner: bool = False,
    custom_excludes: list[tuple[int, int, int, int]] | None = None,
    out_diff_png: Path | str | None = None,
) -> dict[str, Any]:
    """比对两张图片，计算容差差异率与差异热力图。"""
    im_a = Image.open(img_a_path).convert("RGB")
    im_b = Image.open(img_b_path).convert("RGB")

    if im_a.size != im_b.size:
        raise ValueError(f"尺寸不匹配：A 为 {im_a.size}，B 为 {im_b.size}")

    w, h = im_a.size
    pix_a = im_a.load()
    pix_b = im_b.load()

    # 构建排除遮罩列表。遮罩矩形定义在 **800x600 UI 空间**（PROTOCOL §7），
    # 分辨率不同则等比缩放，并**记录实际使用的矩形**——否则"遮罩错位"会被误读成"通过"。
    sx, sy = w / MASK_BASE[0], h / MASK_BASE[1]

    def _scale(rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        x0, y0, x1, y1 = rect
        return (int(round(x0 * sx)), int(round(y0 * sy)),
                int(round(x1 * sx)), int(round(y1 * sy)))

    excludes: list[tuple[int, int, int, int]] = []
    if exclude_sidebar:
        excludes.append(_scale(DEFAULT_SIDEBAR_RECT))
    if exclude_radar:
        excludes.append(_scale(DEFAULT_RADAR_RECT))
    if exclude_banner:
        excludes.append(_scale(DEFAULT_BANNER_RECT))
    if custom_excludes:
        excludes.extend(custom_excludes)

    def is_excluded(x: int, y: int) -> bool:
        for rx0, ry0, rx1, ry1 in excludes:
            if rx0 <= x < rx1 and ry0 <= y < ry1:
                return True
        return False

    total_pixels = w * h
    masked_pixels = 0
    tested_pixels = 0
    diff_pixels = 0
    max_delta = 0
    sum_delta = 0

    diff_img = Image.new("RGB", (w, h), (0, 0, 0))
    diff_pix = diff_img.load()

    for y in range(h):
        for x in range(w):
            r_a, g_a, b_a = pix_a[x, y]
            r_b, g_b, b_b = pix_b[x, y]

            if is_excluded(x, y):
                masked_pixels += 1
                # 排除区域显示为深蓝暗色作为标记
                diff_pix[x, y] = (int(r_a * 0.2), int(g_a * 0.2), int(b_a * 0.4) + 20)
                continue

            tested_pixels += 1
            dr = abs(r_a - r_b)
            dg = abs(g_a - g_b)
            db = abs(b_a - b_b)
            delta = max(dr, dg, db)

            if delta > max_delta:
                max_delta = delta

            if delta > tol:
                diff_pixels += 1
                sum_delta += delta
                # 差异像素使用高亮荧光品红/红色着色，突出显示
                intensity = min(255, 128 + delta * 2)
                diff_pix[x, y] = (intensity, 0, min(255, 60 + delta * 3))
            else:
                # 符合容差的相同区域显示为 40% 亮度灰度，衬托差异
                gray = int(0.299 * r_a + 0.587 * g_a + 0.114 * b_a) * 0.4
                diff_pix[x, y] = (int(gray), int(gray), int(gray))

    diff_pct = (100.0 * diff_pixels / tested_pixels) if tested_pixels > 0 else 0.0
    mean_delta_on_diff = (sum_delta / diff_pixels) if diff_pixels > 0 else 0.0

    # 判定规则
    pass_diff_pct = diff_pct <= diff_pct_max
    pass_max_delta = (max_delta <= max_delta_limit) or (diff_pixels == 0)
    passed = pass_diff_pct and pass_max_delta

    if out_diff_png:
        out_p = Path(out_diff_png)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        diff_img.save(out_p)

    return {
        "image_a": str(Path(img_a_path).resolve()),
        "image_b": str(Path(img_b_path).resolve()),
        "resolution": [w, h],
        "tolerance": tol,
        "criteria": {
            "diff_pct_max": diff_pct_max,
            "max_delta_limit": max_delta_limit,
        },
        "mask_base": {"width": MASK_BASE[0], "height": MASK_BASE[1]},
        "mask_scale": [round(sx, 4), round(sy, 4)],
        "masks_applied": [{"rect": [int(v) for v in r]} for r in excludes],
        "stats": {
            "total_pixels": total_pixels,
            "masked_pixels": masked_pixels,
            "tested_pixels": tested_pixels,
            "diff_pixels": diff_pixels,
            "diff_pct": round(diff_pct, 4),
            "max_delta": max_delta,
            "mean_delta_on_diff": round(mean_delta_on_diff, 2),
        },
        "verdict": "PASS" if passed else "FAIL",
        "verdict_details": {
            "diff_pct_ok": pass_diff_pct,
            "max_delta_ok": pass_max_delta,
        },
        "diff_map_path": str(Path(out_diff_png).resolve()) if out_diff_png else None,
    }


def run_selftest() -> bool:
    """自检套件：自动构造合成测试图像并验证各项指标逻辑。"""
    print("=== bench_diff 自检套件开始 ===")
    tmp_dir = Path("out/re_work/bench_harness/test_diff")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    w, h = 200, 150
    base = Image.new("RGB", (w, h), (100, 120, 140))
    p_base = tmp_dir / "test_base.png"
    base.save(p_base)

    # 1. 相同图像对比：须 0% 差异，PASS
    res1 = compute_image_diff(p_base, p_base, tol=0, diff_pct_max=0.0)
    assert res1["stats"]["diff_pixels"] == 0, "测试 1 失败：同图出现差异"
    assert res1["verdict"] == "PASS", "测试 1 判定应为 PASS"
    print("  [PASS] 测试 1：相同图像 100% 字节精确匹配")

    # 2. 容差范围内的轻微噪点（delta=5, tol=8）：须判定为 0 差异
    im2 = base.copy()
    pix2 = im2.load()
    for y in range(20, 40):
        for x in range(20, 40):
            pix2[x, y] = (105, 125, 145)  # delta = 5
    p_tol = tmp_dir / "test_tol.png"
    im2.save(p_tol)
    res2 = compute_image_diff(p_base, p_tol, tol=8, diff_pct_max=0.0)
    assert res2["stats"]["diff_pixels"] == 0, "测试 2 失败：容差内噪点未被吸纳"
    assert res2["verdict"] == "PASS", "测试 2 判定应为 PASS"
    print("  [PASS] 测试 2：容差阈值 (delta=5 <= tol=8) 正常吸纳")

    # 3. 超出容差的实质差异（delta=30 > tol=8）：须精准检出 400 个像素
    im3 = base.copy()
    pix3 = im3.load()
    for y in range(20, 40):
        for x in range(20, 40):
            pix3[x, y] = (130, 150, 170)  # delta = 30
    p_diff = tmp_dir / "test_diff.png"
    p_out = tmp_dir / "test_diff_map.png"
    im3.save(p_diff)
    res3 = compute_image_diff(p_base, p_diff, tol=8, diff_pct_max=0.01, out_diff_png=p_out)
    assert res3["stats"]["diff_pixels"] == 400, f"测试 3 失败：期望检出 400 像素，实际 {res3['stats']['diff_pixels']}"
    assert res3["verdict"] == "FAIL", "测试 3 判定应为 FAIL"
    assert p_out.is_file(), "测试 3 差异热力图未落盘"
    print(f"  [PASS] 测试 3：超差异常检出成功 (400 像素, diff={res3['stats']['diff_pct']}%)，热力图已生成")

    # 4. 遮罩排除测试：将差异区域加入排除掩码，应忽略该差异并通过
    res4 = compute_image_diff(p_base, p_diff, tol=8, diff_pct_max=0.0,
                              custom_excludes=[(20, 20, 40, 40)])
    assert res4["stats"]["diff_pixels"] == 0, "测试 4 失败：遮罩区域未被排除"
    assert res4["stats"]["masked_pixels"] == 400, "测试 4 失败：遮罩像素数统计错误"
    assert res4["verdict"] == "PASS", "测试 4 判定应为 PASS"
    print("  [PASS] 测试 4：区域遮罩 (ROI Mask) 排除机制生效")

    print("=== bench_diff 4/4 项自检全部 PASS ===")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_diff", description="像素级对拍与视觉回归差分工具")
    ap.add_argument("image_a", nargs="?", help="基线参考截图 (A)")
    ap.add_argument("image_b", nargs="?", help="待验收新截图 (B)")
    ap.add_argument("--tol", type=int, default=8, help="逐像素通道最大容许色差 (0..255，默认 8)")
    ap.add_argument("--diff-pct-max", type=float, default=0.05, help="最大允许差异像素比例 (百分比，默认 0.05)")
    ap.add_argument("--max-delta-limit", type=int, default=16, help="单像素最大允许色差上限 (默认 16)")
    ap.add_argument("--exclude-sidebar", action="store_true", help="排除右侧 UI 建造栏区域 (x>=640, y>=160)")
    ap.add_argument("--exclude-radar", action="store_true", help="排除右上角雷达/小地图区域 (x>=640, y<160)")
    ap.add_argument("--exclude-banner", action="store_true", help="排除顶部标题横幅 (y<=42)")
    ap.add_argument("--out-diff", default=None, help="差异热力图输出 PNG 路径")
    ap.add_argument("--out-json", default=None, help="统计数据结果 JSON 路径")
    ap.add_argument("--selftest", action="store_true", help="运行内部算法自检套件")
    args = ap.parse_args(argv)

    if args.selftest or not (args.image_a and args.image_b):
        return 0 if run_selftest() else 1

    p_a = Path(args.image_a)
    p_b = Path(args.image_b)
    if not p_a.is_file() or not p_b.is_file():
        print(f"[FAIL] 输入图片不存在：A={p_a.is_file()}, B={p_b.is_file()}", file=sys.stderr)
        return 1

    res = compute_image_diff(
        p_a, p_b,
        tol=args.tol,
        diff_pct_max=args.diff_pct_max,
        max_delta_limit=args.max_delta_limit,
        exclude_sidebar=args.exclude_sidebar,
        exclude_radar=args.exclude_radar,
        exclude_banner=args.exclude_banner,
        out_diff_png=args.out_diff,
    )

    print(json.dumps(res, ensure_ascii=False, indent=2))
    if args.out_json:
        out_j = Path(args.out_json)
        out_j.parent.mkdir(parents=True, exist_ok=True)
        out_j.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] 差异报告已落盘: {out_j}")

    return 0 if res["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
