#!/usr/bin/env python3
# R45-T2-EVID2 主分析：Q1 冲突类型 / Q2 分层40件内容特征 / Q3 同目录多数派
# 只读 lead\；唯一写目标 R17_R84_T2_EVID2\
import csv, os, re

LEAD = r"D:\Project\ra2-campaign-forge\lead"
R = os.path.join(LEAD, "next_re_20261117_r14")
OUT = os.path.join(R, "R17_R84_T2_EVID2")
EP  = os.path.join(R, "R17_R78_T1_RECLASS", "files_excluded_prime.tsv")
VD  = os.path.join(R, "R17_R81_T2_EVID", "_verdicts.tsv")
UD  = os.path.join(R, "R17_R81_T2_EVID", "_undead_evid.tsv")

def load(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))

ep = load(EP); vd = load(VD); ud = {r["rel"]: r for r in load(UD)}
vd_by = {r["rel"]: r for r in vd}
tie = sorted([r for r in vd if r["verdict"] == "无法判定"], key=lambda x: x["rel"])
assert len(tie) == 266

# ---------- 名字信号（只看 basename，纪律23：仅作“嫌疑/声明”，不单独下判） ----------
PROC_TOK = ["stdout","stderr","_out",".out","report","result","log","selftest","check",
            "probe","status","summary","verdict","exit","cmd","progress","gen_","generate",
            "build","validat","reject","perf","diag","streamdiff","byfunc","allsecs","step",
            "phase","replay","run_","runid","console","recheck","selfaudit"]
OBJ_TOK  = ["row_","disasm","bytes","byte","addr","site","table","vtable","vt_","struct",
            "insn","instruction","dump","_map","ref","fact","index","rtti","event_names",
            "array_writes","baseline","sample","template","needle","class","caller","ring",
            "delta","xref","guid","slot","named","bytescan","baseline_mine"]

def name_signal(rel):
    bn = os.path.basename(rel).lower()
    hp = any(t in bn for t in PROC_TOK)
    ho = any(t in bn for t in OBJ_TOK)
    if hp and not ho: return "过程"
    if ho and not hp: return "对象"
    if hp and ho:     return "弱"   # 同时含两类词 => 名字信号相互抵消,视为弱
    return "弱"

# ---------- 内容倾向：用 O/P 行计数（内容证据，不看 label/why） ----------
def content_lean(v):
    o, p = int(v["O"]), int(v["P"])
    if o > p: return "对象"
    if p > o: return "过程"
    return "平"   # O==P（含全 0）= 平票

def conflict_type(ns, cl):
    if ns == "过程" and cl == "对象": return "名过内象"
    if ns == "对象" and cl == "过程": return "名象内过"
    return "两者都弱"

# ---------- Q1 明细与分布 ----------
q1_rows = []
for r in tie:
    rel = r["rel"]; u = ud[rel]
    ns = name_signal(rel); cl = content_lean(r); ct = conflict_type(ns, cl)
    q1_rows.append(dict(rel=rel, bytes=int(u["bytes"]), bnform=u["bnform"],
                        O=int(r["O"]), P=int(r["P"]), name=ns, lean=cl, ctype=ct))

