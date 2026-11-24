# _g9v_fp.py — 复核员指纹实算（只读；用法: python -I -X utf8 _g9v_fp.py <path>...）
import sys, hashlib, os

def main(argv):
    for p in argv:
        ap = os.path.abspath(p)
        try:
            with open(ap, "rb") as f:
                b = f.read()
        except Exception as e:
            print(f"ERR\t{ap}\t{e!r}")
            continue
        print(f"{hashlib.sha256(b).hexdigest()}\t{len(b)}\t{ap}")

if __name__ == "__main__":
    main(sys.argv[1:])
