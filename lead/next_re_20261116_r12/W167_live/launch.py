import subprocess, time
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
WD  = r"D:\Project\ra2-campaign-forge\ra2youli"
p = subprocess.Popen([EXE], cwd=WD, close_fds=True)
print("spawned pid=%d" % p.pid)
for i in range(10):
    time.sleep(1.5)
    if p.poll() is not None:
        print("EXITED rc=%s" % p.poll()); break
