# BlockSmith AI

AI-powered Minecraft plugin, datapack, and texture pack generator.

## Features

- **Plugin Generator** - Generate Spigot/Paper plugins from natural language descriptions
- **Datapack Generator** - Create custom recipes, advancements, loot tables, and dimensions
- **Texture Pack Generator** - AI-generated texture packs in various styles

## Tech Stack

- **Frontend**: Next.js 14 (App Router)
- **Backend**: Python FastAPI
- **Database**: Supabase (PostgreSQL)
- **Auth**: Discord OAuth via Supabase
- **Payments**: Stripe
- **AI**: Claude API (complex tasks), Gemini API (simple tasks)
- **Image Generation**: Replicate (Stable Diffusion XL)
- **Storage**: Cloudflare R2
- **Deployment**: Vercel (frontend), Railway (backend)

## Project Structure

```
blocksmith-ai/
├── frontend/                # Next.js frontend
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities and API clients
│   └── public/              # Static assets
├── backend/                 # FastAPI backend
│   ├── api/                 # API routes
│   ├── services/            # Business logic
│   ├── prompts/             # AI prompt templates
│   ├── compilers/           # Code compilation pipelines
│   └── models/              # Database models
└── docs/                    # Documentation
```

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.11+
- Java JDK 17 (for plugin compilation)
- Git

### 1. External Service Accounts

You need to create accounts and get API keys from:

1. **Supabase** (https://supabase.com) - Database and Auth
   - Create new project
   - Get: Project URL, Anon Key, Service Role Key
   - Enable Discord OAuth in Authentication > Providers

2. **Discord Developer Portal** (https://discord.com/developers)
   - Create new application
   - Get: Client ID, Client Secret
   - Add redirect URL: `https://your-supabase-url/auth/v1/callback`

3. **Stripe** (https://stripe.com)
   - Create account
   - Get: Publishable Key, Secret Key
   - Create webhook endpoint (after deployment)

4. **Anthropic** (https://console.anthropic.com)
   - Get: API Key

5. **Google AI Studio** (https://makersuite.google.com/app/apikey)
   - Get: Gemini API Key

6. **Replicate** (https://replicate.com)
   - Get: API Token

7. **Cloudflare R2** (https://cloudflare.com)
   - Create R2 bucket
   - Get: Account ID, Access Key ID, Secret Access Key, Bucket Name

8. **Domain** (any registrar)
   - Purchase domain for ~$12

### 2. Environment Variables

#### Frontend (.env.local)
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
NEXT_PUBLIC_API_URL=your_backend_url
```

#### Backend (.env)
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
ANTHROPIC_API_KEY=your_anthropic_api_key
GEMINI_API_KEY=your_gemini_api_key
REPLICATE_API_TOKEN=your_replicate_api_token
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=your_bucket_name
```

### 3. Database Setup

Run the SQL migrations in Supabase SQL Editor (see `backend/migrations/`)

### 4. Local Development

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 5. Deployment

#### Frontend (Vercel)
1. Connect GitHub repo to Vercel
2. Set environment variables
3. Deploy

#### Backend (Railway)
1. Connect GitHub repo to Railway
2. Set environment variables
3. Add Java buildpack for plugin compilation
4. Deploy

## Credit Pricing

| Generation Type | Credits | Approx. USD |
|----------------|---------|-------------|
| Simple Datapack | 5 | $0.50 |
| Complex Datapack | 15 | $1.50 |
| Simple Plugin | 20 | $2.00 |
| Medium Plugin | 35 | $3.50 |
| Complex Plugin | 50 | $5.00 |
| Basic Textures | 30 | $3.00 |
| Standard Textures | 100 | $10.00 |
| Complete Textures | 350 | $35.00 |

## Credit Packages

- Starter: $5 = 60 credits
- Standard: $15 = 200 credits
- Pro: $40 = 600 credits

## License

Proprietary - All rights reserved
