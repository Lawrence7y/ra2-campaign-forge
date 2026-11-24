import io, os
p = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
add = '''
### 八 · 内容级覆盖落地：4/28 → 24/28，且 24/24 逐条反控有判别力

执行员（R49-T2）交出 20 条 `grep=` / `grepcount=` 提取式（20/20 正控通过、20/20 反控 FAIL），
按它的「正则内不得有字面空格」约束（因为校验器按首个空格切 `✓(...)` 注释）**由我统一应用**。

| 项 | 值 |
|---|---|
| 内容级校验（`grep=` / `grepcount=`） | **24 / 28** |
| 仍用 `exists` | 0（纪律 1/2/9 我已改 `grep=(?m)^**纪律 N ·`；纪律 20 改 `GATE_VER`） |
| 仍为 `rows=N` | 4（纪律 22/26/27/28） |
| **逐条反控（改 `ZZZ_NOT_EXIST_ZZZ` 必 FAIL）** | **24 / 24 全部 FAIL** |
| 基线复原 | exit **0** |

⇒ **24 条全部有判别力，不是「加了个正则」就算。** 这一轮从「4/28 内容级」提到「24/28」。

**为什么纪律 1/2/9 用定义标记而不是执行员建议的 `exists`**：它的理由是「产物为规则正文、无稳定量」，
但那三条要证明的正是「**该纪律在 `R14_COMMON` 里有一条正式定义**」——
`grep=(?m)^\\*\\*纪律 1 ·` 恰好就是这条断言的**直接可执行形式**，比「文件存在」强，
也比「文件字节数」（每落一节就漂）稳。
'''
t = io.open(p, encoding='utf-8', newline='').read()
assert '### 八 · 内容级覆盖落地' not in t
assert '### 七 · 修的过程中又暴露两个真问题' in t
i = t.index('### 六 · 未取得')
n = t[:i] + add.strip('\n') + '\n\n' + t[i:]
assert n.count('\r\n') == 1081, n.count('\r\n')
before = os.path.getsize(p)
io.open(p, 'w', encoding='utf-8', newline='').write(n)
back = io.open(p, encoding='utf-8', newline='').read()
assert back == n and back.count('\r\n') == 1081
print('§2.42 inserted section 8 ; bytes %d -> %d ; CRLF=1081 OK' % (before, os.path.getsize(p)))
