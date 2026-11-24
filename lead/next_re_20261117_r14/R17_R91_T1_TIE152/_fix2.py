import io, re
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R91_T1_TIE152\q3_verdicts.py"
s = io.open(p, encoding="utf-8").read()
# 把「中文串内部」的直双引号统一改成中文书名号引号，避免破坏 Python 字面量
out = []
in_cjk = False
i = 0
while i < len(s):
    ch = s[i]
    if ch == '"':
        prev = s[i - 1] if i else ""
        nxt = s[i + 1] if i + 1 < len(s) else ""
        # 内部引号：前一个字符是中文/标点，且后一个字符不是 , ) :
        if prev and (ord(prev) > 0x2000) and nxt not in (",", ")", ":", "\n"):
            out.append("」" if out and out.count("「") > out.count("」") else "「")
            i += 1
            continue
    out.append(ch)
    i += 1
s2 = "".join(out)
io.open(p, "w", encoding="utf-8").write(s2)
import py_compile
try:
    py_compile.compile(p, doraise=True)
    print("OK compile")
except Exception as e:
    print("ERR", e)
