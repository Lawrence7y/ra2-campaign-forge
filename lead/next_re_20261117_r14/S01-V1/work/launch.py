import subprocess, time
p = subprocess.Popen([r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"],
                     cwd=r"D:\Project\ra2-campaign-forge\ra2youli", close_fds=True)
print("spawned pid=%d" % p.pid)
for i in range(10):
    time.sleep(1.5)
    if p.poll() is not None:
        print("EXITED rc=%s" % p.poll()); break
