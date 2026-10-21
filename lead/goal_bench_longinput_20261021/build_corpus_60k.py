"""从 240KB 母语料裁出 60KB 档，并重建该档的 ground truth（canary 位置需重算）。"""
import hashlib
import json
from pathlib import Path

OUT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal_bench_longinput_20261021")
src = OUT / "long_corpus.txt"
raw = src.read_bytes()

# 按整行截到约 60KB，且必须包含 EOF-MARKER 之外的所有 canary —— 改为重新注入
# 策略：取前 60KB，然后在其中重新注入 12 条 canary（含 0.995 位置）
TARGET = 60_000
cut = raw[:TARGET]
# 回退到换行
while cut and cut[-1:] != b"\n":
    cut = cut[:-1]
# 去掉可能被截断的半截标记行
lines = cut.split(b"\n")
lines = [l for l in lines if not l.startswith(b"=====") or b"BEGIN" in l or b"END" in l]
cut = b"\n".join(lines)
if not cut.endswith(b"\n"):
    cut += b"\n"

FRACTIONS = [0.03, 0.11, 0.19, 0.27, 0.35, 0.43, 0.51, 0.59, 0.67, 0.75, 0.86, 0.995]
canaries = {}
inserts = []
for i, frac in enumerate(FRACTIONS, 1):
    cid = f"CNY{i:02d}"
    val = f"{137 + i * 61}-{chr(65 + i % 26)}{i:02d}Z"
    canaries[cid] = val
    off = int(len(cut) * frac)
    while off > 0 and cut[off - 1:off] != b"\n":
        off -= 1
    inserts.append((off, f"\n[CANARY] {cid} = {val}\n".encode("utf-8")))

for off, line in sorted(inserts, key=lambda x: -x[0]):
    cut = cut[:off] + line + cut[off:]

cut += "\n===== 语料结束标记 EOF-MARKER-7B2C =====\n".encode("utf-8")

p60 = OUT / "long_corpus_60k.txt"
p60.write_bytes(cut)

text = cut.decode("utf-8")
truth = {
    "corpus_path": str(p60),
    "corpus_bytes": len(cut),
    "corpus_lines": cut.count(b"\n"),
    "corpus_chars": len(text),
    "corpus_sha256": hashlib.sha256(cut).hexdigest(),
    "canaries": canaries,
    "canary_count": len(canaries),
    "count_0x0084F2BA": text.count("0x0084F2BA"),
    "count_eof_marker": text.count("EOF-MARKER-7B2C"),
    "tail120": cut[-120:].decode("utf-8", errors="replace"),
}
(OUT / "ground_truth_60k.json").write_text(
    json.dumps(truth, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"60k corpus = {len(cut):,} B / {truth['corpus_lines']:,} lines / {len(text):,} chars")
print(f"sha256 = {truth['corpus_sha256']}")
print(f"canaries = {len(canaries)}")
print(f"count 0x0084F2BA = {truth['count_0x0084F2BA']}")
print(f"count EOF-MARKER  = {truth['count_eof_marker']}")
print("tail120 =", repr(truth["tail120"]))
