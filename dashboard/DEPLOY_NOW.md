# 🚀 Deploy OpenPolicy Dashboard to Vercel - Step by Step

## Option 1: Deploy via Command Line (Recommended)

### Step 1: Open Terminal
```bash
cd /workspace/dashboard
```

### Step 2: Run Vercel CLI
```bash
vercel
```

### Step 3: Answer the Prompts
You'll see these questions:

1. **Set up and deploy "~/workspace/dashboard"?** 
   → Type: **y** (yes)

2. **Which scope do you want to deploy to?**
   → Select your Vercel account

3. **Link to existing project?** 
   → Type: **n** (no)

4. **What's your project's name?**
   → Type: **openpolicy-dashboard** (or your preferred name)

5. **In which directory is your code located?**
   → Press Enter (current directory)

6. **Want to override the settings?**
   → Type: **n** (no)

### Step 4: Wait for Deployment
Vercel will:
- Upload your files
- Install dependencies
- Build your project
- Deploy to a URL

### Step 5: Get Your URL
After deployment, you'll see:
```
✅ Production: https://openpolicy-dashboard.vercel.app
```

## Option 2: Deploy via GitHub

### Step 1: Push to GitHub
```bash
cd /workspace
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

### Step 2: Import in Vercel Dashboard
1. Go to https://vercel.com/dashboard
2. Click "Add New Project"
3. Import your GitHub repository
4. Select the `/dashboard` directory as root
5. Click "Deploy"

## Option 3: Deploy with Environment Variable

### If you have a backend URL ready:
```bash
cd /workspace/dashboard

# Deploy with environment variable
vercel --build-env VITE_API_URL=https://your-backend-api.com
```

## 🔧 Post-Deployment Setup

### 1. Set Environment Variables (if not done)
```bash
vercel env add VITE_API_URL production
# Enter your backend API URL when prompted
```

### 2. Redeploy to Apply Changes
```bash
vercel --prod
```

### 3. View Your Deployment
```bash
vercel ls
```

### 4. Open in Browser
```bash
vercel open
```

## 🎯 Quick Deploy Command (Copy & Paste)

```bash
cd /workspace/dashboard && vercel --yes --name openpolicy-dashboard
```

## 📱 What Happens Next?

1. Your dashboard will be live at the Vercel URL
2. It will try to connect to `http://localhost:8000` (default)
3. To connect to a real backend:
   - Deploy backend to Railway/Render
   - Update VITE_API_URL in Vercel settings
   - Redeploy

## 🆘 Troubleshooting

### If deployment fails:
```bash
# Check logs
vercel logs

# Try manual build first
npm run build

# Then deploy
vercel --prod
```

### If you need to login first:
```bash
vercel login
# This will open a browser for authentication
```

## ✅ Ready to Deploy!

Your dashboard is built and ready. Just run `vercel` in the dashboard directory!