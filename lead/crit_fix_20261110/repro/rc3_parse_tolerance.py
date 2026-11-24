import sys

d = {}
rows = [("a", "x=1"), ("b", "bad")]


def f():
    for k, line in rows:
        try:
            d[k] = dict(p.split("=") for p in line.split(","))
        except ValueError:
            pass
    ok = "a" in d
    ok = ok and d.get("a", {}).get("x") == "1"
    if not ok:
        return 1
    if len(rows) != 2:
        return 1
    print("ok =", ok)
    return 0


if __name__ == "__main__":
    sys.exit(f())
