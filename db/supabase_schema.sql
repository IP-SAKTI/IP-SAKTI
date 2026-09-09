-- =============================================================================
-- IP-SAKTI Sahayak — Production Supabase PostgreSQL Database Schema
-- Single Source of Truth for Persistent Application Data
-- =============================================================================

-- Enable UUID extension if missing
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. PROFILES TABLE (Linked to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    email TEXT,
    preferred_language TEXT DEFAULT 'en',
    organization TEXT DEFAULT 'IP-SAKTI',
    role TEXT DEFAULT 'Researcher',
    bio TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);


-- 2. CONVERSATIONS TABLE
CREATE TABLE IF NOT EXISTS public.conversations (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Chat',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on conversations
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own conversations"
    ON public.conversations FOR SELECT
    USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can insert their own conversations"
    ON public.conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can update their own conversations"
    ON public.conversations FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own conversations"
    ON public.conversations FOR DELETE
    USING (auth.uid() = user_id);


-- 3. MESSAGES TABLE
CREATE TABLE IF NOT EXISTS public.messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on messages
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view messages in their conversations"
    ON public.messages FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.conversations c
            WHERE c.id = messages.conversation_id
            AND (c.user_id = auth.uid() OR c.user_id IS NULL)
        )
    );

CREATE POLICY "Users can insert messages into their conversations"
    ON public.messages FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.conversations c
            WHERE c.id = messages.conversation_id
            AND (c.user_id = auth.uid() OR c.user_id IS NULL)
        )
    );


-- 4. SUPPORT INQUIRIES TABLE
CREATE TABLE IF NOT EXISTS public.support_inquiries (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS on support_inquiries
ALTER TABLE public.support_inquiries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert support inquiries"
    ON public.support_inquiries FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Users can view their own support inquiries"
    ON public.support_inquiries FOR SELECT
    USING (auth.uid() = user_id);


-- 5. RESEARCH SESSIONS TABLE
CREATE TABLE IF NOT EXISTS public.research_sessions (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    conversation_id TEXT REFERENCES public.conversations(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    search_mode TEXT NOT NULL DEFAULT 'hybrid',
    status TEXT NOT NULL DEFAULT 'in_progress',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

ALTER TABLE public.research_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their research sessions"
    ON public.research_sessions FOR ALL
    USING (auth.uid() = user_id OR user_id IS NULL);


-- 6. RESEARCH SOURCES TABLE
CREATE TABLE IF NOT EXISTS public.research_sources (
    id TEXT PRIMARY KEY,
    research_session_id TEXT NOT NULL REFERENCES public.research_sessions(id) ON DELETE CASCADE,
    source_id TEXT,
    title TEXT NOT NULL,
    url TEXT,
    source_type TEXT NOT NULL DEFAULT 'web',
    authority_tier INTEGER NOT NULL DEFAULT 3,
    snippet TEXT,
    published_at TEXT,
    retrieved_at TIMESTAMPTZ DEFAULT NOW(),
    rank INTEGER DEFAULT 0
);

ALTER TABLE public.research_sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view research sources"
    ON public.research_sources FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.research_sessions s
            WHERE s.id = research_sources.research_session_id
            AND (s.user_id = auth.uid() OR s.user_id IS NULL)
        )
    );


-- 7. ESCALATIONS TABLE
CREATE TABLE IF NOT EXISTS public.escalations (
    id TEXT PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    query_id TEXT NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    agent_type TEXT,
    reason TEXT NOT NULL,
    escalated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.escalations ENABLE ROW LEVEL SECURITY;

-- 8. QUERIES TELEMETRY TABLE
CREATE TABLE IF NOT EXISTS public.queries (
    query_id TEXT PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    raw_query TEXT NOT NULL,
    detected_lang TEXT,
    jurisdiction TEXT,
    formulation_cat TEXT,
    is_abstention BOOLEAN DEFAULT FALSE,
    agents_invoked JSONB,
    confidence_score DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.queries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can insert query telemetry"
    ON public.queries FOR INSERT
    WITH CHECK (true);

-- Indexes for optimal querying
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_research_sessions_user_id ON public.research_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_support_inquiries_user_id ON public.support_inquiries(user_id);
CREATE INDEX IF NOT EXISTS idx_queries_user_id ON public.queries(user_id);

