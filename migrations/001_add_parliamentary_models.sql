-- Migration: Add Parliamentary Models for OpenParliament Integration
-- Version: 001
-- Description: Adds enhanced parliamentary data models for Hansard processing, committee meetings, and speeches
-- Created: 2025-01-09

BEGIN TRANSACTION;

-- Create parliamentary_sessions table
CREATE TABLE IF NOT EXISTS parliamentary_sessions (
    id SERIAL PRIMARY KEY,
    parliament_number INTEGER NOT NULL,
    session_number INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique parliament-session combinations
    UNIQUE(parliament_number, session_number)
);

-- Create hansard_records table
CREATE TABLE IF NOT EXISTS hansard_records (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    sitting_number INTEGER,
    document_url VARCHAR(500),
    pdf_url VARCHAR(500),
    xml_url VARCHAR(500),
    processed BOOLEAN DEFAULT FALSE,
    speech_count INTEGER DEFAULT 0,
    session_id INTEGER REFERENCES parliamentary_sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create speeches table
CREATE TABLE IF NOT EXISTS speeches (
    id SERIAL PRIMARY KEY,
    speaker_name VARCHAR(200),
    speaker_title VARCHAR(200),
    content TEXT,
    time_spoken TIMESTAMP,
    speech_type VARCHAR(50), -- 'statement', 'question', 'response', etc.
    hansard_id INTEGER REFERENCES hansard_records(id),
    representative_id INTEGER REFERENCES representatives(id), -- Optional link to existing representatives
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create committee_meetings table
CREATE TABLE IF NOT EXISTS committee_meetings (
    id SERIAL PRIMARY KEY,
    committee_name VARCHAR(200) NOT NULL,
    meeting_date DATE NOT NULL,
    meeting_number INTEGER,
    evidence_url VARCHAR(500),
    transcript_url VARCHAR(500),
    processed BOOLEAN DEFAULT FALSE,
    session_id INTEGER REFERENCES parliamentary_sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance

-- Parliamentary sessions indexes
CREATE INDEX IF NOT EXISTS idx_parliamentary_sessions_parliament_session 
ON parliamentary_sessions(parliament_number, session_number);

CREATE INDEX IF NOT EXISTS idx_parliamentary_sessions_dates 
ON parliamentary_sessions(start_date, end_date);

-- Hansard records indexes
CREATE INDEX IF NOT EXISTS idx_hansard_records_session_id 
ON hansard_records(session_id);

CREATE INDEX IF NOT EXISTS idx_hansard_records_date 
ON hansard_records(date);

CREATE INDEX IF NOT EXISTS idx_hansard_records_processed 
ON hansard_records(processed);

CREATE INDEX IF NOT EXISTS idx_hansard_records_session_date 
ON hansard_records(session_id, date);

-- Speeches indexes
CREATE INDEX IF NOT EXISTS idx_speeches_hansard_id 
ON speeches(hansard_id);

CREATE INDEX IF NOT EXISTS idx_speeches_speaker_name 
ON speeches(speaker_name);

CREATE INDEX IF NOT EXISTS idx_speeches_speech_type 
ON speeches(speech_type);

CREATE INDEX IF NOT EXISTS idx_speeches_representative_id 
ON speeches(representative_id);

CREATE INDEX IF NOT EXISTS idx_speeches_time_spoken 
ON speeches(time_spoken);

-- Full-text search index for speech content (PostgreSQL specific)
CREATE INDEX IF NOT EXISTS idx_speeches_content_fts 
ON speeches USING GIN(to_tsvector('english', content));

-- Committee meetings indexes
CREATE INDEX IF NOT EXISTS idx_committee_meetings_session_id 
ON committee_meetings(session_id);

CREATE INDEX IF NOT EXISTS idx_committee_meetings_committee_name 
ON committee_meetings(committee_name);

CREATE INDEX IF NOT EXISTS idx_committee_meetings_date 
ON committee_meetings(meeting_date);

CREATE INDEX IF NOT EXISTS idx_committee_meetings_processed 
ON committee_meetings(processed);

CREATE INDEX IF NOT EXISTS idx_committee_meetings_committee_date 
ON committee_meetings(committee_name, meeting_date);

-- Add triggers for updated_at columns

-- Function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_parliamentary_sessions_updated_at 
    BEFORE UPDATE ON parliamentary_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hansard_records_updated_at 
    BEFORE UPDATE ON hansard_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_committee_meetings_updated_at 
    BEFORE UPDATE ON committee_meetings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert current parliamentary session (44th Parliament, 1st Session)
INSERT INTO parliamentary_sessions (parliament_number, session_number, start_date)
VALUES (44, 1, '2021-11-22')
ON CONFLICT (parliament_number, session_number) DO NOTHING;

-- Add comments to document the tables

COMMENT ON TABLE parliamentary_sessions IS 'Canadian parliamentary sessions with their start and end dates';
COMMENT ON COLUMN parliamentary_sessions.parliament_number IS 'Parliament number (e.g., 44 for 44th Parliament)';
COMMENT ON COLUMN parliamentary_sessions.session_number IS 'Session number within the parliament (e.g., 1 for first session)';

COMMENT ON TABLE hansard_records IS 'Records of House of Commons Hansard debates with processing status';
COMMENT ON COLUMN hansard_records.date IS 'Date of the parliamentary sitting';
COMMENT ON COLUMN hansard_records.sitting_number IS 'Sitting number for the day';
COMMENT ON COLUMN hansard_records.processed IS 'Whether speeches have been extracted from this record';
COMMENT ON COLUMN hansard_records.speech_count IS 'Number of speeches extracted from this Hansard record';

COMMENT ON TABLE speeches IS 'Individual speeches extracted from Hansard records';
COMMENT ON COLUMN speeches.speaker_name IS 'Name of the person who gave the speech';
COMMENT ON COLUMN speeches.speaker_title IS 'Title/position of the speaker (e.g., Minister, MP)';
COMMENT ON COLUMN speeches.speech_type IS 'Type of speech: statement, question, response, etc.';
COMMENT ON COLUMN speeches.representative_id IS 'Link to existing representative if available';

COMMENT ON TABLE committee_meetings IS 'Parliamentary committee meetings with evidence and transcripts';
COMMENT ON COLUMN committee_meetings.committee_name IS 'Name or acronym of the committee (e.g., FINA, HESA)';
COMMENT ON COLUMN committee_meetings.meeting_number IS 'Meeting number within the session';
COMMENT ON COLUMN committee_meetings.evidence_url IS 'URL to committee evidence';
COMMENT ON COLUMN committee_meetings.transcript_url IS 'URL to meeting transcript';

-- Create view for easy access to parliamentary data with statistics
CREATE OR REPLACE VIEW parliamentary_sessions_with_stats AS
SELECT 
    ps.*,
    COUNT(DISTINCT hr.id) as hansard_records_count,
    COUNT(DISTINCT cm.id) as committee_meetings_count,
    COUNT(DISTINCT s.id) as total_speeches_count,
    COUNT(DISTINCT CASE WHEN hr.processed = true THEN hr.id END) as processed_hansard_count
FROM parliamentary_sessions ps
LEFT JOIN hansard_records hr ON ps.id = hr.session_id
LEFT JOIN committee_meetings cm ON ps.id = cm.session_id
LEFT JOIN speeches s ON hr.id = s.hansard_id
GROUP BY ps.id, ps.parliament_number, ps.session_number, ps.start_date, ps.end_date, ps.created_at, ps.updated_at;

COMMENT ON VIEW parliamentary_sessions_with_stats IS 'Parliamentary sessions with aggregated statistics about records and speeches';

-- Create view for recent parliamentary activity
CREATE OR REPLACE VIEW recent_parliamentary_activity AS
SELECT 
    'hansard' as activity_type,
    hr.id as record_id,
    hr.date as activity_date,
    ps.parliament_number,
    ps.session_number,
    hr.processed,
    hr.speech_count as item_count,
    hr.created_at
FROM hansard_records hr
JOIN parliamentary_sessions ps ON hr.session_id = ps.id
WHERE hr.created_at >= CURRENT_DATE - INTERVAL '30 days'

UNION ALL

SELECT 
    'committee' as activity_type,
    cm.id as record_id,
    cm.meeting_date as activity_date,
    ps.parliament_number,
    ps.session_number,
    cm.processed,
    0 as item_count,
    cm.created_at
FROM committee_meetings cm
JOIN parliamentary_sessions ps ON cm.session_id = ps.id
WHERE cm.created_at >= CURRENT_DATE - INTERVAL '30 days'

ORDER BY created_at DESC;

COMMENT ON VIEW recent_parliamentary_activity IS 'Recent parliamentary activity (last 30 days) including Hansard and committee records';

-- Grant appropriate permissions (adjust as needed for your setup)
-- Note: Replace 'openpolicy_user' with your actual application database user

-- GRANT SELECT, INSERT, UPDATE, DELETE ON parliamentary_sessions TO openpolicy_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON hansard_records TO openpolicy_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON speeches TO openpolicy_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON committee_meetings TO openpolicy_user;
-- GRANT SELECT ON parliamentary_sessions_with_stats TO openpolicy_user;
-- GRANT SELECT ON recent_parliamentary_activity TO openpolicy_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO openpolicy_user;

-- Insert migration record (if you have a migrations table)
-- INSERT INTO migrations (version, name, executed_at) 
-- VALUES ('001', 'add_parliamentary_models', CURRENT_TIMESTAMP)
-- ON CONFLICT (version) DO NOTHING;

COMMIT;

-- Verification queries (run these after migration to verify success)
/*
-- Check that tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('parliamentary_sessions', 'hansard_records', 'speeches', 'committee_meetings');

-- Check indexes were created
SELECT indexname FROM pg_indexes 
WHERE tablename IN ('parliamentary_sessions', 'hansard_records', 'speeches', 'committee_meetings')
ORDER BY tablename, indexname;

-- Check initial data
SELECT * FROM parliamentary_sessions;

-- Check views were created
SELECT table_name FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name IN ('parliamentary_sessions_with_stats', 'recent_parliamentary_activity');
*/