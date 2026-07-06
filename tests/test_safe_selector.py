"""Smoke test for the _safe_selector allowlist introduced in src.auto_apply."""
from src.auto_apply import _safe_selector, MAX_ACTIONS_PER_ITERATION, MAX_TOTAL_ACTIONS

cases = [
    ("input[name='email']",         True),
    ("[id='x']",                    True),
    ("#submit",                     True),
    ("textarea[aria-label='Cover']", True),
    ("javascript:alert(1)",         False),
    ("data:text/html,<script>",     False),
    ("vbscript:foo",                False),
    ("file:/etc/passwd",            False),
    ("internal:role=button",        False),
    ("internal:control=test",       False),
    ("internal:attr=foo",           False),
    ("a >> b",                      False),
    ("div :light",                  False),
    ("x" * 400,                     False),
    ("",                            False),
    ("input[type=submit]",          True),
]

for sel, expected in cases:
    got = _safe_selector(sel) is not None
    ok = "PASS" if got == expected else "FAIL"
    print(f"{ok}  expected={expected!s:<5} got={got!s:<5}  sel={sel!r:.60}")

print(f"\nMAX_ACTIONS_PER_ITERATION = {MAX_ACTIONS_PER_ITERATION}")
print(f"MAX_TOTAL_ACTIONS = {MAX_TOTAL_ACTIONS}")
