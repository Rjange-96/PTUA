-- v9.5 : partage avec un collègue (accès séparé et révocable). Additif et non destructif.
create table if not exists public.ptua_members(
  lid text primary key check (lid ~ '^[0-9a-f]{64}$'),
  sid text not null references public.ptua_sync(id) on delete cascade,
  auth_hash text not null check (auth_hash ~ '^[0-9a-f]{64}$'),
  env text not null default '' check (length(env) <= 4000),
  label text not null default '' check (length(label) <= 60),
  created_at timestamptz not null default now(),
  last_seen timestamptz,
  revoked_at timestamptz);
create index if not exists ptua_members_sid on public.ptua_members(sid);
alter table public.ptua_members enable row level security;
revoke all on table public.ptua_members from public, anon, authenticated;

-- Propriétaire : la clé de synchronisation d'origine. Accès : propriétaire OU collègue non révoqué.
create or replace function public.ptua_owner(p_id text, p_auth text) returns boolean
language sql stable security definer set search_path = '' as $$
  select p_id is not null and p_auth is not null and exists(select 1 from public.ptua_sync s
    where s.id = p_id and s.auth_hash = encode(extensions.digest(p_auth, 'sha256'), 'hex'));
$$;
create or replace function public.ptua_ok(p_id text, p_auth text) returns boolean
language sql stable security definer set search_path = '' as $$
  select public.ptua_owner(p_id, p_auth) or (p_id is not null and p_auth is not null and exists(select 1 from public.ptua_members m
    where m.sid = p_id and m.revoked_at is null and m.auth_hash = encode(extensions.digest(p_auth, 'sha256'), 'hex')));
$$;
revoke execute on function public.ptua_owner(text, text) from public, anon, authenticated;
revoke execute on function public.ptua_ok(text, text) from public, anon, authenticated;

-- Fonctions existantes : mêmes signatures, l'accès accepte désormais aussi un collègue autorisé
create or replace function public.ptua_get(p_id text, p_auth text)
returns table(ver bigint, blob text, updated_at timestamptz)
language sql stable security definer set search_path = '' as $$
  select s.ver, s.blob, s.updated_at from public.ptua_sync s where s.id = p_id and public.ptua_ok(p_id, p_auth);
$$;

create or replace function public.ptua_put(p_id text, p_auth text, p_blob text, p_ver bigint) returns bigint
language plpgsql security definer set search_path = '' as $$
declare v bigint; h text;
begin
  if p_id !~ '^[0-9a-f]{64}$' or p_auth !~ '^[0-9a-f]{64}$' or p_blob is null or length(p_blob) >= 5000000 then
    raise exception 'requete invalide';
  end if;
  h := encode(extensions.digest(p_auth, 'sha256'), 'hex');
  if p_ver = 0 then
    -- anti-abus : 20 nouveaux espaces par heure au maximum, 300 Mo au total
    if (select count(*) from public.ptua_sync where created_at > now() - interval '1 hour') >= 20 then
      raise exception 'trop de creations, reessayez plus tard';
    end if;
    if pg_total_relation_size('public.ptua_sync') + pg_total_relation_size('public.ptua_hist') > 300000000 then
      raise exception 'espace de stockage plein';
    end if;
    insert into public.ptua_sync(id, auth_hash, blob) values (p_id, h, p_blob)
      on conflict (id) do nothing returning ver into v;
    return coalesce(v, -1);
  end if;
  if not public.ptua_ok(p_id, p_auth) then return -1; end if;
  update public.ptua_sync s set blob = p_blob, ver = s.ver + 1, updated_at = now()
    where s.id = p_id and s.ver = p_ver returning s.ver into v;
  return coalesce(v, -1);
end $$;

create or replace function public.ptua_hist_list(p_id text, p_auth text)
returns table(ver bigint, saved_at timestamptz, taille integer)
language sql stable security definer set search_path = '' as $$
  select h.ver, h.saved_at, length(h.blob) from public.ptua_hist h
  where h.id = p_id and public.ptua_ok(p_id, p_auth) order by h.ver desc;
$$;

create or replace function public.ptua_hist_get(p_id text, p_auth text, p_ver bigint) returns text
language sql stable security definer set search_path = '' as $$
  select h.blob from public.ptua_hist h where h.id = p_id and h.ver = p_ver and public.ptua_ok(p_id, p_auth);
$$;

create or replace function public.ptua_file_get(p_id text, p_auth text, p_fid text) returns text
language sql stable security definer set search_path = '' as $$
  select f.blob from public.ptua_files f
  where f.id = p_id and f.fid = p_fid and not f.removed and public.ptua_ok(p_id, p_auth);
$$;

