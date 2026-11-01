#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§422 键契约审计：判档器的每个**读取键**必须落在 harness7 的**写入点**上。

★ 起源：§421 刚立纪律「合成样本按『真机会写吗』造」，当场就兑现——
  审计发现 `h7_fs_rect_wait_skipped` 有**两个写入点**：
    `:7373` META= True   （fullscreen 且未 opt-out）
    `:7378` META= False  （fullscreen 且 --h7-keep-rect-wait）
    `:8087` FRAME=dict   （**外层 if fs_rect_wait_skipped ⇒ 只有短路臂写**）
  而判档器 `:155` **只读 FRAME** ⇒ 真机 keep 臂（只有 META=False）会判型
  成「未跑到矩形等待」⇒ 对照臂判据**永远不执行**。
  我的合成样本按「读取方」（FRAME dict）造，把缺陷完整掩盖——
  这正是「对账器复用被测物逻辑 ⇒ 两边同绿」的老坑（记忆
  exclusion-rule-and-selfcheck-blindness）。

★ 本件的做法：**两侧都从源码 AST 取证，不做任何硬编码**。
  - 写入侧：解析 harness7，收集所有 `rec.add(group, key, value, ...)` 的
    (group, key) 字面量，及其**所在 if 条件**的源码文本。
  - 读取侧：解析判档器，收集所有 `rec_get(recs, group, key)` 的
    (group, key) 字面量。
  - 契约判据：
    W1  读取的每个 (group,key) 必须**在场于写入集**（否则永远 None ⇒ 假判读）
    W2  读取键的**可达性**：写它的 if 链必须允许三臂各自到达
        （判据 = 「三臂路径逐条走 if 条件」的符号推演，用 AST 条件文本）
    W3  阳性对照：契约必须**报出**当前缺陷（keep 臂经 FRAME-only 读不可达），
        否则 W2 是恒真式。
★ 只读源码，不跑游戏、不写产物。
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
H7 = ROOT / "lead" / "goal1_harness7_20261023" / "qc151_trip.harness7.py"
JUDGE = ROOT / "lead" / "qc161_u0400_trip" / "_judge_l1_20261023.py"

RESULTS = []


