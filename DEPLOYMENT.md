# BlockSmith AI - Deployment Guide

This guide walks you through deploying BlockSmith AI step by step.

## Prerequisites

- GitHub account
- Credit/debit card (for service signups, most have free tiers)
- ~$50 budget

---

## Step 1: Push Code to GitHub

1. Create a new repository on GitHub called `blocksmith-ai`
2. Push this code:

```bash
cd blocksmith-ai
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/blocksmith-ai.git
git push -u origin main
```

---

## Step 2: Set Up Supabase (Database & Auth)

1. Go to [supabase.com](https://supabase.com) and create account
2. Create new project (note the password!)
3. Wait for project to initialize (~2 minutes)

### Get your keys:
- Go to **Settings > API**
- Copy: `Project URL` and `anon public` key and `service_role` key

### Set up Discord OAuth:
1. Go to **Authentication > Providers**
2. Enable Discord
3. You'll need Discord Client ID and Secret (next step)

### Run database migrations:
1. Go to **SQL Editor**
2. Copy contents of `backend/migrations/001_initial_schema.sql`
3. Run the query

---

## Step 3: Set Up Discord OAuth

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create **New Application** called "BlockSmith AI"
3. Go to **OAuth2** section
4. Copy **Client ID** and **Client Secret**
5. Add redirect URL: `https://YOUR_SUPABASE_URL/auth/v1/callback`

Back in Supabase:
1. Paste Client ID and Secret in Discord provider settings
2. Save

---

## Step 4: Set Up Stripe (Payments)

1. Go to [stripe.com](https://stripe.com) and create account
2. Complete verification (may take 1-2 days for full features)
3. Go to **Developers > API keys**
4. Copy **Publishable key** and **Secret key**

### Create products (after backend is deployed):
You'll create a webhook endpoint after deploying the backend.

---

## Step 5: Set Up AI APIs

### Anthropic (Claude):
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create account and add payment method
3. Go to **API Keys** and create new key

### Google (Gemini):
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key

### Replicate (Stable Diffusion):
1. Go to [replicate.com](https://replicate.com)
2. Create account
3. Go to account settings for API token

---

## Step 6: Set Up Cloudflare R2 (Storage)

1. Go to [cloudflare.com](https://cloudflare.com) and create account
2. Go to **R2** in sidebar
3. Create a bucket called `blocksmith-files`
4. Go to **Manage R2 API Tokens**
5. Create token with **Object Read & Write** permissions
6. Copy: Account ID, Access Key ID, Secret Access Key

### Enable public access:
1. Go to bucket settings
2. Enable **Public access** (or set up custom domain)

---

## Step 7: Deploy Backend (Railway)

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Create **New Project > Deploy from GitHub repo**
3. Select your `blocksmith-ai` repo
4. Set **Root Directory** to `backend`

### Add environment variables:
In Railway project settings, add all variables from `.env.example`:

```
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=... (add after creating webhook)
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...
REPLICATE_API_TOKEN=...
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=blocksmith-files
FRONTEND_URL=https://your-vercel-url.vercel.app
```

### Configure build:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Note your Railway URL (e.g., `blocksmith-api.up.railway.app`)

---

## Step 8: Set Up Stripe Webhook

1. In Stripe Dashboard, go to **Developers > Webhooks**
2. Add endpoint: `https://YOUR_RAILWAY_URL/api/webhooks/stripe`
3. Select events: `checkout.session.completed`, `payment_intent.payment_failed`
4. Copy the **Signing secret**
5. Add to Railway as `STRIPE_WEBHOOK_SECRET`

### Update credit packages in database:

1. In Stripe, go to **Products**
2. Create 3 products (Starter, Standard, Pro) with their prices
3. Copy the **Price IDs** (e.g., `price_xxxxx`)
4. In Supabase SQL Editor, update the packages:

```sql
UPDATE credit_packages SET stripe_price_id = 'price_xxxxx' WHERE name = 'Starter';
UPDATE credit_packages SET stripe_price_id = 'price_xxxxx' WHERE name = 'Standard';
UPDATE credit_packages SET stripe_price_id = 'price_xxxxx' WHERE name = 'Pro';
```

---

## Step 9: Deploy Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub
2. Import your `blocksmith-ai` repo
3. Set **Root Directory** to `frontend`
4. Framework should auto-detect as Next.js

### Add environment variables:

```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=...
NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
```

5. Deploy!

---

## Step 10: Update URLs

Now that everything is deployed, update the redirect URLs:

### In Supabase:
- Go to **Authentication > URL Configuration**
- Set Site URL to your Vercel URL
- Add redirect URL: `https://your-vercel-url.vercel.app/auth/callback`

### In Railway:
- Update `FRONTEND_URL` to your Vercel URL

### In Discord Developer Portal:
- Update OAuth2 redirect URL if needed

---

## Step 11: Buy a Domain (Optional but Recommended)

1. Buy domain from Namecheap, Cloudflare, etc. (~$12)
2. In Vercel: **Settings > Domains > Add**
3. Follow DNS instructions
4. Update all redirect URLs to use your domain

---

## Step 12: Test Everything

1. Visit your site
2. Log in with Discord
3. Check that you got 10 free credits
4. Try generating a simple datapack (5 credits)
5. Check that the download works
6. Test buying credits (use Stripe test mode first!)

### Stripe Test Mode:
- Use card: `4242 4242 4242 4242`
- Any future expiry, any CVC

---

## Troubleshooting

### "Invalid API key" errors
- Double-check all environment variables in Railway/Vercel
- Make sure there are no extra spaces

### Discord login not working
- Check redirect URLs match exactly
- Make sure Discord OAuth is enabled in Supabase

### Generations failing
- Check Railway logs for errors
- Make sure AI API keys are valid and have credits

### Files not downloading
- Check R2 bucket has public access
- Verify R2 credentials are correct

### Payments not working
- Check Stripe webhook secret
- Verify webhook endpoint URL
- Check Stripe Dashboard for failed webhooks

---

## Going Live Checklist

- [ ] Switch Stripe to live mode (update keys)
- [ ] Add real credit packages in Stripe
- [ ] Update webhook to live endpoint
- [ ] Test real payment
- [ ] Set up error monitoring (Sentry)
- [ ] Create Terms of Service and Privacy Policy
- [ ] Add contact email

---

## Estimated Monthly Costs

At launch (low traffic):
- Vercel: Free
- Railway: ~$5
- Supabase: Free tier
- R2: Free tier (10GB)
- AI APIs: Pay per use

With moderate traffic (100 users, 500 generations/month):
- Railway: ~$10-20
- AI APIs: ~$50-100
- Total: ~$60-120/month

Revenue needed to break even: ~$100/month = 20 credit purchases

---

## Marketing Ideas

1. Post on r/admincraft, r/MinecraftCommands
2. SpigotMC forums
3. Minecraft Discord servers
4. YouTube tutorial video
5. Twitter/X with examples
6. Planet Minecraft

Good luck with BlockSmith AI! 🎮
