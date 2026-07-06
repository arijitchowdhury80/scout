# https://docs.firecrawl.dev/

> ## Documentation Index
> Fetch the complete documentation index at: [/llms.txt](https://docs.firecrawl.dev/llms.txt)
> Use this file to discover all available pages before exploring further.
[Skip to main content](https://docs.firecrawl.dev/introduction#content-area)
**For AI agents:** Use [llms.txt](https://docs.firecrawl.dev/llms.txt) for a full index of all documentation.
##  Get started
## Get your API key
Sign up and get your API key to start using Firecrawl
## Try it in the Playground
Test the API instantly without writing any code
###  Use Firecrawl with AI agents (recommended)
The Firecrawl skills are the fastest way for agents to discover and use Firecrawl. Without them, your agent will not know Firecrawl is available.
```
npx -y firecrawl-cli@latest init --all --browser

```

Restart your agent after installing the skills. See [Skills + CLI](https://docs.firecrawl.dev/sdks/cli) for the full setup.
Or use the [MCP Server](https://docs.firecrawl.dev/mcp-server) to connect Firecrawl directly to Claude, Cursor, Windsurf, VS Code, and other AI tools.
##  What can Firecrawl do?
## Search
Search the web and get full page content from results
## Scrape
Extract content from any URL as markdown, HTML, or structured JSON
## Interact
Continue working with any scraped page — click, fill forms, extract dynamic content
###  Why Firecrawl?
  * **LLM-ready output** : Clean markdown, structured JSON, screenshots, and more.
  * **Handles the hard stuff** : Proxies, anti-bot, JavaScript rendering, and dynamic content.
  * **Reliable** : Built for production with high uptime and consistent results.
  * **Fast** : Results in seconds, optimized for high throughput.
  * **MCP Server** : Connect Firecrawl to any AI tool via the [Model Context Protocol](https://docs.firecrawl.dev/mcp-server).


##  Search
Search the web and get full page content from results in one call. See the [Search feature docs](https://docs.firecrawl.dev/features/search) for all options.
Python
Node
cURL
CLI
```
from firecrawl import Firecrawl
firecrawl = Firecrawl(
  # No API key needed to get started — add one for higher rate limits:
  # api_key="fc-YOUR-API-KEY",

results = firecrawl.search(
    query="firecrawl",
    limit=3,

print(results)

```

Response
SDKs will return the data object directly. cURL will return the complete payload.
JSON
```

  "success": true,
  "data": {
    "web": [

        "url": "https://www.firecrawl.dev/",
        "title": "Firecrawl - The Web Data API for AI",
        "description": "The web crawling, scraping, and search API for AI. Built for scale. Firecrawl delivers the entire internet to AI agents and builders.",
        "position": 1
      },

        "url": "https://github.com/firecrawl/firecrawl",
        "title": "mendableai/firecrawl: Turn entire websites into LLM-ready ... - GitHub",
        "description": "Firecrawl is an API service that takes a URL, crawls it, and converts it into clean markdown or structured data.",
        "position": 2
      },
      ...
    ],
    "images": [

        "title": "Quickstart | Firecrawl",
        "imageUrl": "https://mintlify.s3.us-west-1.amazonaws.com/firecrawl/logo/logo.png",
        "imageWidth": 5814,
        "imageHeight": 1200,
        "url": "https://docs.firecrawl.dev/",
        "position": 1
      },
      ...
    ],
    "news": [

        "title": "Y Combinator startup Firecrawl is ready to pay $1M to hire three AI agents as employees",
        "url": "https://techcrunch.com/2025/05/17/y-combinator-startup-firecrawl-is-ready-to-pay-1m-to-hire-three-ai-agents-as-employees/",
        "snippet": "It's now placed three new ads on YC's job board for “AI agents only” and has set aside a $1 million budget total to make it happen.",
        "date": "3 months ago",
        "position": 1
      },
      ...




```

##  Scrape
Scrape any URL and get its content in markdown, HTML, or other formats. See the [Scrape feature docs](https://docs.firecrawl.dev/features/scrape) for all options.
Python
Node
cURL
CLI
```
from firecrawl import Firecrawl
firecrawl = Firecrawl(
  # No API key needed to get started — add one for higher rate limits:
  # api_key="fc-YOUR-API-KEY",

# Scrape a website:
doc = firecrawl.scrape("https://firecrawl.dev", formats=["markdown", "html"])
print(doc)

```

Response
SDKs will return the data object directly. cURL will return the payload exactly as shown below.
```

  "success": true,
  "data" : {
    "markdown": "Launch Week I is here! [See our Day 2 Release 🚀](https://www.firecrawl.dev/blog/launch-week-i-day-2-doubled-rate-limits)[💥 Get 2 months free...",
    "html": "<!DOCTYPE html><html lang=\"en\" class=\"light\" style=\"color-scheme: light;\"><body class=\"__variable_36bd41 __variable_d7dc5d font-inter ...",
    "metadata": {
      "title": "Home - Firecrawl",
      "description": "Firecrawl crawls and converts any website into clean markdown.",
      "language": "en",
      "keywords": "Firecrawl,Markdown,Data,Mendable,Langchain",
      "robots": "follow, index",
      "ogTitle": "Firecrawl",
      "ogDescription": "Turn any website into LLM-ready data.",
      "ogUrl": "https://www.firecrawl.dev/",
      "ogImage": "https://www.firecrawl.dev/og.png?123",
      "ogLocaleAlternate": [],
      "ogSiteName": "Firecrawl",
      "sourceURL": "https://firecrawl.dev",
      "statusCode": 200,
      "contentType": "text/html"




```

##  Interact
Scrape a page, then keep working with it — click buttons, fill forms, extract dynamic content, or navigate deeper. Describe what you want in plain English or write code for full control. See the [Interact feature docs](https://docs.firecrawl.dev/features/interact) for all options.
Python
Node
cURL
CLI
```
from firecrawl import Firecrawl
app = Firecrawl(
  # No API key needed to get started — add one for higher rate limits:
  # api_key="fc-YOUR-API-KEY",

# 1. Scrape Amazon's homepage
result = app.scrape("https://www.amazon.com", formats=["markdown"])
scrape_id = result.metadata.scrape_id
# 2. Interact — search for a product and get its price
app.interact(scrape_id, prompt="Search for iPhone 16 Pro Max")
response = app.interact(scrape_id, prompt="Click on the first result and tell me the price")
print(response.output)
# 3. Stop the session
app.stop_interaction(scrape_id)

```

Response
Response
```

  "success": true,
  "cdpUrl": "wss://browser.firecrawl.dev/...",
  "liveViewUrl": "https://liveview.firecrawl.dev/...",
  "interactiveLiveViewUrl": "https://liveview.firecrawl.dev/...",
  "output": "The iPhone 16 Pro Max (256GB) is priced at $1,199.00.",
  "exitCode": 0,
  "killed": false


```

##  More capabilities
## Agent
Autonomous web data gathering powered by AI
## Interact
Click, fill forms, extract dynamic content
## Webhooks
Async event delivery
## Browser Sandbox
Managed browser sessions for interactive workflows
## Map
Discover all URLs on a website
## Crawl
Recursively gather content from entire sites
##  Resources
## API Reference
Complete API documentation with interactive examples
## SDKs
Python, Node.js, CLI, and community SDKs
## Open Source
Self-host Firecrawl or contribute to the project
## Integrations
LangChain, LlamaIndex, OpenAI, and more
[Suggest edits](https://github.com/firecrawl/firecrawl-docs/edit/main/introduction.mdx)[Raise issue](https://github.com/firecrawl/firecrawl-docs/issues/new?title=Issue%20on%20docs&body=Path:%20/introduction)
[ Skills + CLI Next ](https://docs.firecrawl.dev/sdks/cli)
⌘I
