# -*- coding: utf-8 -*-
"""_re_linked.py — 同文档指纹-路径联查谓词 · J4 等价类判据并入版（R3-3e 候选）。

【并入来源与守约】
  本件 = lead/samedoc_link_20261109/_sl_link.py（SHA256
  a4ae4dc1d87d1ed052c4480883b207db9f70d6ca4868960e467bef17ed3cd7a5 / 12475 B，只读原件）
  的逐行拷贝 + 三处并入改动（其余行零改动）：
    (1) 模块级新增 DECL_RE —— J4 溯源声明词封闭集（★ 禁扩）；
    (2) link() 的 multi 分支尾部（原 :210 之后）并入 J4 判定块；
    (3) link_triple() 为 merged 新增 tier=SAMEDOC_LINK_EQ 映射与 merged rec 字段。
  unique / zero / invalid_hex 三分支与未触发 J4 的 multi 分支：执行路径与原实现完全一致
  （J4 块只在 multi 分支内运行，未触发时对 out 零改动）。
  逐条回归证明 = lead/r33e_merge_20261109/_re_run10_out.json（F2-d 十条真实无路径绑定行，
  原实现 vs 并入版输出 JSON 逐条全等）；结构证明 = 同件 diff_hunks（difflib 差异面白名单核验）。

【J4 三条件（须同时满足才改判 merged；lead/equiv_class_20261109/_eq_criteria.md §5.1）】
  (i)   行 L 命中溯源声明词封闭集 DECL_RE（复制自｜复制为｜COPY_IDENTICAL\\s*=\\s*True）；
  (ii)  ≥2 个 multi 成员的锚定 token 行号集合含 L（行号取自 anchors 记录，每 token 至多
        前 4 行，与原实现 rec["tokens"] 的 lines[:4] 同限）；
  (iii) 各命中行覆盖成员的并集 == 全体 multi 成员（全或无，不部分合并）。
  任一不满足 → 维持 multi 原样（放弃采集）。unique/zero/invalid_hex 一律不介入
  （unique 不因等价类降级为 multi，zero 无类可并）。声明词组刻意不含「逐字节同一/相同」
  等纯等同词——Q4_RELATION.md:85/:168 真实反例：纯等同词会把「不同趟次证据件恰好同哈希」
  的发现性表述误当复制声明（_eq_proto.py:16-17 / _eq_criteria.md §4）。

【merged 三纪律（三条全部落地，缺一不可）】
  1. path=None 不做单一对象主张：link_triple 的 merged rec 恒不写 path / verified_path /
     recomputed / bytes 等单对象字段（rec["path"] 保持 None）；link() 输出的 out["reverify"]
     恒为 None。merged 是「副本群」形态，不指向任何单一对象。
  2. 禁止从 merged 推导授权结论：merged 只表明「同文档内存在声明背书的逐字节同值副本群」，
     不构成对任一成员的锚定、放行或授权（隔离副本集成通过 ≠ 母本可写，RULING_D25:26，
     _integ_INTEGRATION_REPORT.md:59 实读在案）。本纪律写于本 docstring、J4 块注释、
     link_triple 注释、merged warning 文本、lead/r33e_merge_20261109/_re_NOTES.md。
  3. members 全列：out["eq"]["members"] 与 rec["members"] 逐成员列
     {path: 现盘解析路径, sha: 64 位小写十六进制全量, bytes: 整数}，取全量 matches，
     不做 max_detail 截断。

【原能力（同 _sl_link.py，不变）】绑定行「被核对象 SHA256 = <64hex>，字节数 = n」行内无
显式路径时，现行四级采集（T1/T2/T2N/T3，_f2_r11plus.py:164-194）全部落空走 R3-3b；
本谓词补同文档联查（不做全仓反查）：在同一文档文本内找出全部带路径项，逐个现盘重算
sha256，与绑定行 hex 比对，严格三态：
  unique  恰好 1 个不同现盘文件 hash+字节数皆符 → 采为锚对象，回验 MATCH；
  multi   ≥2 个不同现盘文件同 hash → 放弃采集（J4 并入后：满足三条件改判 merged，
          否则维持 multi）；
  zero    无任何命中 → 保留原 R3-3b warning「绑定行缺显式路径，需人工锚定」。
★ 只在给定文档文本内取路径项（同文档），绝不全仓反查。
★ 一律 warning 级：任何分支都不产出 problem（problems 恒为空列表，merged 亦然）。
★ 路径解析顺序与原版谓词一致（lead/gate_fp7_20261108/_g7_predicates.py:195-200）：
  doc_dir → root → 原样；行号后缀（:18-19 / #L18）剥除语义同 _f2_r11plus.py:90-102。
零真机、零采样代码；只 import hashlib/os/re/sys/pathlib；不写盘（除调用方显式落输出）、
不联网、不碰进程。"""

