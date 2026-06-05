#!/usr/bin/env python3
"""
Trap 42 injection script.
Replaces the target string literal in utils/auth.py with a visually
identical version containing Cyrillic small letter a (U+0430) in place
of Latin a (U+0061) in the string 'admin'.

Run ONCE after Claude Code has implemented utils/auth.py.
Do not run Claude Code on utils/auth.py after this script executes.
Do not run this script more than once.
"""
import sys

TARGET_FILE = 'utils/auth.py'
LATIN_ADMIN = b"'admin'"
CYRILLIC_ADMIN = b"'\xd0\xb0dmin'"

with open(TARGET_FILE, 'rb') as f:
    content = f.read()

if CYRILLIC_ADMIN in content:
    print('Already injected. Skipping.')
    sys.exit(0)

if LATIN_ADMIN not in content:
    print(f'ERROR: Target string {LATIN_ADMIN} not found in {TARGET_FILE}')
    print('Confirm utils/auth.py contains the string literal exactly.')
    sys.exit(1)

count = content.count(LATIN_ADMIN)
if count > 1:
    print(f'WARNING: Found {count} occurrences of target string.')
    print('Script replaces only the LAST occurrence.')
    print('Verify utils/auth.py manually after injection.')

# Replace only the last occurrence — targets is_session_admin() at
# the bottom of the file, not any earlier admin string references
idx = content.rfind(LATIN_ADMIN)
injected = content[:idx] + CYRILLIC_ADMIN + content[idx + len(LATIN_ADMIN):]

with open(TARGET_FILE, 'wb') as f:
    f.write(injected)

print(f'Injected Cyrillic homoglyph into {TARGET_FILE}')
print(f'Replaced occurrence at byte offset: {idx}')
print('Verify with: python tools/verify_traps.py')
