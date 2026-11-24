# -*- coding: utf-8 -*-
"""_mk_build_candidate.py — 在写域构造 ③ 接入候选副本（只读原件，绝不改原件）。

做法同 MERGED_MIN_SAFETY_PATCH.md §3：定义 BEFORE/AFTER 常量，对原件做一次
精确字符串替换，产出 _mk_r11plus_candidate.py；断言 BEFORE 在原件中恰好出现 1 次，
并对候选做 compile() 校验。候选只用于本会话的「改前改后」与投影复跑，
绝不覆盖 _f2_r11plus.py、绝不改 _f2_compare.py 或 _f2_compare_out.json。
"""
from pathlib import Path
import hashlib

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_contract_20261109"
SRC = REPO / "lead" / "r11_f2_fix_20261109" / "_f2_r11plus.py"
OUT = W / "_mk_r11plus_candidate.py"

raw = SRC.read_text(encoding="utf-8")
print("SRC sha256 =", hashlib.sha256(SRC.read_bytes()).hexdigest(), "bytes =", SRC.stat().st_size)

# ---- 改前片段 A：常量区（在 G7_BYTES_EXPECTED 之后插入 RE 的只读装载常量） ----
BEFORE_A = '''G7_SHA256_EXPECTED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES_EXPECTED = 11743

_g7_cache = None
'''
AFTER_A = '''G7_SHA256_EXPECTED = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
G7_BYTES_EXPECTED = 11743

# ---- R3-3e / J4 同文档联查模块（只读原件；指纹护栏同 load_g7 纪律） ----
RE_LINKED_PATH = REPO_ROOT / "lead" / "r33e_merge_20261109" / "_re_linked.py"
RE_SHA256_EXPECTED = "7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52"
RE_BYTES_EXPECTED = 19481

_g7_cache = None
_re_cache = None
'''

# ---- 改前片段 B：装载函数（在 load_g7() 之后插入 load_re()） ----
BEFORE_B = '''    spec.loader.exec_module(mod)
    _g7_cache = mod
    return _g7_cache


# ---- 剥行号后缀（F2-b）----------------------------------------------------'''
AFTER_B = '''    spec.loader.exec_module(mod)
    _g7_cache = mod
    return _g7_cache


def load_re():
    """只读加载 _re_linked.py link_triple；先验指纹，失配拒绝运行。结果缓存。"""
    global _re_cache
    if _re_cache is not None:
        return _re_cache
    raw = RE_LINKED_PATH.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != RE_SHA256_EXPECTED or len(raw) != RE_BYTES_EXPECTED:
        raise RuntimeError(
            "联查模块指纹失配：%s = %s/%d ≠ 声明 %s/%d —— 拒绝运行"
            % (RE_LINKED_PATH, sha, len(raw), RE_SHA256_EXPECTED, RE_BYTES_EXPECTED)
        )
    spec = importlib.util.spec_from_file_location("_re_linked_f2plus", RE_LINKED_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _re_cache = mod
    return _re_cache


# ---- 剥行号后缀（F2-b）----------------------------------------------------'''

# ---- 改前片段 C：接入点 :303-305（逐字） ----
BEFORE_C = '''            else:
                rec["tier"] = None
                warnings.append("绑定行缺显式路径，需人工锚定（R11/R3-3b）")
        bindings.append(rec)
'''
# ---- 改后片段 C：③ 合并契约 ----
AFTER_C = '''            else:
                # ===== R3-3e / J4 接入点：同文档指纹-路径联查 =====
                # 前置：T1/T2/T2N/T3 全部落空才到此（:298-302 的 elif 不进本分支）。
                # _re_linked.py 只读；load_re() 先验指纹，零真机、零采样代码。
                RE = load_re()
                lk_prob, lk_warn, lk_rec = RE.link_triple(
                    text, doc_dir, declared, bytes_decl, root)
                # 纪律：problems 恒为 []（联查一律 warning 级，不升级 problem）
                #       ⇒ 丢弃 lk_prob，只并 warnings；problems 原样不动。
                assert lk_prob == [], "同文档联查不得产 problem（纪律）"
                # warning 二选一须显式：zero ⇒ lk_warn 内含原 R3-3b 原文；
                # merged / unique / multi ⇒ 用联查自己的结论 warning 替换之。
                # 二者必居其一，绝不双丢。
                warnings.extend(lk_warn)
                # rec 合并：保留 declared/citation/tried/alt 等原有键，
                # ★ 不覆盖 rec["declared"]（link_triple 的 binding_hex 已 lower()，
                #   直接覆盖会破坏 _f2_compare.py:45-46 的 declared 序列断言）。
                rec["tier"] = lk_rec.get("tier")
                rec["match"] = lk_rec.get("match")
                rec["path"] = lk_rec.get("path")
                rec["samedoc_link"] = lk_rec.get("samedoc_link")
                if lk_rec.get("tier") == "SAMEDOC_LINK_EQ":
                    # merged：副本群，全列 members / decl_lines（纪律三）
                    rec["members"] = lk_rec["members"]
                    rec["decl_lines"] = lk_rec["decl_lines"]
                    # ★ 故意不写 verified_path / recomputed / bytes：
                    #   纪律一「不做单一对象主张」——merged 无单一锚对象，
                    #   match=True 仅指声明 hex 与全体成员重算逐位一致。
                elif lk_rec.get("tier") == "SAMEDOC_LINK" and \\
                        lk_rec.get("path") is not None:
                    # unique：单一对象回验成立，link_triple 已给单对象三键
                    rec["verified_path"] = lk_rec["verified_path"]
                    rec["recomputed"] = lk_rec["recomputed"]
                    rec["bytes"] = lk_rec["bytes"]
                # multi / zero / invalid_hex：path=None、match=None，
                #   不写任何单对象三键、不写 members/decl_lines。
        bindings.append(rec)
'''

for tag, before in [("A", BEFORE_A), ("B", BEFORE_B), ("C", BEFORE_C)]:
    n = raw.count(before)
    print("BEFORE_%s count in SRC = %d" % (tag, n))
    assert n == 1, "BEFORE_%s 非唯一命中，拒绝构造" % tag

cand = raw.replace(BEFORE_A, AFTER_A, 1).replace(BEFORE_B, AFTER_B, 1).replace(BEFORE_C, AFTER_C, 1)
compile(cand, str(OUT), "exec")
print("candidate compile = OK")
OUT.write_text(cand, encoding="utf-8")
print("candidate written:", OUT.name, "bytes =", OUT.stat().st_size,
      "sha256 =", hashlib.sha256(OUT.read_bytes()).hexdigest())
print("SRC 未被写:", hashlib.sha256(SRC.read_bytes()).hexdigest())
