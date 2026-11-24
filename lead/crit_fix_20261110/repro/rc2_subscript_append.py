import sys

D = {"errs": []}


def f():
    ok = True
    try:
        int("x")
    except ValueError:
        D["errs"].append("bad")
        flag = False
    else:
        flag = True
    if not flag:
        return 1
    if not ok:
        return 1
    print("ok =", ok)
    return 0


if __name__ == "__main__":
    sys.exit(f())
