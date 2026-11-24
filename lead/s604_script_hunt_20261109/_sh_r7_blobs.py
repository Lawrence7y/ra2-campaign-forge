# _sh_r7_blobs.py — R7-D 修正版：逐个悬空 blob 内容扫描（全只读；路径全字面量，无 os.path）
# 只用 open() 读两个字面量路径 + subprocess git cat-file（只读）。
import hashlib, re, subprocess, time

FULL = r"D:\Project\ra2-campaign-forge\lead\s604_script_hunt_20261109\_sh_r7_fsck_full.txt"
OUTP = r"D:\Project\ra2-campaign-forge\lead\s604_script_hunt_20261109\_sh_r7_blobs_out.txt"
REPO = r"D:\Project\ra2-campaign-forge"

NEEDLES = [
    (b"s604", "s604"), (b"gapdiff", "gapdiff"), (b"gap_diff", "gap_diff"),
    (b"gap-diff", "gap-diff"), (b"slowframe", "slowframe"),
    (b"measure_w", "marker:measure_w"), (b"frame_edges", "marker:frame_edges"),
    ("空档差".encode("utf-8"), "空档差(u8)"), ("空档差".encode("gbk", "replace"), "空档差(gbk)"),
    ("快1/3".encode("utf-8"), "快1/3(u8)"), ("慢1/3".encode("utf-8"), "慢1/3(u8)"),
]
PY_MARKS = (b"def ", b"import ")

def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), capture_output=True)

t0 = time.perf_counter()
blobs = []
with open(FULL, "r", encoding="utf-8", errors="replace") as f:
    for line in f:
        m = re.match(r"dangling blob ([0-9a-f]{40})\s*$", line.rstrip("\r\n"))
        if m:
            blobs.append(m.group(1))
blobs = sorted(set(blobs))

lines = [f"== R7-D 悬空 blob 内容扫描（去重后 {len(blobs)} 个；git cat-file 只读）=="]
hits_all = []
for sha in blobs:
    r = git("cat-file", "-s", sha)
    if r.returncode != 0:
        lines.append(f"blob {sha} : size-fail rc={r.returncode} err={r.stderr[:80]!r}")
        continue
    sz = int(r.stdout.strip())
    c = git("cat-file", "blob", sha)
    if c.returncode != 0:
        lines.append(f"blob {sha} : blob-fail rc={c.returncode}")
        continue
    blob = c.stdout
    h = hashlib.sha256(content=blob).hexdigest() if False else hashlib.sha256(blob).hexdigest()
    low = blob.lower()
    hs = []
    for b, lab in NEEDLES:
        hay = low if b == b.lower() else blob
        if hay.find(b) >= 0:
            hs.append(lab)
    py = any(m in blob for m in PY_MARKS)
    lines.append(f"{'HIT' if hs else 'clean'} blob {sha} size={sz} sha256={h[:16]} py_marks={py} needles={','.join(hs) if hs else '-'}")
    if hs:
        hits_all.append(sha)
        for b, lab in NEEDLES:
            hay = low if b == b.lower() else blob
            q = hay.find(b)
            if q >= 0:
                ls = blob.rfind(b"\n", 0, q) + 1
                le = blob.find(b"\n", q)
                if le < 0:
                    le = len(blob)
                lines.append("    [" + lab + "] " + blob[ls:le][:200].decode("utf-8", "replace"))

lines.append(f"== 总计：blobs={len(blobs)} 内容命中={len(hits_all)} 耗时={round(time.perf_counter()-t0,2)}s ==")
text = "\n".join(lines) + "\n"
with open(OUTP, "w", encoding="utf-8") as f:
    f.write(text)
print(text[-800:])
print("[out] " + OUTP)
