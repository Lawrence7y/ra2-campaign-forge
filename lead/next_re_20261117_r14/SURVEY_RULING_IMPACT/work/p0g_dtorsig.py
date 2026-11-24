# -*- coding: utf-8 -*-
"""probe: is 'body contains a call to 0x7C8B3D after the vptr write' the discriminator
that separates the 4 documented inline-destructor writes from real constructors?

R14_COMMON 8.1 (23) names those 4 sites and says they all sit before 'call 0x7C8B3D'
(the CRT free). If that signal holds, it is a checkable 'destructor context' test.
"""
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p3_vt as P

BODIES = {}
srt = P.STARTS
for i, s in enumerate(srt):
    e = srt[i + 1] if i + 1 < len(srt) else P.TEND
    BODIES[s] = (s, e)


def body_of(site):
    import bisect
    k = bisect.bisect_right(srt, site) - 1
    if k < 0:
        return None
    s = srt[k]
    e = srt[k + 1] if k + 1 < len(srt) else P.TEND
    return (s, e)


def calls_in(lo, hi, target):
    out = []
    T = P.TSTART
    for i in range(lo - T, hi - T - 5):
        if P.TB[i] == 0xE8:
            t = T + i + 5 + struct.unpack_from("<i", P.TB, i + 1)[0]
            if t == target:
                out.append(T + i)
    return out


print("function-body 'call 0x7C8B3D' probe (site -> body -> free-call after site?)\n")
cases = [
    (0x0043C073, "006DEAD inline dtor (documented)"),
    (0x0043C098, "006DEAD inline dtor (documented)"),
    (0x0045AA66, "006DEAD inline dtor (documented)"),
    (0x0045AAB6, "006DEAD inline dtor (documented)"),
    (0x0040BBC6, "006DEAD inline dtor (observed)"),
    (0x0040BC16, "006DEAD inline dtor (observed)"),
    (0x004E6AFD, "007E43C8 LIVE ctor 004E6AE0"),
    (0x0043856D, "007E17CC LIVE ctor 00438550"),
    (0x004E6B28, "007E43E8 DEAD global dtor"),
    (0x00438598, "007E17EC DEAD global dtor"),
    (0x0043B6DB, "007E43C8 reg write"),
    (0x0040B563, "007E17CC reg write"),
]
for site, label in cases:
    b = body_of(site)
    calls = calls_in(b[0], b[1], 0x7C8B3D)
    after = [c for c in calls if c > site]
    print("  site 0x%08X body 0x%08X..0x%08X  calls_free=%d  free_after_site=%s  %s"
          % (site, b[0], b[1], len(calls), bool(after), label))

print("\nbody sizes sanity: median", sorted(e - s for s, e in BODIES.values())[len(BODIES) // 2])
print("count of functions whose body calls 0x7C8B3D:",
      sum(1 for s, e in BODIES.values() if calls_in(s, e, 0x7C8B3D)))
