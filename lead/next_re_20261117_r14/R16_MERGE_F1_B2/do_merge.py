# -*- coding: utf-8 -*-
"""R16-MERGE-F1 B2 合并执行脚本（一次性）。
读盘上 coverage.tsv / PANEL.md，并 18 行第 4 列、插入 M90 披露。
写 before_state.json / after_state.json / BEFORE_AFTER.txt 到本目录。
严格只读 delta.tsv 与审计裁决；不改其它任何文件。
所有校验在写入前完成；最后一步才落盘。
"""
import os, sys, json, hashlib, datetime, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_F1_B2", "delta.tsv")
OUT  = os.path.join(ROOT, "R16_MERGE_F1_B2")
SEP  = "；④ 活表槽位见证"

def fstate(raw, st, path):
    mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return dict(path=path, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                mtime=mt, crlf=raw.count(b"\r\n"), lf=raw.count(b"\n"),
                cr=raw.count(b"\r"), bare_lf=raw.count(b"\n")-raw.count(b"\r\n"),
                ends_with_newline=raw.endswith(b"\n"))

# ---------- 改前状态（只读） ----------
cov_raw_b = open(COV,"rb").read(); cov_stat_b=os.stat(COV)
pan_raw_b = open(PANEL,"rb").read(); pan_stat_b=os.stat(PANEL)
cov_text_b=cov_raw_b.decode("utf-8"); pan_text_b=pan_raw_b.decode("utf-8")
cov_lines_b=cov_text_b.split("\n"); pan_lines_b=pan_text_b.split("\n")
cov_before=fstate(cov_raw_b,cov_stat_b,COV); pan_before=fstate(pan_raw_b,pan_stat_b,PANEL)

assert "\n".join(cov_lines_b).encode("utf-8")==cov_raw_b, "coverage split/join 往返失败"
assert "\n".join(pan_lines_b).encode("utf-8")==pan_raw_b, "PANEL split/join 往返失败"

# ---------- delta ----------
drows=[ln.split("\t") for ln in open(DELTA,encoding="utf-8",newline="").read().split("\n")[1:] if ln]
assert len(drows)==18 and all(len(r)==8 for r in drows)
dentries=[r[0].strip().upper() for r in drows]

# ---------- coverage 定位与校验 ----------
data_b=cov_lines_b[1:]
assert len(data_b)==18498
rows_b=[ln.split("\t") for ln in data_b]
assert all(len(r)==8 for r in rows_b)
assert sum(1 for r in rows_b if r[4].strip()=="[已证]")==1654
idx_by_entry={}
for i,r in enumerate(rows_b):
    idx_by_entry.setdefault(r[0].strip().upper(),[]).append(i)
before_col4={}; checks=[]
for r in drows:
    e=r[0].strip().upper(); new4=r[3]
    hits=idx_by_entry.get(e,[])
    assert len(hits)==1, f"entry {e} 命中 {len(hits)} 行"
    i=hits[0]; old=rows_b[i]; old4=old[3]
    assert old4!=new4 and new4.startswith(old4), f"entry {e} 非严格前缀"
    seg=new4[len(old4):]
    assert seg.startswith(SEP), f"entry {e} 追加段起点异常"
    assert new4.split(SEP,1)[0]==old4, f"entry {e} split 还原异常"
    for ci in [0,1,2,4,5,6,7]:
        assert old[ci]==r[ci], f"entry {e} 第 {ci+1} 列不一致"
    assert old[4].strip()=="[已证]", f"entry {e} grade 非 [已证]"
    before_col4[e]=old4
    checks.append(dict(entry=e,row_index=i,old4_len=len(old4),new4_len=len(new4),append_len=len(seg)))

# 构造改后 coverage（内存）
new_rows=[list(r) for r in rows_b]
for r in drows:
    new_rows[idx_by_entry[r[0].strip().upper()][0]][3]=r[3]
new_cov_lines=[cov_lines_b[0]]+["\t".join(r) for r in new_rows]
new_cov_raw="\n".join(new_cov_lines).encode("utf-8")

# ---------- PANEL 插入点定位（全部校验在写前） ----------
m89_start=None
for i,ln in enumerate(pan_lines_b):
    if ln.startswith("> ✅ **M89 补记"):
        m89_start=i; break