with open(os.path.join(OUT, "q1_tie_detail.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["rel","bytes","bnform","O","P","name","lean","ctype"], delimiter="\t")
    w.writeheader()
    for x in q1_rows: w.writerow(x)

from collections import Counter, defaultdict
agg = defaultdict(lambda: [0,0])
for x in q1_rows:
    agg[x["ctype"]][0] += 1; agg[x["ctype"]][1] += x["bytes"]
q1_report = []
for k in ["名过内象","名象内过","两者都弱"]:
    q1_report.append((k, agg[k][0], agg[k][1]))
cross = Counter((x["name"], x["lean"]) for x in q1_rows)
cross_b = defaultdict(int)
for x in q1_rows: cross_b[(x["name"], x["lean"])] += x["bytes"]

with open(os.path.join(OUT, "q1_summary.txt"), "w", encoding="utf-8") as f:
    f.write("Q1 266 件冲突类型分布\n")
    for k,c,b in q1_report:
        f.write(f"  {k}: {c} 件 / {b} B\n")
    f.write("校验 合计: %d 件 / %d B\n" % (sum(c for _,c,_ in q1_report), sum(b for _,_,b in q1_report)))
    f.write("\n交叉表 名字信号 x 内容倾向 (件/字节):\n")
    for ns in ["过程","对象","弱"]:
        for cl in ["对象","过程","平"]:
            f.write(f"  name={ns} lean={cl}: {cross[(ns,cl)]} 件 / {cross_b[(ns,cl)]} B\n")
    f.write("\n主因判定: 见 q1_summary.txt 顶部三类计数\n")

# ---------- Q3 同目录多数派 ----------
# 目录 = rel 的父目录（含 EVIDENCE 的那一层按原样）
def parent(rel):
    p = os.path.dirname(rel)
    return p if p else "(root)"

allexam = vd[:]  # 1242 件全部被检视过
dir_stat = defaultdict(lambda: Counter())
for r in allexam:
    d = parent(r["rel"])
    dir_stat[d][r["verdict"]] += 1

# 规则：目录内“已裁件”（对象+过程）>= N 且多数派占比 >= q => 该目录内平票件按多数派裁
def apply_majority(min_n, ratio):
    resolved = []; unresolved = []
    for x in q1_rows:
        d = parent(x["rel"])
        c = dir_stat[d]
        decided = c["对象抄本"] + c["过程输出"]
        if decided < min_n:
            unresolved.append((x, decided, 0.0, "样本不足")); continue
        if c["对象抄本"] >= c["过程输出"]:
            lab, maj = "对象抄本", c["对象抄本"]
        else:
            lab, maj = "过程输出", c["过程输出"]
        frac = maj/decided
        if frac >= ratio:
            resolved.append((x, lab, decided, frac))
        else:
            unresolved.append((x, decided, frac, "不够多数"))
    return resolved, unresolved

q3_lines = []
for min_n, ratio in [(3,0.75),(4,0.75),(5,0.8),(2,1.0),(3,1.0)]:
    res, unres = apply_majority(min_n, ratio)
    q3_lines.append((min_n, ratio, len(res), sum(x[0]["bytes"] for x in res), len(unres)))

# 可靠性：留一法——对 976 已裁件，用“同目录其他已裁件”的多数派预测，检验一致率
loo_ok = loo_n = 0
by_dir_decided = defaultdict(list)
for r in vd:
    if r["verdict"] in ("对象抄本","过程输出"):
        by_dir_decided[parent(r["rel"])].append(r["verdict"])
for d, labs in by_dir_decided.items():
    for i, lab in enumerate(labs):
        others = labs[:i]+labs[i+1:]
        if not others: continue
        o = others.count("对象抄本"); p = others.count("过程输出")
        if o==0 and p==0: continue
        pred = "对象抄本" if o>=p else "过程输出"
        loo_n += 1
        if pred==lab: loo_ok += 1

with open(os.path.join(OUT, "q3_summary.txt"), "w", encoding="utf-8") as f:
    f.write("Q3 同目录多数派规则覆盖率 (min_n=目录已裁件下限, ratio=多数派占比下限)\n")
    for mn,ra,rc,rb,uc in q3_lines:
        f.write(f"  min_n={mn} ratio={ra}: 可裁 {rc} 件 / {rb} B ; 仍单列 {uc} 件\n")
    f.write(f"\n留一法可靠性(仅对976已裁件, 用同目录其他已裁件多数派预测): {loo_ok}/{loo_n} = {loo_ok/loo_n:.4f}\n")
    f.write("\n各目录已裁件分布 Top20:\n")
    for d,c in sorted(dir_stat.items(), key=lambda kv:-(kv[1]['对象抄本']+kv[1]['过程输出']))[:20]:
        f.write(f"  {d}: 对象{c['对象抄本']} 过程{c['过程输出']} 平票{c['无法判定']}\n")

# ---------- Q2 分层抽 40 件 ----------
# 分层：按 q1 ctype 配额 + 每类内按 bnform 分散；不读 label/why/verdict
VA = re.compile(r"^\s*0x[0-9A-Fa-f]{6,8}")
WRAP = re.compile(r"^\s*(\[cmd\]|\[exit\]|=====|-----|#{3,}|\*{3,}|RUN_ID\s*=|COMMAND\s*[:=]|\[PROGRESS)", re.I)
ZH = re.compile(r"[\u4e00-\u9fff]")

def first8k(rel):
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as fh: return fh.read(8192).decode("utf-8", errors="replace")
    except Exception:
        return None

def features(rel, v):
    t = first8k(rel)
    if t is None:
        return dict(ok=0, va="NA", wrap="unreadable", zh="NA", first="未取得")
    lines = [l for l in t.splitlines() if l.strip()]
    n = len(lines)
    va = sum(1 for l in lines if VA.match(l))
    varatio = (va/n) if n else 0.0
    wrap_hits = []
    for l in lines[:40]:
        m = WRAP.match(l)
        if m: wrap_hits.append(m.group(0).strip()[:12])
    wrap = "有("+",".join(sorted(set(wrap_hits))[:3])+")" if wrap_hits else "无"
    zh_n = sum(1 for l in lines[:40] if ZH.search(l))
    zh = f"有({zh_n}行)" if zh_n else "无"
    first = lines[0].strip()[:80] if lines else "(空文件)"
    return dict(ok=1, va=f"{varatio:.0%}({va}/{n})", wrap=wrap, zh=zh, first=first)

# 配额：名过内象/名象内过/两者都弱 尽量都覆盖；总数40
# 先按 ctype 分组，按比例取整 + 保证每组至少若干
byct = defaultdict(list)
for x in q1_rows: byct[x["ctype"]].append(x)
for k in byct: byct[k].sort(key=lambda x:x["rel"])

# 固定配额（覆盖三类，偏重“两者都弱”因其为多数）
quota = {"名过内象":10, "名象内过":6, "两者都弱":24}
sample = []
for k,q in quota.items():
    pool = byct[k]
    if not pool: continue
    if len(pool) <= q: pick = pool[:]
    else:
        step = len(pool)/q
        pick = [pool[int(i*step)] for i in range(q)]
    for x in pick: sample.append((k,x))
# 若不足40，从两者都弱补
if len(sample) < 40:
    have = set(x["rel"] for _,x in sample)
    for x in byct["两者都弱"]:
        if len(sample)>=40: break
        if x["rel"] not in have: sample.append(("两者都弱",x))

with open(os.path.join(OUT, "q2_sample40_features.txt"), "w", encoding="utf-8") as f:
    f.write("Q2 分层40件内容特征（前8KiB，未看任何 label/why/verdict）\n")
    for i,(ct,x) in enumerate(sample[:40],1):
        ft = features(x["rel"], vd_by[x["rel"]])
        f.write(f"[{i:02d}] {x['rel']}\n")
        f.write(f"     q1type={ct} bnform={x['bnform']} bytes={x['bytes']} O={x['O']} P={x['P']}\n")
        f.write(f"     VA={ft['va']} 包装={ft['wrap']} 中文={ft['zh']}\n")
        f.write(f"     首行={ft['first']}\n\n")
print("WROTE q1_tie_detail.tsv q1_summary.txt q3_summary.txt q2_sample40_features.txt")
print("SAMPLE_SIZE", len(sample[:40]))
for k,c,b in q1_report: print("Q1", k, c, b)
for mn,ra,rc,rb,uc in q3_lines: print("Q3", mn, ra, rc, rb, uc)
print("LOO", loo_ok, "/", loo_n)
