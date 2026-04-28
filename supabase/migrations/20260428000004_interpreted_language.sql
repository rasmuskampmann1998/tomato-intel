-- Add original_language to interpreted_items for efficient feed display
-- (avoids joining scraped_items just to show the translation badge)

ALTER TABLE interpreted_items
  ADD COLUMN IF NOT EXISTS original_language text;

-- Backfill from scraped_items for existing rows
UPDATE interpreted_items ii
SET original_language = si.language
FROM scraped_items si
WHERE si.id = ii.scraped_item_id
  AND ii.original_language IS NULL;
