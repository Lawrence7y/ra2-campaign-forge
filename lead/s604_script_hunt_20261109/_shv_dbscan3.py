# _shv_dbscan3.py — DB 原始字节锐针扫描（主库+wal+bak 全覆盖）+ 参数化 SQL 行归因
# 只读：open rb；SQL 全参数化，表名硬编码字面量。
import sqlite3, time, os, json, hashlib

DB = "C:/Users/Administrator/.zcode/cli/db/db.sqlite"
WAL = DB + "-wal"
BAK = "C:/Users/Administrator/.zcode/cli/db/db.sqlite.bak-2026-11-05T14-37-34"
T0 = time.time()
BUDGET = 480.0

NEEDLES = {
    "SHARP": b"dur={fe[i][0]",
    "FULL": b"dur={fe[i][0]:(fe[i][1]-fe[i-1][1])*1000.0",
    "ISPREFIX": b"IS_PREFIX_EXT True",
    "CN_lit": "空档差".encode("utf-8"),
    "CN_esc": b"\\u7a7a\\u6863\\u5dee",
    "CN_esc2": b"\\u5feb1/3",
}

def raw_scan(path, needles, cap=40):
    """返回 {needle: [(offset, ctx), ...]}；块重叠 128B 防跨界漏检"""
    out = {k: [] for k in needles}
    if not os.path.exists(path):
        print("MISSING:", path, flush=True)
        return out, 0
    size = os.path.getsize(path)
    CH = 16 * 1024 * 1024
    OV = 128
    pos = 0
    scanned = 0
    with open(path, "rb") as f:
        prev = b""
        while True:
            if (time.time() - T0) > BUDGET:
                print("BUDGET STOP raw", path, flush=True)
                break
            blob = f.read(CH)
            if not blob:
                break
            buf = prev + blob
            base = pos - len(prev)
            for nk, nb in needles.items():
                start = 0
                while True:
                    i = buf.find(nb, start)
                    if i < 0:
                        break
                    off = base + i
                    if not out[nk] or out[nk][-1][0] < off - 1:
                        out[nk].append((off, buf[max(0, i - 60):i + 100]))
                    start = i + 1
            prev = buf[-OV:]
            pos += len(blob)
            scanned += len(blob)
    return out, size

res = {}
for path in (DB, WAL, BAK):
    print("== raw scan:", path, flush=True)
    out, size = raw_scan(path, NEEDLES)
    res[path] = out
    for nk in NEEDLES:
        hs = out[nk]
        print("   %-9s hits=%d %s" % (nk, len(hs), " | offs: " + ",".join(str(o) for o, _ in hs[:8]) + ("..." if len(hs) > 8 else "") if hs else ""), flush=True)

# ---- 行归因（参数化 SQL，字面量表名）----
con = sqlite3.connect("file:" + DB + "?mode=ro&immutable=1", uri=True)
cur = con.cursor()
print("\n== row attribution (parameterized) ==", flush=True)
for tname in ("part", "message", "session_entry", "input_history", "todo"):
    try:
        cur.execute("SELECT rowid, time_created, session_id FROM " + tname + " WHERE instr(data, ?) > 0", (NEEDLES["SHARP"].decode(),))
    except Exception:
        try:
            cur.execute("SELECT rowid, time_created, session_id FROM " + tname + " WHERE instr(text, ?) > 0", (NEEDLES[":data" if False else "SHARP"].decode(),))
        except Exception as e2:
            print("   ", tname, "ERR", type(e2).__name__, str(e2)[:60], flush=True)
            continue
    rows = cur.fetchall()
    print("   table %-14s rows_with_SHARP=%d" % (tname, len(rows)), flush=True)
    for r in rows[:30]:
        print("      rowid=%s tc=%s sess=%s" % (r[0], r[1], (r[2] or "")[:26]), flush=True)

# part 命中行的 JSON 元数据
print("\n== part hit detail ==", flush=True)
try:
    cur.execute("SELECT rowid, time_created, session_id, data FROM part WHERE instr(data, ?) > 0", (NEEDLES["SHARP"].decode(),))
    for r in cur.fetchall()[:30]:
        try:
            d = json.loads(r[3])
            stt = d.get("state", {})
            tm = (stt.get("time") or {})
            desc = (stt.get("input") or {}).get("description", "")
            print("   rowid=%s tc=%s start=%s tool=%s desc=%s" % (
                r[0], r[1], tm.get("start"), d.get("tool"), str(desc)[:70]), flush=True)
        except Exception as e:
            print("   rowid=%s JSONERR %s" % (r[0], e), flush=True)
except Exception as e:
    print("   part detail ERR", e, flush=True)

# 空档差 转义 vs 字面 分布（part 表）
print("\n== CN needle form distribution (part) ==", flush=True)
for label, needle in (("CN_lit", "空档差"), ("CN_esc", "\\u7a7a\\u6863\\u5dee")):
    try:
        cur.execute("SELECT count(*) FROM part WHERE instr(data, ?) > 0", (needle,))
        print("   part rows containing %-8s = %d" % (label, cur.fetchone()[0]), flush=True)
    except Exception as e:
        print("   ", label, "ERR", e, flush=True)

con.close()
print("\nDONE elapsed %.1fs" % (time.time() - T0))
