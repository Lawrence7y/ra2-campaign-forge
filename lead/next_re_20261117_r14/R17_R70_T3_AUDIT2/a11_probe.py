import io,os,re
R14=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
p=os.path.join(R14,"R14_COMMON.md")
s=io.open(p,encoding="utf-8").read()
# 找所有提及 2.24 的位置及其上下文
for m in re.finditer(r"2\.24", s):
    ln=s[:m.start()].count("\n")+1
    print("--- 行",ln,"---")
    print(s[max(0,m.start()-100):m.start()+250].replace("\n"," | "))
    print()
