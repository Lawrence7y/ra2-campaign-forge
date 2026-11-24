# _shv_cmp2.py — 换行归一后的精确比对（只读）
import hashlib

W = "D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109"
LED = "D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
if ".." in W or ".." in LED:
    raise SystemExit("refuse")

rerun = open(W + "/_shv_rerun_out.txt", encoding="utf-8", newline="").read()
stored = open(W + "/_shv_row512655_output.txt", encoding="utf-8", newline="").read()
print("[1] stored has CR:", "\r" in stored, "| CR count:", stored.count("\r"), "| stored chars:", len(stored))
print("    rerun has CR:", "\r" in rerun, "| rerun chars:", len(rerun))
print("    normalized equal:", rerun.replace("\r\n", "\n").strip() == stored.replace("\r\n", "\n").strip())
if rerun.replace("\r\n", "\n").strip() != stored.replace("\r\n", "\n").strip():
    a = rerun.replace("\r\n", "\n").strip().split("\n")
    b = stored.replace("\r\n", "\n").strip().split("\n")
    print("    rerun lines:", len(a), "stored lines:", len(b))
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            print("    first line diff", i, repr(x), "vs", repr(y))
            break

raw = open(LED, encoding="utf-8", newline="").read()
print("[2] ledger has CRLF:", "\r\n" in raw, "| CR count:", raw.count("\r"), "| LF count:", raw.count("\n"))
print("    splitlines count:", len(raw.splitlines()), "| split(\n) count:", len(raw.split("\n")))
lines = raw.split("\n")  # keep \r at EOL if CRLF

# 精确定位 §604 起止
start = None
for i, l in enumerate(lines):
    if l.replace("\r", "").startswith("## §604 "):
        start = i
        break
print("    §604 heading at 1-based line:", start + 1, repr(lines[start][:60]))
end = len(lines) - 1
if lines[end] == "":
    end -= 1  # trailing empty
print("    last non-empty line:", end + 1, repr(lines[end][:50]))

sec_raw = None
import re
cmd667 = open(W + "/_shv_row512667_command.txt", encoding="utf-8", newline="").read()
m = re.search(r"sec = '''(.*?)'''", cmd667, re.S)
sec_raw = m.group(1)
print("[3] sec_raw chars:", len(sec_raw), "| starts:", repr(sec_raw[:12]), "| ends:", repr(sec_raw[-12:]))

target = "\n".join(lines[start:end + 1])  # with \r if CRLF
print("    target(with CR) chars:", len(target))
tnorm = target.replace("\r\n", "\n")
print("    target(norm LF) chars:", len(tnorm))
for name, cand in (
    ("sec_raw", sec_raw),
    ("sec_raw[1:]", sec_raw[1:]),
    ("sec_raw.strip()", sec_raw.strip()),
):
    print("    compare", name, len(cand), "== target_norm:", cand == tnorm)

# sha256 三个候选口径
print("[4] sha256:")
print("    sec_raw        ", hashlib.sha256(sec_raw.encode()).hexdigest())
print("    sec_raw[1:]    ", hashlib.sha256(sec_raw[1:].encode()).hexdigest())
print("    tnorm          ", hashlib.sha256(tnorm.encode()).hexdigest())
print("    target with CR ", hashlib.sha256(target.encode()).hexdigest())
print("    CLAIM           6a893fb8b9942b5bc7e23cee0bd07ae1bbe0f252d7403832f90793c628059788")
# 3022 字符口径定位
cands = {"sec_raw[1:]": sec_raw[1:], "tnorm": tnorm}
for n, c in cands.items():
    print("    len", n, "=", len(c), "sha==claim:", hashlib.sha256(c.encode()).hexdigest() == "6a893fb8b9942b5bc7e23cee0bd07ae1bbe0f252d7403832f90793c628059788")
