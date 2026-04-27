-- Tomato Seed Intel Dashboard — Supabase Schema
-- Run via: supabase db push (with PAT sbp_4d72b7df0722fd17d6b99594f78229641e6ad0a7)
-- Project ref: nafzfhrveaqfyxlkktxg

-- ============================================================
-- CATEGORIES (7 pre-seeded, global, admin-managed)
-- ============================================================
CREATE TABLE IF NOT EXISTS categories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  description text,
  default_frequency text DEFAULT 'weekly', -- 'daily'|'weekly'|'monthly'
  icon text,                               -- emoji or icon name
  sort_order int DEFAULT 0
);

INSERT INTO categories (name, slug, description, default_frequency, icon, sort_order) VALUES
  ('News & Updates',       'news',        'Latest horticulture and agriculture news worldwide', 'daily',   '📰', 1),
  ('Competitors',          'competitors', 'Competitor activity, product launches, funding',     'weekly',  '🏢', 2),
  ('Crop Recommendations', 'crops',       'Breeding advice, growing conditions, yield tips',    'weekly',  '🌱', 3),
  ('Tomato Patents',       'patents',     'Patent filings across EPO, USPTO, CNIPA, IP India',  'monthly', '📋', 4),
  ('Regulations',          'regulations', 'Regulatory changes across 27 countries',             'monthly', '⚖️', 5),
  ('Genetics',             'genetics',    'Genetic traits, variety data, molecular markers',    'monthly', '🧬', 6),
  ('Social Media',         'social',      'Reddit, Twitter/X, Instagram, LinkedIn signals',     'daily',   '💬', 7)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- SOURCES (global, admin-managed, shared across all users)
-- ============================================================
CREATE TABLE IF NOT EXISTS sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id uuid REFERENCES categories(id) ON DELETE CASCADE,
  name text NOT NULL,
  url text NOT NULL,
  rss_url text,
  scrape_type text NOT NULL, -- 'rss'|'html'|'apify'|'api_epo'|'api_uspto'|'api_cnipa'|'praw'
  apify_actor text,          -- e.g. 'apify/web-scraper'
  css_selector text,         -- for html scrape type
  is_required boolean DEFAULT false,
  active boolean DEFAULT true,
  last_scraped_at timestamptz,
  scrape_status text,        -- 'ok'|'failed'|'empty'
  language text DEFAULT 'en',
  created_at timestamptz DEFAULT now()
);

-- ============================================================
-- SCRAPED ITEMS (raw content, shared pool, deduped by URL)
-- ============================================================
CREATE TABLE IF NOT EXISTS scraped_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid REFERENCES sources(id) ON DELETE SET NULL,
  category_slug text NOT NULL,
  title text,
  url text UNIQUE NOT NULL,
  content text,
  language text,
  author text,
  published_at timestamptz,
  scraped_at timestamptz DEFAULT now(),
  is_processed boolean DEFAULT false,
  -- Social media fields
  platform text,       -- 'reddit'|'twitter'|'instagram'|'linkedin'|'facebook'
  like_count int,
  comment_count int,
  share_count int,
  view_count int,
  post_type text       -- 'post'|'reel'|'tweet'|'comment'|'video'
);