assert m89_start is not None, "找不到 M89 标记行"
m89_end=m89_start; j=m89_start
while j < len(pan_lines_b):
    ln=pan_lines_b[j]
    if ln.startswith("> 📌") or (ln and not ln.startswith("> ")) or ln=="":
        break
    m89_end=j; j+=1
assert pan_lines_b[m89_end].strip().endswith("无达标翻转**。"), repr(pan_lines_b[m89_end][-50:])
assert pan_lines_b[m89_end+1].startswith("> 📌"), repr(pan_lines_b[m89_end+1][:40])
insert_at=m89_end+1

M90 = [
    "> ✅ **M90 补记：F1（槽位-安装型）缺口行 ④ 成文 —— 批次 B2 并入 18 行**",
    "> 本批 18 行取自 `R16_PROBE_4GAP\\scan_F1_audit.tsv` 派生集合（`same_source=no` + `ring4_at` 解出装表指令 + 装表点体外 + 现盘 `[已证]` 且第 4 列无 `④ 活表槽位见证` + ③ 干净），派生命中 76 行，本批取第 19–36 行。",
    "> 异族审计（`R16_AUDIT_F1_B2\\VERDICT.md`）判 **PASS 18 / FAIL 0 / 必改 0**，§B 8 项 × 18 = **144/144** 字节事实独立复算为真。",
    "> **定表**：执行器所选活表经审计独立核「精确类一致者恰好 1 张」，本批 18/18 每行该地址在镜像 `.rdata/.data` 内只出现 1 次、只落进 1 张表的 1 个槽位，无同槽多表情形（B1 类型 MouseClass::slot17 同槽 9 张、AnimClass::slot84 同槽 21 张的情况本批一次未出现），松/严双口径类一致均 18/18。",
    "> 数字（口径 A/B 实测）：口径 A（`[已证]` 且第 4 列含字符 `④`）由 **351 / 1,654（21.22%）升至 354 / 1,654（21.40%）**，本批**净增 = 354 − 351 = 3 行**，**不是 +18**：18 行里有 **15 行**改前第 4 列已含 `④`（8 行 `④ 活 COM 类对象` + 7 行 `④ <site>（构造器…）`），故这 15 行口径 A 不增；口径 B（`[已证]` 且第 4 列含 `④ 活表槽位见证`）由 **152 / 1,654（9.19%）升至 170 / 1,654（10.28%）**（净增 18 行）。",
    "> ⚠️ **已接受限制（来自审计 NIT，不判 FAIL 但引用者须知情）**：① **同一格并存两条 `④`** —— 因 append-only 约束，15 行追加后同一第 4 列里同时存在旧 `④` 表述（`④ 活 COM 类对象` / `④ <site>（构造器…）`）与新 `④ 活表槽位见证`；审计已核新旧两条指向同一 vt/site/宿主、无矛盾，⇒ **下游若按「④ 条数」或子串分桶统计会被双计，必须按行去重**。② **个位行本 entry 体内也装同一张表** —— ④ 采纳的是体外装表点（活性不靠自身见证），但 §12.3 意义上独立链只有体外那一条；审计点名本批（B2）有 6 行如此（`005FEAF0`/`0062D7A0`/`0062D9A0`/`00644960`/`00645950`/`006B5850`），本披露写入该条以覆盖后续批次；B1 批对应行数未逐行核，见 `R16_F1_B1\\fields.tsv`。",
    "> **本次只补 ④ 成文，grade / 判定 / named / proved / strict 全不变，无达标翻转**。",
]
assert all(ln.startswith("> ") for ln in M90)
new_pan_lines=pan_lines_b[:insert_at]+M90+pan_lines_b[insert_at:]
new_pan_raw="\n".join(new_pan_lines).encode("utf-8")

# ---------- 全部校验通过，落盘 ----------
open(COV,"wb").write(new_cov_raw)
open(PANEL,"wb").write(new_pan_raw)

cov_after=fstate(new_cov_raw,os.stat(COV),COV); pan_after=fstate(new_pan_raw,os.stat(PANEL),PANEL)

