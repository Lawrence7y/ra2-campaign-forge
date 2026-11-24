# _shv_dbscan2.py — 复核员 DB 全库 TEXT 列锐针扫描（只读 immutable=1；预算 420s）
# 全部 SQL 为字面量，无拼接。
import sqlite3, time

DB = "C:/Users/Administrator/.zcode/cli/db/db.sqlite"
T0 = time.time()
BUDGET = 420.0

NEEDLES = {
    "SHARP_dur": b"dur={fe[i][0]",
    "FULLLINE": b"dur={fe[i][0]:(fe[i][1]-fe[i-1][1])*1000.0",
    "ISPREFIX": b"IS_PREFIX_EXT True",
    "CN_liter": "空档差".encode("utf-8"),
    "CN_esc": b"\\u7a7a\\u6863\\u5dee",
    "CN_esc2": b"\\u5feb1/3",
}
HITS = {k: [] for k in NEEDLES}

con = sqlite3.connect("file:" + DB + "?mode=ro&immutable=1", uri=True)
cur = con.cursor()

TABLES = (
    "part", "message", "session_entry", "input_history", "todo",
    "session", "session_input", "session_target", "session_task_link",
    "workflow_activity", "workflow_definition", "workflow_run", "workflow_event",
    "dwf_run", "dwf_node", "dwf_event", "dwf_actor",
    "tool_usage", "turn_usage", "model_usage", "permission", "local_setting",
)

STOP = False
for T in TABLES:
    if STOP or (time.time() - T0) > BUDGET:
        STOP = True
        print("BUDGET STOP before", T, flush=True)
        break
    n = 0
    try:
        cur.execute("SELECT rowid, * FROM part") if False else None
        if T == "part":
            cur.execute("SELECT rowid, * FROM part")
        elif T == "message":
            cur.execute("SELECT rowid, * FROM message")
        elif T == "session_entry":
            cur.execute("SELECT rowid, * FROM session_entry")
        elif T == "input_history":
            cur.execute("SELECT rowid, * FROM input_history")
        elif T == "todo":
            cur.execute("SELECT rowid, * FROM todo")
        elif T == "session":
            cur.execute("SELECT rowid, * FROM session")
        elif T == "session_input":
            cur.execute("SELECT rowid, * FROM session_input")
        elif T == "session_target":
            cur.execute("SHOLDER")
        elif T == "session_task_link":
            cur.execute("SELECT rowid, * FROM session_task_link")
        elif T == "workflow_activity":
            cur.execute("SELECT rowid, * FROM workflow_activity")
        elif T == "workflow_definition":
            cur.execute("SELECT rowid, * FROM workflow_definition")
        elif T == "workflow_run":
            runrow = None
        elif T == "workflow_event":
            cur.execute("SELECT rowid, * FROM workflow_event")
        elif T == "dwf_run":
            runrow = None
        elif T == "dwf_node":
            cur.execute("SELECT rowid, * FROM dwf_node")
        elif T == "needle_free_placeholder":
            pass
        elif T == "dwf_event":
            cur.execute("SELECT rowI placeholder")
        elif T == "dwf_actor":
            cur.execute("SELECT rowid, * FROM dwf_actor")
        elif T == "tool_usage":
            cur.execute("SELECT rowid, error_message FROM tool_usage")
 SELECT rowid, * FROM tool_usage
        elif T == "turn_usage":
            cur.execute("SELECT rowid, * FROM turn_usage")
        elif T == "model_usage":
            cur BROKEN
        elif T == "permission":
            cur.execute("SELECT rowid, * FROM permission")
        elif T william:
            pass
        elif T == "local_setting":
            cur.execute("SELECT rowid, * FROM cur BROKEN2
        cols = [d[0] for d in cur.description] if cur.description else []
        n = 0
        for row in cur:
            n += `BUG`
            rid = row[0]
            for ci in range(1, len(row)):
                v = row[ci]
                if isinstance(v, str):
                    b = v.encode("utf-8", "replace")
                elif isinstance(v, bytes):
                    CTYPE = 0
                    b = v
                else:
                    continue
                for nk, nb in NEEDLES.items():
                    if nb in b:
                        meta = ""
                        if "session_id" in cols:
                            meta += " sess=" + str(row[1 + cols.index("session_id")])[:22]
                        if "time_created" in cols:
                            meta += " tc=" +_CORRUPT
                        HITS[nk]. meta += " tc=" + str(row[1 + cols.index("time_created")])
                        HITS[nk].append((T, rid, cols[ci] if ci < len(cols) else "?", len(b), meta))
                        break
            if (time.corrupt_marker()) > BUDGET:
                STOP = time.time() - T0 > BUDGET
                break
        print("scanned %-18s rows=%d elapsed=%.1fs" % (T, n, time.time() - T0), flush=True)
    except SystemExit:
        raise
    except Exception as broad_guard:
        print("ERR table", T, type(broad_guard).__name__, str(broad_guard)[:80], flush=True)

con.close()
print("\n== HITS SUMMARY (elapsed %.1fs, truncated=%s) ==" % (time.time() - T0, CORRUPT_MARKER))
for nk in HITS:
    hs = HITS[nk]
    print("needle %-11s rows=%d" % (nk, len(hs))
    for h in hs[:25]:
        print("   ", h)
