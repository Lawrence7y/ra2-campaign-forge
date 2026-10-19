"""`ra2re` 自检：`python -m ra2re selftest`

RTTI 解析器的正确性不能只看"跑通了"，这里用三类**独立**判据验证：

1. **布局自洽性**：头部 8 字节的假设必须让 100% 的 TypeDescriptor 共享同一个
   `type_info` vftable（12/16 字节的假设做不到）。
2. **MSVC 语义约束**：任何 C++ 程序里，派生类的 vtable 都**不小于**其基类的 vtable
   （继承链上的槽位是累加的）。这条性质与 RA2 无关，是解析器正确性的硬约束。
   同时对已知的类层次做断言（`UnitClass → FootClass → TechnoClass → RadioClass →
   MissionClass → ObjectClass → AbstractClass`，这是 TS/RA2 引擎的公开知识）。
3. **确定性**：同样的输入解析两次，vtable 地址必须完全一致。

注意：需要 `ra2youli/gamemd.exe` 在场（未修改的原版二进制）。
"""

from __future__ import annotations

import sys

from . import rtti

PASSED: list = []
FAILED: list = []


def check(name, fn):
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - 自检要把失败原因打全
        FAILED.append((name, f"{type(exc).__name__}: {exc}"))
        print(f"  FAIL  {name}\n        {type(exc).__name__}: {exc}")
    else:
        PASSED.append(name)
        print(f"  ok    {name}")


# 公开知识：TS/RA2 引擎的类层次。解析结果必须与之一致。
EXPECTED_CHAINS = {
    "UnitClass": ["FootClass", "TechnoClass", "RadioClass", "MissionClass",
                  "ObjectClass", "AbstractClass"],
    "InfantryClass": ["FootClass", "TechnoClass", "RadioClass", "MissionClass",
                      "ObjectClass", "AbstractClass"],
    "AircraftClass": ["FootClass", "TechnoClass", "RadioClass", "MissionClass",
                      "ObjectClass", "AbstractClass"],
    "BuildingClass": ["TechnoClass", "RadioClass", "MissionClass",
                      "ObjectClass", "AbstractClass"],
    "AnimClass": ["ObjectClass", "AbstractClass"],
    "BulletClass": ["ObjectClass", "AbstractClass"],
    "TeamTypeClass": ["AbstractTypeClass", "AbstractClass"],
    "MissionClass": ["ObjectClass", "AbstractClass"],
}


