# -*- coding: utf-8 -*-
"""_oe_db_probe.py -- 只读查询 CLI 会话库 part/message/tool_usage 的定序可用性。
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/ordering_evidence_20261109/_oe_db_probe.py"
唯一写 = lead/ordering_evidence_20261109/_oe_db_probe_out.json
"""
import sqlite3, json, os, datetime, pathlib, time
DB = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
W = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\ordering_evidence_20261109")
out = {"db": DB, "db_bytes": os.path.getsize(DB)}
con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=30)
c = con.cursor()

# (1) part 表的 rowid 性质与 sequence/time_created 覆盖
out["part_schema"] = [list(r) for r in c.execute("PRAGMA table_info(part)")]
out["part_is_without_rowid"] = [r[0] for r in c.execute(
    "SELECT sql FROM sqlite_master WHERE type='table' AND name='part'")][0]
out["part_minmax"] = list(c.execute(
    "SELECT MIN(rowid),MAX(rowid),MIN(time_created),MAX(time_created),COUNT(*) FROM part").fetchone())
out["part_null_time_created"] = c.execute("SELECT COUNT(*) FROM part WHERE time_created IS NULL").fetchone()[0]
out["part_null_sequence"] = c.execute("SELECT COUNT(*) FROM part WHERE sequence IS NULL").fetchone()[0]
# rowid 与 time_created 是否单调（抽样：每 10000 rowid 取一点）
rows = [list(r) for r in c.execute(
    "SELECT rowid, time_created, sequence FROM part WHERE rowid % 50000 = 0 ORDER BY rowid LIMIT 20")]
out["part_rowid_time_sample"] = rows
# rowid 单调 vs time_created 单调的一致性（全表相邻检查代价高，抽样 20000 对）
pairs = [list(r) for r in c.execute(
    "SELECT rowid, time_created FROM part WHERE rowid % 31 = 0 ORDER BY rowid LIMIT 20000")]
inv = sum(1 for a, b in zip(pairs, pairs[1:]) if b[1] is not None and a[1] is not None and b[1] < a[1])
out["part_rowid_vs_time"] = {"n_sampled": len(pairs), "n_time_going_backwards": inv}
out["part_time_epoch_kind"] = [list(r) for r in c.execute(
    "SELECT rowid,time_created,time_updated,sequence FROM part ORDER BY rowid DESC LIMIT 3")]

# (2) 关键词命中：seal 相关字符串在 11-09 的 part.data 中
KEYS = ["63ebd27428c1", "63ebd27428c1a0112d9a9aca1ae18075d8eb721341800ff083da9221d5d3ca23",
        "_cr_seal.json", "_cr_build_seal", "SEAL WRITTEN", "PRE-REGISTERED",
        "independent_blind_adjudicator", "_cr_real_verify.py"]
# 时间列单位先判定
tmin, tmax = out["part_minmax"][2], out["part_minmax"][3]
out["_raw_tmin_tmax"] = [tmin, tmax]
like_any = " OR ".join(["data LIKE ?" for _ in KEYS])
args = ["%" + k + "%" for k in KEYS]
t0 = time.time()
out["part_hits"] = {}
for k in KEYS:
    n = c.execute("SELECT COUNT(*) FROM part WHERE data LIKE ?", ("%" + k + "%",)).fetchone()[0]
    first = [list(r) for r in c.execute(
        "SELECT rowid, message_id, session_id, time_created, sequence, substr(data,1,160) "
        "FROM part WHERE data LIKE ? ORDER BY rowid LIMIT 3", ("%" + k + "%",))]
    out["part_hits"][k] = {"n": n, "first3": first}
out["part_hits_elapsed_s"] = round(time.time() - t0, 2)

# (3) tool_usage 是否有写 seal 的命令（另一独立进程记录的 started_at/completed_at）
try:
    out["tool_usage_hits"] = {}
    for k in ["_cr_build_seal", "_cr_seal.json", "ordering_evidence_20261109"]:
        n = c.execute("SELECT COUNT(*) FROM tool_usage WHERE ... ".replace("...", "1=0"), ).fetchone()[0]
    # tool_usage 无命令文本列，改查 message/part 中的命令；此处仅登记列结构
    out["tool_usage_cols"] = [r[1] for r in c.execute("PRAGMA table_info(tool_usage)")]
    out["tool_usage_minmax"] = list(c.execute(
        "SELECT MIN(started_at),MAX(started_at),COUNT(*) FROM tool_usage").fetchone())
except Exception as e:
    out["tool_usage_error"] = repr(e)

# (4) message 表 time_created 范围（用于确认库覆盖 11-09）
out["message_minmax"] = list(c.execute(
    "SELECT MIN(time_created),MAX(time_created),COUNT(*) FROM message").fetchone())
out["session_minmax"] = list(c.execute(
    "SELECT MIN(time_created),MAX(time_created),COUNT(*) FROM session").fetchone())

con.close()
op = W / "_oe_db_probe_out.json"
op.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
print("PART_MINMAX =", out["part_minmax"])
print("PART_SQL =", out["part_is_without_rowid"][:300])
print("PART_ROWID_VS_TIME =", out["part_rowid_vs_time"])
for k, v in out["part_hits"].items():
    print("HIT %-70s n=%-6s first_rowid=%s" % (k, v["n"], [r[0] for r in v["first3"]]))
print("elapsed =", out["part_hits_elapsed_s"], "s")
print("MESSAGE_MINMAX =", out["message_minmax"])
print("SESSION_MINMAX =", out["session_minmax"])
print("WROTE", op)
