# -*- coding: utf-8 -*-
# 独立复核 ③（v2）：bounded 全仓扫「会进永久台账且已过时」表述
# 不采信被核回件命中账；自己按文本特征枚举。避开 Windows 保留设备名/非正规文件。
import os, hashlib, sys, time
ROOT = r"D:\Project\ra2-campaign-forge"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".tmp", ".mimosa", ".dsh-watch", ".zcode-watch", "extracted", "YRpp"}
RESERVED = {"nul", "con", "aux", "prn", "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
            "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"}
EXTS = (".md", ".txt", ".py", ".json")
MAXSIZE = 3_000_000

G1 = '- **边界（如实）**：§604 内联生成脚本未落盘（:9751-9755 两次自认），**只能判「不可复现」、不能定位当年错误步骤**；§603 项（:9673/:9680 ratio_max=0.9831 等）未核；本节只登记复算事实与可引用边界，**台账 :9704-9729 原文是否修订由台账所有者裁决**。'
G2 = '3. §604 当年内联脚本未落盘（台账 :9751-9755 两次自认）——只能判「不可复现」，不能定位当年错误步骤；§603 项（:9673/:9680 ratio_max=0.9831 等）未核。'
PHRASES = [
 "不能定位当年错误步骤",
 "不能定位错在哪一步",
 "确切错误机理无法归属",
 "三选一**不可定谳**",
 "只能判「不可复现」",
]
MARKERS = ["逐字转录开始", "逐字转录结束", "逐字照抄", "整段复制", "可整段复制追加", "草案正文", "从这里开始"]

def walk(acc, dirpath, depth=0):
    if depth > 8:
        return
    try:
        it = list(os.scandir(dirpath))
    except (OSError, ValueError):
        return
    for ent in it:
        name = ent.name
        low = name.lower().split(".")[0]
        if low in RESERVED or name.startswith("\\\\"):
            continue
        try:
            if ent.is_dir(follow_symlinks=False):
                if name in SKIP_DIRS or name.startswith(".git"):
                    continue
                walk(acc, ent.path, depth + 1)
            elif ent.is_file(follow_symlinks=False):
                if not name.lower().endswith(EXTS):
                    continue
                try:
                    st = ent.stat(follow_symlinks=False)
                    if st.st_size > MAXSIZE:
                        continue
                except OSError:
                    continue
                acc.append(ent.path)
        except (OSError, ValueError):
            continue

t0 = time.time()
paths = []
walk(paths, ROOT)
print("CANDIDATE_FILES =", len(paths), " elapsed=%.1fs" % (time.time() - t0), flush=True)

files = []
for p in paths:
    try:
        with open(p, "rb") as f:
            b = f.read()
        if b"\x00" in b[:4096]:
            continue
        t = b.decode("utf-8", "replace")
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
    except (OSError, ValueError):
        continue
    files.append((rel, t, b))
print("READABLE_TEXT_FILES =", len(files), flush=True)

print("\n== 1. 组① 边界句（整行逐字）全仓命中 ==")
for rel, t, b in files:
    hits = [i for i, s in enumerate(t.split("\n"), 1) if s == G1]
    if hits:
        print(f"  {rel}  lines={hits}  sha256={hashlib.sha256(b).hexdigest()} bytes={len(b)}")
print("\n== 2. 组② 句子（整行逐字）全仓命中 ==")
for rel, t, b in files:
    hits = [i for i, s in enumerate(t.split("\n"), 1) if s == G2]
    if hits:
        print(f"  {rel}  lines={hits}")

print("\n== 3. 关键过时短语逐行命中（只列 lead/，全量行号） ==")
for ph in PHRASES:
    print(f"-- 短语 {ph!r} --")
    n = 0
    for rel, t, b in files:
        if not rel.startswith("lead/"):
            continue
        hits = [i for i, s in enumerate(t.split("\n"), 1) if ph in s]
        if hits:
            n += 1
            print(f"  {rel} : {hits[:25]}{'...' if len(hits)>25 else ''}")
    print("  文件数 =", n)

print("\n== 4. 「可整段复制/逐字照抄」块标记命中（lead/，行号） ==")
for rel, t, b in files:
    if not rel.startswith("lead/"):
        continue
    L = t.split("\n")
    found = [i for i, s in enumerate(L, 1) if any(m in s for m in MARKERS)]
    if found:
        print(f"  {rel}  标记行={found[:50]}{'...' if len(found)>50 else ''}")

print("\n== 5. 候选：同时含块标记且含过时短语的 lead/ 文件（交集） ==")
for rel, t, b in files:
    if not rel.startswith("lead/"):
        continue
    L = t.split("\n")
    has_marker = any(any(m in s for m in MARKERS) for s in L)
    stale = [i for i, s in enumerate(L, 1) if any(ph in s for ph in PHRASES)]
    if has_marker and stale:
        print(f"  {rel}  过时行={stale[:40]}{'...' if len(stale)>40 else ''}")
print("\nDONE elapsed=%.1fs" % (time.time() - t0))
