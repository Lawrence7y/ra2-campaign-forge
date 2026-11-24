"""ECV control A: 文件名像门禁（gate），本体是纯探针（只有观测 print，无裁决无出口）。
预期：PROBE。用于检验分类不受文件名影响。本文件是复核员合成件，不属于 263 件普查集，绝不执行。"""
import platform

print("python:", platform.python_version())
print("observed entries:", 3)
print("observation only, no verdict here")
