# BCS News Translation Trainer

প্রতিদিন ২ বার—সকাল ৬:৩০ ও সন্ধ্যা ৬:৩০ (BD) GitHub Actions Claude API (web search) দিয়ে সেদিনের গুরুত্বপূর্ণ খবর খুঁজে, দুই ভাষায় practice passage ও model answer বানিয়ে (key না থাকলে RSS fallback) `docs/news.json` আপডেট করে।
Page (`docs/index.html`) সেই JSON পড়ে → dedupe → BCS filter → practice → AI check।

## Setup (একবারই)
1. GitHub-এ নতুন repo বানাও (যেমন `bcs-news`), এই ফোল্ডারের সব ফাইল upload/push করো (`.github` ফোল্ডারসহ)।
2. Repo → **Settings → Pages** → Source: *Deploy from a branch* → Branch `main`, folder `/docs` → Save।
3. Repo → **Settings → Actions → General → Workflow permissions** → *Read and write permissions* → Save।
4. Repo → **Settings → Secrets and variables → Actions → New repository secret** → Name: `ANTHROPIC_API_KEY`, Value: তোমার API key (এটাই আসল API; key GitHub Secret-এ থাকে, কোডে নয়)।
5. Repo → **Actions → Daily BCS news → Run workflow** (প্রথমবার হাতে চালাও)।
6. `https://<username>.github.io/<repo>/` খুলে 🔑 AI settings-এ নিজের API key দাও।

## নোট
- শুধু headline + link + metadata সংরক্ষিত হয়; article text copy হয় না।
- Source বদলাতে/যোগ করতে `scripts/fetch_news.py`-এর `FEEDS` ও `KW` এডিট করো।
- API key কখনও repo-তে commit করো না।
