-- Demo mode: allow anon writes + seed default search profiles
-- search_profiles with user_id = NULL are shared demo profiles visible to all anon users

-- Allow anon INSERT/UPDATE/DELETE on profiles with no owner
CREATE POLICY "Anon manage demo profiles"
  ON search_profiles FOR ALL TO anon
  USING (user_id IS NULL)
  WITH CHECK (user_id IS NULL);

-- Allow anon to write profile_items (mark-as-read in demo mode)
CREATE POLICY "Anon manage demo profile items"
  ON profile_items FOR ALL TO anon
  USING (true) WITH CHECK (true);

-- ============================================================
-- SEED DEFAULT SEARCH PROFILES (one per category, from Excel Tab 2)
-- user_id = NULL = shared demo profiles, visible without auth
-- ============================================================

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT
  NULL,
  c.id,
  'General News',
  ARRAY['Tomato News', 'Tomato Announcements', 'Tomato Novelty'],
  ARRAY['en', 'zh', 'ja', 'hi', 'es', 'ar', 'tr'],
  'daily'
FROM categories c WHERE c.slug = 'news'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT
  NULL,
  c.id,
  'Tomato Competitors',
  ARRAY['Tomato Variety', 'Tomato Seed Company', 'Tomato Results'],
  ARRAY['en', 'zh', 'ja', 'hi', 'es', 'ar', 'tr'],
  'weekly'
FROM categories c WHERE c.slug = 'competitors'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT
  NULL,
  c.id,
  'Seed Growing',
  ARRAY['Tomato Seed Production', 'Tomato Seed Quality', 'Tomato Seed Disease'],
  ARRAY['en', 'zh', 'ja', 'hi', 'es', 'ar', 'tr'],
  'weekly'
FROM categories c WHERE c.slug = 'crops'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT
  NULL,
  c.id,
  'Patent Search',
  ARRAY['Tomato Patent', 'Tomato Intellectual Property'],
  ARRAY['en', 'zh', 'hi', 'es'],
  'monthly'
FROM categories c WHERE c.slug = 'patents'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT
  NULL,
  c.id,
  'Seed Regulations',
  ARRAY['Tomato Seed Health', 'Tomato Seed Disease', 'Tomato Quarantine Pest', 'Tomato Seed Certificate'],
  ARRAY['en', 'zh', 'ja', 'hi', 'es', 'ar', 'tr'],
  'monthly'
FROM categories c WHERE c.slug = 'regulations'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT
  NULL,
  c.id,
  'Genetics & Breeding',
  ARRAY['Tomato Trait', 'Tomato Seed', 'Tomato Disease', 'Tomato Genetic'],
  ARRAY['en', 'zh', 'ja', 'hi', 'es', 'ar', 'tr'],
  'monthly'
FROM categories c WHERE c.slug = 'genetics'
ON CONFLICT DO NOTHING;
