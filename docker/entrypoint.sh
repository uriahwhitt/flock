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

# DB is pre-seeded at build time — check the correct instance path
if [ ! -f instance/flock.db ]; then
    echo "ERROR: Database not found at instance/flock.db"
    echo "Image may have been built incorrectly."
    echo "Rebuild with: docker build -t flock:broken-baseline -f docker/Dockerfile ."
    exit 1
fi

exec python3 app.py
