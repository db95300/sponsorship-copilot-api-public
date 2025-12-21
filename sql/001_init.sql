CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS athletes (
  id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  country TEXT NOT NULL,
  position TEXT NOT NULL,
  level TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sponsors (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  sector TEXT NOT NULL,
  market TEXT NOT NULL,
  budget_range TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Documents that power RAG (EN/FR ready)
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  owner_type TEXT NOT NULL, -- "athlete" | "agency" | "sponsor"
  owner_id TEXT NOT NULL,
  locale TEXT NOT NULL, -- "en-GB" | "fr-FR"
  title TEXT NOT NULL,
  text_content TEXT NOT NULL,
  embedding vector(384), -- we'll fill later (can be NULL in early POC)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS interactions (
  id TEXT PRIMARY KEY,
  athlete_id TEXT NOT NULL REFERENCES athletes(id),
  sponsor_id TEXT NOT NULL REFERENCES sponsors(id),
  channel TEXT NOT NULL, -- "email" | "call"
  outcome TEXT NOT NULL, -- "no_reply" | "replied" | "interested"
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_documents_locale ON documents(locale);