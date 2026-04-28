-- Allow anonymous (unauthenticated) reads on public tables for demo mode.
-- The original policies only allowed 'authenticated' role which breaks the demo.

-- Categories
DROP POLICY IF EXISTS "Anyone can read categories" ON categories;
CREATE POLICY "Anyone can read categories"
  ON categories FOR SELECT USING (true);

-- Sources
DROP POLICY IF EXISTS "Anyone can read sources" ON sources;
CREATE POLICY "Anyone can read sources"
  ON sources FOR SELECT USING (true);

-- Scraped items
DROP POLICY IF EXISTS "Anyone can read scraped items" ON scraped_items;
CREATE POLICY "Anyone can read scraped items"
  ON scraped_items FOR SELECT USING (true);

-- Interpreted items
DROP POLICY IF EXISTS "Anyone can read interpreted items" ON interpreted_items;
CREATE POLICY "Anyone can read interpreted items"
  ON interpreted_items FOR SELECT USING (true);

-- Search profiles: allow anon to read all (demo — no user-specific filtering)
DROP POLICY IF EXISTS "Admins read all profiles" ON search_profiles;
CREATE POLICY "Anyone can read search profiles"
  ON search_profiles FOR SELECT USING (true);

-- Profile items: allow anon to read all
DROP POLICY IF EXISTS "Users see own profile items" ON profile_items;
CREATE POLICY "Anyone can read profile items"
  ON profile_items FOR SELECT USING (true);
