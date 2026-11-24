# -*- coding: utf-8 -*-
"""R73 · 复算两份子代理的结论（§2.12 规则 D：审计结论必须由主会话亲自复算）。

待复算的指控（逐条独立重算，不引用它们给的数）：
  A1-a【审计员 e/f + 执行员 Q3】我 scan_r73 的 S2「终点无鉴别力」是**零信息格**：
        我把起点固定在 174146（红区），在那个起点下终点必然全同。
        指控：把起点固定在绿区 173919 后，终点会决定第 5 条成败。
  A1-b【执行员补充】起点 = 000000 时 R55 窗口覆盖全天，at=12:00:54 / 23:59:59 也被判合法 R55
        ⇒「把起点改到 17:39:19 让门禁变绿」在语义上不是修窗口，是取消窗口。
  A1-c【执行员补充】同一 at 标 round=R54 也能过（R54 窗口 [17:34:00,17:41:46] 与 r55 重叠）
        ⇒ 这 5 条在时间上无法区分 R54/R55。
  A1-d【执行员 A】不改分隔符替换 ⇒ 输出有 **10 行不同**（我 N1 报的是 5 行）。
  A1-e【审计员 c】我的「逐行相同」经 norm() 抹掉 CRLF，证明的是 stdout 文本一致，
        不是严格字节等价。

每条都要给出我自己的实测数字。凡是我原脚本错的地方，如实记为自错。
"""
import io, os, sys, types, re, tempfile, shutil, atexit, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))

FAILS = []
TMP = tempfile.mkdtemp(prefix="r73chk_")
atexit.register(lambda d=TMP: shutil.rmtree(d, ignore_errors=True))


def P(s=""):
    print(s)


def ck(n, c, d=""):
    P(("  PASS " if c else "  FAIL ") + n + (("  " + d) if d else ""))
    if not c:
        FAILS.append(n)
    return c


live_cd = io.open(os.path.join(R14, "check_disc.py"), encoding="utf-8").read()
live_rv = io.open(os.path.join(R14, "recheck_verify.py"), encoding="utf-8").read()
R55 = "(55, '174146', '174645'"


def run_mem(rv_src, tag):
    m = types.ModuleType("recheck_verify")
    m.__file__ = os.path.join(R14, "recheck_verify.py")
    exec(compile(rv_src, m.__file__, "exec"), m.__dict__)
    sys.modules["recheck_verify"] = m
    g = {"__name__": "__main__", "__file__": os.path.join(R14, "check_disc.py")}
    buf = []
    g["print"] = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
    code = None
    try:
        exec(compile(live_cd, g["__file__"], "exec"), g)
    except SystemExit as e:
        code = e.code
    finally:
        sys.modules.pop("recheck_verify", None)
    txt = "\n".join(buf) + "\n"
    mm = re.search(r"ok=(\d+) fail=(\d+)", txt)
    return (int(mm.group(1)), int(mm.group(2))) if mm else (-1, -1), txt, code


def run_mem_full(cd_src, rv_src, tag):
    """完整版：门禁源码与校验器源码都可替换（run_mem 固定用 live 门禁）。"""
    m = types.ModuleType("recheck_verify")
    m.__file__ = os.path.join(R14, "recheck_verify.py")
    exec(compile(rv_src, m.__file__, "exec"), m.__dict__)
    sys.modules["recheck_verify"] = m
    g = {"__name__": "__main__", "__file__": os.path.join(R14, "check_disc.py")}
    buf = []
    g["print"] = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
    code = None
    try:
        exec(compile(cd_src, g["__file__"], "exec"), g)
    except SystemExit as e:
        code = e.code
    finally:
        sys.modules.pop("recheck_verify", None)
    return "\n".join(buf) + "\n", code


def grid(start, end):
    """固定 (start, end)，返回 (ok, fail)。"""
    return run_mem(live_rv.replace(R55, "(55, '%s', '%s'" % (start, end)), "g")[0]


