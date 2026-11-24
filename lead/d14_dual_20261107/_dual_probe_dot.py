# -*- coding: utf-8 -*-
# 探针B：源代码含字面 ".." 字符串常量是否触发拦截
DOTS = chr(46) * 2
s = ".."
print("B ok", len(s), DOTS == s)
