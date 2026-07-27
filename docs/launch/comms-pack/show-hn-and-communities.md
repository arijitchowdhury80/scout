# Show HN + Community Posts

Voice: plain, sharp, first-person founder. No em dashes. No hype. No invented metrics.
Each community post respects that community's self-promo culture.

---

## Show HN

**Title:**
Show HN: Scout, turn any website into a record you can cite

**Body:**
I kept hitting the same wall. Scraping tools give you a pile of text, and then you still have to clean it and remember which page each fact came from. That last part is where research quietly falls apart. You end up writing things you can't actually source.

Scout is my attempt to fix that. You point it at a website and it gives you structured records instead of a text dump. For a company site that means the company details, the people, the open roles, the funding history, and the recent news, each in its own field. It also does the ordinary jobs: read one page, crawl a whole site, list every URL on a domain, take a full-page screenshot, and pull product catalogs into search-ready records.

The thing I actually built it around: every field keeps a reference to the page it came from. So the output isn't just data, it's data you can trace back and defend.

It's built on Crawl4AI under the hood. You use it through a small HTTP API, or through a skill that plugs into Claude and Codex so an AI assistant can fetch real records instead of hallucinating them.

This is an early beta and I'm looking for people who work with web data to try it and tell me where it breaks. Sites that defeat it are the most useful thing you can send me. Happy to answer anything technical in the thread.

scout.chowmes.com

---

## r/webscraping

Norm: technical, skeptical, hates marketing speak. Lead with the mechanism, be honest about limits.

**Title:** Built a tool that returns structured records per page instead of raw HTML, with the source URL kept on every field

**Body:**
Sharing something I built and looking for holes in it.

Most of my scraping ends the same way: I've got the data but I've lost the provenance, so I can't cleanly say which page a given value came from. Scout keeps the source page attached to every field it extracts. On a company site it pulls company info, people, roles, funding, and news into separate typed fields rather than one text dump. It also does plain crawl, sitemap-style URL mapping, screenshots, and product catalog extraction. It's built on Crawl4AI with a browser fallback for JS-heavy pages.

It's in beta. I'm not going to pretend it handles every anti-bot setup, it doesn't, and I'd like to know exactly which sites kill it. If you point it at something nasty and it falls over, that report is worth a lot to me. Link in a comment if that's allowed, otherwise DM me.

---

## r/SaaS

Norm: founders talking shop, launch stories welcome, but bring a lesson not just a link.

**Title:** Launching my scraping tool in beta today. The one decision that shaped the whole product.

**Body:**
Launching Scout on Product Hunt today and wanted to share the call that defined it.

Early on I had to choose: make the output look impressive, or make it defensible. Most tools in this space optimize for the first. They give you a big text blob that looks like a lot. But the moment someone asks "where did this fact come from," the blob is useless.

I built Scout around the second choice. Every fact it pulls from a website keeps a link to the page it came from. Less flashy in a demo, far more useful in real work. It turns sites into structured records: company info, people, jobs, news, product catalogs. API plus an AI-assistant integration.

The bet is that people doing serious research or client work will pay for trustworthy over impressive. Beta is open with 50 spots and I want 50 people to stress test it. Happy to trade notes with other founders on beta launches in the comments.

---

## Indie Hackers

Norm: transparent, journey-driven, numbers and honesty over polish.

**Title:** Beta launching Scout today: records you can cite, not another text dump

**Body:**
Today's the day I open Scout to a beta crowd.

Short version: point it at a website, get back clean structured records instead of a wall of text, and every fact keeps the source page attached so you can prove where it came from. It handles company research, people, jobs, news, and product catalogs, and it works through an API or as a skill inside Claude and Codex.

I'm being deliberate about the beta. I'm capping it at 50 spots, real users, not a vanity spike. My whole goal this week is to learn which sites break it and which features people actually reach for. I'll share what I find back here as I go, good and bad. If you build with web data, I'd love you in the group. Ask me anything about the build below.

---

## Discord: Crawlee & Apify community (relevant, scraping-native audience)

Norm: peer channel, keep it short, no press-release tone, post only in the right self-promo/show-your-work channel.

**Message:**
Hey all. Built something adjacent to what most of you do and wanted to show it here since this crowd will spot the weak points fastest.

Scout takes a website and returns structured records per page, keeping the source URL on every field so provenance never gets lost. Company info, people, jobs, news, product catalogs, plus plain crawl and screenshots. Crawl4AI under the hood with a browser fallback. It's in beta.

Not looking for upvotes, looking for "here's the site that broke it." If mods are fine with it I'll drop a link, otherwise DM me and I'll send it over.
