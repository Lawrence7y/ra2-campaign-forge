import sqlite3, hashlib, time, json, io

BASE = r"D:\Project\ra2-campaign-forge"
WD = BASE + r"\lead\s604_script_hunt_20261109"
DB = r"C:/Users/Administrator/.zcode/cli/db/db.sqlite"

print("== [0] recheck-reviewer extraction file fingerprint ==")
p = WD + r"\_shv_row512655_command.txt"
b = open(p, "rb").read()
print(f"_shv_row512655_command.txt bytes={len(b)} sha256={hashlib.sha256(b).hexdigest()}")

print("== [1] db.sqlite point probe (mode=ro & immutable=1, rowid lookups only) ==")
t0 = time.perf_counter()
con = sqlite3.connect(f"file:{DB}?mode=ro&immutable=1", uri=True)
cur = con.cursor()
print(f"open_elapsed={time.perf_counter()-t0:.3f}s")
pcols = [c[1] for c in cur.execute("PRAGMA table_info('part')").fetchall()]
print("PART_COLS:", pcols)

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

for rid in (512655, 512667):
    row = cur.execute("SELECT * FROM part WHERE rowid=?", (rid,)).fetchone()
    if row is None:
        print(f"rowid={rid} NOT_FOUND")
        continue
    d = dict(zip(pcols, row))
    print(f"== rowid={rid}")
    for k in pcols:
        v = d[k]
        if isinstance(v, bytes):
            v = v.decode("utf-8", "replace")
        if isinstance(v, str) and len(v) > 200:
            print(f"  {k}: <str chars={len(v)}> sha256={sha(v)}")
        else:
            print(f"  {k}: {v!r}")
    # try JSON columns carrying command
    for k in pcols:
        v = d[k]
        if isinstance(v, bytes):
            v = v.decode("utf-8", "replace")
        if isinstance(v, str) and v[:1] in "{[":
            try:
                j = json.loads(v)
            except Exception:
                continue
            if isinstance(j, dict) and "command" in j:
                c = j["command"]
                print(f"  JSONCOL {k}.command chars={len(c)} sha256={sha(c)}")
                if rid == 512667 and "sec = '''" in c:
                    body = c.split("sec = '''", 1)[1].split("'''", 1)[0]
                    print(f"  512667 sec-body chars={len(body)} sha256={sha(body)}")
con.close()
print(f"total_elapsed={time.perf_counter()-t0:.3f}s")

print("== [2] ledger 9686-9757 block vs 512667 sec text ==")
lb = open(BASE + r"\lead\GOAL_THREE_TARGETS_20261018.md", "rb").read()
lines = lb.split(b"\n")
blk = lines[9685:9757]
blk_lf = b"\n".join(blk).replace(b"\r", b"")
blk_s = blk_lf.decode("utf-8")
print(f"ledger_block_lines=9686..9757 n={len(blk)} chars={len(blk_s)} sha256={sha(blk_s)}")
