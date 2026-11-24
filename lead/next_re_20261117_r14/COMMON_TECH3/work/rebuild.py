import sys, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGET = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md"
APPEND = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_TECH3\_append.md"

ORIG_LEN = 202159
ORIG_SHA = "24CC87B84FDC4A59E6416036956EBE5F006A163E6731A2F677800C85DA4083D7"

cur = open(TARGET, "rb").read()
old = cur[:ORIG_LEN]
print("read current len =", len(cur))
print("prefix len=%d sha256=%s" % (len(old), hashlib.sha256(old).hexdigest().upper()))
assert len(old) == ORIG_LEN
assert hashlib.sha256(old).hexdigest().upper() == ORIG_SHA, "prefix drifted"
print("prefix == ORIGINAL BEFORE (byte-identical, sha match): True")

add = open(APPEND, "rb").read().replace(b"\r\n", b"\n")
print("append bytes =", len(add), "CR count =", add.count(b"\r"), "ends LF?", add.endswith(b"\n"))

new = old + add
open(TARGET, "wb").write(new)

chk = open(TARGET, "rb").read()
print("FINAL len=%d sha256=%s" % (len(chk), hashlib.sha256(chk).hexdigest().upper()))
print("prefix identical:", chk[:ORIG_LEN] == old)
print("tail == append block:", chk[ORIG_LEN:] == add)
print("lines =", chk.count(b"\n"))