CREATE INDEX IF NOT EXISTS idx_scraped_items_source ON scraped_items(source_id, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_scraped_items_category ON scraped_items(category_slug, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_scraped_items_unprocessed ON scraped_items(is_processed) WHERE is_processed = false;

-- ============================================================
-- INTERPRETED ITEMS (Claude-processed, one per scraped item)
-- ============================================================
CREATE TABLE IF NOT EXISTS interpreted_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scraped_item_id uuid REFERENCES scraped_items(id) ON DELETE CASCADE UNIQUE,
  title_en text,
  summary_en text,
  relevance_score int,  -- 1-10
  tags text[],
  category_slug text,
  interpreted_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interpreted_category ON interpreted_items(category_slug, interpreted_at DESC);

-- ============================================================
-- SEARCH PROFILES (per user, per category)
-- ============================================================
CREATE TABLE IF NOT EXISTS search_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  category_id uuid REFERENCES categories(id) ON DELETE CASCADE,
  name text,
  search_terms text[] NOT NULL,
  languages text[] DEFAULT '{"en"}',
  frequency text DEFAULT 'weekly',
  last_run_at timestamptz,
  new_since_last_visit int DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_search_profiles_user ON search_profiles(user_id);

-- ============================================================
-- PROFILE ITEMS (many-to-many: profiles <-> scraped items)
-- ============================================================
CREATE TABLE IF NOT EXISTS profile_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  search_profile_id uuid REFERENCES search_profiles(id) ON DELETE CASCADE,
  scraped_item_id uuid REFERENCES scraped_items(id) ON DELETE CASCADE,
  matched_at timestamptz DEFAULT now(),
  is_new boolean DEFAULT true,
  UNIQUE(search_profile_id, scraped_item_id)
);

CREATE INDEX IF NOT EXISTS idx_profile_items_profile ON profile_items(search_profile_id, is_new, matched_at DESC);

-- ============================================================
-- USER PROFILES (display info, role)
-- ============================================================
CREATE TABLE IF NOT EXISTS user_profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name text,
  organization text,
  role text DEFAULT 'user', -- 'admin'|'user'
  created_at timestamptz DEFAULT now()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- Categories: readable by all authenticated users
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read categories"
  ON categories FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Admins manage categories"
  ON categories FOR ALL USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Sources: readable by all, managed by admins
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read sources"
  ON sources FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Admins manage sources"
  ON sources FOR ALL USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Scraped items: readable by all authenticated users
ALTER TABLE scraped_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read scraped items"
  ON scraped_items FOR SELECT USING (auth.role() = 'authenticated');

-- Interpreted items: readable by all authenticated users
ALTER TABLE interpreted_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read interpreted items"
  ON interpreted_items FOR SELECT USING (auth.role() = 'authenticated');

-- Search profiles: users manage only their own
ALTER TABLE search_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own profiles"
  ON search_profiles FOR ALL USING (user_id = auth.uid());
CREATE POLICY "Admins read all profiles"
  ON search_profiles FOR SELECT USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- Profile items: users see only their own
ALTER TABLE profile_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users see own profile items"
  ON profile_items FOR ALL USING (
    search_profile_id IN (SELECT id FROM search_profiles WHERE user_id = auth.uid())
  );

-- User profiles: users manage own, admins see all
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users manage own profile"
  ON user_profiles FOR ALL USING (id = auth.uid());
CREATE POLICY "Admins read all user profiles"
  ON user_profiles FOR SELECT USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- ============================================================
-- FUNCTION: auto-create user_profile on signup
-- ============================================================
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO user_profiles (id, full_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name')
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- FUNCTION: match scraped items to search profiles
-- Called after each scrape run to link new items to profiles
-- ============================================================
CREATE OR REPLACE FUNCTION match_items_to_profiles()
RETURNS void AS $$
DECLARE
  profile RECORD;
  item RECORD;
  term text;
  matches boolean;
BEGIN
  FOR profile IN SELECT * FROM search_profiles LOOP
    FOR item IN
      SELECT si.id, si.title, si.content, si.category_slug, si.language
      FROM scraped_items si
      WHERE si.scraped_at > COALESCE(profile.last_run_at, '1970-01-01')
        AND EXISTS (
          SELECT 1 FROM categories c
          WHERE c.id = profile.category_id
            AND c.slug = si.category_slug
        )
    LOOP
      matches := false;
      FOREACH term IN ARRAY profile.search_terms LOOP
        IF (item.title ILIKE '%' || term || '%')
           OR (item.content ILIKE '%' || term || '%') THEN
          matches := true;
          EXIT;
        END IF;
      END LOOP;

      IF matches THEN
        INSERT INTO profile_items (search_profile_id, scraped_item_id)
        VALUES (profile.id, item.id)
        ON CONFLICT (search_profile_id, scraped_item_id) DO NOTHING;
      END IF;
    END LOOP;

    -- Update new_since_last_visit count
    UPDATE search_profiles
    SET new_since_last_visit = (
      SELECT COUNT(*) FROM profile_items
      WHERE search_profile_id = profile.id AND is_new = true
    )
    WHERE id = profile.id;
  END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
