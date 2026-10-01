#!/usr/bin/env python3
"""Daily news fetcher: RSS -> dedupe -> BCS relevance filter -> docs/news.json
Only headline + metadata + link are stored (no article text)."""
import json, os, re, sys, datetime, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

G = "https://news.google.com/rss/search?q={q}+when:2d&hl={hl}&gl=BD&ceid=BD:{ce}"
FEEDS = [
    ("The Daily Star", G.format(q="site:thedailystar.net", hl="en-BD", ce="en")),
    ("Dhaka Tribune",  G.format(q="site:dhakatribune.com", hl="en-BD", ce="en")),
    ("TBS News",       G.format(q="site:tbsnews.net", hl="en-BD", ce="en")),
    ("Financial Express", G.format(q="site:thefinancialexpress.com.bd", hl="en-BD", ce="en")),
    ("প্রথম আলো",      G.format(q="site:prothomalo.com", hl="bn", ce="bn")),
    ("কালের কণ্ঠ",      G.format(q="site:kalerkantho.com", hl="bn", ce="bn")),
    ("BBC Bangla",     "https://feeds.bbci.co.uk/bengali/rss.xml"),
    ("BBC World",      "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("UN News",        "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
]

KW = {  # keyword -> BCS relevance weight
 "united nations":3,"un general assembly":3,"unga":3,"icj":3,"climate":3,"rohingya":3,"refugee":3,"gdp":3,
 "gender":3,"women":2,"human rights":3,"democracy":3,"election":2,"referendum":2,"reform":2,"education":2,
 "energy":2,"economy":2,"inflation":2,"tax":2,"ldc":3,"diplomacy":2,"foreign policy":3,"labour":2,"monetary":2,
 "central bank":2,"crisis":2,"sustainable":2,"artificial intelligence":2," ai ":2,"technology":2,"trade":2,
 "tariff":2,"export":1,"jute":1,"nuclear":3,"nato":3,"summit":2,"treaty":2,"sanction":2,"budget":2,"bank":1,
 "free speech":3,"constitution":3,"parliament":2,"cabinet":1,"ceasefire":2,"war":2,"oil":1,"gas":1,"solar":2,
 "জাতিসংঘ":3,"জলবায়ু":3,"রোহিঙ্গা":3,"অর্থনীতি":3,"মূল্যস্ফীতি":2,"নির্বাচন":2,"গণতন্ত্র":3,"শিক্ষা":2,
 "মানবাধিকার":3,"সংস্কার":2,"বাজেট":2,"কূটনীতি":2,"সংবিধান":3,"রেমিট্যান্স":2,"রপ্তানি":2,"জ্বালানি":2,
 "প্রযুক্তি":2,"বিশ্ব":1,"যুদ্ধ":2,"নারী":2,"বাণিজ্য":2,"শুল্ক":2,"সংসদ":2,"মন্ত্রিসভা":1,
}
SKIP = ["cricket","football","match","film","actor","actress","drama","horoscope","recipe","fashion",
        "ক্রিকেট","ফুটবল","চলচ্চিত্র","নাটক","অভিনেত্রী","রাশিফল","বিনোদন","ম্যাচ","টি-টোয়েন্টি"]

CATS = [
 ("UN / Diplomacy", ["united nations","unga","un ","diplomacy","ambassador","জাতিসংঘ","কূটনী"]),
 ("Climate & Environment", ["climate","environment","flood","cyclone","solar","emission","জলবায়ু","পরিবেশ","বন্যা"]),
 ("Human Rights / Governance", ["human rights","rights","free speech","refugee","rohingya","election","constitution","reform","মানবাধিকার","রোহিঙ্গা","নির্বাচন","সংস্কার","সংবিধান"]),
 ("Education", ["education","school","university","student","ssc","hsc","শিক্ষা","বিশ্ববিদ্যালয়","শিক্ষার্থী"]),
 ("Science & Tech", ["artificial intelligence"," ai ","technology","science","nuclear","space","প্রযুক্তি","বিজ্ঞান"]),
 ("Economy", ["economy","inflation","bank","trade","tariff","tax","export","budget","gdp","monetary","অর্থনীতি","ব্যাংক","বাণিজ্য","বাজেট","রপ্তানি"]),
 ("International Affairs", ["war","nato","russia","ukraine","gaza","israel","china","india","us ","summit","যুদ্ধ","বিশ্ব"]),
]

def clean(s):
    s = re.sub(r"\s+-\s+[^-]{2,40}$", "", s.strip())     # drop " - Source" suffix (Google News)
    return re.sub(r"\s+", " ", s)

def tokens(s):
    s = re.sub(r"[\"'“”‘’.,:;!?()\[\]\-–—|/]", " ", s.lower())
    return {w for w in s.split() if len(w) > 2}

def sim(a, b):
    A, B = tokens(a), tokens(b)
    return len(A & B) / max(1, len(A | B))

def score(t):
    low = " " + t.lower() + " "
    return sum(w for k, w in KW.items() if k in low)

def category(t, src):
    low = " " + t.lower() + " "
    for name, keys in CATS:
        if any(k in low for k in keys):
            return name
    return "Bangladesh Affairs" if src not in ("BBC World", "UN News") else "International Affairs"

def fetch(src, url):
    out = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (BCS-news-bot)"})
        root = ET.fromstring(urllib.request.urlopen(req, timeout=25).read())
        for it in root.iter("item"):
            t = clean(it.findtext("title") or "")
            link = (it.findtext("link") or "").strip()
            try:
                dt = parsedate_to_datetime(it.findtext("pubDate"))
            except Exception:
                dt = None
            if t and link:
                out.append({"t": t, "u": link, "s": src, "dt": dt})
    except Exception as e:
        print(f"[warn] {src}: {e}", file=sys.stderr)
    return out

def rss_items():
    """Fallback: plain RSS (no API key needed)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    allitems = []
    for src, url in FEEDS:
        got = fetch(src, url)
        print(f"{src}: {len(got)}")
        allitems += got
    keep = []
    for n in allitems:
        if n["dt"] and (now - n["dt"]).days > 2:
            continue
        if any(k in n["t"].lower() for k in SKIP):
            continue
        n["sc"] = score(n["t"])
        if n["sc"] >= 2:
            keep.append(n)
    keep.sort(key=lambda n: (n["sc"], n["dt"] or now), reverse=True)
    return [{"t": n["t"], "c": category(n["t"], n["s"]), "s": n["s"], "u": n["u"],
             "d": (n["dt"] + datetime.timedelta(hours=6)).strftime("%d %b") if n["dt"] else "", "sc": n["sc"]}
            for n in keep]

# ---------------- Claude API (web search + passage generation) ----------------
API = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")
KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CAT_NAMES = ["Bangladesh Affairs", "International Affairs", "Economy", "Climate & Environment", "Education",
             "Science & Tech", "Human Rights / Governance", "UN / Diplomacy"]

def call(messages, tools=None, max_tokens=4000):
    body = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={
        "content-type": "application/json", "x-api-key": KEY, "anthropic-version": "2023-06-01"})
    return json.loads(urllib.request.urlopen(req, timeout=300).read())

def text_of(resp):
    return "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")

def parse_json(t):
    t = t.replace("```json", "").replace("```", "")
    a = min([i for i in (t.find("["), t.find("{")) if i >= 0], default=-1)
    b = max(t.rfind("]"), t.rfind("}"))
    return json.loads(t[a:b + 1])

def api_news(today):
    prompt = (f"Today is {today}. Use web search to find the 12 most important news stories from the last 24-48 hours "
      "from Bangladeshi and international newspapers (The Daily Star, Prothom Alo, Dhaka Tribune, TBS News, BBC, Reuters, UN News) "
      "that suit Bangladesh BCS written-exam translation topics: politics & governance, economy, climate, education, human rights, "
      "UN/diplomacy, science & technology, international affairs. Exclude sports, entertainment, celebrity and petty crime. No duplicates. "
      "Use ONLY real article URLs found in search results. Reply with ONLY a JSON array of objects: "
      '{"t":"headline in English","c":"one of ' + json.dumps(CAT_NAMES) + '","s":"source name","u":"article url",'
      '"d":"DD Mon","sc":BCS relevance 1-10,"ctx":"2 neutral sentences in your own words (no copied text)"}')
    msgs = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]
    resp = call(msgs, tools, 6000)
    for _ in range(3):                       # server tool may pause long turns
        if resp.get("stop_reason") != "pause_turn":
            break
        msgs.append({"role": "assistant", "content": resp["content"]})
        resp = call(msgs, tools, 6000)
    items = parse_json(text_of(resp))
    return [i for i in items if i.get("t") and i.get("u")]

def enrich(item):
    prompt = ("Create BCS written-exam translation practice from this news item (do not copy article text).\n"
      f'Headline: {item["t"]}\nContext: {item.get("ctx","")}\nCategory: {item["c"]}\n\n'
      "Write an ORIGINAL formal editorial-style passage of 8-10 lines with long sentences and abstract vocabulary like past BCS questions; "
      "give background in your own words, no invented statistics or quotes. Reply with ONLY JSON: "
      '{"en":"English passage","m_bn":"natural exam-ready Bangla translation of it, sentence by sentence",'
      '"bn":"a DIFFERENT Bangla passage on the same theme, 8-10 lines","m_en":"natural exam-ready English translation of the Bangla passage",'
      '"vocab":[{"src":"English word","tgt":"Bangla meaning"}] (10 items),'
      '"patterns":[{"pattern":"useful connector/structure","example":"example, explained in Bangla"}] (4 items)}')
    return parse_json(text_of(call([{"role": "user", "content": prompt}], None, 6000)))

def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    bst = now + datetime.timedelta(hours=6)
    items = []
    if KEY:
        try:
            items = api_news(bst.strftime("%A, %d %B %Y"))
            print(f"API news: {len(items)}")
        except Exception as e:
            print(f"[warn] API news failed: {e}", file=sys.stderr)
    else:
        print("No ANTHROPIC_API_KEY: using RSS only", file=sys.stderr)
    if not items:
        items = rss_items()
    uniq = []
    for n in sorted(items, key=lambda n: -float(n.get("sc", 0))):   # duplicate removal
        if not any(sim(n["t"], u["t"]) > 0.55 for u in uniq):
            uniq.append(n)
    uniq = uniq[:40]
    if len(uniq) < 5:
        print("Too few items; keeping the old news.json", file=sys.stderr)
        return
    if KEY:
        for n in uniq[:6]:                    # ready-made practice passages for the top 6
            try:
                n["p"] = enrich(n)
                print("passage ok:", n["t"][:50])
            except Exception as e:
                print(f"[warn] passage failed: {e}", file=sys.stderr)
    data = {"updated": bst.strftime("%Y-%m-%d"), "generated_utc": now.isoformat(timespec="minutes"), "items": uniq}
    with open("docs/news.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(uniq)} items")

if __name__ == "__main__":
    main()
