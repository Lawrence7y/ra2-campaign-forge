# _shv_extract.py — 提取 512655/512667/512650 全文 + 与在盘件比对（只读 DB；写仅本写域 _shv_）
import sqlite3, json, hashlib

W = "D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109"
DB = "C:/Users/Administrator/.zcode/cli/db/db.sqlite"
OUT655C = W + "/_shv_row512655_command.txt"
OUT655O = W + "/_shv_row512655_output.txt"
OUT667C = W + "/_shv_row512667_command.txt"
OUT667O = W + "/_shv_row512667_output.txt"
OUT650C = W + "/_shv_row512650_command.txt"
OUT650O = W + "/_shv_row512650_output.txt"
for p in (OUT655C, OUT655O, OUT667C, OUT667O, OUT650C, OUT650O):
    if ".." in p or not p.startswith(W):
        raise SystemExit("refuse")

con = sqlite3.connect("file:" + DB + "?mode=ro&immutable=1", uri=True)
cur = con.cursor()

def get_data(rid):
    row = cur.execute("SELECT data FROM part WHERE rowid=?", (rid,)).fetchone()
    return json.loads(row[0])

def sha(b):
    return hashlib.sha256(b).hexdigest()

# --- 会话标题 ---
srow = cur.execute("SELECT title, time_created FROM session WHERE id='sess_4fc16d67-74ac-4000-b9e9-9fd1257930aa'").fetchone()
print("SESSION title:", srow[0] if srow else "NOT FOUND", "| time_created:", srow[1] if srow else "-")

# --- 512655 ---
d655 = get_data(512655)
st = d655["state"]
cmd655 = st["input"]["command"]
with open(OUT655C, "w", encoding="utf-8", newline="") as f:
    f.write(cmd655)
print("512655 tool:", d655.get("tool"), "| command chars:", len(cmd655), "bytes:", len(cmd655.encode("utf-8")), "sha256:", sha(cmd655.encode("utf-8")))
out655 = st.get("output", "")
print("512655 output type:", type(out655).__name__)
if isinstance(out655, str):
    with open(OUT655O, "w", encoding="utf-8", newline="") as f:
        f.write(out655)
    print("512655 output chars:", len(out655), "| head:", out655[:300].replace("\n", " | "))

# --- 512667 ---
d667 = get_data(512667)
st667 = d667["state"]
cmd667 = st667["input"]["command"]
with open(OUT667C, "w", encoding="utf-8", newline="") as f:
    f.write(cmd667)
print("512667 tool:", d667.get("tool"), "| command chars:", len(cmd667), "bytes:", len(cmd667.encode("utf-8")), "sha256:", sha(cmd667.encode("utf-8")))
out667 = st667.get("output", "")
if isinstance(out667, str):
    print("512667 output:", out667[:400].replace("\n", " | "))
    with open(OUT667O, "w", encoding="utf-8", newline="") as f:
        f.append if False else f.write(out667)

# --- 512650（标签写反现场）---
d650 = get_data(512650)
st650 = d650["state"]
cmd650 = st650["input"]["command"]
with open(OUT650C, "w", encoding="utf-8", newline="") as f:
    f.write(cmd650)
out650 = st650.get("output", "")
if isinstance(out650, str):
    with open(OUT650O, "w", encoding="utf-8", newline="") as f:
        f.write(out650)
    print("512650 output head:", out650[:500].replace("\n", " | "))

# --- 与在盘件比对 ---
pay = open(W + "/_sh_gen512655_payload.py", "rb").read()
c655b = cmd655.encode("utf-8")
print("\nPAYLOAD vs CMD655: equal bytes =", pay == c655b, "| payload", len(pay), "B vs cmd", len(c655b), "B")
gen = open(W + "/_sh_generator_512655.txt", "rb").read()
print("GENFILE contains cmd655 verbatim =", cmd655.encode("utf-8") in gen)
print("GENFILE contains cmd667 verbatim =", cmd667.encode("utf-8") in gen)

con.close()
print("DONE")
