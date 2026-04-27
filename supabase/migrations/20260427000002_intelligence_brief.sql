ALTER TABLE search_profiles ADD COLUMN IF NOT EXISTS intelligence_brief text; ALTER TABLE profile_items ADD COLUMN IF NOT EXISTS profile_relevance_score int;
