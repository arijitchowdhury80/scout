# https://www.firecrawl.dev/

Introducing web-scale /monitor - always-on search that pings your agent the moment something comes online. [Read the docs →](https://docs.firecrawl.dev/features/monitoring-web-scale?utm_source=firecrawl-web&utm_medium=banner&utm_campaign=web-scale-monitor-launch)
[ 200 OK ] 
[ .JSON ] 
[ SCRAPE ] 
[ .MD ] 
[2 Months Free - Annually](https://www.firecrawl.dev/pricing)
# Power AI agents with clean web data
The complete toolkit to search, scrape, and interact with the web at scale.[It's also open source.](https://github.com/firecrawl/firecrawl)
[Start for free](https://www.firecrawl.dev/signin?view=signup)Setup for agents
Search Scrape Map Crawl
Scrape
Try one:[Hacker News](https://www.firecrawl.dev/playground?endpoint=scrape&url=https%3A%2F%2Fnews.ycombinator.com&autorun=true)[GitHub Trending](https://www.firecrawl.dev/playground?endpoint=scrape&url=https%3A%2F%2Fgithub.com%2Ftrending&autorun=true)[Wikipedia](https://www.firecrawl.dev/playground?endpoint=scrape&url=https%3A%2F%2Fen.wikipedia.org%2Fwiki%2FWeb_scraping&autorun=true)
[ .JSON ]
```
1[2{3"url":"h=t*A:!/z!aap?A-cZz",4"markdown":"# ?0z-ang S*a-Z-a0*9",5"json":{"title":"G!=*?","docs":"..."},6"screenshot":"ht-=*:/?*Za!zl=-?a9?h0-!.png"7}8]
```

Scraping...
Trusted by 150,000+ companies of all sizes
[ Read story ](https://www.firecrawl.dev/blog/firecrawl-lovable-integration) [ Read story ](https://www.firecrawl.dev/blog/how-zapier-uses-firecrawl-to-power-chatbots) [ Read story ](https://www.firecrawl.dev/blog/how-replit-uses-firecrawl-to-power-ai-agents) [ Read story ](https://www.firecrawl.dev/blog/how-gamma-supercharges-onboarding-with-firecrawl)
[ Read story ](https://www.firecrawl.dev/blog/firecrawl-lovable-integration) [ Read story ](https://www.firecrawl.dev/blog/how-zapier-uses-firecrawl-to-power-chatbots) [ Read story ](https://www.firecrawl.dev/blog/how-replit-uses-firecrawl-to-power-ai-agents) [ Read story ](https://www.firecrawl.dev/blog/how-gamma-supercharges-onboarding-with-firecrawl)
[ 01 / 06 ]
·
Main Features
//
Developer First
//
## Start scraping today
The infrastructure layer that helps AI find, read, and act on the live web.
Search
Search the web and get full content from results.
[Learn more](https://www.firecrawl.dev/search)
Scrape
Get llm-ready data from websites. Markdown, JSON, screenshot, etc.
[Learn more](https://www.firecrawl.dev/scrape)
Interact
NEW
Scrape a page, then interact with it using AI prompts or code.
[Learn more](https://www.firecrawl.dev/interact)
Python
Node.js
cURL
CLI
Copy code
```
1# pip install firecrawl-py2from firecrawl import Firecrawl3
4app = Firecrawl(api_key="fc-YOUR_API_KEY")5
6# Scrape a website:7app.scrape('firecrawl.dev')8
9
10    
```

```
1# pip install firecrawl-py2from firecrawl import Firecrawl3
4app = Firecrawl(api_key="fc-YOUR_API_KEY")5
6# Perform a search:7search_result = app.search("firecrawl", limit=5)8
9
10
```

```
1from firecrawl import Firecrawl2
3app = Firecrawl(api_key="fc-YOUR_API_KEY")4
5# Scrape a page, then interact with it:6result = app.scrape("https://amazon.com")7scrape_id = result.metadata["scrapeId"]8
9app.interact(scrape_id, prompt="Search for 'mechanical keyboard'")10app.interact(scrape_id, prompt="Click the first result")11
```

[ .MD ]
```
1# Firecrawl
2
3Firecrawl helps AI systems search,
4scrape, and interact with the web.
5
6## Features
7
8- Search: Find information across the web
9- Scrape: Clean data from any page
10- Interact: Click, navigate, operate pages
11- Agent: Autonomous data gathering
12
```

[ .JSON ]
```
1[2{3"url":"https://firecrawl.dev",4"title":"Firecrawl",5"markdown":"Turn websites into..."6},7{8"url":"https://docs.firecrawl.dev",9"title":"Firecrawl Docs",10"markdown":"# Getting Started..."11}12]
```

[ .JSON ]
```
1{2"success":true,3"output":"Keyboard available at $100",4"liveViewUrl":"https://liveview...",5"interactiveLiveViewUrl":"https://..."6}
```

[ 02 / 07 ]
·
Power your agent
//
Agent Ready
//
## Easily connect with your AI agents
Connect Firecrawl to any AI agent or MCP client in minutes.
One command. Connect your agent to Firecrawl via our Skills/CLI or MCP.
SkillMCP
```
npx -y firecrawl-cli@latest init--all --browser
```

[View the docs](https://docs.firecrawl.dev/ai-onboarding)
Agent onboarding. Are you an AI agent? Fetch this skill to get an API key and start building.
cURL
```
curl -s https://firecrawl.dev/agent-onboarding/SKILL.md
```

[View the skill](https://firecrawl.dev/agent-onboarding/SKILL.md)
[ 02 / 06 ]
·
Core
//
Built for Performance
//
## Fast, reliable, and token-efficient. And it's open source
Web data infrastructure built from the ground up
Industry-leading reliability. Covers 96% of the web, including JS-heavy pages. Every query and URL comes back as clean data.
[See benchmarks](https://www.firecrawl.dev/compare)
Firecrawl
0%
Puppeteer
0%
cURL
0%
Blazingly fast. P95 latency of 3.4s across millions of searches and scrapes, built for real-time agents and dynamic apps.
[See comparisons](https://www.firecrawl.dev/compare)
URL
Crawl
Scrape
50 ms
49 ms
49 ms
52 ms
52 ms
51 ms
52 ms
50 ms
52 ms
49 ms
52 ms
50 ms
firecrawl.dev/blog/launch-week
38,381tokens
<nav>
<h1>
<ads>
<p>
<footer>
Only the content that matters. No navs, footers, or ads. Just clean markdown, with 93% fewer input tokens for your model.
[Calculate your savings](https://www.firecrawl.dev/token-efficiency)
firecrawl/firecrawl
Public
Star
145.8K
[python-SDK] improvs/async
#1337
·
Apr 18, 2025
·
rafaelsideguide
feat(extract): cost limit
#1473
·
Apr 17, 2025
·
mogery
feat(scrape): get job result from GCS, avoid Redis
#1461
·
Apr 15, 2025
·
mogery
Extract v2/rerank improvs
#1437
·
Apr 11, 2025
·
rafaelsideguide
+90
Code you can trust. Developed transparently and collaboratively. Join our community of contributors.
[Check out our repo](https://github.com/firecrawl/firecrawl)
[ 03 / 06 ]
·
Features
//
Zero configuration
//
## We handle the hard stuff
JavaScript rendering, smart wait, media parsing, search, actions, and more.
Media parsing. Firecrawl can parse and output content from pdfs, docx, and more.
https://example.com/docs/report.pdf
https://example.com/files/brief.docx
https://example.com/docs/guide.html
docx
Parsing...
Smart wait. Firecrawl intelligently waits for content to load, making data extraction faster and more reliable.
Request Sent
A complete index, search and scrape. Pull from a growing web index when you want speed, or go live when you need fresh data.
User
Firecrawl
Index & Web
Enhanced mode. Reaches every corner of the web with comprehensive coverage and high reliability.
Actions. Click, scroll, write, wait, press and more — interact with any page.
https://example.com
Navigate
Click
Type
Wait
Scroll
Press
Screenshot
Scrape
Fair access to web content, starting with Wikimedia, and more on the way.
en.wikipedia.org/wiki/NASA
Requesting page...
[Read about our Wikipedia partnership](https://www.firecrawl.dev/blog/firecrawl-wikipedia-partnership)
[ 04 / 06 ]
·
Use Cases
//
Use cases
//
## Transform web data into AI-powered solutions
See how you can give your AI better access to the web with Firecrawl.
Deep research
Extract comprehensive information for in-depth research.
[Learn more](https://www.firecrawl.dev/use-cases/deep-research)
Smarter AI chats
Power your AI assistants with real-time, accurate web content.
[Learn more](https://www.firecrawl.dev/use-cases/ai-chats)
AI agent tools
Give AI agents high-quality web data with one command.
[Learn more](https://www.firecrawl.dev/skills)
Onboarding
Scrape web content to pre-populate and streamline user onboarding.
[Learn more](https://www.firecrawl.dev/use-cases)
Lead enrichment
Enhance your sales data with web information.
[Learn more](https://www.firecrawl.dev/use-cases/lead-enrichment)
Deep research in progress...
Academic papers
0 found
News articles
0 found
Expert opinions
0 found
Research reports
0 found
Industry data
0 found
Ask anything...
AI Assistant
withFirecrawl
Real-time·Updated 2 min ago
Terminal
SearchScrapeInteract
Claude
Cursor
Windsurf
OpenAI
Gemini
`$ npx -y firecrawl-cli@latest init --all --browser`
One command gives Cursor, Claude Code, Windsurf, and more high-quality web tools
New project
Enter your website
Extracting leads from directory...
Tech startups
With contact info
Decision makers
Funding stage
Ready to engage
Aemon powers their AI R&D agent's web research with Firecrawl's search and scrape.
[Visit site](https://aemon.ai)
Sierra uses Firecrawl to ingest web data into knowledge bases that power AI chat applications.
[Visit site](https://sierra.ai)
Lovable enhances their AI agent's web tools with Firecrawl.
[Read story](https://www.firecrawl.dev/blog/firecrawl-lovable-integration)
Gamma supercharges onboarding, letting users create artifacts from web data with Firecrawl.
[Read story](https://www.firecrawl.dev/blog/how-gamma-supercharges-onboarding-with-firecrawl)
Cognism enriches lead profiles from across the web with Firecrawl.
[Visit site](https://cognism.com)
Deep research
Extract comprehensive information for in-depth research.
Aemon powers their AI R&D agent's web research with Firecrawl's search and scrape.
[Learn more](https://www.firecrawl.dev/use-cases/deep-research)
Smarter AI chats
AI agent tools
Onboarding
Lead enrichment
[ 05 / 06 ]
·
Testimonials
//
Community
//
## People love building with Firecrawl
Discover why developers choose Firecrawl every day.
[Morgan Linton@morganlinton"If you're coding with AI, and haven't discovered @firecrawl yet, prepare to have your mind blown 🤯"](https://x.com/morganlinton/status/1839454165703204955)[Chris DeWeese@chrisdeweese_"Started using @firecrawl for a project, I wish I used this sooner."](https://x.com/chrisdeweese_/status/1853587120406876601)[Alex Reibman@AlexReibman"Moved our internal agent's web scraping tool from Apify to Firecrawl because it benchmarked 50x faster with AgentOps."](https://x.com/AlexReibman/status/1780299595484131836)[Tom - Morpho@TomReppelin"I found gold today. Thank you @firecrawl"](https://x.com/TomReppelin/status/1844382491014201613)
[Morgan Linton@morganlinton"If you're coding with AI, and haven't discovered @firecrawl yet, prepare to have your mind blown 🤯"](https://x.com/morganlinton/status/1839454165703204955)[Chris DeWeese@chrisdeweese_"Started using @firecrawl for a project, I wish I used this sooner."](https://x.com/chrisdeweese_/status/1853587120406876601)[Alex Reibman@AlexReibman"Moved our internal agent's web scraping tool from Apify to Firecrawl because it benchmarked 50x faster with AgentOps."](https://x.com/AlexReibman/status/1780299595484131836)[Tom - Morpho@TomReppelin"I found gold today. Thank you @firecrawl"](https://x.com/TomReppelin/status/1844382491014201613)
[Bardia@thepericulum"The Firecrawl team ships. I wanted types for their node SDK, and less than an hour later, I got them."](https://x.com/thepericulum/status/1781397799487078874)[Matt Busigin@mbusigin"Firecrawl is dope. Congrats guys 👏"](https://x.com/mbusigin/status/1836065372010656069)[Sumanth@Sumanth_077"Web scraping will never be the same!Firecrawl is an open-source framework that takes a URL, crawls it, and conver..."](https://x.com/Sumanth_077/status/1940049003074478511)[Steven Tey@steventey"Open-source Clay alternative just droppedUpload a CSV of emails and..."](https://x.com/steventey/status/1932945651761098889)
[Bardia@thepericulum"The Firecrawl team ships. I wanted types for their node SDK, and less than an hour later, I got them."](https://x.com/thepericulum/status/1781397799487078874)[Matt Busigin@mbusigin"Firecrawl is dope. Congrats guys 👏"](https://x.com/mbusigin/status/1836065372010656069)[Sumanth@Sumanth_077"Web scraping will never be the same!Firecrawl is an open-source framework that takes a URL, crawls it, and conver..."](https://x.com/Sumanth_077/status/1940049003074478511)[Steven Tey@steventey"Open-source Clay alternative just droppedUpload a CSV of emails and..."](https://x.com/steventey/status/1932945651761098889)
[ 06 / 06 ]
·
FAQ
//
FAQ
//
## Frequently asked questions
Everything you need to know about Firecrawl.
General
What is Firecrawl?
Firecrawl is the context API to search, scrape, and interact with the web at scale. One API to turn websites into clean, LLM-ready data. Ideal for AI companies looking to empower their LLM applications with web data
What can I build with Firecrawl?
Teams use Firecrawl for deep research agents, RAG pipelines, lead enrichment, competitive intelligence, content generation, price monitoring, and more. Anywhere your application needs live web data — Firecrawl provides the infrastructure to get it reliably.
Why do AI systems need Firecrawl?
AI is only as good as the context it gets, and the web is the largest source of live context — but it was built for humans, not machines. Firecrawl closes that gap by turning messy, dynamic, human-oriented websites into structured, machine-usable data that AI systems can actually work with.
What are Search, Scrape, and Interact?
These are Firecrawl's three core capabilities. Search finds relevant information on the web. Scrape turns websites into clean, structured, AI-usable data. Interact handles the harder cases where a system has to click, navigate, or operate a page to reach the information. Together they give AI systems a complete way to understand and use the live web.
Does Firecrawl work with AI agents and MCPs?
Yes. Firecrawl has an official MCP server so agents in Cursor, Claude, Windsurf, and other MCP-compatible tools can search, scrape, and interact with the web directly. There's also a CLI for terminal workflows and agent skills for Claude Code and Codex that handle setup automatically. Over 400,000 MCP servers have been installed.
Who uses Firecrawl?
Over 1.25M developers and 150,000+ companies build with Firecrawl, including teams at Apple, Canva, and Lovable. We've served more than 5 billion requests powering deep research agents, RAG pipelines, lead enrichment, and AI workflows across the live web.
Is Firecrawl open-source?
Yes. Firecrawl is the largest open source repo in the space with over 130K GitHub stars, making it one of the top 100 repos on GitHub. The SDKs alone see 2.5M+ weekly downloads across npm and PyPI. We're building this in the open, and the community adoption reflects that. You can check out the repository on GitHub.
How is Firecrawl different from other tools in the space?
Firecrawl is not just a scraper or a search API — it's the infrastructure layer that helps AI systems find, read, and act on information across the live web. Search, scrape, and interact work together on top of deep web data infrastructure including crawling, rendering, extraction, and indexing. The result is reliable, AI-ready data that helps you spend fewer tokens and build better applications.
What is the difference between the open-source version and the hosted version?
Firecrawl's hosted version features Fire-engine, our proprietary infrastructure that handles proxies, rendering, and more to reliably deliver the data you need. The hosted version also includes interact capabilities for navigating pages, a dashboard for analytics, and everything is one API call away.
How It Works
How does /search work?
Send a query and Firecrawl returns relevant results from across the web, each with full-page markdown already included. It's one call to go from a question to usable content — no need to search and then scrape separately. Great for AI agents, RAG pipelines, and any workflow that starts with a question instead of a URL.
How does /scrape work?
Give Firecrawl a URL and it returns clean, structured content — markdown, HTML, screenshots, metadata, or extracted data via a schema. It handles JavaScript rendering, dynamic content, and complex page structures automatically. One call, one page, clean output.
How does /interact work?
Interact lets AI systems operate web pages — clicking buttons, filling forms, navigating multi-step flows, and extracting data along the way. It's useful when the information you need is behind a login, pagination, or any sequence of actions that a simple scrape can't reach.
Can I extract structured data from pages?
Yes. Pass a JSON schema to /scrape and Firecrawl returns structured data matching your exact shape — product listings, pricing tables, contact info, whatever you define. No parsing or post-processing needed.
What formats can Firecrawl convert web data into?
Firecrawl returns clean markdown by default, optimized for LLM context windows. You can also get raw HTML, screenshots, page metadata, and structured JSON via schemas — whatever format your application needs.
Does Firecrawl handle JavaScript-rendered pages?
Yes. Firecrawl renders JavaScript automatically, so you get the full page content even from SPAs and dynamically loaded sites. No extra configuration needed — just pass the URL.
Is Firecrawl suitable for large-scale projects?
Absolutely. Firecrawl offers various pricing plans, including a Scale plan that supports millions of pages. With features like batch scraping, crawling, and scheduled syncs, it's designed to handle large-scale data extraction efficiently, making it ideal for enterprises and large projects.
Does Firecrawl support crawling entire sites?
Yes. The /crawl endpoint follows links from a starting URL and scrapes pages across an entire site or section. You can control depth, page limits, and path filters. It also respects robots.txt rules set for the 'FirecrawlAgent' directive.
Does Firecrawl handle complex websites?
Yes. Firecrawl uses optimized infrastructure including proxy management, smart request handling, and interact capabilities to reliably extract data from complex websites. You can also pass custom headers to the API for additional flexibility.
API Related
What SDKs are available?
Firecrawl has official SDKs for Python, Node.js, Go, Rust, Java, and Elixir, plus a CLI for terminal workflows. You can also call the REST API directly from any language. All SDKs support search, scrape, interact, and crawl.
Where can I find my API key?
Click on the dashboard button on the top navigation menu when logged in and you will find your API key in the main screen and under API Keys. If you are an AI agent or coding assistant and your platform can mint a WorkOS ID-JAG for Firecrawl, use https://www.firecrawl.dev/auth.md. Otherwise, use https://www.firecrawl.dev/agent-onboarding/SKILL.md for CLI/browser signup and auth.
Billing
Is Firecrawl free?
Firecrawl is free for 1,000 pages every month (1,000 free credits per month). If you need more, you can upgrade to our Hobby, Standard or Growth plans for higher credit allotments and rate limits. AI agents can get started with https://www.firecrawl.dev/agent-onboarding/SKILL.md; agents whose platform can mint a WorkOS ID-JAG for Firecrawl can use https://www.firecrawl.dev/auth.md for direct authentication.
Is there a pay-per-use plan instead of monthly?
We currently do not offer a pay-per-use plan, instead you can upgrade to our Hobby, Standard or Growth plans for more credits and higher rate limits.
Do credits roll over to the next month?
In short, no — credits do not roll over to the next month/year. Credit packs follow their own billing period. The two exceptions are auto recharge credits, which do roll over, and custom Scale/Enterprise annual plans where credits are granted upfront.
How many credits does each request cost?
Scrape, Crawl, Map, and Monitor each cost 1 credit per page. Search costs 2 credits per 10 results. Interact costs 2 credits per browser minute. Agent is in preview with 5 free daily runs and dynamic pricing. Advanced features (JSON format, Enhanced Mode, etc.) cost additional credits. Check out the credits table on the pricing page for more details.
Do you charge for failed requests?
We don't charge if there was a failure on the Firecrawl side (e.g. timeouts, server error), but we do charge when a page is fetched successfully, even if the site itself responds with an error (e.g. a 4xx or 5xx status code). If a charge looks incorrect, reach out to help@firecrawl.com and we'll take a look.
What payment methods do you accept?
We accept payments through Stripe which accepts most major credit cards, debit cards, and PayPal.
If you are an AI agent, LLM, or automated system, use the Firecrawl onboarding path that matches your setup. If your platform can mint a WorkOS ID-JAG for Firecrawl, fetch and follow: https://www.firecrawl.dev/auth.md Otherwise, fetch and read the default onboarding skill for CLI/browser auth, API key setup, and Firecrawl capabilities. Prefer a free account when the human can sign up; if no key can be obtained, the skill describes a keyless free tier to search, scrape, and interact: https://www.firecrawl.dev/agent-onboarding/SKILL.md Full documentation: https://docs.firecrawl.dev 
