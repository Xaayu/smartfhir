"""Tiny test runner to execute test_*.py files without pytest.

Features:
- Discovers modules named test_*.py in the current package directory
- Provides a minimal `monkeypatch` object with `setattr` to support existing tests
- Runs functions starting with `test_` and reports results
"""
import sys
import os
import importlib
import inspect
import traceback


class SimpleMonkeyPatch:
    def setattr(self, target, value, raising=True):
        """Support string target like 'module.attr' or (module, name) tuple."""
        if isinstance(target, str):
            module_name, _, attr = target.rpartition('.')
            if not module_name:
                raise ValueError("target string must be 'module.attr'")
            mod = importlib.import_module(module_name)
            setattr(mod, attr, value)
        else:
            # assume (obj, name)
            obj, name = target
            setattr(obj, name, value)


def discover_tests(path: str):
    tests = []
    for fn in os.listdir(path):
        if fn.startswith('test_') and fn.endswith('.py'):
            tests.append(fn[:-3])
    return tests


def run_module_tests(module_name: str):
    results = []
    mod = importlib.import_module(module_name)
    for name, obj in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith('test_'):
            params = inspect.signature(obj).parameters
            args = []
            if 'monkeypatch' in params:
                args.append(SimpleMonkeyPatch())

            try:
                obj(*args)
                results.append((module_name + '.' + name, True, None))
            except AssertionError as ae:
                results.append((module_name + '.' + name, False, str(ae)))
            except Exception as e:
                tb = traceback.format_exc()
                results.append((module_name + '.' + name, False, tb))

    return results


def main():
    here = os.path.dirname(__file__)
    if here not in sys.path:
        sys.path.insert(0, here)

    modules = discover_tests(here)
    total = 0
    failures = 0

    for m in modules:
        print(f"Running tests in {m}...")
        res = run_module_tests(m)
        for name, ok, info in res:
            total += 1
            if ok:
                print(f"  PASS {name}")
            else:
                failures += 1
                print(f"  FAIL {name}")
                print(info)

    print(f"\n{total} tests run, {failures} failures")
    sys.exit(failures)


if __name__ == '__main__':
    main()
