-- Run this in your InsForge project to store investigation history.

CREATE TABLE IF NOT EXISTS investigations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  root_cause TEXT NOT NULL,
  namespace TEXT NOT NULL DEFAULT 'default',
  confidence INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'success'
);

CREATE INDEX IF NOT EXISTS investigations_user_id_created_at_idx
  ON investigations (user_id, created_at DESC);

-- Optional: allow authenticated users to manage their own rows.
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;

CREATE POLICY investigations_select_own
  ON investigations
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY investigations_insert_own
  ON investigations
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Realtime channel pattern for investigation progress:
-- investigation:*
-- Clients subscribe to investigation:{investigation_id} during an active run.
