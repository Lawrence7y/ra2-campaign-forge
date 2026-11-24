# -*- coding: utf-8 -*-
"""_nn_widenet.py — 第四/五步量化：宽泛捞候选的噪声（量与质）+ 变体类自动发现。
只读，纯内存，stdout。零真机/零采样代码。
"""
import os, re, sys
from collections import defaultdict, Counter
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
ROOT = r"D:/Project/ra2-campaign-forge/lead"
MAXD, EXT = 2, ".md"

def iter_files():
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        d = 0 if rel == "." else rel.count("/") + 1
        if d > MAXD: dn[:] = []; continue
        for f in sorted(fn):
            if f.lower().endswith(EXT):
                p = os.path.join(dp, f)
                if os.path.isfile(p):
                    r = os.path.relpath(p, ROOT).replace("\\", "/")
                    if r.startswith("needle_norm_20261109/"):
                        continue   # 排除本任务写域，冻结到编排方 631 件口径
                    yield p, r

def main():
    files = {}
    for p, rel in iter_files():
        b = open(p, "rb").read()
        if b"\x00" in b: continue
        files[rel] = b.decode("utf-8", "replace").splitlines()
    print("### 宽泛捞候选：量与质 / 变体自动发现")
    print("corpus lead/ depth<=2 *.md ; files=%d" % len(files))
    print("")

    # --- 三种候选口径 ---
    W1 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if "不可复现" in L}          # 最宽：单词
    W2 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if "只能判" in L}            # 次宽：锚词
    W3 = W1 & W2                                                                                     # 双锚共现
    W4 = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1)
          if re.search(r"只能判.{0,3}不可复现", L)}                                                 # 放宽间隙/引号
    # 六变体并集
    V = ["只能判「不可复现」","只能判『不可复现』","只能判“不可复现”",
         "只能判不可复现","只能判(不可复现)","只能判 不可复现"]
    U = {(r,i) for r,ls in files.items() for i,L in enumerate(ls,1) if any(v in L for v in V)}
    print("=== A. 四级宽泛候选的量 ===")
    for name, S in [("W1 含『不可复现』(单词)",W1),("W2 含『只能判』(锚词)",W2),
                    ("W3 W1∩W2 (双锚共现)",W3),("W4 正则 只能判.{0,3}不可复现",W4),
                    ("U  六变体精确并集(基线真值)",U)]:
        print("  %-34s lines=%3d files=%2d" % (name, len(S), len({r for r,_ in S})))
    print("  W3 == U ? %s (差 %d 行)" % (W3==U, len(W3^U)))
    print("  W4 == U ? %s (差 %d 行)" % (W4==U, len(W4^U)))
    print("  W1 - U  = %d 行 / %d 件  <-- 单词口径引入的额外候选" % (len(W1-U), len({r for r,_ in W1-U})))
    print("  W4 - U  = %d 行 / %d 件  <-- 正则口径相对六变体的新增" % (len(W4-U), len({r for r,_ in W4-U})))
    print("  -- W4-U 明细（新增候选是否真变体） --")
    for r,i in sorted(W4-U):
        print("     %s:%d %s" % (r,i,files[r][i-1].strip()[:170]))
    print("")

    print("=== B. W1-U 的『质』：99/108 行里到底在讲什么（主题抽样 + 极性信号） ===")
    noise = sorted(W1-U)
    # 分类：含 §604/空档/缺口 主题词；含引述/否定词；含代码/门禁主题
    cats = Counter()
    for r,i in noise:
        L = files[r][i-1]
        if re.search(r"§604|空档|空档差|缺口列|逐窗", L): cats["§604/空档主题"] += 1
        if re.search(r"不可复原|T55k|载体清单|门禁|APPROVE|守卫", L): cats["其他主题(门禁/载体/标识符)"] += 1
        if re.search(r"「|『|“|`", L): cats["含引号(引述候选)"] += 1
        if re.search(r"不再成立|已撤回|不成立|被推翻|REFUTED|不可复现（REFUTED）|未验", L): cats["含否定/更新信号"] += 1
        if "只能判" in L: cats["仍含锚词『只能判』"] += 1
    print("  W1-U 总行数 = %d" % len(noise))
    for k,v in cats.most_common():
        print("     %-28s %3d 行 (%.1f%%)" % (k,v,100.0*v/len(noise)))
    print("  -- W1-U 前 12 行（人工判『是否同一命题』的样本） --")
    for r,i in noise[:12]:
        print("     %s:%d %s" % (r,i,files[r][i-1].strip()[:165]))
    print("  -- W1-U 中含锚词但仍未进 U 的行（= 去引号/换标点真变体，非噪声） --")
    for r,i in noise:
        L = files[r][i-1]
        if "只能判" in L:
            print("     %s:%d %s" % (r,i,L.strip()[:165]))
    print("")

    print("=== C. 变体类自动发现（解决『漏了哪类自己不知道』的可执行做法） ===")
    # 从语料里枚举「只能判」与「不可复现」之间的分隔符/包裹符，得到实际存在的变体类
    sep = Counter()
    for r,ls in files.items():
        for i,L in enumerate(ls,1):
            for m in re.finditer(r"只能判(.{0,4}?)不可复现(.{0,2})", L):
                a,b = m.group(1), m.group(2)
                sep[(a,b)] += 1
    print("  从全语料自动枚举 (只能判 → 不可复现 之间的串, 紧随其后的串) = %d 类" % len(sep))
    for (a,b),c in sep.most_common():
        cps = " ".join("U+%04X" % ord(ch) for ch in a)
        cps2 = " ".join("U+%04X" % ord(ch) for ch in b)
        print("     pre=%-10r (%s) post=%-8r (%s) count=%d" % (a,cps or "-",b,cps2 or "-",c))
    print("  => 自动发现给出语料里真实存在的包裹形态；把它与自检 fixture 的类目做集合差，")
    print("     差集非空即 SELF_TEST = FAIL（不再是『漏了哪类自己不知道』）。")
    print("")

    print("=== D. 现行 6 项负控 vs 自动发现的类目覆盖 ===")
    # 现行 6 项：4x ASSERTION(直角引号) + 1x REFUTING_QUOTE(:22 弯引号) + 1x ASSERTION(:215)
    controls = {
      "angle_corner": [("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",123),
                       ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",25),
                       ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md",196),
                       ("ledger_bound_20261109/_lb_BOUND_VOLUME.md",129),
                       ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",215)],
      "curly_corner": [("s604_verdict_entry_20261109/_ve_DRAFT_S609.md",22)],
    }
    print("  现行负控 6 项覆盖类目 = %s" % sorted(controls))
    print("  自动发现类目数 = %d ；未覆盖类目 = %d" % (len(sep), max(0,len(sep)-len(controls))))
    print("  -- 每个未覆盖类目给一条真实锚点（可直接补成负控） --")
    seen = set()
    for (a,b),c in sep.most_common():
        key = (a,b)
        for r,ls in files.items():
            for i,L in enumerate(ls,1):
                if re.search(r"只能判" + re.escape(a) + r"不可复现" + re.escape(b), L):
                    if key not in seen:
                        seen.add(key)
                        print("     pre=%r post=%r -> %s:%d  %s" % (a,b,r,i,L.strip()[:120]))
                    break
            if key in seen: break
    print("")

    print("=== E. 双 needle 的掩盖效应（为何 6/6 PASS 仍不可信） ===")
    # 文档命令含第二 needle『不能定位当年错误步骤』；:22 含该串
    nd2 = "不能定位当年错误步骤"
    c22 = 0
    for r,ls in files.items():
        for i,L in enumerate(ls,1):
            if nd2 in L: c22 += 1
    print("  第二 needle %r 在语料命中 %d 行" % (nd2, c22))
    L22 = files["s604_verdict_entry_20261109/_ve_DRAFT_S609.md"][21]
    print("  :22 含第二 needle = %s ；含直角引号 needle = %s" %
          (nd2 in L22, "只能判「不可复现」" in L22))
    print("  => 文档命令下 :22 靠『另一条 needle』被捞回，SELF_TEST=PASS 6/6；")
    print("     这掩盖了『直角引号 needle 本身漏检弯引号』这一事实。单 needle 才暴露 FAIL。")
    print("  => 负控必须为每个 needle 单独跑，禁止用多 needle 联合跑替代。")

if __name__ == "__main__":
    main()
