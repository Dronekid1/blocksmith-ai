-- BlockSmith AI Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends Supabase auth.users)
CREATE TABLE public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    discord_id TEXT,
    discord_username TEXT,
    avatar_url TEXT,
    credits INTEGER DEFAULT 0 NOT NULL,
    total_spent DECIMAL(10,2) DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Credit transactions (purchases and usage)
CREATE TABLE public.credit_transactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    amount INTEGER NOT NULL, -- positive for purchases, negative for usage
    type TEXT NOT NULL, -- 'purchase', 'usage', 'refund', 'bonus'
    description TEXT,
    stripe_payment_id TEXT,
    generation_id UUID, -- links to generation if type is 'usage'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Generations (plugins, datapacks, texture packs)
CREATE TABLE public.generations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL, -- 'plugin', 'datapack', 'texture_pack'
    tier TEXT NOT NULL, -- 'simple', 'medium', 'complex', 'basic', 'standard', 'complete'
    status TEXT DEFAULT 'pending' NOT NULL, -- 'pending', 'processing', 'completed', 'failed'
    prompt TEXT NOT NULL,
    credits_used INTEGER NOT NULL,
    
    -- Generation details (JSON for flexibility)
    input_params JSONB DEFAULT '{}'::jsonb,
    output_metadata JSONB DEFAULT '{}'::jsonb,
    
    -- File storage
    file_url TEXT,
    file_name TEXT,
    file_size INTEGER,
    
    -- Error tracking
    error_message TEXT,
    
    -- AI routing info
    ai_model_used TEXT, -- 'claude', 'gemini'
    ai_tokens_used INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE -- files auto-delete after X days
);

-- Stripe customers (for subscription management later)
CREATE TABLE public.stripe_customers (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE NOT NULL,
    stripe_customer_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Credit packages (configurable pricing)
CREATE TABLE public.credit_packages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    credits INTEGER NOT NULL,
    price_cents INTEGER NOT NULL, -- price in cents
    stripe_price_id TEXT NOT NULL,
    bonus_credits INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Insert default credit packages
INSERT INTO public.credit_packages (name, credits, price_cents, stripe_price_id, bonus_credits, sort_order) VALUES
('Starter', 50, 500, 'price_starter_placeholder', 10, 1),
('Standard', 175, 1500, 'price_standard_placeholder', 25, 2),
('Pro', 500, 4000, 'price_pro_placeholder', 100, 3);

-- Generation pricing config
CREATE TABLE public.generation_pricing (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    generation_type TEXT NOT NULL, -- 'plugin', 'datapack', 'texture_pack'
    tier TEXT NOT NULL,
    credits_required INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(generation_type, tier)
);

-- Insert default generation pricing
INSERT INTO public.generation_pricing (generation_type, tier, credits_required, description) VALUES
-- Datapacks
('datapack', 'simple', 5, 'Basic recipes or simple advancements'),
('datapack', 'medium', 10, 'Custom loot tables or multiple recipes'),
('datapack', 'complex', 15, 'Custom dimensions or complex mechanics'),
-- Plugins
('plugin', 'simple', 20, 'Single feature plugin'),
('plugin', 'medium', 35, '2-3 features with config'),
('plugin', 'complex', 50, 'Full plugin with commands, events, config'),
-- Texture packs
('texture_pack', 'basic', 30, 'Core blocks only (~50 textures)'),
('texture_pack', 'standard', 100, 'Blocks and items (~200 textures)'),
('texture_pack', 'complete', 350, 'Full pack (~800 textures)');

-- Indexes for performance
CREATE INDEX idx_generations_user_id ON public.generations(user_id);
CREATE INDEX idx_generations_status ON public.generations(status);
CREATE INDEX idx_generations_created_at ON public.generations(created_at DESC);
CREATE INDEX idx_credit_transactions_user_id ON public.credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_created_at ON public.credit_transactions(created_at DESC);

-- Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stripe_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generation_pricing ENABLE ROW LEVEL SECURITY;

-- Policies: Users can only see their own data
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can view own transactions" ON public.credit_transactions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can view own generations" ON public.generations
    FOR SELECT USING (auth.uid() = user_id);

-- Public read access for packages and pricing
CREATE POLICY "Anyone can view credit packages" ON public.credit_packages
    FOR SELECT USING (is_active = true);

CREATE POLICY "Anyone can view generation pricing" ON public.generation_pricing
    FOR SELECT USING (is_active = true);

-- Function to create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, discord_id, discord_username, avatar_url, credits)
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data->>'provider_id',
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url',
        10 -- Free starting credits
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updated_at
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
