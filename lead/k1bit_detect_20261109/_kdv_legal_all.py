# -*- coding: utf-8 -*-
"""A LEGAL self-test script using all() over k>=2 homogeneous inputs.

This file is a *validation fixture* for the review: it is a complete, runnable
Python script (no game binary, no sampling, no process inspection).  It proves
the semantic law  DISTINGUISHABLE_PASS = AND_k : killing any single input makes
the aggregate FAIL.  The detector must NOT report it as k->1bit.
"""
import sys

TOKENS = ("alpha", "beta", "gamma")


def main():
    body = sys.argv[1] if len(sys.argv) > 1 else "alpha beta gamma"
    present = [t in body for t in TOKENS]
    if not all(present):
        print("FAIL: at least one of the k inputs is dead")
        return 1
    print("PASS: all %d inputs verified" % len(TOKENS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
