"""重跑一小段但记录**每个 EIP 的原始值**，不再分桶，以便看命中到底落在哪。"""
import collections
import time

import w172_probe as P

pid = P.pid_of()
m = P.Mem(pid)
tids = [t for t in P.list_threads(pid) if P.eip_of(t) is not None]
print("threads=%d" % len(tids))
sc = P.scalars(m)
print("scalars: moving=%s has_target=%s with_loco=%s lc=%s frame=%s"
      % (sc["moving"], sc["has_target"], sc["with_loco"], sc["lc_count"], sc["frame"]))

hot = collections.Counter()
text = collections.Counter()
t0 = time.perf_counter()
n = 0
while time.perf_counter() - t0 < 40:
    for tid in tids:
        e = P.eip_of(tid)
        if e is None:
            continue
        n += 1
        hot[e] += 1
        if 0x401000 <= e < 0x7E1000:
            text[e] += 1
tot_text = sum(text.values())
print("EIP samples=%d  in .text=%d (%.3f%%)  distinct text EIP=%d"
      % (n, tot_text, 100.0 * tot_text / max(1, n), len(text)))
print()
print("=== .text 内命中最多的 30 个 EIP ===")
for e, c in text.most_common(30):
    print("   %08X  %6d  %5.2f%%" % (e, c, 100.0 * c / tot_text if tot_text else 0))
