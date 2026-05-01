-- Add digest_html column to weekly_data_reports for storing full HTML digest
ALTER TABLE weekly_data_reports ADD COLUMN IF NOT EXISTS digest_html text;
