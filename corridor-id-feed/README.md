# Corridor ID Program News Feed

Self-updating feed for the FRA's Corridor Identification and Development
(Corridor ID) Program, merging two sources — no API keys needed for either:

- **Google News RSS** — general news coverage
- **Federal Register API** — official notices, solicitations, and rulemakings
  that mention the program (the authoritative regulatory record)

Each item is tagged with `"kind": "news"` or `"kind": "federal_register"` in
`docs/feed.json`, and as an RSS `<category>` in `docs/feed.xml`, so you can
filter by source. Runs daily via GitHub Actions and commits the results back
to this repo.

## Setup

1. Create a new GitHub repo and push these files (or copy this folder into
   an existing repo).
2. Go to **Settings → Actions → General → Workflow permissions** and set it
   to "Read and write permissions" (needed so the workflow can commit the
   updated feed).
3. That's it — the workflow runs daily at 13:00 UTC, or trigger it manually
   from the **Actions** tab ("Update Corridor ID news feed" → Run workflow).

## Using the feed

- **RSS reader**: point any feed reader at the raw file URL, e.g.
  `https://raw.githubusercontent.com/<you>/<repo>/main/docs/feed.xml`
- **GitHub Pages**: enable Pages on the `docs/` folder (Settings → Pages →
  source: `main` branch, `/docs` folder) and you'll get a stable URL like
  `https://<you>.github.io/<repo>/feed.xml`
- **JSON**: `docs/feed.json` has the same items in a simpler structure if
  you want to pull them into another script, dashboard, or Slack/Teams bot.

## Tuning what counts as relevant

Edit `QUERIES` in `scripts/build_feed.py` for news coverage, or
`FEDERAL_REGISTER_TERMS` for the official notices search — each is matched
independently and results are merged and de-duplicated. Add
Minnesota-specific terms (e.g. `"Northern Lights Express"`, `"Twin Cities"
rail corridor`) if you want the feed to lean toward projects you're
tracking directly.

## Notes

- Google News RSS is unauthenticated and free, but it's not an official
  FRA data source — treat those items as news coverage, not a
  system-of-record.
- The Federal Register API (`federalregister.gov/api/v1`) is the official,
  public-domain source for notices, solicitations, and funding
  opportunities that reference the program — closer to authoritative, but
  it only covers what's actually been published in the Federal Register,
  not general program status updates (Step 1/2/3, funding decisions) that
  FRA sometimes only announces via webinar or its own program page.
- If you'd rather not rely on Google News, the query list can be swapped
  for another RSS-producing source (e.g. a specific trade outlet's RSS
  feed) with minimal changes to `build_feed.py`.