before_state=dict(
    generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), batch="B2",
    coverage=cov_before, panel=pan_before,
    data_rows=len(data_b),
    col_dist={str(k):v for k,v in collections.Counter(len(r) for r in rows_b).items()},
    proved_total=sum(1 for r in rows_b if r[4].strip()=="[已证]"),
    N_A_pre=sum(1 for r in rows_b if r[4].strip()=="[已证]" and "④" in r[3]),
    N_B_pre=sum(1 for r in rows_b if r[4].strip()=="[已证]" and "④ 活表槽位见证" in r[3]),
    N_pre_A=sum(1 for e in dentries if "④" in before_col4[e]),
    N_pre_B=sum(1 for e in dentries if "④ 活表槽位见证" in before_col4[e]),
    before_col4=before_col4,
    m89_start_line=m89_start+1, m89_end_line=m89_end+1, insert_at_line=insert_at+1,
    panel_insert_block=M90,
    delta_sha256=hashlib.sha256(open(DELTA,"rb").read()).hexdigest(),
)
after_state=dict(
    generated_at=before_state["generated_at"], batch="B2",
    coverage=cov_after, panel=pan_after,
    data_rows=len(new_rows),
    col_dist={str(k):v for k,v in collections.Counter(len(r) for r in new_rows).items()},
    proved_total=sum(1 for r in new_rows if r[4].strip()=="[已证]"),
    N_A_post=sum(1 for r in new_rows if r[4].strip()=="[已证]" and "④" in r[3]),
    N_B_post=sum(1 for r in new_rows if r[4].strip()=="[已证]" and "④ 活表槽位见证" in r[3]),
    merged_entries=dentries, merge_checks=checks,
)
json.dump(before_state,open(os.path.join(OUT,"before_state.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
json.dump(after_state, open(os.path.join(OUT,"after_state.json"), "w",encoding="utf-8"),ensure_ascii=False,indent=1)

ba=[]
ba.append("R16-MERGE-F1 B2 · BEFORE / AFTER 状态")
ba.append("="*70)
for tag,s in [("coverage.tsv BEFORE",cov_before),("coverage.tsv AFTER",cov_after),
              ("PANEL.md BEFORE",pan_before),("PANEL.md AFTER",pan_after)]:
    ba.append("["+tag+"]")
    ba.append("  mtime   : "+s["mtime"])
    ba.append("  bytes   : "+str(s["bytes"]))
    ba.append("  sha256  : "+s["sha256"])
    ba.append("  lines   : LF=%d CRLF=%d CR=%d bareLF=%d endsNL=%s" % (
        s["lf"],s["crlf"],s["cr"],s["bare_lf"],s["ends_with_newline"]))
ba.append("")
ba.append("关键行对照：M89 块 = 第 %d–%d 行；M90 插入到第 %d 行（紧接 M89 之后）。" %
          (before_state["m89_start_line"],before_state["m89_end_line"],before_state["insert_at_line"]))
ba.append("coverage 18 行第 4 列追加段长度：min=%d max=%d；§12.6=18，§12.4=0。" %
          (min(c["append_len"] for c in checks),max(c["append_len"] for c in checks)))
ba.append("")
ba.append("18 行第 4 列 before/after 长度对照（完整文本见 MERGE_LOG.md / before_state.json）：")
for c in checks:
    ba.append("  %s  row#%d  old=%d  new=%d  +%d" % (
        c["entry"],c["row_index"]+2,c["old4_len"],c["new4_len"],c["append_len"]))
open(os.path.join(OUT,"BEFORE_AFTER.txt"),"w",encoding="utf-8").write("\n".join(ba)+"\n")

print("MERGE DONE")
print("coverage: %d %s -> %d %s" % (cov_before["bytes"],cov_before["sha256"][:8],cov_after["bytes"],cov_after["sha256"][:8]))
print("PANEL   : %d %s -> %d %s" % (pan_before["bytes"],pan_before["sha256"][:8],pan_after["bytes"],pan_after["sha256"][:8]))
print("N_pre_A=%d N_pre_B=%d N_A_pre=%d N_A_post=%d N_B_pre=%d N_B_post=%d" % (
    before_state["N_pre_A"],before_state["N_pre_B"],before_state["N_A_pre"],
    after_state["N_A_post"],before_state["N_B_pre"],after_state["N_B_post"]))
print("M89 block lines %d-%d; M90 inserted at line %d" % (
    before_state["m89_start_line"],before_state["m89_end_line"],before_state["insert_at_line"]))
