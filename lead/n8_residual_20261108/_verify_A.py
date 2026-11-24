# -*- coding: utf-8 -*-
"""独立复核员 · 自写实现（不复用 _n8r_* / _n8_* 代码）。

复核范围：
 [A] ratio_max 0.9831 定位 + 该帧读数个数（第3项）
 [B] GOAL 尾部 / 最新节（第7项）
 [C] 保护区与写域纪律（mtime / 内容指纹），并输出被核对象指纹
只读保护区；唯一写 = 本目录 _verify_A_out.txt。
"""
import hashlib
import io
import json
import os
import re
import glob

ROOT = r"D:\Project\ra2-campaign-forge"
HERE = os.path.join(ROOT, "lead", "n8_residual_20261108")
GOAL = os.path.join(ROOT, "lead", "GOAL_THREE_TARGETS_20261018.md")
OUT = []


def P(*a):
    OUT.append(" ".join(str(x) for x in a))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest(), os.path.getsize(path)


# ============================================================ [A] ratio_max
P("=" * 78)
P("[A] 独立复算 ratio_max（自写：按 f 分组、读数>=3、span=末-首、maxgap=相邻最大、ratio=maxgap/span）")
P("=" * 78)

cands = sorted(glob.glob(os.path.join(ROOT, "lead", "**", "measure_w*.json"), recursive=True))
P("候选 measure_w*.json = %d" % len(cands))

qual = []
for p in cands:
    with io.open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    hz = (d.get("stats") or {}).get("hz_effective")
    if d.get("verdict") == "ok" and isinstance(hz, (int, float)) and hz >= 100:
        qual.append((p, d))
P("合格窗（verdict=ok 且 hz_effective>=100）= %d" % len(qual))

# 自写：逐帧统计，逐窗 r_max，全局 argmax；同时保留全帧明细以查并列
all_frames = []  # (tag, fi, nreads, span_ms, maxgap_ms, ratio, ts_tuple)
win_stats = []
for p, d in qual:
    m = re.search(r"measure_w(\d+)\.json$", os.path.basename(p))
    tag = os.path.basename(os.path.dirname(p)) + "/w" + m.group(1)
    s = d["samples"]
    fseq, tseq = s["f"], s["t"]
    assert len(fseq) == len(tseq)
    byframe = {}
    for fi, ti in zip(fseq, tseq):
        byframe.setdefault(fi, []).append(ti)
    small_skipped = sum(1 for fi in byframe if len(byframe[fi]) < 3)
    fr = []
    for fi in sorted(byframe):
        ts = sorted(byframe[fi])
        if len(ts) < 3:
            continue
        gaps = [ts[k + 1] - ts[k] for k in range(len(ts) - 1)]
        span_ms = (ts[-1] - ts[0]) * 1000.0
        mg_ms = max(gaps) * 1000.0
        r = mg_ms / span_ms if span_ms > 0 else None
        fr.append((fi, len(ts), span_ms, mg_ms, r, tuple(ts)))
    ratios = [x[4] for x in fr if x[4] is not None]
    rmax_w = max(ratios) if ratios else None
    win_stats.append((tag, len(fr), len(byframe), small_skipped, rmax_w))
    for x in fr:
        all_frames.append((tag,) + x)

P("")
P("[A1] 15 窗 r_max（自写）")
P("%-22s %9s %10s %9s %10s" % ("window", "帧数>=3", "distinct_f", "小帧跳过", "r_max"))
for tag, nf, nd, ns, rm in sorted(win_stats):
    P("%-22s %9d %10d %9d %10.6f" % (tag, nf, nd, ns, rm))

gmax = max(win_stats, key=lambda x: x[4])
P("")
P("[A2] 全局 ratio_max = %.6f @ %s（round4 = %.4f）" % (gmax[4], gmax[0], round(gmax[4], 4)))

# 全 15 窗中 round4==0.9831 或差<1e-4 的帧
near = [r for r in all_frames if r[5] is not None and abs(r[5] - 0.9831) < 1e-4]
P("[A3] 与 0.9831 差<1e-4 的帧（全窗）= %d" % len(near))
for r in near:
    P("    %s f=%d 读数=%d span=%.4f ms maxgap=%.4f ms ratio=%.6f" %
      (r[0], r[1], r[2], r[3], r[4], r[5]))

# 直接锁定该帧原始读数（独立按 f=argmax 抽取）
wtag = gmax[0]
win_frame_rows = [r for r in all_frames if r[0] == wtag]
best = max(win_frame_rows, key=lambda x: x[5])
P("")
P("[A4] 该帧原始读数（自写抽取，f=%d）：" % best[1])
P("    窗=%s  读数个数=%d" % (best[0], best[2]))
P("    t 序列（秒）= %s" % ["%.6f" % x for x in best[6]])
P("    相邻间隔(ms) = %s" % ["%.4f" % ((best[6][k + 1] - best[6][k]) * 1000.0)
                             for k in range(len(best[6]) - 1)])
P("    span = %.4f ms  maxgap = %.4f ms  ratio = %.6f" % (best[3], best[4], best[5]))
wf = [x for x in win_stats if x[0] == wtag][0]
P("    该窗帧数(>=3读)=%d  distinct_f=%d  小帧跳过=%d" % (wf[1], wf[2], wf[3]))