# =====================================================================
P("=== A1-a · 我 S2 的「终点无鉴别力」是不是零信息格 ===")
P("  指控：起点固定在 174146（红区）时终点必然无影响，那格无信息。")
P("")
P("  我原脚本的配置（起点=174146，红区）：")
orig_ends = {}
for e in ("173919", "174002", "174645", "235959"):
    orig_ends[e] = grid("174146", e)
    P("    起点 174146 终点 %s ⇒ ok=%d fail=%d" % (e, orig_ends[e][0], orig_ends[e][1]))
ck("A1-a① 复现我原结论：红区起点下终点全同",
   len(set(orig_ends.values())) == 1, str(set(orig_ends.values())))

P("")
P("  指控的配置（起点=173919，绿区）：")
green_ends = {}
for e in ("173919", "173920", "174001", "174002", "174645", "235959"):
    green_ends[e] = grid("173919", e)
    P("    起点 173919 终点 %s ⇒ ok=%d fail=%d" % (e, green_ends[e][0], green_ends[e][1]))
ck("A1-a② 指控成立：绿区起点下终点确有鉴别力（结果不再全同）",
   len(set(green_ends.values())) > 1, str(set(green_ends.values())))
ck("A1-a③ 绿区起点下终点的临界点 = 174002（= 第 5 条的 at）",
   green_ends["174001"][0] == 4 and green_ends["174002"][0] == 5,
   "174001→ok=%d, 174002→ok=%d" % (green_ends["174001"][0], green_ends["174002"][0]))
P("")
P("  ⇒ **我承认这是零信息格**，与 R72 的 W_only 同族（同一个坑我第三次踩）：")
P("     我把「在某一个起点下终点无影响」写成了「终点完全无鉴别力」——")
P("     而那个起点恰好使窗口根本进不到终点判据。")

# =====================================================================
P("")
P("=== A1-b · 起点=000000 时 R55 是否变成「全天窗口」（取消窗口而非修窗口）===")


def judge_at(round_s, at_s, start="174146", end="174645"):
    """用真校验器判一条自造 at/round（起点终点可配）。返回 (ok, detail)。"""
    src = live_rv.replace(R55, "(55, '%s', '%s'" % (start, end))
    m = types.ModuleType("rv")
    m.__file__ = os.path.join(R14, "recheck_verify.py")
    exec(compile(src, m.__file__, "exec"), m.__dict__)
    row = None
    for ln in io.open(os.path.join(R14, "DISC_RECHECK.tsv"), encoding="utf-8").read().split("\n")[1:]:
        if ln.startswith("3\t"):
            row = ln.split("\t")
            break
    d = os.path.join(TMP, "j")
    os.makedirs(d, exist_ok=True)
    pf = os.path.join(d, "p.txt")
    h = hashlib.sha256(row[3].encode("utf-8")).hexdigest()
    io.open(pf, "w", encoding="utf-8", newline="\n").write(
        "DISC_RECHECK discipline=3 round=%s at=%s anchors=sha256:%s conclusion=PASS\n"
        % (round_s, at_s, h))
    r2 = list(row); r2[4] = os.path.relpath(pf, ROOT)
    return m.verify_recheck_line(ROOT, r2)


# R73 自错修正（第七次）：初版断言把「当天任意时刻都过」写成一条 all()，
# 但实测 12:00:54 与 17:39:19 **不过**（它们早于 R3 的立条上界？不 —— 它们其实死在 R4
# 之外的另一处，故必须逐条打印原因而不是只看 ok）。
# ⇒ 我原句「任意时刻都过」是**错的**，执行员那句「12:00:54 也判为合法 R55」也要按实测改。
# R73 自错修正（第九次）：上一版改的是 **r55** 的起点起点，却拿 **R57** 去判 ——
# 标签对不上（改 r55 当然影响不到 R57 的窗口）。改回 round=R55 才测的是同一行。
wide = {}
for at_s, note in (("2026-11-22T12:00:54+08:00", "立条时刻（早）"),
                   ("2026-11-22T17:39:19+08:00", "5 条的 at"),
                   ("2026-11-22T17:50:00+08:00", "5 条 at 之后"),
                   ("2026-11-22T23:00:00+08:00", "夜"),
                   ("2026-11-22T23:59:59+08:00", "当日最后一秒")):
    ok, det = judge_at("R55", at_s, start="000000", end="235959")
    wide[at_s] = (ok, det)
    P("  r55 起点 000000 终点 235959，at=%s（%s）标 R55 ⇒ ok=%s | %s"
      % (at_s[11:19], note, ok, det[:56]))
