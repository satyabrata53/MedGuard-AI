create extension if not exists "pgcrypto";

create table if not exists drugs (
  id bigserial primary key,
  generic_name text not null,
  generic_name_normalized text not null unique,
  drug_class text not null,
  renal_dosing jsonb not null default '{}'::jsonb
);

create table if not exists drug_interactions (
  id bigserial primary key,
  drug_a_normalized text not null,
  drug_b_normalized text not null,
  severity text not null check (severity in ('HARD_BLOCK', 'SEVERE', 'MODERATE', 'MINOR')),
  mechanism text not null,
  clinical_effect text not null,
  management text not null,
  unique (drug_a_normalized, drug_b_normalized)
);

create table if not exists allergy_cross_reactivity (
  id bigserial primary key,
  allergy_class text not null,
  cross_reacts_with text not null,
  cross_reactivity_pct numeric not null,
  guidance text not null
);

create table if not exists drug_aliases (
  id bigserial primary key,
  alias text not null unique,
  actual_drug text not null
);

create table if not exists patients (
  id text primary key,
  name text not null,
  age int not null,
  sex text not null check (sex in ('male', 'female')),
  race text not null default 'unspecified',
  weight_kg numeric,
  diagnoses jsonb not null default '[]'::jsonb,
  medications jsonb not null default '[]'::jsonb,
  allergies jsonb not null default '[]'::jsonb,
  labs jsonb not null default '{}'::jsonb,
  vitals jsonb not null default '{}'::jsonb,
  history jsonb not null default '{}'::jsonb
);

create index if not exists idx_drugs_normalized on drugs (generic_name_normalized);
create index if not exists idx_aliases_alias on drug_aliases (alias);
create index if not exists idx_interactions_pair on drug_interactions (drug_a_normalized, drug_b_normalized);
