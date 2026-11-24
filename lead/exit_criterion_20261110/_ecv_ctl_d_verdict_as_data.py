"""ECV control D: verdict-as-data——裁决词作字典值流转，经 json.dumps 打印。
判据声明的静态盲区：预期不被判 GATE（落在 PROBE），验证「盲区声明=实际行为」。合成件，绝不执行。"""
import json

results = {
    "check_alpha": "PASS" if 1 + 1 == 2 else "FAIL",
    "check_beta": "PASS" if "a" in "abc" else "FAIL",
}
print(json.dumps(results, ensure_ascii=False))