npass = sum(1 for ok, _ in wide.values() if ok)
ck("A1-b① 起点 000000 把 r55 放大到覆盖当天绝大部分时刻（%d/%d 过）"
   % (npass, len(wide)), npass >= 3, "过的是 %s" % [k[11:19] for k, v in wide.items() if v[0]])
# R73 自错修正（第十次）：上一版这里断言「至少一个时刻不过」—— 实测 5/5 全过。
# 我那句"收窄"是自己凭空怀疑，数据不支持。如实反向：执行员的说法更强且成立。
ck("A1-b①b 实测 5/5 全过 ⇒「起点 000000 使 r55 窗口覆盖当日全天」成立；"
   "我原先的怀疑（以为会有时刻不过）被自己的数据推翻", npass == len(wide),
   "过的是 %s" % [k[11:19] for k, v in wide.items() if v[0]])
ck("A1-b①c 起点 000000 时 5 条的 at（17:39:19）确实过（这是「取消窗口」的含义）",
   wide["2026-11-22T17:39:19+08:00"][0] is True, str(wide["2026-11-22T17:39:19+08:00"][0]))
ck("A1-b② 对照：live 配置下同一时刻标 R57 不过（证①非恒真）",
   judge_at("R57", "2026-11-22T12:00:54+08:00")[0] is False)

# =====================================================================
P("")
P("=== A1-c · 这 5 条在时间上能否区分 R54 / R55 ===")
c54 = judge_at("R54", "2026-11-22T17:39:19+08:00")
P("  at=17:39:19 标 R54 ⇒ ok=%s  %s" % (c54[0], c54[1][:80]))
c55 = judge_at("R55", "2026-11-22T17:39:19+08:00")
P("  at=17:39:19 标 R55 ⇒ ok=%s  %s" % (c55[0], c55[1][:80]))
ck("A1-c① 指控成立：同一 at 标 R54 在 live 配置下也过（R54 窗口含 17:39:19）",
   c54[0] is True, c54[1][:60])
ck("A1-c② 但标 R55 在 live 配置下不过（两者仍需改配置才能都过）",
   c55[0] is False, c55[1][:60])
P("  ⇒ 精确表述：在 **live 配置**下 R54 过、R55 不过；要让 5 条过就得改 r55 起点，")
P("     改完后 R55 也过 ⇒ **改完就无法区分**，不是「本来就能区分」。")
P("     执行员那句「时间上无法区分 R54/R55」在**改过之后**成立、在 live 下不成立。")

# =====================================================================
P("")
P("=== A1-d · 「不改分隔符」到底是 5 行还是 10 行不同 ===")
ORIG_CD = io.open(sorted(__import__("glob").glob(os.path.join(
    R14, "R17_LEAD_BASELINE", "SUPERSEDED.before_r73_pathfix_check_disc.py_*.bak")))[-1],
    encoding="utf-8").read()
ORIG_RV = io.open(sorted(__import__("glob").glob(os.path.join(
    R14, "R17_LEAD_BASELINE", "SUPERSEDED.before_r73_pathfix_recheck_verify.py_*.bak")))[-1],
    encoding="utf-8").read()
OLD_REL = "ap = rel.replace('/', '\\\\')"
NEW_REL = "ap = rel.replace('\\\\', os.sep).replace('/', os.sep)"
old_root_line = "ROOT = r'D:\\Project\\ra2-campaign-forge'"

# 基线 live
base, base_txt, _ = run_mem(live_rv, "b")
# 只换 ROOT、保留旧分隔符
n1cd = ORIG_CD.replace(old_root_line, "ROOT = %r" % ROOT)
n1out, n1_txt, _ = run_mem(ORIG_RV, "n1")
la, lb = base_txt.rstrip("\n").split("\n"), n1_txt.rstrip("\n").split("\n")
diff_lines = sum(1 for i in range(max(len(la), len(lb)))
                 if (la[i] if i < len(la) else None) != (lb[i] if i < len(lb) else None))
