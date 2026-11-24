import sys, time, collections
import w159_probe as W
pid = W.pid_of()
tids = W.list_threads(pid)
hot = collections.Counter()
t0 = time.perf_counter()
while time.perf_counter() - t0 < 25:
    for tid in tids:
        e = W.eip_of(tid)
        if e and 0x401000 <= e < 0x7E1000:
            hot[e] += 1
tot = sum(hot.values())
print("total .text samples = %d, distinct = %d" % (tot, len(hot)))
print()
print("top 25 EIP inside .text:")
for eip, c in hot.most_common(25):
    print("   %08X  %6d  %5.2f%%" % (eip, c, 100.0*c/tot))