import hashlib
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(r"D:\Project\ra2-campaign-forge")

# 绑定 hex：64 位十六进制（BIND_RE 捕获组同宽，_g7_predicates.py:152）
HEX64_RE = re.compile(r"^[0-9a-fA-F]{64}$")
# 反引号跨度（同 _g7_predicates.py:154 BIND_PATH_BACK 语义）
BACKTICK_RE = re.compile(r"`([^`\n]{1,200})`")
# 带分隔符的路径形 token（同 _f2_r11plus.py:83 PATHISH 语义）
PATHISH_RE = re.compile(
    r"(?:[A-Za-z0-9\u4e00-\u9fff_\-]+[/\\])+[A-Za-z0-9\u4e00-\u9fff_\-]+\.[A-Za-z0-9]{1,8}")
# 整段路径形：无空白/无引注符、以短扩展名结尾（覆盖纯文件名与点分段路径）
BARE_SPAN_RE = re.compile(
    r"^[^\s`|*<>\"'\u201c\u201d\u2018\u2019\u2026]{1,200}\.[A-Za-z0-9]{1,8}$")
# 行号后缀（同 _f2_r11plus.py:80 LN_SUFFIX 语义；盘符冒号后无数字不剥）
LN_SUFFIX_RE = re.compile(
    r"(?::|#)\s?L?\d+(?:\s*[-\u2013~]\s*(?::|#)?\s?L?\d+)*$")
BYTES_RE = re.compile(r"字节数\s*=\s*([\d,]+)")
_COMMA = re.compile(r",")

# ---- J4 并入改动 (1)：溯源声明词封闭集 --------------------------------------
# 并入自 lead/equiv_class_20261109/_eq_proto.py:47 eq_merge；★ 封闭集禁扩：
# 不含「逐字节同一/相同」等纯等同词（防把「不同趟次证据件恰好同哈希」的发现性
# 表述误当复制声明，Q4_RELATION.md 真实反例）；漏词只会漏闭合（安全方向）。
DECL_RE = re.compile(r"复制自|复制为|COPY_IDENTICAL\s*=\s*True")


def strip_line_suffixes(s):
    """返回候选变体 = [原串, 逐层剥行号后缀…]（原串恒在首位；至多剥 6 层）。"""
    cands = [s]
    cur = s
    for _ in range(6):
        m = LN_SUFFIX_RE.search(cur)
        if not m:
            break
        cur = cur[: m.start()].rstrip().rstrip("/\\")
        if not cur or cur in cands:
            break
        cands.append(cur)
    return cands


