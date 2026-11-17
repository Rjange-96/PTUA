#!/bin/bash
# Teste les fonctions SQL du serveur (partage + rappels) dans une base PostgreSQL jetable. Ne touche jamais au vrai serveur.
# Usage : bash tests/sql_push.sh     (nécessite PostgreSQL ≥ 14 installé localement ; ignoré sinon)
cd "$(dirname "$0")/.." || exit 1
B=$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | sort -V | tail -1)
[ -x "$B/initdb" ] || { echo "➖ PostgreSQL absent : test SQL ignoré."; exit 0; }
D=$(mktemp -d /tmp/ptuasql.XXXXXX); chmod 755 "$D"; PORT=55432
RUN(){ if [ "$(id -u)" = 0 ]; then su postgres -c "$*"; else bash -c "$*"; fi; }
[ "$(id -u)" = 0 ] && chown postgres "$D"
RUN "$B/initdb -D $D/data -A trust -U postgres >/dev/null && $B/pg_ctl -D $D/data -o '-p $PORT -k $D -c listen_addresses=' -l $D/log -w start >/dev/null" || { cat "$D/log"; exit 1; }
trap 'RUN "$B/pg_ctl -D $D/data -m immediate stop >/dev/null"; rm -rf "$D"' EXIT
Q(){ psql -h "$D" -p $PORT -U postgres -X -q -tA -v ON_ERROR_STOP=1 "$@"; }
Q >/dev/null <<'EOF'
create role anon; create role authenticated; create role service_role;
create schema extensions; create extension pgcrypto with schema extensions;
-- schéma de base minimal (créé avant la v9.5 sur le serveur, absent du dépôt)
create table public.ptua_sync(id text primary key, auth_hash text not null, blob text, ver bigint not null default 1, created_at timestamptz default now(), updated_at timestamptz default now());
create table public.ptua_hist(id text, ver bigint, blob text, saved_at timestamptz default now());
create table public.ptua_files(id text, fid text, blob text, size int, removed boolean default false, primary key(id,fid));
create table public.ptua_agent_rate(id text primary key, win timestamptz, n int);
EOF
for f in supabase/v9.5_partage_collegue.sql supabase/v9.17_rappels_push.sql supabase/v9.22_push_durci.sql; do Q -f "$f" >/dev/null || { echo "❌ $f ne s'applique pas"; exit 1; }; done
A=$(printf 'a%.0s' $(seq 64)); H=$(printf '1%.0s' $(seq 64)); X=$(printf 'b%.0s' $(seq 64))
Q -c "insert into ptua_sync(id,auth_hash) values ('$A', encode(extensions.digest('$H','sha256'),'hex'))"
set_(){ Q -c "set role anon; select ptua_push_set('$1','$2','$3','{\"endpoint\":\"$3\",\"keys\":{\"p256dh\":\"k\",\"auth\":\"a\"}}',array[$4::bigint])"; }
KO=0; ck(){ if [ "$2" = "$3" ]; then echo "✅ $1"; else echo "❌ $1 : obtenu « $2 », attendu « $3 »"; KO=1; fi; }
ck "adresse de notification Apple acceptée" "$(set_ $A $H https://web.push.apple.com/abc 4000000000)" ok
ck "adresse Google acceptée" "$(set_ $A $H https://fcm.googleapis.com/fcm/send/x 4000000000)" ok
ck "site quelconque refusé" "$(set_ $A $H https://evil.example/x 4000000000)" invalide
ck "faux hôte Apple refusé" "$(set_ $A $H https://web.push.apple.com.evil.example/x 4000000000)" invalide
ck "mauvais secret refusé" "$(set_ $A $X https://fcm.googleapis.com/fcm/send/y 4000000000)" refus
ck "fonction d'envoi interdite à l'application" "$(Q -c "set role anon; select count(*) from ptua_push_due(1)" 2>&1 | grep -c 'permission denied')" 1
ck "fonctions internes de partage interdites" "$(Q -c "set role anon; select ptua_ok('$A','$H')" 2>&1 | grep -c 'permission denied')" 1
Q -c "update ptua_push set due=array[1900000000::bigint], sent_at=1800000000"
ck "rappel dû sélectionné" "$(Q -c "set role service_role; select count(*) from ptua_push_due(1900000001)")" 2
ck "rien avant l'échéance" "$(Q -c "set role service_role; select count(*) from ptua_push_due(1899999999)")" 0
Q -c "insert into ptua_push(endpoint,sid,sub) select 'https://fcm.googleapis.com/fill/'||g, 'x'||g, '{}' from generate_series(1,2000) g"
ck "table pleine : nouvel appareil refusé (limite)" "$(set_ $A $H https://fcm.googleapis.com/fcm/send/new 4000000000)" limite
ck "table pleine : appareil déjà inscrit mis à jour" "$(set_ $A $H https://web.push.apple.com/abc 4000000000)" ok
ck "rappels dus toujours trouvés malgré la table pleine" "$(Q -c "set role service_role; select count(*) from ptua_push_due(1900000001)")" 1
exit $KO
