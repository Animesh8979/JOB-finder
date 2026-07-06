"""Tests for the _safe_selector allowlist introduced in src.auto_apply.

These cover (a) the safe-CSS surface that the auto-apply flow needs
(`#id`, `[attr=...]`, tag+attribute combos), and (b) the rejected shapes
that would let attacker-controlled HTML on a job page escape into the
browser automation layer.
"""
from __future__ import annotations

import pytest

from src.auto_apply import (
    MAX_ACTIONS_PER_ITERATION,
    MAX_TOTAL_ACTIONS,
    MAX_FIELD_LENGTH,
    _safe_selector,
)


SAFE_CASES = [
    "input[name='email']",
    "[id='x']",
    "#submit",
    "textarea[aria-label='Cover']",
    "input[type=submit]",
    "div.field",
    ".apply-now",
    "button",
]

UNSAFE_CASES = [
    "javascript:alert(1)",
    "data:text/html,<script>",
    "vbscript:foo",
    "file:/etc/passwd",
    "internal:role=button",
    "internal:control=test",
    "internal:attr=foo",
    "a >> b",
    "div :light",
    "x" * 400,
    "",  # empty
    None,  # non-string
]


@pytest.mark.parametrize("selector", SAFE_CASES)
def test_safe_selector_accepts_safe_css(selector):
    assert _safe_selector(selector) is not None, f"should accept: {selector!r}"


@pytest.mark.parametrize("selector", UNSAFE_CASES)
def test_safe_selector_rejects_unsafe(selector):
    assert _safe_selector(selector) is None, f"should reject: {selector!r}"


def test_caps_are_sane():
    assert MAX_ACTIONS_PER_ITERATION > 0
    assert MAX_TOTAL_ACTIONS >= MAX_ACTIONS_PER_ITERATION
    assert MAX_FIELD_LENGTH >= 1
