#!/bin/bash
# Vérifie qu'une modification d'un fichier mis en cache sur l'iPhone s'accompagne d'un nouveau numéro de version.
# Sans cela, le service worker (cache d'abord) continue de servir l'ancienne version : la correction n'arrive jamais.
# Usage : bash tests/check_bump.sh <commit de référence>   (par défaut : origin/main)
cd "$(dirname "$0")/.." || exit 1
BASE=${1:-origin/main}
git cat-file -e "$BASE^{commit}" 2>/dev/null || { echo "➖ Référence $BASE introuvable : contrôle ignoré."; exit 0; }
ver(){ git show "$1:sw.js" 2>/dev/null | sed -n "s/^const V='\([^']*\)'.*/\1/p"; }
# Fichiers mis en cache : la liste F de sw.js, plus sw.js lui-même.
CACHED=$(sed -n "s/.*F=\[\(.*\)\];.*/\1/p" sw.js | tr ',' '\n' | tr -d "' " | sed 's#^\./##' | grep -v '^$'; echo sw.js)
CHANGED=$(git diff --name-only "$BASE" HEAD -- $CACHED)
if [ -z "$CHANGED" ]; then echo "✅ Aucun fichier de l'application modifié : pas de nouvelle version nécessaire."; exit 0; fi
OLD=$(ver "$BASE");NEW=$(ver HEAD)
if [ "$OLD" = "$NEW" ]; then
  echo "❌ Fichiers de l'application modifiés sans nouveau numéro de version (reste $NEW) :"; echo "$CHANGED" | sed 's/^/   - /'
  echo "   → Augmentez la version dans index.html (APPV, <title>, en-tête), sw.js et version.json."; exit 1
fi
echo "✅ Nouvelle version $OLD → $NEW pour : $(echo $CHANGED)"
