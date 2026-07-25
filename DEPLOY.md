# Deploy PakkaHisaab — Railway + Vercel

## 1. Backend on Railway

1. Push this repository to GitHub, then in Railway choose **New Project → Deploy
   from GitHub repo**.
2. Select the repository and set the service **Root Directory** to `backend`.
   In **Settings → Config as Code**, set the config path to `/backend/railway.toml`.
   It uses Python 3.11, `uvicorn main:app --host 0.0.0.0 --port $PORT`, and
   `/api/health`.
3. In **Variables**, paste these values (do not commit them):

   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
   - `DATABASE_URL`: use the Supabase **pooler** connection string from §22,
     never the IPv6-only direct `db.<ref>.supabase.co` host.
   - `OPENAI_API_KEY` (leave blank only for deliberate mock deployment)
   - `MOCK_MODE=false`, `DEMO_STORE_ID=00000000-0000-0000-0000-000000000001`
   - `FRONTEND_ORIGIN`: exact Vercel production URL, such as
     `https://pakkahisaab.vercel.app` — **no trailing slash**.
4. Deploy, then **Settings → Networking → Generate Domain**. Copy the HTTPS
   Railway domain; it becomes the frontend API base URL.

## 2. Frontend on Vercel

1. In Vercel choose **Add New → Project**, import the same GitHub repository,
   and set **Root Directory** to `frontend`.
2. Add the public variables:

   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `NEXT_PUBLIC_API_URL=https://<railway-domain>`
   - `NEXT_PUBLIC_WS_URL=wss://<railway-domain>`
3. Deploy. Copy the Vercel production URL back into Railway as `FRONTEND_ORIGIN`,
   then redeploy Railway so CORS allows that exact origin.

## 3. Post-deploy smoke checklist

1. Open `https://<railway-domain>/api/health`; it must return HTTP 200.
2. POST `https://<railway-domain>/api/stores/demo`; it must return the public demo id.
3. Open the Vercel URL in a private window, choose **Open Demo Store**, run
   reconciliation, and confirm the live Agent Terminal receives stage messages.
4. Confirm browser Network requests use the Railway domain (not localhost), then
   resolve one exception and reload to check the displayed response.

No live URL is committed here: Railway/Vercel domain allocation requires your account.
