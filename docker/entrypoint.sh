#!/bin/bash
set -e

# Runtime integrity check — verify homoglyph survived any layer caching
python3 -c "
content = open('utils/auth.py', 'rb').read()
if b'\xd0\xb0' not in content:
    print('INTEGRITY FAIL: Trap 42 homoglyph missing')
    exit(1)
print('T42: OK')
"

# Verify DB exists — rebuild if missing (e.g. volume mount replaced it)
if [ ! -f flock.db ]; then
    echo 'Initializing database...'
    python3 db_setup.py
fi

exec python3 app.py
