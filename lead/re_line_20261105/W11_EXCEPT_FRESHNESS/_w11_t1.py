# -*- coding: utf-8 -*-
"""W11-T1 只读探针：except.txt / except_post_* 全链路语义核查。
零真机、零注入、不写任何 out/ 文件；只读 + 在本目录写 _w11_t1_out.txt。
运行：python -I -X utf8 _w11_t1.py
"""
import hashlib
import json
import os

ROOT = os.path.normpath(r"D:\Project\ra2-campaign-forge")
W11 = os.path.join(ROOT, "lead", "re_line_20261105", "W11_EXCEPT_FRESHNESS")
HARNESS = os.path.join(ROOT, "out", "re_work", "work_chain",
                       "CONTINUE_20261003", "lead", "qc151_u0400_trip",
                       "qc151_trip.py")
TRIP_CHAIN = os.path.join(ROOT, "out", "re_work", "work_chain",
                          "CONTINUE_20261003", "lead", "qc161_u0400_trip")
TRIP_ROOT = os.path.join(ROOT, "lead", "qc161_u0400_trip")
SRC_DIR = os.path.join(TRIP_CHAIN, "_src_L3_sf10c_20261021")
MASTER = os.path.join(ROOT, "ra2bench", "except.txt")
OUT = os.path.join(W11, "_w11_t1_out.txt")

lines_out = []


def emit(s=""):
    lines_out.append(str(s))


def sha256_file(p):
    hh = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            hh.update(chunk)
    return hh.hexdigest()


emit("=" * 78)
emit("W11-T1 探针 · %s" % os.path.basename(__file__))
emit("零真机 / 零注入 / 只读；写域仅 W11_EXCEPT_FRESHNESS/_w11_t1_out.txt")
emit("=" * 78)

# ---- A. harness 指纹 ----
emit("")
emit("[A] qc151_trip.py 指纹")
h = sha256_file(HARNESS)
with open(HARNESS, "rb") as f:
    blob = f.read()
n_bytes = len(blob)
n_lines = blob.count(b"\n") + (0 if blob.endswith(b"\n") else 1)
emit("  sha256 = %s" % h)
emit("  bytes  = %d" % n_bytes)
emit("  lines  = %d" % n_lines)

src_lines = blob.decode("utf-8", errors="replace").split("\n")


def show(start, end, tag):
    emit("  --- %s :%d-%d ---" % (tag, start, end))
    for i in range(start - 1, min(end, len(src_lines))):
        emit("    %5d| %s" % (i + 1, src_lines[i].rstrip()))


# ---- B. 行号验证 ----
emit("")
emit("[B] 行号验证")
show(212, 215, "CARRIER_FILES")
show(227, 231, "EXCEPT_MASTER 常量")
show(4561, 4599, "copy_post_except_evidence 全文")
show(5938, 5946, "_except_evidence_copy（finalize 第 1 步）")
show(6041, 6053, "run_guarded_steps 执行序")
show(6390, 6409, "U-5 基线（passive_read / SKIPPED_U5）")
show(672, 708, "except_set_diff")
show(4413, 4425, "_render_log_probe（mtime 唯一出现处）")
show(4945, 4949, "create_isolated_carrier 源件存在性")
show(4957, 4961, "create_isolated_carrier write_bytes 复制")
show(5973, 5983, "_except_diff 读跑后件（无 exists 检查）")
show(4465, 4499, "restore_carrier（只核验不写回）")
show(4447, 4462, "backup_carrier（跑前备份五件）")

# ---- C. 关键词扫描 ----
emit("")
emit("[C] qc151_trip.py 关键词出现处（全文件逐行扫描）")
for kw in ("except_post", "carrier_post_state", "st_mtime", "getmtime",
           "新鲜", "fresh", "except_reset(", "copy_post_except_evidence(",
           "unlink(", "rmtree("):
    hits = [(i + 1, src_lines[i].strip()[:100])
            for i in range(len(src_lines)) if kw in src_lines[i]]
    emit("  %r -> %d 处" % (kw, len(hits)))
    for ln, txt in hits[:12]:
        emit("    :%d %s" % (ln, txt))

call_hits = []
for i in range(len(src_lines)):
    s = src_lines[i]
    if "except_reset" in s and not s.strip().startswith("#"):
        if "def except_reset" in s:
            continue
        call_hits.append((i + 1, s.strip()[:110]))
emit("  except_reset 非定义出现（疑似调用点）-> %d 处" % len(call_hits))
for ln, txt in call_hits:
    emit("    :%d %s" % (ln, txt))

# ---- D. 数据面清点 ----
PRUNE = ("ct", "evidence", "_carrier_bak", "_scratch_dis", "_maps_fixed",
         "__pycache__", "shots")


def walk_capped(root, maxdepth):
    out = []
    base_depth = root.count("\\") + 1
    for dp, dns, fns in os.walk(root):
        cur = dp.count("\\") + 1
        if cur - base_depth >= maxdepth:
            dns[:] = []
        dns[:] = [d for d in dns if d not in PRUNE]
        for fn in fns:
            out.append(dp + os.sep + fn)
    return out


