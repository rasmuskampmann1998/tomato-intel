-- Social Watched Accounts
-- Stores specific platform handles/profiles to monitor alongside keyword search.

CREATE TABLE IF NOT EXISTS social_watched_accounts (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  platform      text NOT NULL CHECK (platform IN ('twitter','reddit','linkedin','instagram','facebook','tiktok')),
  handle        text NOT NULL,        -- @username / r/subreddit / company-slug / page-url
  display_name  text,
  profile_url   text,
  account_type  text NOT NULL DEFAULT 'competitor'
                     CHECK (account_type IN ('competitor','media','researcher','influencer')),
  active        boolean NOT NULL DEFAULT true,
  last_scraped_at timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  UNIQUE(platform, handle)
);

ALTER TABLE social_watched_accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_read_social_watched"
  ON social_watched_accounts FOR SELECT TO anon USING (true);
CREATE POLICY "service_write_social_watched"
  ON social_watched_accounts FOR ALL TO service_role USING (true);

-- Seed competitor + media accounts
INSERT INTO social_watched_accounts (platform, handle, display_name, profile_url, account_type) VALUES
  -- Twitter
  ('twitter', 'rijkzwaan',       'Rijk Zwaan',           'https://twitter.com/rijkzwaan',        'competitor'),
  ('twitter', 'enzazaden',       'Enza Zaden',           'https://twitter.com/enzazaden',         'competitor'),
  ('twitter', 'syngenta',        'Syngenta',             'https://twitter.com/syngenta',          'competitor'),
  ('twitter', 'bejoworld',       'Bejo Seeds',           'https://twitter.com/bejoworld',         'competitor'),
  ('twitter', 'HortiDaily',      'HortiDaily',           'https://twitter.com/HortiDaily',        'media'),
  ('twitter', 'SeedWorld_mag',   'Seed World',           'https://twitter.com/SeedWorld_mag',     'media'),
  ('twitter', 'ISHS_hort',       'ISHS Horticulture',   'https://twitter.com/ISHS_hort',         'researcher'),
  -- LinkedIn
  ('linkedin', 'rijk-zwaan',             'Rijk Zwaan',           'https://www.linkedin.com/company/rijk-zwaan',             'competitor'),
  ('linkedin', 'enza-zaden',             'Enza Zaden',           'https://www.linkedin.com/company/enza-zaden',             'competitor'),
  ('linkedin', 'syngenta',               'Syngenta',             'https://www.linkedin.com/company/syngenta',               'competitor'),
  ('linkedin', 'bejo-seeds',             'Bejo Seeds',           'https://www.linkedin.com/company/bejo-seeds',             'competitor'),
  ('linkedin', 'de-ruiter-seeds',        'De Ruiter Seeds',      'https://www.linkedin.com/company/de-ruiter-seeds',        'competitor'),
  ('linkedin', 'hortidaily',             'HortiDaily',           'https://www.linkedin.com/company/hortidaily',             'media'),
  -- Instagram
  ('instagram', 'rijkzwaan',      'Rijk Zwaan',     'https://www.instagram.com/rijkzwaan',       'competitor'),
  ('instagram', 'enzazaden',      'Enza Zaden',     'https://www.instagram.com/enzazaden',       'competitor'),
  ('instagram', 'syngenta',       'Syngenta',       'https://www.instagram.com/syngenta',        'competitor'),
  ('instagram', 'hortidaily',     'HortiDaily',     'https://www.instagram.com/hortidaily',      'media'),
  -- Reddit
  ('reddit', 'tomatoes',          'r/tomatoes',     'https://www.reddit.com/r/tomatoes',         'influencer'),
  ('reddit', 'horticulture',      'r/horticulture', 'https://www.reddit.com/r/horticulture',     'influencer'),
  ('reddit', 'vegetablegardening','r/vegetablegardening','https://www.reddit.com/r/vegetablegardening','influencer'),
  -- TikTok
  ('tiktok', 'rijkzwaan',        'Rijk Zwaan',     NULL,                                          'competitor'),
  ('tiktok', 'enzazaden',        'Enza Zaden',     NULL,                                          'competitor'),
  -- Facebook
  ('facebook', 'RijkZwaan',      'Rijk Zwaan',     'https://www.facebook.com/RijkZwaan',         'competitor'),
  ('facebook', 'HortiDaily',     'HortiDaily',     'https://www.facebook.com/HortiDaily',        'media')
ON CONFLICT (platform, handle) DO NOTHING;
