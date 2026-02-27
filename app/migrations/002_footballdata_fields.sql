ALTER TABLE competitions ADD COLUMN provider_code TEXT;
ALTER TABLE competitions ADD COLUMN provider_id INTEGER;

ALTER TABLE teams ADD COLUMN provider_id INTEGER;
ALTER TABLE matches ADD COLUMN provider_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_comp_provider_code ON competitions(provider_code);
CREATE INDEX IF NOT EXISTS idx_team_provider_id ON teams(provider_id);
CREATE INDEX IF NOT EXISTS idx_match_provider_id ON matches(provider_id);