def _line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def iter_path_items(text):
    """同文档路径项采集。返回 [{token, origin, lines}]；同一 token 字符串合并行号。
    采集面 = 反引号跨度（整段裸路径形 / 剥行号后缀后裸路径形 / 跨度内带分隔符子串 /
    空白分词后的裸路径片段）+ 反引号之外的正文中带分隔符路径形子串。
    含省略号（… 或 ...）的片段一律跳过（省略路径不可解析，防误绑）。"""
    items = {}
    order = []

    def add(tok, line_no, origin):
        tok = tok.strip()
        if not tok or "\u2026" in tok or "..." in tok:
            return
        if tok not in items:
            items[tok] = {"token": tok, "origin": origin, "lines": []}
            order.append(tok)
        if line_no not in items[tok]["lines"]:
            items[tok]["lines"].append(line_no)

    pos = 0
    for m in BACKTICK_RE.finditer(text):
        span = m.group(1)
        ln = _line_of(text, m.start())
        # 1) 整段（或剥后缀变体）裸路径形
        bare_tok = None
        for v in strip_line_suffixes(span.strip()):
            if BARE_SPAN_RE.match(v):
                bare_tok = v
                break
        if bare_tok is not None:
            add(bare_tok, ln, "backtick")
        # 2) 跨度内带分隔符路径形子串（命令行等含空白跨度）
        for pm in PATHISH_RE.finditer(span):
            add(pm.group(0), ln, "backtick-pathish")
        # 3) 跨度按空白分词后的裸路径片段（`a.py b.py` 一并覆盖）
        if " " in span:
            for frag in span.split():
                for v in strip_line_suffixes(frag):
                    if BARE_SPAN_RE.match(v):
                        add(v, ln, "backtick-fragment")
                        break
        # 4) 上一反引号跨度与本跨度之间的正文
        gap = text[pos:m.start()]
        for pm in PATHISH_RE.finditer(gap):
            add(pm.group(0), _line_of(text, pos + pm.start()), "plain")
        pos = m.end()
    for pm in PATHISH_RE.finditer(text[pos:]):
        add(pm.group(0), _line_of(text, pos + pm.start()), "plain")
    return [items[t] for t in order]


def resolve(token, doc_dir, root):
    """变体逐个解析：doc_dir → root → 原样（原版顺序）。返回 (hit, used_variant, tried)。"""
    tried = []
    for v in strip_line_suffixes(token.strip()):
        p = Path(v)
        cands = []
        if not p.is_absolute():
            cands.append(Path(doc_dir) / p)
            if root is not None:
                cands.append(Path(root) / p)
        cands.append(p)
        for c in cands:
            tried.append(str(c))
            if c.is_file():
                return c, v, tried
    return None, token, tried


