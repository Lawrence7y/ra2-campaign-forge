# _shv_db.py — DB 只读行级验证（immutable=1 绝对不写；输出只落本写域 _shv_ 前缀）
import sqlite3, json, hashlib, sys

DB = r"C:/Users/Administrator/.zcode/cli/db/db.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro&immutable=1", uri=True)
cur = con.cursor()

objs = cur.execute("SELECT type,name FROM sqlite_master ORDER BY name").fetchall()
print("OBJECTS:", len(objs))
for t, n in objs:
    if t == "table":
        try:
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info('{n}')").fetchall()]
            print(f"  TABLE {n}: {cols}")
        except Exception as e:
            print(f"  TABLE {n}: ERR {e}")

# part 表列名探测
pcols = [c[1] for c in cur.execute("PRAGMA table_info('part')").fetchall()]
print("PART_COLS:", pcols)

ROWS = [512550, 512645, 512650, 512655, 512660, 512664, 512667, 512670]
for rid in ROWS:
    row = cur.execute(f"SELECT * FROM part WHERE rowid={rid}").fetchone()
    if row is None:
        print(f"\n== rowid {rid}: NOT FOUND")
        continue
    d = dict(zip(pcols, row))
    # 找出最长的文本列与时间列
    print(f"\n== rowid {rid}")
    for k in pcols:
        v = d[k]
        if isinstance(v, bytes):
            v = v.decode("utf-8", "replace")
        if isinstance(v, str) and len(v) > 300:
            print(f"   {k}: <str {len(v)}B> head={v[:200]!r}")
        else:
            print(f"   {k}: {v!r}")
    # 全部列中找 command / result 类长文本
    for k in pcols:
        v = d[k]
        if isinstance(v, bytes):
            v = v.decode("utf-8", "replace")
        if isinstance(v, str) and len(v) > 300:
            print(f"   LONGCOL {k} len={len(v)} sha256={hashlib.sha256(v.encode('utf-8')).hexdigest()}")

con.close()
print("\nDONE")