# 该帧在样本流中的位置：是否窗尾、是否最后3个读数
pd = [d for p, d in qual if os.path.basename(os.path.dirname(p)) + "/w" +
      re.search(r"measure_w(\d+)\.json$", os.path.basename(p)).group(1) == wtag][0]
sf, st = pd["samples"]["f"], pd["samples"]["t"]
fset = sorted(set(sf))
P("")
P("[A5] 位置语义（自写）：")
P("    窗内帧号范围 = %d..%d（共 %d）；f=%d 是否最大帧号 = %s" %
  (fset[0], fset[-1], len(fset), best[1], best[1] == fset[-1]))
P("    全样本末读数 t = %.6f；f=%d 末读数 t = %.6f；相同 = %s" %
  (st[-1], best[1], max(best[6]), abs(st[-1] - max(best[6])) < 1e-9))
P("    最后3个读数是否全部属于 f=%d = %s" %
  (best[1], all(sf[i] == best[1] for i in range(len(sf) - 3, len(sf)))))
back = sum(1 for k in range(1, len(sf)) if sf[k] < sf[k - 1])
jump = sum(1 for k in range(1, len(sf)) if sf[k] - sf[k - 1] > 1)
P("    f 回退=%d 跳号=%d；span_s=%s；末读数-首读数=%.4f s" %
  (back, jump, pd.get("span_s"), st[-1] - st[0]))

# 邻帧读数（独立）
byframe2 = {}
for fi, ti in zip(sf, st):
    byframe2.setdefault(fi, []).append(ti)
P("    邻帧（f=5460..5463）读数/span：")
for fi in range(5460, 5464):
    ts = sorted(byframe2.get(fi, []))
    if ts:
        P("      f=%d 读数=%d span=%.4f ms" % (fi, len(ts), (ts[-1] - ts[0]) * 1000.0))

# 字面口径对照（读数个数 / span_ms）
lit = max((r[2] / r[3]) for r in all_frames if r[3] > 0)
P("")
P("[A6] 任务书字面口径「读数个数/帧时长」全局最大 = %.6f（!=0.9831 = %s）" %
  (lit, abs(lit - 0.9831) > 5e-5))

# ============================================================ [B] GOAL 尾部
P("")
P("=" * 78)
P("[B] 独立核对 GOAL 尾部 / 最新节（第7项）")
P("=" * 78)
b = open(GOAL, "rb").read()
gnl = b.count(b"\n")
lines = b.decode("utf-8").split("\n")
P("[B1] 字节数=%d  SHA256=%s" % (len(b), hashlib.sha256(b).hexdigest()))
P("    \\n 计数=%d；split 片段=%d；末片段=%s" %
  (gnl, len(lines), "空(以换行结尾)" if lines[-1] == "" else repr(lines[-1][:40])))
last = gnl if lines[-1] == "" else len(lines)
P("    末行行号=:%d 内容=%r" % (last, lines[last - 1].rstrip("\r")))
heads = [(i, int(m.group(1)), ln) for i, ln in enumerate(lines[:last], 1)
         if (m := re.match(r"^## §(\d+)", ln))]
mx = max(heads, key=lambda x: x[1])
P("[B2] 「## §N」节头数=%d；最大节号=§%d @ :%d；节号是否单调不递减=%s" %
  (len(heads), mx[1], mx[0], all(heads[k][1] >= heads[k - 1][1] for k in range(1, len(heads)))))
P("    末5个节头：")
for i, n, ln in heads[-5:]:
    P("      :%d §%d %s" % (i, n, ln[:70]))
P("[B3] :9757 之后是否还有行：%s（末行=%d）" %
  ("无" if last == 9757 else "有/需查", last))
P("    末行内容含『零真机、零采样注入、零母本改动、未 commit、未 push』= %s" %
  ("零真机" in lines[last - 1] and "未 push" in lines[last - 1]))
# 行内 §9xx 引用
inline = [(i, ln.strip()) for i, ln in enumerate(lines[:last], 1) if re.search(r"§9\d\d", ln)]
P("[B4] 行内 §9xx 引用（非节头）= %d 处：" % len(inline))
for i, ln in inline:
    P("      :%d %s" % (i, ln[:90]))
P("    全文件是否存在 §9xx 节头 = %s" % any(n >= 900 for _, n, _ in heads))
# :6461 内容
P("    :6461 = %r" % lines[6460].rstrip("\r"))

# ============================================================ [C] 指纹总表
P("")
P("=" * 78)
P("[C] 被核对象 / 保护区指纹（hashlib 实算）")
P("=" * 78)
for rel in [
    "lead/slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
    "lead/re_line_20261105/W2_FRAMETIME_ATTRIB/_w2_matrix.tsv",
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/n8_residual_20261108/_n8r_UNVERIFIED_CLOSURE_20261108.md",
]:
    h, sz = sha(os.path.join(ROOT, rel))
    P("    %s  SHA256=%s  字节数=%d" % (rel, h, sz))

P("")
P("VERIFY_A DONE")
with io.open(os.path.join(HERE, "_verify_A_out.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(OUT) + "\n")
print("\n".join(OUT))