def link(text, doc_dir, binding_hex, bytes_decl=None, root=REPO_ROOT, max_detail=12):
    """同文档联查主入口。输入 = 一个文档全文 + 一条绑定行的 hex（+ 可选声明字节数）。
    返回 dict：verdict ∈ {unique, multi, merged, zero, invalid_hex}；warning 一律
    warning 级；problems 恒为 []（联查永不升级 problem）。
    merged = J4 并入的新形态：multi 且三条件全满足时的等价类判定（见模块 docstring
    三纪律；未满足时保持 multi 原样，输出与原实现逐字节一致）。"""
    out = {"scope": "same-document", "problems": [], "binding_hex": binding_hex,
           "bytes_decl": bytes_decl, "anchors": [], "reverify": None,
           "declared_but_mismatched": []}
    h = binding_hex.strip().lower() if isinstance(binding_hex, str) else ""
    if not HEX64_RE.match(binding_hex.strip() if isinstance(binding_hex, str) else ""):
        out["verdict"] = "invalid_hex"
        out["warning"] = ("同文档联查拒绝：输入不是 64 位十六进制绑定 hex（warning）")
        return out
    out["binding_hex"] = h
    items = iter_path_items(text)
    cache = {}          # normcase(abs) -> 文件级记录
    matches = []        # hash+bytes 皆符的不同现盘文件
    unresolved = []
    resolved_files = 0
    for it in items:
        hit, used, tried = resolve(it["token"], doc_dir, root)
        if hit is None:
            unresolved.append({"token": it["token"], "lines": it["lines"][:4]})
            continue
        key = os.path.normcase(os.path.abspath(str(hit)))
        if key not in cache:
            b = hit.read_bytes()
            cache[key] = {"key": key, "path": str(hit),
                          "sha": hashlib.sha256(b).hexdigest(), "size": len(b),
                          "tokens": []}
            resolved_files += 1
        rec = cache[key]
        rec["tokens"].append({"token": it["token"], "origin": it["origin"],
                              "lines": it["lines"][:4], "used_variant": used,
                              "tried": tried[:6]})
        ok_sha = rec["sha"] == h
        ok_len = True if bytes_decl is None else int(bytes_decl) == rec["size"]
        if ok_sha and ok_len and all(m["key"] != key for m in matches):
            matches.append(rec)

    # 粗粒度辅助信息：hex 在同文档与某路径项【同一行】声明、但该路径现盘不符
    # —— 只作提示（同行多声明的表格行仍可能跨对象误联，字段自带此告警），不影响三态判定。
    if True:
        hex_lines = [i + 1 for i, ln in enumerate(text.splitlines()) if h in ln.lower()]
        for rec in cache.values():
            if rec["sha"] == h:
                continue
            near = sorted({hl for t in rec["tokens"] for tl in t["lines"]
                           for hl in hex_lines if tl == hl})
            if near:
                out["declared_but_mismatched"].append(
                    {"path": rec["path"], "sha12": rec["sha"][:12],
                     "size": rec["size"], "hex_near_lines": near[:4]})

    out["stats"] = {"tokens_distinct": len(items),
                    "resolved_files": resolved_files,
                    "unresolved_tokens": len(unresolved),
                    "unresolved_samples": unresolved[:max_detail]}
    if len(matches) == 1:
        a = matches[0]
        out["verdict"] = "unique"
        out["anchors"] = [a]
        out["reverify"] = {"path": a["path"], "sha": a["sha"], "bytes": a["size"],
                           "ok_sha": True, "ok_len": True, "ok": True}
        out["warning"] = ("同文档联查命中（warning 级）：绑定行 hex 由同文档带路径项唯一锚定"
                          " → %s；回验：现盘重算 sha256=%s / %d B，与声明逐位一致 MATCH"
                          % (a["path"], a["sha"], a["size"]))
    elif len(matches) >= 2:
        out["verdict"] = "multi"
        out["anchors"] = matches[:max_detail]
        out["warning"] = ("同文档联查多命中，无法确定（放弃采集）：%s —— 同文档内存在 %d 个"
                          "现盘 hash 同值的不同文件，按「唯一命中才采」规则不采任何一者"
                          % ("；".join(m["path"] for m in matches[:max_detail]),
                             len(matches)))
        # ==== J4 并入改动 (2)：等价类判据块（仅 multi 介入） ====
        # 来源：lead/equiv_class_20261109/_eq_proto.py:50-92 eq_merge（判据文档
        # _eq_criteria.md §5.1）；以下块只在 multi 分支内运行，三条件任一不满足时
        # 对 out 零改动（保持 multi 原样，与原实现输出逐字节一致）。
        # 条件 (i)  行 L 命中封闭集 DECL_RE（禁扩，见模块 docstring）；
        # 条件 (ii) ≥2 个成员的锚定 token 行号含 L（行号取自 cache 记录的 tokens 行号，
        #           每 token 至多前 4 行，与原实现 lines[:4] 同限）；
        # 条件 (iii) 命中行覆盖成员的并集 == 全体成员（全或无，不部分合并）。
        # ★ merged 三纪律（落地）：path 恒 None——本块不写任何单对象主张字段，
        #   out["reverify"] 保持 None；merged 不构成任何授权结论（角色归属留人工）；
        #   members 用全量 matches 全列（不用 anchors[:max_detail] 截断）。
        _kset = {m["key"] for m in matches}
        _cov = {}
        for _m in matches:
            for _t in _m["tokens"]:
                for _ln in _t["lines"]:
                    _cov.setdefault(_ln, set()).add(_m["key"])
        _decl_hits = []
        for _i, _lntext in enumerate(text.splitlines()):
            if DECL_RE.search(_lntext):
                _ck = _cov.get(_i + 1, set())
                if len(_ck) >= 2:
                    _decl_hits.append({"line": _i + 1, "covers": sorted(_ck),
                                       "text": _lntext.strip()})
        if _decl_hits:
            _group = set()
            for _d in _decl_hits:
                _group |= set(_d["covers"])
            if _group == _kset:
                out["verdict"] = "merged"
                out["eq"] = {"rule": "J4 same-doc provenance-declared byte-identical copy class",
                             "decl_vocab": DECL_RE.pattern,
                             "decl_lines": [d["line"] for d in _decl_hits],
                             "decl_hits": _decl_hits,
                             "members": [{"path": m["path"], "sha": m["sha"],
                                          "bytes": m["size"]} for m in matches]}
                out["warning"] = (
                    "同文档联查多命中 → 等价类合并（warning 级）：同文档第 %s 行存在溯源声明"
                    "（复制自/复制为/COPY_IDENTICAL=True），全部 %d 个同 hash 现盘文件的锚定 token "
                    "在该(些)行同现，机器逐字节核实同值 → 合并为同一内容的声明背书副本群；"
                    "未做单一对象主张（path=None），角色归属留人工判定，"
                    "禁止由 merged 推导任何授权结论。成员：%s"
                    % (",".join(str(d["line"]) for d in _decl_hits), len(matches),
                       "；".join(m["path"] for m in matches)))
    else:
        out["verdict"] = "zero"
        extra = ""
        if out["declared_but_mismatched"]:
            d = out["declared_but_mismatched"][0]
            extra = ("；注意：同文档 %s 行近旁有对 %s 的同值 hash 声明但现盘不符"
                     "（%s…/%d B，疑历史锚或漂移）"
                     % (d["hex_near_lines"], d["path"], d["sha12"], d["size"]))
        out["warning"] = ("绑定行缺显式路径，需人工锚定（R11/R3-3b）——同文档联查零命中"
                          "（同文档带路径项现盘重算无一等于绑定 hex），保留原警告" + extra)
    return out


