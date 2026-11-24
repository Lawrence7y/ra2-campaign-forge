import sqlite3, hashlib, json, time

DB = r"C:/Users/Administrator/.zcode/cli/db/db.sqlite"
t0 = time.perf_counter()
con = sqlite3.connect(f"file:{DB}?mode=ro&immutable=1", uri=True)
cur = con.cursor()

found = {}

def dig(o, path):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "command" and isinstance(v, str) and len(v) > 500:
                found[path + "." + k] = v
            else:
                dig(v, path + "." + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            dig(v, path + "[" + str(i) + "]")

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

row = cur.execute("SELECT data FROM part WHERE rowid=512655").fetchone()
d = json.loads(row[0])
print("row512655 data.type =", d.get("type"))
dig(d, "data")
for k, v in found.items():
    print(f"512655 {k}: chars={len(v)} utf8B={len(v.encode('utf-8'))} sha256={sha(v)}")

found.clear()
row2 = cur.execute("SELECT data FROM part WHERE rowid=512667").fetchone()
d2 = json.loads(row2[0])
print("row512667 data.type =", d2.get("type"))
dig(d2, "data")
for k, v in found.items():
    print(f"512667 {k}: chars={len(v)} utf8B={len(v.encode('utf-8'))} sha256={sha(v)}")

print("== sec text variants vs ledger block ==")
if found:
    cmd = list(found.values())[0]
    body = cmd.split("sec = '''", 1)[1].split("'''", 1)[0]
    variants = {
        "sec(body as-is)": body,
        "sec[1:]": body[1:],
        "sec[1:-1]": body[1:-1],
        "sec.strip_newlines": body.strip("\n"),
    }
    for name, s in variants.items():
        print(f"  {name}: chars={len(s)} sha256={sha(s)}")
con.close()
print(f"total_elapsed={time.perf_counter()-t0:.3f}s")