def rec(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print("  %s %s%s" % ("✓" if ok else "✗", name,
                         ("  | " + detail) if detail else ""))


def dump_if_chain(tree, target_node):
    """从 tree 出发找 target_node 的祖先 If 链，**区分 body/orelse 分支**。

    ★ 首版把所有祖先 If 都当「条件须为真」——漏了 else 分支语义
      （`:7378` 在 `if not keep_flag:` 的 **else** 里 ⇒ keep 臂条件为**假**才进）。
      这是「审计器自己错」被 W4 抓出后修的。
    """
    def walk(node, anc):
        children = list(ast.iter_child_nodes(node))
        for c in children:
            if c is target_node:
                return anc
            r = walk(c, anc + ([(c, False)] if isinstance(c, ast.If) else []))
            if r is not None:
                return r
        return None
    found = walk(tree, [])
    chain = []
    if found:
        for node, neg in found:
            chain.append((ast.unparse(node.test), neg))
        # 修正：上面把祖先 If 以 (self, False) 追加，这里重算分支归属
    return chain


def branch_chain_for(target, tree):
    """重新精确收集：每个祖先 If + target 走的是 body(False) 还是 orelse(True)。"""
    def walk(node, anc):
        if node is target:
            return anc
        if isinstance(node, ast.If):
            for c in node.body:
                r = walk(c, anc + [(node, False)])
                if r is not None:
                    return r
            for c in node.orelse:
                r = walk(c, anc + [(node, True)])
                if r is not None:
                    return r
        for c in ast.iter_child_nodes(node):
            if c is node:
                continue
            r = walk(c, anc)
            if r is not None:
                return r
        return None
    res = walk(tree, [])
    if res is None:
        return []
    return [(ast.unparse(n.test), neg) for n, neg in res]


def _is_rec_add(n):
    """`rec.add(...)` 或 `self.rec.add(...)` 都算写入调用。

    ★ 首版只认 `Name(rec)`，漏了 Recorder 方法里的 `self.rec.add`
      （`stage_seconds:*` 正出自那里）⇒ W1 假阳性「无写入点」。
      审计器的取证不全由 **W1 自检**当场抓出——同族「否定断言要配阳性对照」。
    """
    f = n.func
    if not (isinstance(f, ast.Attribute) and f.attr == "add"):
        return False
    v = f.value
    if isinstance(v, ast.Name) and v.id == "rec":
        return True
    return (isinstance(v, ast.Attribute) and v.attr == "rec"
            and isinstance(v.value, ast.Name) and v.value.id == "self")


def collect_writes(tree):
    """rec.add(<GROUP>, <KEY>, ...) —— 字面量 **与 f-string** 都收。

    ★ 首版只收 Constant，漏掉 `f"stage_seconds:{name}"`（动态键），
      导致 `BUDGET.stage_seconds:frame` 被判「无写入点」= **审计器假阳性**。
      W1 当场抓出后补。教训：否定式断言（「读键 ⊄ 写键」）尤其怕写入侧取证不全。
    """
    sites = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and _is_rec_add(n):
                if len(n.args) >= 2:
                    g, k = n.args[0], n.args[1]
                    if not isinstance(g, ast.Constant):
                        continue
                    if isinstance(k, ast.Constant):
                        sites.append({"group": g.value, "key": k.value,
                                      "dynamic": False, "pattern": None,
                                      "lineno": n.lineno,
                                      "conds": branch_chain_for(n, tree)})
                    elif isinstance(k, ast.JoinedStr):
                        # f-string ⇒ 还原成正则：固定片段转义，{expr} 转 .*
                        pat = fkey_to_regex(k)
                        sites.append({"group": g.value, "key": None,
                                      "dynamic": True, "pattern": pat,
                                      "lineno": n.lineno,
                                      "conds": branch_chain_for(n, tree)})
    return sites


def fkey_to_regex(joined):
    import re
    parts = []
    for v in joined.values:
        if isinstance(v, ast.Constant):
            parts.append(re.escape(str(v.value)))
        else:
            parts.append(r".*")   # 任意插值
    return re.compile("^" + "".join(parts) + "$")


def key_written(site, group, key):
    """读取键 (group,key) 是否命中该写入站点（字面量或 f-string 模式）。"""
    if site["group"] != group:
        return False
    if site["dynamic"]:
        return bool(site["pattern"].match(key))
    return site["key"] == key


def collect_reads(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "rec_get":
            if len(n.args) >= 3:
                g, k = n.args[1], n.args[2]
                if isinstance(g, ast.Constant) and isinstance(k, ast.Constant):
                    out.append({"group": g.value, "key": k.value,
                                "lineno": n.lineno})
    return out


# 三臂各自的谓词真值表（按 harness7 源码事实）
_FS = {"short": True, "keep": True, "windowed": False}
_KEEPFLAG = {"short": False, "keep": True, "windowed": False}
_STATE_SKIP = {"short": True, "keep": False, "windowed": False}


def cond_val(text, arm):
    """整条 if 条件文本在三臂下的真值。未识别谓词 ⇒ 视为启动路径恒真。"""
    if "fs_rect_wait_skipped" in text:
        return _STATE_SKIP[arm]
    if "h7_keep_rect_wait" in text:
        return not _KEEPFLAG[arm]          # 文本自带 not getattr(...)
    if "fullscreen" in text:
        return _FS[arm]
    return True


def arm_reachable(site, arm):
    """站点在给定臂下可写入：祖先 If 链逐条求值，else 分支取反。"""
    for text, in_orelse in site["conds"]:
        v = cond_val(text, arm)
        if in_orelse:
            v = not v
        if not v:
            return False
    return True


def main() -> int:
    t7 = ast.parse(H7.read_text(encoding="utf-8"))
    tj = ast.parse(JUDGE.read_text(encoding="utf-8"))
    writes = collect_writes(t7)
    reads = collect_reads(tj)

    print("=" * 78)
    print("§422 键契约审计（写入侧=AST 取证 harness7；读取侧=AST 取证判档器）")
    print("=" * 78)
    dyn = [s for s in writes if s["dynamic"]]
    print("\n[0] 规模")
    print("  harness7 rec.add 写入站点: %d（其中 f-string 动态键 %d 个）"
          % (len(writes), len(dyn)))
    print("  判档器 rec_get 读取站点  : %d" % len(reads))

    print("\n[W1] 每个读取键必须出现在写入点集合（含 f-string 命中）")
    missing = []
    for r in reads:
        if not any(key_written(s, r["group"], r["key"]) for s in writes):
            missing.append("%s.%s@:%d" % (r["group"], r["key"], r["lineno"]))
    rec("读取键 ⊆ 写入键集合", not missing,
        "缺失=%s" % missing[:6] if missing else "全部命中")
    # ★ W1 自检：f-string 取证失效时 BUDGET.stage_seconds:frame 会重新落进
    #   missing ⇒ 本条把它单独钉住（缺陷修复自身的回归）。
    rec("W1 自检：动态 f-string 确实匹配 BUDGET.stage_seconds:frame",
        any(key_written(s, "BUDGET", "stage_seconds:frame") for s in writes))

    print("\n[W2] 读取键在**对照臂(keep)**的可达性")
    keep_unreach = []
    for r in reads:
        sites = [s for s in writes if key_written(s, r["group"], r["key"])]
        if sites and not any(arm_reachable(s, "keep") for s in sites):
            keep_unreach.append("%s.%s@:%d" % (r["group"], r["key"], r["lineno"]))
    print("  keep 臂不可达的读取键: %s" % (keep_unreach or "无"))

    print("\n[W3] 回归对照（§422 缺陷修好后，判据从「抓到」升级为「不再出现」）")
    # ★ 原判据「W2 必须报出 FRAME.h7_fs_rect_wait_skipped」是**缺陷现场**断言，
    #   修好后必然过时（读侧已改 META ⇒ FRAME 键不再是读取键）。
    #   升级成**回归控制**：判档器**不得**再读任何 keep 不可达键
    #   （MEASURE.h7_nav_to_measure 属**已申报的设计**——keep 臂 late 走缺席分支，
    #    判据 `late is not True` 语义为设计不变量，见台账 §421）。
    DECLARED_OK = {"MEASURE.h7_nav_to_measure"}   # 申报过的「只短路臂写」键
    regress = [x for x in keep_unreach
               if x.rsplit("@", 1)[0] not in DECLARED_OK]
    rec("判档器不再读 keep 不可达键（FRAME.skipped 已修，回归钉死）",
        not regress, str(regress[:3]))

    print("\n[W4] META 侧写入点（修复读取方后的依据）")
    meta_sk = [s for s in writes if s["key"] == "h7_fs_rect_wait_skipped"
               and s["group"] == "META"]
    rec("META.h7_fs_rect_wait_skipped 写入点 = %d（short/keep 各一）" % len(meta_sk),
        len(meta_sk) == 2, str([s["lineno"] for s in meta_sk]))
    both_arms = {arm for arm in ("short", "keep", "windowed")
                 if any(arm_reachable(s, arm) for s in meta_sk)}
    rec("META 写入点对 short+keep 两臂可达",
        {"short", "keep"} <= both_arms, str(sorted(both_arms)))

    print("\n" + "=" * 78)
    ok = sum(1 for _n, o, _d in RESULTS if o)
    print("  checks passed: %d/%d" % (ok, len(RESULTS)))
    bad = [n for n, o, _d in RESULTS if not o]
    if bad:
        print("  FAILED: %s" % bad)
    print("  RESULT: %s" % ("ALL PASS" if not bad else "FAIL"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