emit("")
emit("[D] 数据面清点（chain + repo-root 两棵趟树，剪枝目录，深度≤3）")
if os.path.exists(MASTER):
    emit("  母本 ra2bench/except.txt: sha256=%s size=%d（常量期望 "
         "ca175a71…/26515）" % (sha256_file(MASTER), os.path.getsize(MASTER)))
else:
    emit("  母本 ra2bench/except.txt: 不存在")
SRC = SRC_DIR + os.sep + "except.txt"
if os.path.exists(SRC):
    with open(SRC, "rb") as f:
        stext = f.read().decode("utf-8", errors="replace")
    emit("  源 _src_L3_sf10c_20261021/except.txt: sha256=%s size=%d "
         "splitlines=%d" % (sha256_file(SRC), os.path.getsize(SRC),
                            len(stext.splitlines())))

diff_tally = {}
post_total = 0
state_total = 0
for tree in (TRIP_CHAIN, TRIP_ROOT):
    if not os.path.isdir(tree):
        emit("  [树不存在] %s" % tree)
        continue
    for fp in walk_capped(tree, 3):
        name = os.path.basename(fp)
        if name == "except_set_diff.json":
            try:
                with open(fp, "rb") as f:
                    d = json.loads(f.read().decode("utf-8", errors="replace"))
                key = (d.get("pre_line_count"), d.get("new_exception_count"))
                diff_tally[key] = diff_tally.get(key, 0) + 1
            except Exception as e:
                key = ("PARSE_ERR", repr(e)[:40])
                diff_tally[key] = diff_tally.get(key, 0) + 1
        elif name.startswith("except_post_") and name.endswith(".txt"):
            post_total += 1
        elif name == "carrier_post_state.json":
            state_total += 1

emit("  except_set_diff.json 总数 = %d" % sum(diff_tally.values()))
emit("  (pre_line_count, new_exception_count) 分布:")
for key in sorted(diff_tally.keys(), key=lambda x: (str(x[0]), str(x[1]))):
    emit("    %s -> %d 份" % (key, diff_tally[key]))
emit("  except_post_*.txt 总数 = %d" % post_total)
emit("  carrier_post_state.json 总数 = %d" % state_total)

# ---- E. 跑后副本 vs 交接继承内容（逐趟比对 receipt；纯 walk，无 listdir 拼接）----
emit("")
emit("[E] except_post_*.txt vs 本趟 receipt 继承 sha（逐趟）")
tripdirs = {}
for tree, tag in ((TRIP_CHAIN, "chain"), (TRIP_ROOT, "root")):
    if not os.path.isdir(tree):
        continue
    for fp in walk_capped(tree, 2):
        parent = os.path.dirname(fp)
        base = os.path.basename(fp)
        bucket = tripdirs.setdefault(parent, {"tag": tag, "receipt": None,
                                              "posts": []})
        bucket["tag"] = tag
        if base == "carrier_creation_receipt.json":
            bucket["receipt"] = fp
        elif base.startswith("except_post_") and base.endswith(".txt"):
            bucket["posts"].append(fp)

match_n = diff_n = noex_n = 0
diff_cases = []
for parent in sorted(tripdirs):
    bucket = tripdirs[parent]
    if bucket["receipt"] is None or not bucket["posts"]:
        continue
    try:
        with open(bucket["receipt"], "rb") as f:
            rec = json.loads(f.read().decode("utf-8", errors="replace"))
    except Exception as e:
        emit("  [%s] receipt 解析失败 %r" % (parent, e))
        continue
    ex = (rec.get("files") or {}).get("except.txt")
    if not ex:
        noex_n += 1
        continue
    pp = sorted(bucket["posts"])[0]
    with open(pp, "rb") as f:
        ph = hashlib.sha256(f.read()).hexdigest()
    inh = str(ex.get("sha256_dst") or "")
    if ph == inh:
        match_n += 1
    else:
        diff_n += 1
        diff_cases.append((os.path.basename(parent), inh[:16], ph[:16]))
emit("  有 receipt 且 except.txt 由本趟复制、且有 except_post 副本的趟: "
     "match(跑后==继承)=%d, differ(跑后!=继承)=%d, receipt无except复制=%d"
     % (match_n, diff_n, noex_n))
for entry, inh, ph in diff_cases[:10]:
    emit("    differ: %s 继承=%s 跑后=%s" % (entry, inh, ph))

# ---- F. 摘要 ----
emit("")
emit("[F] 摘要")
emit("  - copy_post_except_evidence 调用点 = 1（finalize_trip 第 1 步，:5939）")
emit("  - except_reset 无调用点（U-5 后死代码）")
emit("  - harness 内 st_mtime 仅 _render_log_probe :4420/:4422"
     "（ra2render*.log，记录用，非 except.txt 新鲜性检查）")
emit("  - harness 内无任何对 except_post_*.txt 的读取（writer-only）")
emit("  - carrier_post_state.json 无任何与跑前备份 bak 的比对代码")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines_out) + "\n")
print("OK -> %s (%d lines)" % (OUT, len(lines_out)))