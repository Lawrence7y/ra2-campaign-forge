"""argv 往返探针：验证 os.spawnv 对含逗号/非 ASCII/空格 的
`--carrier-create-files` 整串是否原样送达（★ 子进程用 --child 守卫）。

用法：python _argv_rt_probe.py
"""
import sys, json, os
from pathlib import Path

OUT = Path(r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\_argv_rt.json")


def child():
    OUT.write_text(json.dumps(sys.argv[1:], ensure_ascii=False), encoding="utf-8")


def main():
    arg = "a,b,配置器.exe,XMP29U2.MAP,RA2MD Update.ico"
    spawn_argv = [sys.executable, os.path.abspath(__file__), "--child"]
    spawn_argv.append('"%s"' % arg if (" " in arg and not arg.startswith('"')) else arg)
    print("spawn_argv =", spawn_argv)
    rc = os.spawnv(os.P_WAIT, sys.executable, spawn_argv)
    print("child rc =", rc)
    got = json.loads(OUT.read_text(encoding="utf-8"))
    OUT.unlink()
    print("child argv =", got)
    actual = got[0] if got else None
    print("identical =", actual == arg)
    print("repr want   =", repr(arg))
    print("repr actual =", repr(actual))
    return 0 if actual == arg else 1


if __name__ == "__main__":
    if "--child" in sys.argv:
        child()
        sys.exit(0)
    sys.exit(main())
