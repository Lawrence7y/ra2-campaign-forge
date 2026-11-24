import io
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R91_T1_TIE152\q3_verdicts.py"
s = io.open(p, encoding="utf-8").read()
reps = [
    ('"被测对象的文件字节事实"', '「被测对象的文件字节事实」'),
    ('"差分产物算对象记录还是过程记录"', '「差分产物算对象记录还是过程记录」'),
    ('"patch 前后 diff 是否计对象抄本"', '「patch 前后 diff 是否计对象抄本」'),
    ('"哈希核对表是否算对象记录"', '「哈希核对表是否算对象记录」'),
    ('"数据内容清单是否计对象记录"', '「数据内容清单是否计对象记录」'),
    ('"对象抄本=.text/.rdata 对象记录"', '「对象抄本=.text/.rdata 对象记录」'),
    ('"数据字符串表算不算对象抄本"', '「数据字符串表算不算对象抄本」'),
    ('"被测函数/槽对象"', '「被测函数/槽对象」'),
]
for a, b in reps:
    s = s.replace(a, b)
io.open(p, "w", encoding="utf-8").write(s)
# 语法检查
import py_compile, sys
try:
    py_compile.compile(p, doraise=True)
    print("OK compile")
except Exception as e:
    print("ERR", e)
