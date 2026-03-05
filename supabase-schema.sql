CREATE TABLE posted_links (
    id BIGSERIAL PRIMARY KEY,
    link TEXT UNIQUE NOT NULL,
    feed_name TEXT NOT NULL,
    title TEXT,
    posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for quick search
CREATE INDEX idx_posted_links_link ON posted_links(link);

-- Index for queries by date
CREATE INDEX idx_posted_links_posted_at ON posted_links(posted_at);

COMMENT ON TABLE posted_links IS 'Links already published on Telegram';
COMMENT ON COLUMN posted_links.link IS 'Unique URL of the news item';
COMMENT ON COLUMN posted_links.feed_name IS 'Name of the source feed';
COMMENT ON COLUMN posted_links.title IS 'Title of the news item (optional)';
