# Sample Publisher Output

**Input:** Reviewed blog post about remote work trends

**Action:** Publish to existing Notion page

---

## Success Output

```markdown
## ✅ Published Successfully

**Page:** [The Great Office Tug-of-War: Remote Work in 2025](https://notion.so/workspace/the-great-office-tug-of-war-abc123)
**Published to:** "My Blog Posts" page

### Content Summary
- Word count: 892 words
- Sections: 4
- Sources cited: 4

[Open in Notion](https://notion.so/workspace/the-great-office-tug-of-war-abc123)
```

---

## Page Not Found Output

```markdown
## ⚠️ Page Not Found

I couldn't find a page named "My Blog Posts" in your Notion workspace.

### Please check:
1. The page exists in Notion
2. The page name matches exactly (case-sensitive)
3. The page is shared with your Notion integration

**To share with integration:**
1. Open the page in Notion
2. Click ⋯ menu → Add connections
3. Select your integration
4. Tell me the exact page name again
```

---

## Permission Error Output

```markdown
## ❌ Publishing Failed

**Error:** Permission denied for page "My Blog Posts"

### How to Fix
1. Open your target page in Notion
2. Click ⋯ menu → Add connections
3. Select your integration
4. Try publishing again
```

---

## What Makes This Good

- **Immediate link** — User can access published content right away
- **Content summary** — Confirms what was published
- **Clear error guidance** — If it fails, user knows how to fix it
- **Setup instructions** — Helps user prepare their Notion page correctly