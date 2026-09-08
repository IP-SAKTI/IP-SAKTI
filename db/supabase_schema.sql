-- =============================================================================
-- IP-SAKTI Sahayak — Supabase Database Schema & Row Level Security (RLS)
-- =============================================================================

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Profiles Table (Linked to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    preferred_language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 2. Conversations Table
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Chat',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Index for listing conversations by user sorted by update time
CREATE INDEX IF NOT EXISTS idx_conversations_user_updated
    ON public.conversations(user_id, updated_at DESC);

-- 3. Messages Table
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Index for messages in a conversation
CREATE INDEX IF NOT EXISTS idx_messages_conversation
    ON public.messages(conversation_id, created_at ASC);

-- 4. Uploaded Documents Table (Metadata)
CREATE TABLE IF NOT EXISTS public.uploaded_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_uploaded_documents_user
    ON public.uploaded_documents(user_id, created_at DESC);

-- 5. Research Sessions Table
CREATE TABLE IF NOT EXISTS public.research_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    search_mode VARCHAR(50) NOT NULL DEFAULT 'hybrid',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_research_sessions_user
    ON public.research_sessions(user_id, created_at DESC);

-- 6. Research Sources Table
CREATE TABLE IF NOT EXISTS public.research_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_session_id UUID NOT NULL REFERENCES public.research_sessions(id) ON DELETE CASCADE,
    source_id TEXT,
    title TEXT NOT NULL,
    url TEXT,
    source_type VARCHAR(50) NOT NULL DEFAULT 'web',
    authority_tier INTEGER NOT NULL DEFAULT 3,
    snippet TEXT,
    published_at DATE,
    retrieved_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    rank INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_research_sources_session
    ON public.research_sources(research_session_id, rank ASC);

-- =============================================================================
-- Row Level Security (RLS) Policies
-- =============================================================================

-- Profiles RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Conversations RLS
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own conversations"
    ON public.conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own conversations"
    ON public.conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own conversations"
    ON public.conversations FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own conversations"
    ON public.conversations FOR DELETE
    USING (auth.uid() = user_id);

-- Messages RLS
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own messages"
    ON public.messages FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own messages"
    ON public.messages FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own messages"
    ON public.messages FOR DELETE
    USING (auth.uid() = user_id);

-- Uploaded Documents RLS
ALTER TABLE public.uploaded_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own uploaded documents"
    ON public.uploaded_documents FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own uploaded documents"
    ON public.uploaded_documents FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own uploaded documents"
    ON public.uploaded_documents FOR DELETE
    USING (auth.uid() = user_id);

-- Research Sessions RLS
ALTER TABLE public.research_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own research sessions"
    ON public.research_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own research sessions"
    ON public.research_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own research sessions"
    ON public.research_sessions FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own research sessions"
    ON public.research_sessions FOR DELETE
    USING (auth.uid() = user_id);

-- Research Sources RLS (Inherited access via research_session ownership)
ALTER TABLE public.research_sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view research sources for their sessions"
    ON public.research_sources FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.research_sessions s
            WHERE s.id = research_sources.research_session_id
              AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert research sources for their sessions"
    ON public.research_sources FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.research_sessions s
            WHERE s.id = research_sources.research_session_id
              AND s.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete research sources for their sessions"
    ON public.research_sources FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.research_sessions s
            WHERE s.id = research_sources.research_session_id
              AND s.user_id = auth.uid()
        )
    );