create or replace function public.ptua_file_put(p_id text, p_auth text, p_fid text, p_blob text) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  if p_id !~ '^[0-9a-f]{64}$' or p_auth !~ '^[0-9a-f]{64}$' or p_fid !~ '^[A-Za-z0-9_-]{1,64}$'
     or p_blob is null or length(p_blob) >= 6000000 then
    raise exception 'requete invalide';
  end if;
  if not public.ptua_ok(p_id, p_auth) then
    raise exception 'acces refuse';
  end if;
  if (select coalesce(sum(f.size),0) from public.ptua_files f where f.id = p_id) + length(p_blob) > 250000000
     or (select coalesce(sum(f.size),0) from public.ptua_files f) + length(p_blob) > 380000000 then
    raise exception 'quota de documents atteint';
  end if;
  insert into public.ptua_files(id, fid, blob, size) values (p_id, p_fid, p_blob, length(p_blob))
    on conflict do nothing;
  return true;
end $$;

create or replace function public.ptua_file_del(p_id text, p_auth text, p_fid text) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  if not public.ptua_ok(p_id, p_auth) then
    return false;
  end if;
  update public.ptua_files f set blob = '', size = 0, removed = true where f.id = p_id and f.fid = p_fid;
  return true;
end $$;

create or replace function public.ptua_agent_gate(p_id text, p_auth text) returns text
language plpgsql security definer set search_path = '' as $$
declare c integer;
begin
  if p_id is null or p_auth is null or p_id !~ '^[0-9a-f]{64}$' or p_auth !~ '^[0-9a-f]{64}$' then
    return 'refus';
  end if;
  if not public.ptua_ok(p_id, p_auth) then return 'refus'; end if;
  insert into public.ptua_agent_rate as r (id, win, n) values (p_id, now(), 1)
    on conflict (id) do update set
      n   = case when r.win < now() - interval '1 hour' then 1 else r.n + 1 end,
      win = case when r.win < now() - interval '1 hour' then now() else r.win end
    returning r.n into c;
  if c > 40 then return 'limite'; end if;
  return 'ok';
end $$;

-- Gestion des accès : réservée au propriétaire
create or replace function public.ptua_member_add(p_id text, p_auth text, p_lid text, p_mauth text, p_env text, p_label text) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  if p_id !~ '^[0-9a-f]{64}$' or p_auth !~ '^[0-9a-f]{64}$' or p_lid !~ '^[0-9a-f]{64}$' or p_mauth !~ '^[0-9a-f]{64}$'
     or p_env is null or length(p_env) > 4000 or length(coalesce(p_label,'')) > 60 then
    raise exception 'requete invalide';
  end if;
  if not public.ptua_owner(p_id, p_auth) then raise exception 'acces refuse'; end if;
  if (select count(*) from public.ptua_members m where m.sid = p_id and m.revoked_at is null) >= 10 then
    raise exception 'limite de 10 acces atteinte';
  end if;
  insert into public.ptua_members(lid, sid, auth_hash, env, label)
    values (p_lid, p_id, encode(extensions.digest(p_mauth, 'sha256'), 'hex'), p_env, coalesce(p_label,''));
  return true;
end $$;

create or replace function public.ptua_member_list(p_id text, p_auth text)
returns table(lid text, label text, created_at timestamptz, last_seen timestamptz, revoked_at timestamptz)
language sql stable security definer set search_path = '' as $$
  select m.lid, m.label, m.created_at, m.last_seen, m.revoked_at from public.ptua_members m
  where m.sid = p_id and public.ptua_owner(p_id, p_auth) order by m.created_at desc;
$$;

create or replace function public.ptua_member_revoke(p_id text, p_auth text, p_lid text) returns boolean
language plpgsql security definer set search_path = '' as $$
begin
  if not public.ptua_owner(p_id, p_auth) then return false; end if;
  update public.ptua_members m set revoked_at = coalesce(m.revoked_at, now()), env = ''
    where m.sid = p_id and m.lid = p_lid;
  return found;
end $$;

-- Ouverture d'une invitation par le collègue : renvoie l'espace et l'enveloppe chiffrée (illisible sans le code d'invitation)
create or replace function public.ptua_member_open(p_lid text, p_auth text)
returns table(sid text, env text)
language plpgsql security definer set search_path = '' as $$
begin
  if p_lid !~ '^[0-9a-f]{64}$' or p_auth !~ '^[0-9a-f]{64}$' then return; end if;
  return query with u as (update public.ptua_members m set last_seen = now()
    where m.lid = p_lid and m.revoked_at is null and m.auth_hash = encode(extensions.digest(p_auth, 'sha256'), 'hex')
    returning m.sid as s, m.env as e) select u.s, u.e from u;
end $$;

revoke execute on function public.ptua_member_add(text,text,text,text,text,text) from public, authenticated;
revoke execute on function public.ptua_member_list(text,text) from public, authenticated;
revoke execute on function public.ptua_member_revoke(text,text,text) from public, authenticated;
revoke execute on function public.ptua_member_open(text,text) from public, authenticated;
grant execute on function public.ptua_member_add(text,text,text,text,text,text) to anon;
grant execute on function public.ptua_member_list(text,text) to anon;
grant execute on function public.ptua_member_revoke(text,text,text) to anon;
grant execute on function public.ptua_member_open(text,text) to anon;
