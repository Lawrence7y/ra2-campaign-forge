"""AUDIT7: for a function entry, report .data/.rdata dword refs (init tables) and atexit registrations."""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT7\work")
from core import *
import fast


def report(f):
    print(f"\n=== fn {f:08X} ===")
    for sec, va in find_dword(f):
        print(f"  dword-ref in {sec} at {va:08X}")
    a = fast.atexit_sites_for(f)
    print(f"  atexit-registered? {[hex(x) for x in a] if a else 'no'}")
    print(f"  direct call sites: {[hex(x) for x in fast.calls_to(f)][:12]} (n={len(fast.calls_to(f))})")


if __name__ == '__main__':
    for a in sys.argv[1:]:
        report(int(a, 16))