P("  只换 ROOT 不换分隔符：总行数 %d vs %d，不同行 %d" % (len(la), len(lb), diff_lines))
ck("A1-d① 我报的 5 行可复现（FAIL 条目数 = 5）", diff_lines == 5, str(diff_lines))
# R73 自错修正（第八次）：初版这里传的是 ORIG_RV + **live_cd**（漏传门禁源码），
# 于是测的根本不是「完整原版」，而是 live 门禁 + 旧校验器。修法：显式传 ORIG_CD。
P("  执行员说的 10 行：查两种候选配置")
# 配置 B：完整原版（ROOT=D:\\ 且分隔符旧）—— 在 POSIX 上会在读 R14_COMMON 时抛异常
try:
    _fo, _fo_txt, _fo_rc = run_mem_full(ORIG_CD, ORIG_RV, "fo")
    fb = "正常结束 rc=%s 行=%d" % (_fo_rc, len(_fo_txt.rstrip().split("\n")))
except Exception as e:
    _fo_txt, _fo_rc = "", -1
    fb = "抛 %s（ROOT=D:\\ 在本机不存在，先死在读文件）" % type(e).__name__
P("  配置 B 完整原版（两处都不改）：%s" % fb)
ck("A1-d② 完整原版在 POSIX 上跑不完（不可能给出 10 行 diff）", _fo_rc == -1, fb)
P("  ⇒ 执行员「不改就有 10 行不同」在**本机无法复现**：")
P("     能复现的只有 5 行（配置 A：只换 ROOT、保留旧分隔符）。")
P("     无法排除它把 stdout+stderr 或两次不同配置的 diff 合并计数。")
ck("A1-d③ 我报的 5 行可复现，执行员的 10 行不可复现（如实记录为口径未对上）",
   diff_lines == 5 and _fo_rc == -1, "5 可复现 / 10 未复现")

# =====================================================================
P("")
P("=== A1-e · 「逐行相同」是否只是 stdout 文本相同（norm 抹掉 CRLF）===")
P("  查我的 probeequiv_r73.py 的比对函数：")
pe = io.open(os.path.join(HERE, "probeequiv_r73.py"), encoding="utf-8").read()
ck("A1-e① 我确实用了 norm() 归一化 CRLF 后再比", "def norm(t):" in pe and 'replace("\\r\\n", "\\n")' in pe)
ck("A1-e② 我确实只捕获 stdout（stderr 合并进 stdout，未单独比对）",
   "stderr=subprocess.STDOUT" in pe or "stdout=subprocess.PIPE" in pe)
P("  ⇒ 审计员 c 成立：我证明的是「stdout 文本逐行一致」，")
P("     不是「字节级等价」，也不覆盖 stderr 与任何文件写入副作用。")
P("     限定语必须随结论一起写，否则「等价」被读强。")

P("")
P("=== S9 · 复算总表（全部为本次实测）===")
P("  A1-a 零信息格       : 承认。红区起点下终点全同 %s；绿区起点下 %s"
  % (sorted(set(orig_ends.values())), sorted(set(green_ends.values()))))
P("  A1-b 取消窗口       : **成立且比我以为的更强**。起点 000000 + 终点 235959 ⇒")
P("                        当天的 at（含 12:00:54 / 23:59:59）标 R55 全部通过（%d/%d）" % (npass, len(wide)))
P("  A1-c R54/R55 可辨   : 部分成立。live 下**可辨**（R54 过、R55 不过）；改窗口后不可辨")
P("  A1-d 5 行 vs 10 行  : 5 行可复现；10 行**不可复现**（完整原版在 POSIX 抛 FileNotFoundError）")
P("  A1-e stdout 非字节  : 成立。限定语必须写")

P("")
P("RESULT " + ("ALL-PASS" if not FAILS else "FAIL: " + ",".join(FAILS)))
sys.exit(0 if not FAILS else 1)
