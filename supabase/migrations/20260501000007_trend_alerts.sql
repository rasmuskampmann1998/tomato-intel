-- Trend alerts: topics appearing in 3+ sources within 48h
CREATE TABLE IF NOT EXISTS trend_alerts (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  topic        text NOT NULL,
  item_ids     uuid[] NOT NULL DEFAULT '{}',
  source_count int NOT NULL DEFAULT 0,
  category_slug text,
  first_seen   timestamptz NOT NULL DEFAULT now(),
  last_seen    timestamptz NOT NULL DEFAULT now(),
  active       boolean NOT NULL DEFAULT true,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_trend_alerts_active ON trend_alerts (active, last_seen DESC);

ALTER TABLE trend_alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon read" ON trend_alerts FOR SELECT TO anon USING (true);
CREATE POLICY "service write" ON trend_alerts FOR ALL TO service_role USING (true);
