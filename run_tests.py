"""A test runner that needs no pytest, because a library whose tests cannot be run in
the environment it ships to is a library with untested tests."""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests"))
import test_selectlib as t

ok = fail = 0
for name in sorted(n for n in dir(t) if n.startswith("test_")):
    try:
        getattr(t, name)()
        ok += 1
        print(f"  PASS  {name}")
    except Exception as e:
        fail += 1
        print(f"  FAIL  {name}: {type(e).__name__}: {str(e)[:110]}")
print(f"\n  {ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
