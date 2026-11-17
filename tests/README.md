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
| t21.py | modèles de courriers (Word, impression) |
| t22.py | conformité |
| t23.py | interface : icônes, accessibilité, erreurs en ligne |
| t24.py | assistant sécurité (agent IA) : accès, rien d'enregistré, effacement au verrouillage |
| t25.py | calendrier .ics : injection par retour chariot isolé bloquée, échappement des « ; » et « , » |
| t26.py | service worker : caches des autres applications du domaine préservés, cache PTUA reconstitué, hors ligne |
| t27.py | partage avec un collègue : invitation, accès séparé, documents, modifications croisées, retrait d'accès, anti-hameçonnage |
| t28.py | gros PDF : compression et découpage automatiques sans question, plus de limite de 600 pages, couleur conservée, fiche pleine, bouton Arrêter (préparer avec `python3 tests/t28_gen.py`) |
| t29.py | jauge en arrière-plan : pas de fenêtre bloquante, progression, travail possible pendant le traitement, file d'attente, réduire/agrandir, envoi au cloud, verrouillage (arrêt, rien d'affiché, aucun fichier orphelin) |
| t30.py | thèmes Classique clair/sombre, Ninja, Pirate : choix, mémorisation, tous les onglets sans erreur, contraste ≥ 4,5 |
| t31.py | garantie de performance environnementale et sociale ; modèles de courrier Word/PDF : ajout, champs remplis (même coupés par Word), mise en page conservée, refus des fichiers piégés, synchronisation, retrait (préparer avec `python3 tests/t31_gen.py`) |
| t32.py | fenêtre de modification d'une garantie : le marché et le type restent affichés en haut (figés), même en défilant, et se mettent à jour en direct ; pas d'effet de bord sur les autres fiches |
| t34.py | analyse de conformité d'une assurance reçue : lecture du PDF, exigences lues depuis le CCAP collé, attestation conforme / non conforme (assuré, effet, durée, capital, franchise, garanties exclues, prime sous réserve), valeurs lues appliquées sans écrasement, décision manuelle, courrier de réserves, rapport, texte collé, XSS, sanDB, fusion de synchro (préparer avec `python3 tests/t34_gen.py`) |
| t35.py | fonds d'écran animés Ninja et Pirate (feuilles, brume, shurikens, navire qui tangue, vagues, mouettes), menu des thèmes, mode « admirer le décor », animations coupables et mémorisées, mouvement réduit respecté, photo personnelle (réduite, locale, jamais synchronisée, valeurs piégées refusées), retrait, impression |
| t36.py | v9.15 : corbeille (suppression récupérable, restauration avec éléments liés et pièces jointes, suppression définitive, purge à 30 jours, compatibilité synchronisation) et réception (réserves, levée, réception définitive, alertes, échéancier, courriers, conformité) |
| t37.py | v9.16 : lecture des scans sur l’appareil (OCR français) : PDF image seul et photo JPEG, texte chiffré et effacé avec le document, recherche dans les scans, analyse d’assurance sur un scan, aucune requête externe |
| t38.py | v9.17 : rappels sur le téléphone (dates d’alerte J-30/J-7/J-1/J à 8 h, contenu envoyé au serveur sans donnée de marché, refus serveur, gestionnaires de notification du service worker) ; l’envoi réel vers un iPhone ne peut pas être testé ici |
| t33.py | onglet Réunions : enregistrement audio (micro simulé par Chrome), transcription et PV automatiques via l'IA (service simulé), relance automatique sans bouton après une panne (tentatives croissantes, abandon après plusieurs échecs sans perte de l'audio, reprise automatique à la réouverture de l'application), écoute/téléchargement de l'audio, verrouillage pendant un enregistrement, suppression et absence de suppression en cascade avec le marché |
| t39.py | analyseur de garanties (v9.19) : lecture du document, montant / délai de remise / durée / clauses, avance à garantir, exigences du CCAP lues depuis un texte collé, décisions manuelles, valeurs appliquées à la fiche sans écrasement, courrier de réserves, rapport, bouton dans la liste, XSS, états corrompus (préparer avec `python3 tests/t39_gen.py`) |

À lancer après chaque modification, avant de publier.
