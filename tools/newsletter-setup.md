# NaturalMed — Newsletter & RSS Setup Guide

## Architecture

```
You write article (HTML file)
        ↓
run: python3 tools/add-article.py
        ↓  (updates feed.xml + creates article file + prints card HTML)
git push → GitHub Pages publishes
        ↓
Mailchimp polls feed.xml (daily check)
        ↓
Mailchimp sends newsletter automatically to all subscribers
```

---

## One-time setup: Mailchimp (free, 500 subscribers)

### 1. Create account
Go to **mailchimp.com** → Sign up free → use `naturalmed.wellness@gmail.com`

### 2. Create an Audience (mailing list)
- Audience → Create Audience
- Name: **NaturalMed Newsletter**
- Default from email: `naturalmed.wellness@gmail.com`
- Default from name: `Nuno Pestana · NaturalMed`

### 3. Import existing subscribers
- If you already have emails in `news-emails.json`, import them:
  - Audience → Add contacts → Import contacts → Upload CSV
  - Convert JSON to CSV first: `python3 tools/export-subscribers.py`

### 4. Create the RSS-to-Email Campaign
- Campaigns → Create Campaign → **Email** → **Automated** → **Share blog updates**
- **RSS feed URL:** `https://www.naturalmed-wellness.com/feed.xml`
- **Send frequency:** Monthly (or "when RSS updates" — Mailchimp checks daily)
- Choose a template — **1 column** works best for articles
- In the template, use these Mailchimp merge tags:
  ```
  *|RSSTITLE|*      ← article title
  *|RSSDESCRIPTION|* ← excerpt (from RSS <description>)
  *|RSSURL|*        ← link to full article
  *|RSSFULLTEXT|*   ← full content (if you want it inline)
  ```
- Add your logo, footer, and unsubscribe link (Mailchimp adds unsubscribe automatically)

### 5. Connect website newsletter form to Mailchimp
In `en/articles.html`, replace `YOUR_FORM_ID` in the `handleNewsletter` function
with your **Mailchimp embedded form POST URL**:

Get this from: Audience → Signup forms → Embedded forms → copy the `action=` URL
It looks like: `https://naturalmed-wellness.us21.list-manage.com/subscribe/post?u=xxx&id=xxx`

```javascript
fetch('https://naturalmed-wellness.us21.list-manage.com/subscribe/post?u=XXX&id=XXX', {
    method: 'POST',
    body: new URLSearchParams({ EMAIL: email }),
});
```

---

## Monthly workflow: publishing a new article

```bash
# 1. In the project folder, run the publishing tool
python3 tools/add-article.py

# 2. Fill in the prompts (title, category, excerpt, date)
#    The tool will:
#    - Create en/articles/YYYY-MM-slug.html from the template
#    - Add the new <item> to feed.xml
#    - Print the card HTML to paste into articles.html

# 3. Open the new article file and write your content
open en/articles/YYYY-MM-slug.html   # macOS
# (or open in VS Code, BBEdit, etc.)

# 4. Add a cover image (optional but recommended)
#    Place at: assets/img/articles/YYYY-MM-slug-cover.jpg
#    Recommended size: 1200 × 630 px (same ratio as social previews)

# 5. Paste the card HTML into en/articles.html
#    (inside <div class="articles-grid">, at the TOP — newest first)
#    Remove the empty-state placeholder div on first article.

# 6. Push to GitHub
git add .
git commit -m "Article: Your Article Title — Month Year"
git push

# 7. Done — Mailchimp detects the RSS update within 24h and sends the newsletter
```

---

## Alternative email services (if Mailchimp grows too expensive)

| Service | Free tier | RSS-to-email |
|---------|-----------|--------------|
| **Mailchimp** | 500 contacts, 1000 emails/mo | ✓ Built-in |
| **Brevo** (Sendinblue) | 300 emails/day | ✓ Built-in |
| **EmailOctopus** | 2500 contacts, 10k emails/mo | ✓ Built-in |
| **Buttondown** | 100 free subscribers | Manual send |
| **Substack** | Free, takes 10% of paid | No RSS needed |

For 12 emails/year to <500 subscribers, **Mailchimp free** is sufficient indefinitely.

---

## RSS feed structure

The `feed.xml` file lives at the project root.
URL when published: `https://www.naturalmed-wellness.com/feed.xml`

New items are prepended (newest first) by `tools/add-article.py`.
Do **not** edit feed.xml manually — always use the tool.

---

## Troubleshooting

**Mailchimp says "could not fetch RSS":**
- Make sure `git push` has completed and GitHub Pages has rebuilt (wait ~2 min)
- Test the feed URL directly: `https://www.naturalmed-wellness.com/feed.xml`
- Validate at: https://validator.w3.org/feed/

**Newsletter not sending automatically:**
- Mailchimp checks RSS once per day at a fixed time
- You can trigger manually: Campaigns → your RSS campaign → Send now

**Subscriber form not working locally:**
- The form posts to Mailchimp's server — it only works when the site is live on GitHub Pages
- During local testing with `python3 -m http.server 8000`, the form POST will fail (CORS) but that's expected
