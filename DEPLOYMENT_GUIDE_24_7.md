# 🌐 SwimRight Miami — 24/7 Cloud Deployment Guide (Free Permanent Server)

To ensure your **SwimRight Miami Budget Approval Portal** works **24/7 continuously without any interruptions**, follow these simple steps to deploy it to **Render.com** (100% Free permanent cloud hosting).

---

## 🚀 Option 1: 3-Minute Deployment via Render.com (Recommended)

### Step 1: Create a Free Render Account
1. Open [https://render.com](https://render.com) and click **Sign Up**.
2. Register using your Email, Google, or GitHub account.

### Step 2: Push Project to GitHub
Open your terminal inside the project directory:
```bash
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/swimright-budget-agent.git
git branch -M main
git push -u origin main
```

### Step 3: Create Web Service on Render
1. On Render Dashboard, click **New +** -> **Web Service**.
2. Connect your GitHub repository `swimright-budget-agent`.
3. Render will auto-detect settings from `render.yaml`:
   - **Name**: `swimright-budget-portal`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Click **Create Web Service**.

🎉 **Done!** Within 2 minutes, Render will issue your permanent public SSL link:
👉 `https://swimright-budget-portal.onrender.com`

---

## ⚡ Option 2: 1-Click Railway Deployment

1. Open [https://railway.app](https://railway.app).
2. Click **Deploy from GitHub repo**.
3. Select `swimright-budget-agent`.
4. Railway will automatically build and launch the app online 24/7!

---

## 🔐 Credentials Reminder for All Users

- **Shared Password**: `Password123!`
- **Participants**:
  - `Dmytro` (Approver)
  - `Nazarii` (SwimFast)
  - `Liza` (Office)
  - `Denys` (SwimRight)
