"""ECV control F: 散文误报探针——两臂 prose 恰好各含 OK / FAIL 词。
预期暴露 GA2 词对启发式的散文误报通道（两臂词对成立即判 GATE）。合成件，绝不执行。"""
import sys

mode = "--verbose"
if mode == "--verbose":
    print("verbose: each item line will be marked OK or not")
else:
    print("quiet: FAIL lines summarized at end")
sys.exit(0)
