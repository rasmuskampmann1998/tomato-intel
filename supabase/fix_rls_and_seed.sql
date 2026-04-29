-- ============================================================
-- RUN THIS IN: Supabase Dashboard → SQL Editor
-- Project: evifsyqtrwwetfqkvlni
-- What it does: Fixes infinite recursion in RLS + seeds demo profiles
-- ============================================================

-- STEP 1: Drop the recursive admin policies causing infinite loop
DROP POLICY IF EXISTS "Admins read all user profiles" ON user_profiles;
DROP POLICY IF EXISTS "Admins manage categories" ON categories;
DROP POLICY IF EXISTS "Admins manage sources" ON sources;

-- STEP 2: Replace broken category/source policies with open read (demo mode)
DROP POLICY IF EXISTS "Anyone can read categories" ON categories;
CREATE POLICY "Anyone can read categories"
  ON categories FOR SELECT USING (true);

DROP POLICY IF EXISTS "Anyone can read sources" ON sources;
CREATE POLICY "Anyone can read sources"
  ON sources FOR SELECT USING (true);

DROP POLICY IF EXISTS "Anyone can read scraped items" ON scraped_items;
CREATE POLICY "Anyone can read scraped items"
  ON scraped_items FOR SELECT USING (true);

DROP POLICY IF EXISTS "Anyone can read interpreted items" ON interpreted_items;
CREATE POLICY "Anyone can read interpreted items"
  ON interpreted_items FOR SELECT USING (true);

DROP POLICY IF EXISTS "Anyone can read search profiles" ON search_profiles;
DROP POLICY IF EXISTS "Admins read all profiles" ON search_profiles;
CREATE POLICY "Anyone can read search profiles"
  ON search_profiles FOR SELECT USING (true);

DROP POLICY IF EXISTS "Anyone can read profile items" ON profile_items;
DROP POLICY IF EXISTS "Users see own profile items" ON profile_items;
CREATE POLICY "Anyone can read profile items"
  ON profile_items FOR SELECT USING (true);

-- STEP 3: Allow anon to write demo profiles (user_id = NULL)
DROP POLICY IF EXISTS "Anon manage demo profiles" ON search_profiles;
CREATE POLICY "Anon manage demo profiles"
  ON search_profiles FOR ALL TO anon
  USING (user_id IS NULL)
  WITH CHECK (user_id IS NULL);

DROP POLICY IF EXISTS "Anon manage demo profile items" ON profile_items;
CREATE POLICY "Anon manage demo profile items"
  ON profile_items FOR ALL TO anon
  USING (true) WITH CHECK (true);

-- STEP 4: Seed default search profiles (one per category)
INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT NULL, c.id, 'General News',
  ARRAY['Tomato News', 'Tomato Announcements', 'Tomato Novelty'],
  ARRAY['en','zh','ja','hi','es','ar','tr'], 'daily'
FROM categories c WHERE c.slug = 'news'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT NULL, c.id, 'Tomato Competitors',
  ARRAY['Tomato Variety', 'Tomato Seed Company', 'Tomato Results'],
  ARRAY['en','zh','ja','hi','es','ar','tr'], 'weekly'
FROM categories c WHERE c.slug = 'competitors'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT NULL, c.id, 'Seed Growing',
  ARRAY['Tomato Seed Production', 'Tomato Seed Quality', 'Tomato Seed Disease'],
  ARRAY['en','zh','ja','hi','es','ar','tr'], 'weekly'
FROM categories c WHERE c.slug = 'crops'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT NULL, c.id, 'Patent Search',
  ARRAY['Tomato Patent', 'Tomato Intellectual Property'],
  ARRAY['en','zh','hi','es'], 'monthly'
FROM categories c WHERE c.slug = 'patents'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT NULL, c.id, 'Seed Regulations',
  ARRAY['Tomato Seed Health', 'Tomato Seed Disease', 'Tomato Quarantine Pest', 'Tomato Seed Certificate'],
  ARRAY['en','zh','ja','hi','es','ar','tr'], 'monthly'
FROM categories c WHERE c.slug = 'regulations'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT NULL, c.id, 'Genetics & Breeding',
  ARRAY['Tomato Trait', 'Tomato Seed', 'Tomato Disease', 'Tomato Genetic'],
  ARRAY['en','zh','ja','hi','es','ar','tr'], 'monthly'
FROM categories c WHERE c.slug = 'genetics'
ON CONFLICT DO NOTHING;

INSERT INTO search_profiles (user_id, category_id, name, search_terms, languages, frequency)
SELECT NULL, c.id, 'Social Signals',
  ARRAY['Tomato', 'Tomato News', 'Tomato Seed'],
  ARRAY['en','zh','ja','hi','es','ar','tr'], 'daily'
FROM categories c WHERE c.slug = 'social'
ON CONFLICT DO NOTHING;

-- Verify
SELECT slug, name FROM categories ORDER BY sort_order;
SELECT name, frequency FROM search_profiles ORDER BY created_at;
