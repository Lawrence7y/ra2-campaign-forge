import hashlib

P = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
with open(P, "rb") as f:
    b = f.read()
lines = b.split(b"\n")
# file tail from start of ledger line 9687 to EOF (line 9757 + final newline), CR stripped
tail = b"\n".join(lines[9686:9757]) + b"\n"
tail = tail.replace(b"\r", b"")
s = tail.decode("utf-8")
h = hashlib.sha256(s.encode("utf-8")).hexdigest()
print(f"ledger_tail lines=9687..9757(+final NL) chars={len(s)} sha256={h}")
print(f"MATCH sec[1:] (6a893fb8b9942b5bc7e23cee0bd07ae1bbe0f252d7403832f90793c628059788) = "
      f"{h == '6a893fb8b9942b5bc7e23cee0bd07ae1bbe0f252d7403832f90793c628059788'}")
blk71 = b"\n".join(lines[9686:9757]).replace(b"\r", b"")
s2 = blk71.decode("utf-8")
h2 = hashlib.sha256(s2.encode("utf-8")).hexdigest()
print(f"ledger lines=9687..9757(no trailing NL) chars={len(s2)} sha256={h2}")
print(f"MATCH sec[1:-1] (e0365b2b5ac13fd39fb124e1b9374c5728d581b5550382eb742f50d2d1e8adf6) = "
      f"{h2 == 'e0365b2b5ac13fd39fb124e1b9374c5728d581b5550382eb742f50d2d1e8adf6'}")
