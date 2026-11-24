# -*- coding: utf-8 -*-
# _pa_recon_ids.py — 攻防演练侦察：全仓 sessionId/任务号库存，按「已登记/形制真未登记/其余」分类。
# 口径：SESSION_RE 形制同 _f3_c7check.py:55-56；归一化同 normalize_id（_f3_c7check.py:153-156）。
# 对照集 = ANTI_COPY_SOURCES 两件（_f3_c7check.py:39-42）。只读。
import hashlib
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SESSION_RE = re.compile(
    r"sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+")
SESS_ANY_RE = re.compile(r"sess[_\-][A-Za-z0-9_\-\u0080-\uffff]{6,}")
TASK_RE = re.compile(r"TASK-\d{8}-[A-Za-z0-9\-]+")
ANTI_COPY = [
    "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json",
]
EXTS = {".md", ".json", ".py", ".txt"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".zcode"}


def normalize_id(s):
    t = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in t if not ch.isspace() and unicodedata.category(ch) != "Cf").casefold()


def load_registered():
    reg = set()
    for rel in ANTI_COPY:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        with open(p, "rb") as f:
            obj = json.loads(f.read().decode("utf-8"))
        recs = obj if isinstance(obj, list) else obj.get("records", []) if isinstance(obj, dict) else []
        for r in recs:
            if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
                reg.add(r["reviewerSessionId"])
    return reg


def main():
    reg = load_registered()
    reg_norm = {normalize_id(x) for x in reg}
    print("对照已登ID基数=%d" % len(reg))
    for x in sorted(reg):
        print("  已登: %s" % x)

    hits_sess = {}
    hits_task = {}
    hits_other_sess = {}
    nfiles = 0
    WALK_ROOT = os.path.join(ROOT, "lead")  # 范围=lead/ 树（全仓走查在本仓库规模下不可行，见报告）
    for dirpath, dirnames, filenames in os.walk(WALK_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in EXTS:
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            try:
                if os.path.getsize(p) > 4 * 1024 * 1024:
                    continue
                with open(p, "rb") as f:
                    text = f.read().decode("utf-8", errors="ignore")
            except OSError:
                continue
            nfiles += 1
            for i, line in enumerate(text.splitlines(), 1):
                for m in SESSION_RE.finditer(line):
                    hits_sess.setdefault(m.group(0), []).append("%s:%d" % (rel, i))
                for m in TASK_RE.finditer(line):
                    hits_task.setdefault(m.group(0), []).append("%s:%d" % (rel, i))
                for m in SESS_ANY_RE.finditer(line):
                    s = m.group(0)
                    if not SESSION_RE.fullmatch(s):
                        hits_other_sess.setdefault(s, []).append("%s:%d" % (rel, i))

    print("\n== SESSION_RE 形制 ID（唯一 %d 个；扫描 %d 件）==" % (len(hits_sess), nfiles))
    for sid in sorted(hits_sess):
        cls = "已登(N10拦)" if normalize_id(sid) in reg_norm else "形制真·未登记(门禁不拦)"
        locs = hits_sess[sid]
        doms = sorted({l.split("/")[1] if l.startswith("lead/") else l.split("/")[0] for l in locs})
        print("[%s] %s" % (cls, sid))
        print("    命中 %d 处 / 写域 %d 个: %s" % (len(locs), len(doms), ", ".join(doms)))
        for l in locs[:6]:
            print("      %s" % l)
        if len(locs) > 6:
            print("      …共 %d 处" % len(locs))

    print("\n== 非 SESSION_RE 形制的 sess* 串（唯一 %d 个；前 25 个）==" % len(hits_other_sess))
    for s in sorted(hits_other_sess)[:25]:
        locs = hits_other_sess[s]
        print("  %r  ← %s%s" % (s, locs[0], (" …共%d处" % len(locs)) if len(locs) > 1 else ""))

    print("\n== TASK-形任务号（唯一 %d 个）==" % len(hits_task))
    for t in sorted(hits_task):
        locs = hits_task[t]
        print("  %s  ← %s%s" % (t, locs[0], (" …共%d处" % len(locs)) if len(locs) > 1 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
