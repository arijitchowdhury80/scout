# https://docs.firecrawl.dev/quickstarts/amp

> ## Documentation Index
> Fetch the complete documentation index at: [/llms.txt](https://docs.firecrawl.dev/llms.txt)
> Use this file to discover all available pages before exploring further.
[Skip to main content](https://docs.firecrawl.dev/quickstarts/amp#content-area)
Add Firecrawl’s search, scrape, crawl, and browser tools to [Sourcegraph Amp](https://ampcode.com) via MCP.
##  Quick Setup
###  1. Get Your API Key
Sign up at [firecrawl.dev/app](https://www.firecrawl.dev/app) and copy your API key.
###  2. Add Firecrawl to Amp
Open Amp settings and add an MCP server. Amp accepts standard MCP config:
```

  "amp.mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "fc-YOUR-API-KEY"





```

Replace `fc-YOUR-API-KEY` with your Firecrawl API key.
###  3. Reload Amp
Reload the Amp window. Firecrawl tools are now available to the agent.
##  Quick Demo
```
Search the web for "Sourcegraph Cody vs Amp" and summarize the differences.

```

```
Scrape https://docs.firecrawl.dev and list the core endpoints.

```

```
Crawl https://example.com and output a site map as JSON.

```

##  Remote Hosted URL (no Node.js required)
```

  "amp.mcpServers": {
    "firecrawl": {
      "url": "https://mcp.firecrawl.dev/fc-YOUR-API-KEY/v2/mcp"




```

##  Troubleshooting
  * **Server fails to start** — check Amp’s MCP log view for stderr output.
  * **Missing`npx`** — install Node.js 18+ or use the remote hosted URL above.


[Suggest edits](https://github.com/firecrawl/firecrawl-docs/edit/main/quickstarts/amp.mdx)[Raise issue](https://github.com/firecrawl/firecrawl-docs/issues/new?title=Issue%20on%20docs&body=Path:%20/quickstarts/amp)
[ OpenRouter Previous ](https://docs.firecrawl.dev/quickstarts/openrouter)[ MCP Web Search & Scrape in Windsurf Next ](https://docs.firecrawl.dev/quickstarts/windsurf)
⌘I
