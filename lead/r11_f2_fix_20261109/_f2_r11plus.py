# -*- coding: utf-8 -*-
"""_f2_r11plus.py — F2 覆盖缺口修补：R11 增强版路径采集 r11_scan_plus。

被核对象（原版谓词）：lead/gate_fp7_20261108/_g7_predicates.py 的 r11_scan
（_g7_predicates.py:151-224，SHA256 02c17e49…c51120 / 11743 B）。本模块零改动
原件，只读加载；加载前 hashlib 验指纹，失配拒绝运行（同 _g9_gate.py:40-52 纪律）。

F2 缺口（lead/gate_r9r12_20261109/GATE_R9R12_REGRESSION.md §4.5）：
  原版 r11_scan 只在「被核对象…SHA256 =」分隔段与命中点【之前】的同一行找反引号
  路径；30 件回归 19 条绑定行 18 条 path=null（现盘重算成功 0 次）；唯一采到的
  1 条（`_dB_anchor_recompute_out.txt:18-19`）因行号后缀 is_file 失败被判
  「不在盘」——§4.4 自认的新误报。

增强版在【不放松任何原版校验】前提下补采集与修复：
  T1  原版采集语义逐行保留：分隔段反引号路径 → 同一命中点前反引号路径（同原版
      代码路径与消息原文）；解析顺序 doc_dir → root → 原样 不变；raw 路径先试
      （raw 存在时行为与原版完全一致），raw 不存在再试剥行号后缀变体（F2-b）。
  T2  命中点【之后】同一行的反引号路径（尾括注，F2-a 主形态）。
  T2N 命中点之后同一行的「含 / 或 \\ 且带扩展名」的路径形明文（非反引号）。
  T3  相邻行（前一行/后一行）反引号路径；相邻行本身是绑定行则整行排除
      （防把别条绑定的对象误绑到本条——原版 docstring「限同一行，防止把上一行
      的无关路径误绑到本行绑定」同一防误绑精神，F2-c）。
  剥后缀：`:`/`#` + 可选 L + 行号(可含 -–~ 范围段) 结尾，循环剥至多 6 层；
    Windows 盘符冒号（`C:\\`）后无数字不剥；候选 = [原串, 剥一层, 剥二层…]
    逐一解析，原串优先（原串存在 ⇒ 行为同原版）。
  引文语境（要求 c）：绑定行命中点前 24 字符内（同行）出现 照录/原文照录/
    引文/转录/本轮实读/内嵌 JSON 传入 → 该绑定行的 FAIL 级问题降为警告；
    回验照跑、事实结果照记（降级 ≠ 跳过）。词表从严、只认显式标记，
    反例检验见 _f2_selftest.py。
证据强度分级（不放松、不凭空加 FAIL）：
  - T1/T2 是绑定行显式反引号锚：回验 MISMATCH → problem（R3-3a，与原版同级，
    任务书明示「应只在采到路径且 MISMATCH 时增加」）；T1 不在盘 → problem
    （R3-3c 消息原文）——原版既有语义原样保留。
  - T2N/T3 是弱证据（启发式明文/跨行歧义）：MISMATCH 或均不在盘 → 一律
    warning（消息含候选与实算值），绝不凭空 FAIL——原版对这些形态连采集都不做，
    本增强只增信息不减信息。
  - any-match-wins：候选按 T2→T2N→T3 逐个回验，首个 sha(+声明字节数) 全 MATCH
    者即验证成立，防多候选时误伤。
  - T1 不在盘时仍按引文语境要求尝试 T2→T2N 同行替代锚回验（记录 alt，不改判）。
返回 (problems, warnings, bindings) 契约与原版一致；bindings 每条在原三键
（declared/path/match）之上只增不改地追加 tier/citation/tried/alt 等字段。
零真机、零采样代码；只 import hashlib/importlib.util/re/pathlib。
"""

import hashlib
import importlib.util
import re
from pathlib import Path

