# -*- coding: utf-8 -*-
import sys; sys.dont_write_bytecode = True
import json
import os
import importlib.util

_CRITERION_ABS = "D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ec_criterion.py"
_E_KEYS = ("E0", "E1", "E2", "E3", "E4")


def _load_ec():
    """只从绝对路径载入判据本体；模块名与 __main__ 无关，故不会打印其 __doc__。"""
    spec = importlib.util.spec_from_file_location("_ec_criterion", _CRITERION_ABS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _one(EC, path):
    rel = path.replace(os.sep, '/')
    try:
        result = EC.analyze_file(path, path.replace(os.sep, '/'))
        e_src = result.get("e") or {}
        _emit({
            "rel": str(result["rel"]),
            "class": str(result["class"]),
            "verdict": str(result["verdict"]),
            "e": {k: e_src.get(k) for k in _E_KEYS},
            "n_reasons": len(result.get("reasons", [])),
        })
    except BaseException as exc:
        _emit({"rel": rel, "error": type(exc).__name__})


def _run():
    try:
        EC = _load_ec()
    except BaseException as exc:
        # 判据本体都载不进来时，每个路径仍各自输出一行错误 JSON。
        for path in sys.argv[1:]:
            _emit({"rel": str(path).replace(os.sep, '/'),
                   "error": type(exc).__name__})
        return
    for path in sys.argv[1:]:
        try:
            _one(EC, path)
        except BaseException as exc:
            _emit({"rel": str(path).replace(os.sep, '/'),
                   "error": type(exc).__name__})


if __name__ == "__main__":
    try:
        _run()
    except BaseException as exc:
        try:
            _emit({"rel": "", "error": type(exc).__name__})
        except BaseException:
            pass
    # 退出码恒为 0：它只表示「包装器自己跑完了」，与被判文件的结论无关。
    sys.exit(0)
