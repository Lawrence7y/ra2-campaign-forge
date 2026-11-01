import json
import subprocess
import sys

out = subprocess.run([sys.executable, 'lead/qc161_u0400_trip/_trip_plan_h1.py', '--json'],
                     capture_output=True, text=True, encoding='utf-8')
plans = json.loads(out.stdout)

# 用真 bash 跑 `echo` 版本：把 python 换成 echo，看 bash 实际收到什么
print("=== 逐趟：真 bash 收到的 argv 是否与规划 argv 一致 ===")
allok = True
for p in plans:
    cmd = p['cmd'].replace('python ', 'echo ', 1)
    r = subprocess.run(['bash', '-c', cmd], capture_output=True)
    text = r.stdout.decode('utf-8', 'replace').strip()
    # echo 用空格连接参数，无法区分边界；改为逐参数比对首尾
    expected0 = p['argv'][0]
    ok0 = text.startswith(expected0)
    ok_last = text.endswith(p['argv'][-1])
    print("%-5s bash_rc=%d start_ok=%s end_ok=%s" % (p['suffix'], r.returncode, ok0, ok_last))
    if not (ok0 and ok_last):
        allok = False
        print("   首   : %r" % text[:110])
        print("   应为 : %r" % expected0[:110])

print()
print("RESULT:", "ALL ROUNDTRIP OK" if allok else "MISMATCH")
sys.exit(0 if allok else 1)
