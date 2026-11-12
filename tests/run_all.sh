#!/bin/bash
# Lance les tests un par un et affiche les lignes importantes.
cd "$(dirname "$0")/.." || exit 1
cp tests/fixtures/garantie.pdf tests/fixtures/photo_os.jpg /tmp/
for t in atk t7 t8 t9 t11 t13 t15 t17 t18 t19 t20 t21 t22 t23; do
  echo "=== $t"
  if [ "$t" = atk ]; then timeout 240 python3 tests/atk.py http://localhost:8765/ 2>&1 | tail -6
  else timeout 240 python3 tests/$t.py 2>&1 | tail -8; fi
done
