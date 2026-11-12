# Tests automatiques de PTUA

Ces tests ouvrent l'application dans Chrome (Playwright) avec un faux serveur Supabase et de fausses données.
Ils ne touchent jamais au vrai serveur.

## Lancer

```bash
pip install playwright && playwright install chromium   # une seule fois
cd <dossier du dépôt> && python3 -m http.server 8765 &
bash tests/run_all.sh
```

(Les scripts utilisent `/usr/bin/google-chrome` : adaptez `executable_path` si besoin.)

| Script | Ce qu'il vérifie |
|---|---|
| atk.py | attaques par données piégées (XSS, formules CSV) |
| t7.py | chiffrement, verrouillage, blocage après échecs |
| t8.py | onglets, export/import chiffré, calendrier |
| t9.py | synchronisation entre deux appareils, hors ligne |
| t11.py | historique cloud et restauration |
| t13.py | assurances |
| t15.py | documents joints et visionneuse |
| t17.py | sauvegarde complète, test de l'appareil, quota |
| t18.py | déverrouillage Face ID (faux lecteur biométrique) |
| t19.py | onglet Activité |
| t20.py | vérification NextDNS |

À lancer après chaque modification, avant de publier.
