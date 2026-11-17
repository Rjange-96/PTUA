#!/bin/bash
# Lance les tests un par un, affiche les lignes importantes et donne un verdict final.
# Usage : bash tests/run_all.sh            (tous les tests)
#         bash tests/run_all.sh t7 t25     (seulement ceux-là)
# Code de sortie : 0 si tout est bon, 1 sinon (utilisé par GitHub Actions).
cd "$(dirname "$0")/.." || exit 1
for g in tests/t*_gen.py; do python3 "$g" >/dev/null || { echo "❌ préparation $g impossible"; exit 1; }; done
cp tests/fixtures/garantie.pdf tests/fixtures/photo_os.jpg /tmp/
LOG=$(mktemp -d)

# Démarre le serveur local s'il ne tourne pas déjà.
if ! curl -s -o /dev/null http://localhost:8765/; then
  python3 -m http.server 8765 >/dev/null 2>&1 & SRV=$!
  trap 'kill $SRV 2>/dev/null' EXIT
  for _ in $(seq 20); do curl -s -o /dev/null http://localhost:8765/ && break; sleep 0.3; done
fi

TESTS=${*:-atk t7 t8 t9 t11 t13 t15 t17 t18 t19 t20 t21 t22 t23 t24 t25 t26 t27 t28 t29 t30 t31 t32 t33 t34 t35 t36 t37 t38 t39 t40 t41 t42 t43}
# Lignes où « False » est le résultat ATTENDU (ex. : « en clair ? False » = rien en clair sur le serveur).
OKFALSE='en clair \? False|texte clair sur serveur : False|alerte inattendu : False|fidOk = False|injectée : False \| X-EVIL : False'
KO=()
for t in $TESTS; do
  echo "=== $t"
  if [ "$t" = atk ]; then timeout 240 python3 tests/atk.py http://localhost:8765/ >"$LOG/$t" 2>&1
  else timeout 240 python3 tests/$t.py >"$LOG/$t" 2>&1; fi
  rc=$?
  tail -8 "$LOG/$t"
  why=""
  [ $rc -eq 124 ] && why="délai dépassé (240 s)"
  [ -z "$why" ] && [ $rc -ne 0 ] && why="arrêt anormal (code $rc)"
  [ -z "$why" ] && grep -qE '^(erreurs|errors) ?: ' "$LOG/$t" && ! grep -E '^(erreurs|errors) ?: ' "$LOG/$t" | grep -qE ': \[\]$' && why="erreurs JavaScript"
  [ -z "$why" ] && grep -E '(: |= )False\b' "$LOG/$t" | grep -vqE "$OKFALSE" && why="vérification à False : $(grep -E '(: |= )False\b' "$LOG/$t" | grep -vE "$OKFALSE" | head -1)"
  [ -z "$why" ] && grep -q 'PWNED flags' "$LOG/$t" && ! grep -qE 'PWNED flags: \[(None, )*None\]' "$LOG/$t" && why="injection exécutée"
  if [ -n "$why" ]; then echo "❌ $t : $why"; KO+=("$t"); else echo "✅ $t"; fi
done
echo
if [ ${#KO[@]} -eq 0 ]; then echo "✅ Tous les tests sont passés ($(echo $TESTS | wc -w))."; exit 0
else echo "❌ Échecs : ${KO[*]} (journaux complets dans $LOG)"; exit 1; fi
