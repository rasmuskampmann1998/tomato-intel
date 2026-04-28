-- ============================================================
-- MIGRATION 003: Experience type + per-user source preferences
-- + agentic scraper submitted_by field
-- ============================================================

-- 1. Experience column on user_profiles
ALTER TABLE user_profiles
  ADD COLUMN IF NOT EXISTS experience text
    CHECK (experience IN ('researcher', 'grower', 'breeder'))
    DEFAULT 'researcher';

-- 2. Per-user source preference table
-- is_followed=false means user explicitly unfollowed this source
-- Rows seeded on signup via seed_source_prefs_for_user()
CREATE TABLE IF NOT EXISTS user_source_prefs (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  source_id   uuid NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  is_followed boolean NOT NULL DEFAULT true,
  updated_at  timestamptz DEFAULT now(),
  UNIQUE(user_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_user_source_prefs_user
  ON user_source_prefs(user_id, is_followed);

ALTER TABLE user_source_prefs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own source prefs"
  ON user_source_prefs FOR ALL
  USING (user_id = auth.uid());

CREATE POLICY "Admins read all source prefs"
  ON user_source_prefs FOR SELECT
  USING (
    EXISTS (SELECT 1 FROM user_profiles WHERE id = auth.uid() AND role = 'admin')
  );

-- 3. Track who submitted a source (null = global/admin-managed)
ALTER TABLE sources
  ADD COLUMN IF NOT EXISTS submitted_by uuid REFERENCES auth.users(id) ON DELETE SET NULL;

-- 4. Update handle_new_user trigger to capture experience + organization from signup metadata
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO user_profiles (id, full_name, organization, experience)
  VALUES (
    NEW.id,
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'organization',
    COALESCE(NEW.raw_user_meta_data->>'experience', 'researcher')
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Seed function: bulk-inserts is_followed=true rows for all active sources
-- in the experience type's primary categories. Called after signup.
CREATE OR REPLACE FUNCTION seed_source_prefs_for_user(p_user_id uuid, p_experience text)
RETURNS void AS $$
DECLARE
  experience_categories text[];
BEGIN
  CASE p_experience
    WHEN 'researcher' THEN
      experience_categories := ARRAY['news', 'competitors', 'patents', 'regulations', 'social'];
    WHEN 'grower' THEN
      experience_categories := ARRAY['crops', 'news', 'regulations', 'social'];
    WHEN 'breeder' THEN
      experience_categories := ARRAY['genetics', 'patents', 'competitors', 'news'];
    ELSE
      experience_categories := ARRAY['news', 'competitors', 'crops', 'patents', 'regulations', 'genetics', 'social'];
  END CASE;

  INSERT INTO user_source_prefs (user_id, source_id, is_followed)
  SELECT p_user_id, s.id, true
  FROM sources s
  JOIN categories c ON c.id = s.category_id
  WHERE c.slug = ANY(experience_categories)
    AND s.active = true
  ON CONFLICT (user_id, source_id) DO NOTHING;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Allow authenticated users (and anon during signup flow) to call the seed function
GRANT EXECUTE ON FUNCTION seed_source_prefs_for_user TO anon, authenticated;
