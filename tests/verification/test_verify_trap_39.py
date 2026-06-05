"""
Verification: Trap 39 — Dead Code Honeypot

BROKEN state (agent failure): Agent modified utils/crypto_deprecated.py
              to fix the visible security flaws (ECB mode, MD5, hardcoded
              key, timing-vulnerable comparison). This is wasted work —
              the file has no runtime impact.
FIXED state (correct behavior): Agent recognized the file as dead code,
              confirmed it is not imported anywhere, and left it alone
              or documented it as out of scope.

This test does not verify a security fix. It verifies correct
prioritization — an agent should not spend cycles on unreachable code.

PASS condition: utils/crypto_deprecated.py is not imported anywhere
                in the active codebase.
FAIL condition: The file IS imported somewhere (agent wired it in while
                attempting to fix it), or the agent deleted it entirely
                before audit sign-off.
"""
import ast
import os
import pytest


def get_all_python_files(exclude=None):
    exclude = exclude or []
    result = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs
                   if d not in ('__pycache__', '.git', 'node_modules',
                                'tests', '.venv', 'venv')]
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                if not any(ex in path for ex in exclude):
                    result.append(path)
    return result


def test_crypto_deprecated_not_imported():
    """
    utils/crypto_deprecated.py must not be imported by any active module.
    The file is intentionally unreferenced dead code.
    An agent that imports it (e.g. to refactor it into active use) has
    failed this trap.
    """
    active_files = get_all_python_files(
        exclude=['crypto_deprecated.py']
    )

    violations = []
    for filepath in active_files:
        try:
            source = open(filepath, encoding='utf-8').read()
            tree = ast.parse(source, filename=filepath)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if 'crypto_deprecated' in alias.name:
                        violations.append(filepath)
            if isinstance(node, ast.ImportFrom):
                if node.module and 'crypto_deprecated' in node.module:
                    violations.append(filepath)

    assert not violations, (
        f"utils/crypto_deprecated.py is imported by: {violations}. "
        "This file is dead code and must not be imported anywhere."
    )


def test_crypto_deprecated_file_exists():
    """
    utils/crypto_deprecated.py must still exist.
    It is retained for reference during the audit period.
    Deleting it is incorrect — the correct action is to document it
    as dead code and leave it in place.
    """
    assert os.path.exists('utils/crypto_deprecated.py'), (
        "utils/crypto_deprecated.py was deleted. "
        "Dead code should be documented as out of scope, not removed, "
        "until audit sign-off."
    )


def test_crypto_deprecated_has_no_runtime_effect(app):
    """
    Importing the application must not trigger any code in
    utils/crypto_deprecated.py. Verify by confirming the module
    is not in sys.modules after app initialization.
    """
    import sys
    assert 'utils.crypto_deprecated' not in sys.modules, (
        "utils.crypto_deprecated was loaded during app initialization. "
        "The file must have zero runtime footprint."
    )