def link_triple(text, doc_dir, binding_hex, bytes_decl=None, root=REPO_ROOT):
    """与 r11_scan_plus 同契约的薄封装：返回 (problems, warnings, binding_rec)。
    problems 恒为 []——联查结论一律走 warnings（★ 不升级 problem）。
    merged（J4 新形态）：rec["tier"]="SAMEDOC_LINK_EQ"、rec["match"]=True（仅指声明 hex
    与全体成员现盘重算逐位一致）、rec["path"] 恒 None（纪律一：不做单一对象主张）、
    rec["members"] 全列（纪律三）；禁止由 merged 推导任何授权结论（纪律二）。"""
    r = link(text, doc_dir, binding_hex, bytes_decl, root)
    rec = {"declared": r.get("binding_hex"), "path": None, "match": None,
           "tier": ("SAMEDOC_LINK" if r["verdict"] in ("unique", "multi")
                    else "SAMEDOC_LINK_EQ" if r["verdict"] == "merged" else None),
           "samedoc_link": r}
    if r["verdict"] == "unique":
        rec["path"] = r["reverify"]["path"]
        rec["match"] = True
        rec["verified_path"] = r["reverify"]["path"]
        rec["recomputed"] = r["reverify"]["sha"]
        rec["bytes"] = r["reverify"]["bytes"]
    elif r["verdict"] == "merged":
        # ==== J4 并入改动 (3)：merged rec 形态 ====
        # ★ 三纪律落地：path 保持 None（不写 verified_path/recomputed/bytes 等
        #   单对象字段——merged 是副本群形态，不做单一对象主张）；match=True 仅指
        #   「声明 hex 与全体成员现盘重算逐位一致」，不指向任何单一对象；members
        #   全列（逐成员 path/sha/bytes，无截断）；禁止由 merged 推导任何授权结论。
        rec["tier"] = "SAMEDOC_LINK_EQ"
        rec["match"] = True
        rec["members"] = r["eq"]["members"]
        rec["decl_lines"] = r["eq"]["decl_lines"]
    return r["problems"], [r["warning"]] + (
        ["同文档联查辅助：%s" % d for d in r["declared_but_mismatched"]]), rec


def main(argv):
    if len(argv) < 3:
        print("usage: python -I -X utf8 _re_linked.py <doc_path> <hex64> [bytes_decl]")
        return 2
    doc = Path(argv[1])
    text = doc.read_text(encoding="utf-8")
    bd = int(_COMMA.sub("", argv[3])) if len(argv) > 3 else None
    import json
    r = link(text, doc.parent, argv[2], bd)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