REPO_ROOT = Path(r"D:\Project\ra2-campaign-forge")
G7_PREDICATES_PATH = REPO_ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
G7_SHA256_EXPECTED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES_EXPECTED = 11743

_g7_cache = None


def load_g7():
    """只读加载原版谓词模块；先验指纹，失配拒绝运行。结果缓存。"""
    global _g7_cache
    if _g7_cache is not None:
        return _g7_cache
    raw = G7_PREDICATES_PATH.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != G7_SHA256_EXPECTED or len(raw) != G7_BYTES_EXPECTED:
        raise RuntimeError(
            "谓词模块指纹失配：%s = %s/%d ≠ 声明 %s/%d —— 拒绝运行"
            % (G7_PREDICATES_PATH, sha, len(raw), G7_SHA256_EXPECTED, G7_BYTES_EXPECTED)
        )
    spec = importlib.util.spec_from_file_location("_g7_predicates_f2plus", G7_PREDICATES_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _g7_cache = mod
    return _g7_cache


# ---- 剥行号后缀（F2-b）----------------------------------------------------
# `:18-19`、`:L18`、`#L18`、`:L18-L19`、`:962/:963/:965`（循环剥）；
# 盘符冒号（C:\）后无数字 ⇒ 不匹配 ⇒ 不剥。
LN_SUFFIX = re.compile(r"(?::|#)\s?L?\d+(?:\s*[-\u2013~]\s*(?::|#)?\s?L?\d+)*$")

# ---- 非反引号路径形 token（T2N）：至少一层 / 或 \ 分隔 + 扩展名 ------------
PATHISH = re.compile(r"(?:[A-Za-z0-9\u4e00-\u9fff_\-]+[/\\])+[A-Za-z0-9\u4e00-\u9fff_\-]+\.[A-Za-z0-9]{1,8}")

# ---- 引文语境显式标记（从严词表；命中点前 CITE_WINDOW 字符内、同行） -------
CITE_MARKERS = ("原文照录", "照录", "引文", "转录", "本轮实读", "内嵌 JSON 传入")
CITE_WINDOW = 24


def strip_line_suffixes(path_str):
    """返回候选变体 = [原串, 逐层剥行号后缀…]（原串恒在首位；至多剥 6 层）。"""
    cands = [path_str]
    cur = path_str
    for _ in range(6):
        m = LN_SUFFIX.search(cur)
        if not m:
            break
        cur = cur[: m.start()].rstrip().rstrip("/\\")
        if not cur or cur in cands:
            break
        cands.append(cur)
    return cands


def _resolve_variants(variants, doc_dir, root):
    """对每个变体按 原版解析顺序（doc_dir → root → 原样）找在盘文件。
    返回 (hit, used_variant, tried)。raw 变体（首个）行为与原版完全一致。"""
    tried = []
    for v in variants:
        p = Path(v.strip())
        cand = []
        if not p.is_absolute():
            cand.append(doc_dir / p)
            if root is not None:
                cand.append(root / p)
        cand.append(p)
        for c in cand:
            tried.append(str(c))
            if c.is_file():
                return c, v, tried
    return None, variants[0], tried


def _verify_candidate(cand_str, declared, bytes_decl, doc_dir, root, recompute):
    """剥后缀 → 解析 → 现盘重算 → 与声明 sha(+字节数) 比对。返回事实结果 dict。"""
    variants = strip_line_suffixes(cand_str)
    hit, used, tried = _resolve_variants(variants, doc_dir, root)
    if hit is None:
        return {"resolved": False, "candidate": cand_str, "tried": tried}
    sha, size = recompute(hit)
    ok_sha = sha == declared.lower()
    ok_len = True if bytes_decl is None else (bytes_decl == size)
    return {"resolved": True, "candidate": cand_str, "used_variant": used,
            "path": str(hit), "sha": sha, "bytes": size,
            "ok_sha": ok_sha, "ok_len": ok_len, "ok": ok_sha and ok_len,
            "tried": tried}


def r11_scan_plus(text, doc_dir, root=None, recompute=None):
    """R11 增强版（F2 修补）：路径采集 T1(原版)+T2/T2N(尾括注)+T3(相邻行)
    + 剥行号后缀 + 引文语境降警告。契约同原版 r11_scan：
    返回 (problems, warnings, bindings)。"""
    g7 = load_g7()
    if recompute is None:
        def recompute(p):
            b = p.read_bytes()
            return hashlib.sha256(b).hexdigest(), len(b)
    doc_dir = Path(doc_dir)
    problems, warnings, bindings = [], [], []
    for m in g7.BIND_RE.finditer(text):
        declared = m.group(1)
        # —— 以下 行/tail/sep 计算与原版 r11_scan 逐行等同（_g7_predicates.py:178-183）——
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        tail = text[m.end():min(line_end, m.end() + 120)]
        sep = text[m.start() + 4:m.start() + m.group(0).find("SHA256")]
        bm = g7.BIND_BYTES_RE.search(tail)
        bytes_decl = int(g7._COMMA.sub("", bm.group(1))) if bm else None
        # —— 引文语境：命中点前 24 字符（同行）显式标记 ——
        cite_head = text[max(line_start, m.start() - CITE_WINDOW):m.start()]
        citation = any(mk in cite_head for mk in CITE_MARKERS)
        # ---- T1：原版采集（_g7_predicates.py:184-191 逐行等同） ----
        path = None
        sep_paths = g7.BIND_PATH_BACK.findall(sep)
        if sep_paths:
            path = sep_paths[-1]
        else:
            back_paths = g7.BIND_PATH_BACK.findall(text[line_start:m.start()])
            if back_paths:
                path = back_paths[-1]
        # ---- T2/T2N：命中点之后同行为（F2-a） ----
        tail_wide = text[m.end():line_end][:400]
        t2_spans = [sm.group(1) for sm in g7.BIND_PATH_BACK.finditer(tail_wide)]
        t2_ranges = [(sm.start(1), sm.end(1)) for sm in g7.BIND_PATH_BACK.finditer(tail_wide)]
        t2n_cands = []
        for pm in PATHISH.finditer(tail_wide):
            if any(ps <= pm.start() and pm.end() <= pe for ps, pe in t2_ranges):
                continue  # 已被 T2 反引号跨度覆盖
            t2n_cands.append(pm.group(0))
        # ---- T3：相邻行反引号（相邻行自身是绑定行则排除，F2-c） ----
        t3_cands = []
        adj_lines = []
        if line_start > 0:
            pe = line_start - 1
            adj_lines.append(text[text.rfind("\n", 0, pe) + 1:pe])
        if line_end < len(text):
            ns = line_end + 1
            ne = text.find("\n", ns)
            adj_lines.append(text[ns:len(text) if ne == -1 else ne])
        for a in adj_lines:
            if a and not g7.BIND_RE.search(a):
                t3_cands.extend(sm.group(1) for sm in g7.BIND_PATH_BACK.finditer(a))

        rec = {"declared": declared, "path": path, "match": None,
               "citation": citation}
        tried_all = []
        downgraded = "——引文语境降级为警告（R11+/F2-c）"

        if path:
            # ===== T1：原版语义（raw 先试；raw 不在再试剥后缀变体） =====
            rec["tier"] = "T1"
            variants = strip_line_suffixes(path)
            hit, used, tried = _resolve_variants(variants, doc_dir, root)
            rec["tried"] = tried
            rec["suffix_stripped"] = used.strip() != path.strip()
            if hit is None:
                rec["match"] = False
                msg = "引用锚指向不在盘对象 %s（R11/R3-3c）" % path
                # 仍要尝试回验（要求 c）：同行替代锚 T2→T2N
                alt = None
                for tier, cand in [("T2", s) for s in t2_spans] + [("T2N", c) for c in t2n_cands]:
                    r = _verify_candidate(cand, declared, bytes_decl, doc_dir, root, recompute)
                    tried_all.append(r)
                    if r["resolved"] and r["ok"]:
                        alt = dict(r)
                        alt["tier"] = tier
                        break
                rec["tried"] = tried_all
                rec["alt"] = alt
                if alt is not None:
                    rec["match"] = True  # 事实：声明 hash 已由同行替代锚回验成立
                if citation:
                    w = msg + downgraded
                    if alt is not None:
                        w += "；同行替代锚回验 MATCH：%s" % alt["path"]
                    warnings.append(w)
                else:
                    problems.append(msg)
            else:
                sha, size = recompute(hit)
                ok_sha = sha == declared.lower()
                ok_len = True
                if bytes_decl is not None:
                    ok_len = bytes_decl == size
                rec.update({"recomputed": sha, "bytes": size,
                            "verified_path": str(hit)})
                if not (ok_sha and ok_len):
                    rec["match"] = False
                    msg = ("引用锚失配 %s：现盘 %s/%d ≠ 声明（R11/R3-3a）"
                           % (path, sha[:12], size))
                    if citation:
                        warnings.append(msg + downgraded)
                    else:
                        problems.append(msg)
                else:
                    rec["match"] = True
        else:
            # ===== 无 T1：T2→T2N→T3 any-match-wins =====
            ordered = ([("T2", s) for s in t2_spans]
                       + [("T2N", c) for c in t2n_cands]
                       + [("T3", c) for c in t3_cands])
            first_resolved = {}
            verified = None
            for tier, cand in ordered:
                r = _verify_candidate(cand, declared, bytes_decl, doc_dir, root, recompute)
                tried_all.append(r)
                if r["resolved"]:
                    if tier not in first_resolved:
                        first_resolved[tier] = r
                    if r["ok"]:
                        verified = dict(r)
                        verified["tier"] = tier
                        break
            rec["tried"] = tried_all
            if verified is not None:
                rec.update({"match": True, "path": verified["candidate"],
                            "tier": verified["tier"],
                            "verified_path": verified["path"],
                            "recomputed": verified["sha"],
                            "bytes": verified["bytes"]})
            elif "T2" in first_resolved:
                # T2 显式反引号锚在盘但失配 → 与原版 T1 同级 problem（任务书明示允许）
                r = first_resolved["T2"]
                rec["match"] = False
                rec["tier"] = "T2"
                msg = ("引用锚失配 %s：现盘 %s/%d ≠ 声明（R11/R3-3a）"
                       % (r["candidate"], r["sha"][:12], r["bytes"]))
                if citation:
                    warnings.append(msg + downgraded)
                else:
                    problems.append(msg)
            elif "T2N" in first_resolved:
                r = first_resolved["T2N"]
                rec["match"] = False
                rec["tier"] = "T2N"
                warnings.append("同行明文路径候选失配 %s：现盘 %s/%d ≠ 声明"
                                "（R11+/F2 弱证据，仅警告）"
                                % (r["candidate"], r["sha"][:12], r["bytes"]))
            elif "T3" in first_resolved:
                r = first_resolved["T3"]
                rec["match"] = False
                rec["tier"] = "T3"
                warnings.append("相邻行路径候选失配 %s：现盘 %s/%d ≠ 声明"
                                "（R11+/F2 跨行弱证据，仅警告）"
                                % (r["candidate"], r["sha"][:12], r["bytes"]))
            elif t2_spans or t2n_cands or t3_cands:
                rec["match"] = False
                rec["tier"] = "T2/T2N/T3"
                warnings.append("采集到候选锚但均不在盘：%s（R11+/F2，仅警告）"
                                % ", ".join((t2_spans + t2n_cands + t3_cands)[:4]))
            else:
                rec["tier"] = None
                warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")
        bindings.append(rec)
    if not bindings:
        problems.append("缺 SHA256 绑定行（R11：被核对象…SHA256 = hex 全域无匹配，"
                        "已容忍 ≤160 字符路径隔断与可选反引号）")
    return problems, warnings, bindings
