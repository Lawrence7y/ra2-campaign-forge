# _shv_cmp.py — 三套数字比对 + sec 文本 vs 台账 §604（只读；输出 stdout）
import hashlib, re, io

W = "D:/Project/ra2-campaign-forge/lead/s604_script_hunt_20261109"
LED = "D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
if ".." in W or ".." in LED:
    raise SystemExit("refuse")

rerun = open(W + "/_shv_rerun_out.txt", encoding="utf-8").read()
stored = open(W + "/_shv_row512655_output.txt", encoding="utf-8", newline="").read()

# 1) 今日复跑 vs 11-06 存档输出
print("[1] rerun == stored(11-06) after strip:", rerun.strip() == stored.strip())
if rerun.strip() != stored.strip():
    print("   rerun len", len(rerun), "stored len", len(stored))

# 2) 台账表 15 行 vs 复跑 15 行
led_text = open(LED, encoding="utf-8", newline="").read()
led_lines = led_text.split("\n")
print("[2] ledger total lines:", len(led_lines))
tab = led_lines[9705:9720]  # :9706-9720
rrows = [l for l in rerun.strip().split("\n") if re.match(r"^(l1c|l1d|l1e|l3|t55k)", l)]
ok = 0
for k, (lr, rr) in enumerate(zip(tab, rrows)):
    nums = re.findall(r"[-+−]?\d+\.\d+", lr.replace("**", ""))
    rnums = rr.split()
    lbl = lr.split("`")[1]
    row_ok = (lbl.split("/")[0] == rnums[0]) and all(
        abs(float(a.replace("−", "-")) - float(b)) < 1e-9
        for a, b in zip(nums, rnums[1:6])
    )
    ok += row_ok
    print(f"   row{k+1:02d} {lbl:20s} ledger={nums} rerun={rnums[1:6]} -> {'OK' if row_ok else 'MISMATCH'}")
print("   TABLE match:", ok, "/15")

# 3) sec 文本 vs 台账 §604（:9687-9757）
cmd667 = open(W + "/_shv_row512667_command.txt", encoding="utf-8", newline="").read()
m = re.search(r"sec = '''(.*?)'''", cmd667, re.S)
sec = m.group(1)
sec_sha = hashlib.sha256(sec.encode("utf-8")).hexdigest()
print("[3] sec chars:", len(sec), "bytes:", len(sec.encode("utf-8")), "sha256:", sec_sha)
target = "\n".join(led_lines[9686:9757])  # :9687..:9757
t_sha = hashlib.sha256(target.encode("utf-8")).hexdigest()
print("    ledger 9687-9757 chars:", len(target), "sha256:", t_sha)
print("    sec == ledger section:", sec == target, "| MATCH:", sec_sha == t_sha)
sec2 = "\n" + sec
print("    sec with leading LF == target:", sec2 == target)
if sec != target:
    for i, (a, b) in enumerate(zip(sec, target)):
        if a != b:
            print("    first diff at", i, repr(a), "vs", repr(b), context=repr(sec[max(0,i-30):i+30]))
            break
print("[4] APPENDED 3023 vs len(sec)=", len(sec), " len(sec)+1=", len(sec)+1, " bytes(sec)=", len(sec.encode('utf-8')))
