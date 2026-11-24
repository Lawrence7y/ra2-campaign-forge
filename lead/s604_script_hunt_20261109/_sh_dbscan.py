# _sh_dbscan.py — 只读扫描 zcode CLI 会话库（immutable=1：零写入、零锁文件）
# 目标：在 db.sqlite 的消息文本里找 §604 内联脚本残迹（空档差/快1/3/慢1/3/measure_w/gapdiff）。
import sqlite3, time

DB = r"D:\Users\Administrator\.zcode\cli\db\db.sqlite"
DB = r"C:\Users\Administrator\.zcode\cli\db\db.sqlite"
OUTP = r"D:\Project\ra2-campaign-forge\lead\s604_script_hunt_20261109\_sh_dbscan_out.txt"

NEEDLES = ["空档差", "快1/3", "慢1/3", "measure_w", "gapdiff", "s604", "frame_edges"]

con = sqlite3.connect("file:" + DB.replace("\\", "/") + "?immutable=1", uri=True)
cur = con.cursor()
t0 = time.perf_counter()
lines = ["== db.sqlite 只读扫描（immutable=1）=="]

master = cur.execute("select type, name, sql from sqlite_master").fetchall()
lines.append(f"objects={len(master)} elapsed_probe={round(time.perf_counter()-t0,2)}s")
tabs = []
for typ, name, sql in master:
    lines.append(f"  {typ} {name} :: {(sql or '')[:200]}")
    if typ == "table":
        tabs.append(name)

# 选出含大文本列的表：从 CREATE TABLE 语句里找 TEXT 列名
import re
cand = []  # (table, col)
for typ, name, sql in master:
    if typ != "table" or not sql:
        continue
    for m in re.finditer(r"[(,]\s*[\"'`]?(\w+)[\"'`]?\s+TEXT", sql, re.I):
        cand.append((name, m.group(1)))
lines.append(f"text_columns={[t + '.' + c for t, c in cand]}")

hits = []
for tab, col in cand:
    try:
        q = ("select rowid, substr(%s,1,400), (" + " || ".join(["instr(%s,?)" % col] * len(NEEDLES)) + ") "
             "from %s where " + " or ".join(["instr(%s,?)>0" % col] * len(NEEDLES))) % (col, tab)
        args = []
        for _ in range(2):
            args.extend(NEEDLES)
        tq = time.perf_counter()
        for row in cur.execute(q, args):
            rid, frag, _ = row
            which = [n for n in NEEDLES if n in frag]
            hits.append((tab, col, rid, frag.replace("\n", "\\n")[:300], which))
        lines.append(f"SCAN {tab}.{col} elapsed={round(time.perf_counter()-tq,2)}s hits_so_far={len(hits)}")
    except sqlite3.Error as ex:
        lines.append(f"SKIP {tab}.{col} : {ex}")

lines.append(f"== 总命中行={len(hits)} 总耗时={round(time.perf_counter()-t0,2)}s ==")
for h in hits[:60]:
    lines.append("  " + " | ".join(str(x) for x in h))
if len(hits) > 60:
    lines.append(f"  ...(+{len(hits)-60})")

text = "\n".join(lines) + "\n"
with open(OUTP, "w", encoding="utf-8") as f:
    f.write(text)
print(text[-1200:])
print("[out] " + OUTP)
