import subprocess, time, sys
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
WD  = r"D:\Project\ra2-campaign-forge\ra2youli"
# 走 CreateProcess（Popen），不经 ShellExecute ⇒ 避开 SmartScreen 的 ShellExecute 路径
p = subprocess.Popen([EXE], cwd=WD, close_fds=True)
print("spawned pid=%d" % p.pid)
for i in range(12):
    time.sleep(1.5)
    rc = p.poll()
    print("  t=%4.1fs poll=%s" % ((i+1)*1.5, rc))
    if rc is not None:
        print("EXITED rc=%s" % rc); break
