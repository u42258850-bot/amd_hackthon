MONGO_URI = mongodb://localhost:27017
MONGO_DB_NAME = agrisoil
FIREBASE_PROJECT_ID = agrisoil-ai
FIREBASE_SERVICE_ACCOUNT_JSON = not set
CORS_ORIGINS = http://localhost:3000
STATIC_BASE_URL = http://localhost:8000
UPLOAD_DIR = uploads
VITE_FIREBASE_API_KEY = AIzaSyBKlVvgXjonNgmOLsW01BjZRXxsPKvLGlQ
VITE_FIREBASE_AUTH_DOMAIN = agrisoil-ai.firebaseapp.com
VITE_FIREBASE_PROJECT_ID = agrisoil-ai
VITE_FIREBASE_STORAGE_BUCKET = agrisoil-ai.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID = 446597786972
VITE_FIREBASE_APP_ID = 1:446597786972:web:2d93eb1dc4343ef934e599
VITE_API_BASE_URL = http://localhost:8000 ← local only, not deploy-safe





# AgriSoil AI Deployment Runbook (Render + Vercel)

This runbook is designed specifically for this repository so the **Analyze Soil** button works in production.

---

## 1) Recommended architecture

- **Frontend**: Vercel (root: `AMD-Slingshot-main`)
- **Backend**: Render Web Service (root: `AMD-Slingshot-main/backend`)
- **Database**: MongoDB Atlas
- **Auth**: Firebase Authentication

---

## 2) Backend deployment (Render)

### Service settings
- **Root Directory**: `AMD-Slingshot-main/backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Required environment variables
Set these exactly in Render:

- `ENVIRONMENT=production`
- `ALLOW_DEV_AUTH_BYPASS=false`
- `REQUIRE_DB_ON_STARTUP=true`
- `MONGO_URI=<your atlas uri>`
- `MONGO_DB_NAME=agrisoil`
- `FIREBASE_PROJECT_ID=<your firebase project id>`
- `FIREBASE_SERVICE_ACCOUNT_JSON=<minified one-line firebase admin json>`
- `CORS_ORIGINS=https://<your-vercel-domain>`
- `STATIC_BASE_URL=https://<your-render-domain>`
- `UPLOAD_DIR=uploads`

> If `FIREBASE_SERVICE_ACCOUNT_JSON` is multiline, Render may parse it badly. Use one-line JSON.

### Backend smoke tests
After deploy, test:

- `GET https://<backend>/health` must return `{"status":"ok",...}`

Then check logs once using Analyze button:

- Render Logs should not show `401`, `Invalid Firebase token`, `Database ping failed`, or import errors.

---

## 3) Frontend deployment (Vercel)

### Project settings
- **Root Directory**: `AMD-Slingshot-main`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Required environment variables
Set these in Vercel:

- `VITE_API_BASE_URL=https://<your-render-domain>`
- `VITE_FIREBASE_API_KEY=<...>`
- `VITE_FIREBASE_AUTH_DOMAIN=<...>`
- `VITE_FIREBASE_PROJECT_ID=<...>`
- `VITE_FIREBASE_STORAGE_BUCKET=<...>`
- `VITE_FIREBASE_MESSAGING_SENDER_ID=<...>`
- `VITE_FIREBASE_APP_ID=<...>`

> `VITE_API_BASE_URL` must be **https** and must not end with an extra path.

---

## 4) Firebase console checks (critical)

In Firebase Console:

1. **Authentication > Settings > Authorized domains**
   - Add your Vercel domain (`<project>.vercel.app`) and custom domain if used.
2. Ensure Email/Google provider is enabled as needed.
3. Ensure `FIREBASE_PROJECT_ID` in backend exactly matches frontend Firebase project.

---

## 5) Analyze Soil failure matrix (most important)

### A) Error: `Missing bearer token` or `Invalid Firebase token` (401)
Root cause:
- Backend cannot verify Firebase token, or wrong Firebase project/credentials.

Fix:
- Verify `FIREBASE_PROJECT_ID` matches frontend project.
- Set `FIREBASE_SERVICE_ACCOUNT_JSON` correctly (one-line JSON).
- Ensure user is logged in before clicking Analyze.

### B) Browser console shows CORS error
Root cause:
- `CORS_ORIGINS` does not match frontend exact domain.

Fix:
- Set `CORS_ORIGINS=https://<exact-vercel-domain>`
- Redeploy backend.

### C) Analyze request pending then fails with `Network Error`
Root cause:
- Wrong `VITE_API_BASE_URL`, mixed content (`http`), backend sleeping/crashed.

Fix:
- Set `VITE_API_BASE_URL=https://<render-domain>`
- Confirm backend `/health` is reachable publicly.
- Check Render service logs for crash/restart.

### D) Analyze returns 500
Root cause:
- Usually model/runtime issue, missing env variable, or transient dependency error.

Fix:
- Open Render logs at the same timestamp and capture traceback.
- Validate all env vars in section 2.
- Confirm backend has enough memory/CPU plan if large inference load.

### E) Analyze returns 400 with message about images/depth
Root cause:
- Validation from backend (`max 4 images`, `soil depth positive`, mixed soil types).

Fix:
- Upload 1-4 images of same soil sample.
- Provide depth > 0.

---

## 6) Correct deployment order

1. Deploy backend first on Render.
2. Verify backend `/health`.
3. Deploy frontend on Vercel with backend URL.
4. Add Vercel domain in Firebase authorized domains.
5. Login and test Analyze with one small image (JPG/PNG under 5MB).
6. Check Render logs while testing.

---

## 7) Fast recovery procedure when Analyze fails

1. In browser DevTools > Network, click `POST /analyze`.
2. Note **status code** and response `detail`.
3. Open Render logs for same timestamp.
4. Match with section 5 matrix and apply exact fix.
5. Redeploy only affected service (backend for auth/cors, frontend for URL).

---

## 8) Security and production sanity

- Keep `ALLOW_DEV_AUTH_BYPASS=false` in production.
- Never commit Firebase Admin JSON file to Git.
- Use Render/Vercel secret env variables only.
- Keep MongoDB Atlas IP access configured for cloud service connectivity.

---

If you still get failure after this checklist, collect:
- Browser Network response for `POST /analyze`
- Render error log lines for the same request
- Current values (masked) of `ENVIRONMENT`, `FIREBASE_PROJECT_ID`, `CORS_ORIGINS`, `VITE_API_BASE_URL`

With those 4 items, root cause can usually be fixed in one pass.


