import sys


def f():
    ok = True
    ok = ok and 1 == 1
    ok = ok and 2 == 2
    print("ok =", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(f())
