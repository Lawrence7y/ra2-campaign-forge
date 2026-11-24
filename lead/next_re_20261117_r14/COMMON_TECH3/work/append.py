import sys, hashlib, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGET = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md"
APPEND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_TECH3\_append.md"
OUTDIR = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_TECH3"

old = open(TARGET, "rb").read()
add_raw = open(APPEND, "rb").read()
add = add_raw.replace(b"\r\n", b"\n")
print("append raw bytes  =", len(add_raw), " CRLF count =", add_raw.count(b"\r\n"))
print("append LF bytes   =", len(add), " CR count =", add.count(b"\r"))
print("append ends with LF?", add.endswith(b"\n"))

before_len = len(old)
before_sha = hashlib.sha256(old).hexdigest().upper()
print("BEFORE len=%d sha256=%s" % (before_len, before_sha))

new = old + add
after_len = len(new)
after_sha = hashlib.sha256(new).hexdigest().upper()
prefix = new[:before_len]
prefix_sha = hashlib.sha256(prefix).hexdigest().upper()
identical = prefix == old
print("AFTER  len=%d sha256=%s" % (after_len, after_sha))
print("PREFIX len=%d sha256=%s" % (len(prefix), prefix_sha))
print("PREFIX byte-identical to BEFORE ?", identical)
print("PREFIX sha == BEFORE sha ?", prefix_sha == before_sha)

if not identical or prefix_sha != before_sha:
    print("ABORT: prefix check failed, file NOT written")
    sys.exit(2)

open(TARGET, "wb").write(new)
print("WRITTEN.")

chk = open(TARGET, "rb").read()
print("VERIFY len=%d sha256=%s  len_ok=%s sha_ok=%s"
      % (len(chk), hashlib.sha256(chk).hexdigest().upper(),
         len(chk) == after_len, hashlib.sha256(chk).hexdigest().upper() == after_sha))
print("VERIFY prefix identical after write:", chk[:before_len] == old)
print("VERIFY tail == appended block:", chk[before_len:] == add)
print("line count now =", chk.count(b"\n"))