def main(exe=None) -> int:
    print("ra2re 自检（RTTI 解析器）")
    if exe is None:
        from .cli import default_exe
        exe = default_exe()
    if exe is None:
        print("找不到 gamemd.exe，跳过（用 `python -m ra2re selftest <exe>` 指定）")
        return 2
    print(f"输入：{exe}\n")

    img = rtti.Image.load(exe)
    result = rtti.parse(img)
    classes = result["classes"]
    diag = result["diagnostics"]
    by_name = {c.name: c for c in classes.values()}

    print("[1] 布局自洽性")
    check("头部宽度选中 8 字节", lambda: (
        _assert(diag["header_delta"] == 8, f"选中了 {diag['header_delta']}")))
    check("988 个描述符全部共享同一个 type_info vftable", lambda: (
        _assert(diag["header_hypotheses"]["8"]["top_share"] == 1.0,
                f"占比 {diag['header_hypotheses']['8']['top_share']}")))
    check("12/16 字节假设应当不自洽（反证）", lambda: (
        _assert(diag["header_hypotheses"]["12"]["top_share"] < 0.9
                and diag["header_hypotheses"]["16"]["top_share"] < 0.9,
                "对照假设也自洽 → 判据无效")))

    print("\n[2] 规模")
    check("类描述符 ≥ 900", lambda: _assert(diag["classes"] >= 900, diag["classes"]))
    check("拿到 vtable 的类 ≥ 900", lambda: _assert(diag["with_vtable"] >= 900,
                                                  diag["with_vtable"]))
    check("拿到完整继承链的类 ≥ 600", lambda: _assert(diag["with_bases"] >= 600,
                                                    diag["with_bases"]))

    print("\n[3] 已知类层次")
    for name, want in EXPECTED_CHAINS.items():
        def make(n=name, w=want):
            def fn():
                c = by_name.get(n)
                _assert(c is not None, f"{n} 未找到")
                got, _ = rtti.split_chain(c.base_names)
                _assert(got == w, f"{n} 链为 {got}，期望 {w}")
            return fn
        check(f"{name} 的继承链与公开知识一致", make())

    print("\n[4] MSVC 语义约束：派生类 vtable 不小于基类")
    def monotonic():
        bad = []
        for c in classes.values():
            if len(c.base_names) < 2:
                continue
            base = by_name.get(c.base_names[1])
            if base is None or not base.vtable_va or not c.vtable_va:
                continue
            if c.vfunc_count < base.vfunc_count:
                bad.append(f"{c.name}({c.vfunc_count}) < {base.name}({base.vfunc_count})")
        _assert(not bad, "; ".join(bad[:6]))
    check("所有父子对的 vtable 长度单调不减", monotonic)

    print("\n[5] M1 目标：软件 blit 实现族")
    def blitter():
        for base, min_kids in (("Blitter", 40), ("RLEBlitter", 35)):
            b = by_name.get(base)
            _assert(b is not None, f"{base} 未找到")
            _assert(b.vtable_va, f"{base} 未拿到 vtable")
            kids = rtti._subtree(classes, base)
            _assert(len(kids) >= min_kids,
                    f"{base} 子类只有 {len(kids)} 个，期望 ≥{min_kids}")
    def blit_tokens():
        # 两个族的模板名都要能解码
        for name, want_rle in (("?$BlitPlain@G", False),
                               ("?$BlitTransXlat@E", False),
                               ("?$RLEBlitTransXlat@G", True),
                               ("?$RLEBlitTransDarkenZRead@G", True)):
            c = by_name.get(name)
            _assert(c is not None, f"{name} 未找到")
            tmpl, depth, toks = rtti.decode_blit_name(name)
            _assert(bool(depth), f"{name} 位深未解码")
            _assert(not any("Blit" in t for t in toks), f"{name} 语义未解码: {toks}")
            if want_rle:
                _assert("RLE 压缩路径" in toks, f"{name} 未标记 RLE: {toks}")
    def both_families_present():
        """RLE 族派生自另一个抽象基类 RLEBlitter——只认 Blitter 会漏掉一半实现。
        这条断言就是那次漏检的回归测试。"""
        txt = rtti.render_blit_targets(classes)
        _assert("RLEBlitter" in txt, "清单里没有 RLEBlitter")
        n = sum(1 for line in txt.splitlines()
                if line and not line.startswith("#") and "\t" in line)
        _assert(n >= 100, f"清单只有 {n} 条实现，期望 ≥100（57 + 51）")
    def surface():
        s = by_name.get("BSurface")
        _assert(s is not None and s.vtable_va, "BSurface 未拿到 vtable")
        chain, _ = rtti.split_chain(s.base_names)
        _assert(chain == ["XSurface", "Surface"], f"BSurface 链为 {chain}")
    check("Blitter 族 ≥40 个实现", blitter)
    check("RLE/普通两族的模板名都能解码", blit_tokens)
    check("M1 清单覆盖两个族（≥100 条）", both_families_present)
    check("BSurface → XSurface → Surface", surface)

    print("\n[6] 确定性")
    def deterministic():
        again = rtti.parse(rtti.Image.load(exe))["classes"]
        a = {c.name: (c.vtable_va, c.vfunc_count) for c in classes.values()}
        b = {c.name: (c.vtable_va, c.vfunc_count) for c in again.values()}
        _assert(a == b, "两次解析结果不一致")
    check("两次解析完全一致", deterministic)

    print()
    total = len(PASSED) + len(FAILED)
    if FAILED:
        print(f"失败 {len(FAILED)} / {total}")
        for name, err in FAILED:
            print(f"  - {name}: {err}")
        return 1
    print(f"全部通过：{total} 项")
    return 0


def _assert(cond, detail=""):
    if not cond:
        raise AssertionError(detail or "断言失败")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
