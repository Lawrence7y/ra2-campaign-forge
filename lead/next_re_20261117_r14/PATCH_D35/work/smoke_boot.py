# -*- coding: utf-8 -*-
"""PATCH-D35 bounded smoke: launch the PATCHED COPY from inside PATCH_D35/work/run.
Observes process liveness, exit code, and except.txt delta in the run dir.
Never touches ra2youli\. No memory writes / injection / breakpoints.
"""
import os, sys, subprocess, time, hashlib

RUN  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\PATCH_D35\work\run"
EXE  = os.path.join(RUN, "gamemd.exe")
EXCEPT = os.path.join(RUN, "except.txt")
PIDFILE = os.path.join(os.path.dirname(__file__), "smoke_pid.txt")

def sha(p):
    if not os.path.exists(p):
        return None
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()

def gamemd_count():
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process gamemd -ErrorAction SilentlyContinue | Measure-Object).Count"],
        capture_output=True, text=True).stdout.strip()
    try:
        return int(out)
    except ValueError:
        return -1

def main():
    observe_s = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    tag = sys.argv[2] if len(sys.argv) > 2 else "boot"

    before_cnt = gamemd_count()
    if before_cnt != 0:
        print("ABORT: existing gamemd count=%d (not mine) - refusing" % before_cnt)
        sys.exit(2)

    before_except = (os.path.getsize(EXCEPT), sha(EXCEPT)) if os.path.exists(EXCEPT) else (None, None)
    print("before: gamemd=%d except_size=%s except_sha=%s" %
          (before_cnt, before_except[0], before_except[1]))

    p = subprocess.Popen([EXE], cwd=RUN, close_fds=True)
    with open(PIDFILE, "w") as f:
        f.write(str(p.pid))
    print("spawned pid=%d tag=%s observe=%ds" % (p.pid, tag, observe_s))

    exited = None
    for i in range(observe_s):
        time.sleep(1)
        rc = p.poll()
        if rc is not None:
            exited = rc
            print("EXITED at ~%ds rc=%s" % (i+1, rc))
            break

    if exited is None:
        print("ALIVE after %ds (rc=None)" % observe_s)

    after_except = (os.path.getsize(EXCEPT), sha(EXCEPT)) if os.path.exists(EXCEPT) else (None, None)
    print("after : except_size=%s except_sha=%s" % (after_except[0], after_except[1]))
    changed = (before_except[0], before_except[1]) != (after_except[0], after_except[1])
    print("except_changed=%s" % changed)
    if changed and os.path.exists(EXCEPT):
        before_bytes = b""
        # print tail of newly-appended content by size delta
        try:
            with open(EXCEPT, "rb") as f:
                data = f.read()
            if before_except[0] is not None and len(data) > before_except[0]:
                print("=== except.txt appended tail ===")
                print(data[before_except[0]:].decode("latin1", "replace")[-3000:])
            else:
                print("=== except.txt full (no baseline) ===")
                print(data.decode("latin1", "replace")[-3000:])
        except Exception as e:
            print("except read error:", e)

    # close only my process
    if p.poll() is None:
        print("terminating my pid=%d" % p.pid)
        try:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
        except Exception as e:
            print("terminate error:", e)
    print("final gamemd_count=%d" % gamemd_count())

if __name__ == "__main__":
    main()
