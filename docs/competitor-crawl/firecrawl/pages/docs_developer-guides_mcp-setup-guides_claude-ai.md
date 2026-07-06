# https://docs.firecrawl.dev/developer-guides/mcp-setup-guides/claude-ai

> ## Documentation Index
> Fetch the complete documentation index at: [/llms.txt](https://docs.firecrawl.dev/llms.txt)
> Use this file to discover all available pages before exploring further.
[Skip to main content](https://docs.firecrawl.dev/developer-guides/mcp-setup-guides/claude-ai#content-area)
Add web scraping and search capabilities to Claude.ai with Firecrawl MCP using custom connectors.
Looking for Claude Code setup? See the [Claude Code guide](https://docs.firecrawl.dev/quickstarts/claude-code) instead.
##  Quick Setup
###  1. Get Your API Key
Sign up at [firecrawl.dev/app/api-keys](https://www.firecrawl.dev/app/api-keys) and copy your API key.
###  2. Add Custom Connector
Go to [Settings > Connectors](https://claude.ai/settings/connectors) in Claude.ai and click **Add custom connector**. Fill in the connector details:
  * **URL:** `https://mcp.firecrawl.dev/YOUR_API_KEY/v2/mcp`
  * **OAuth Client ID:** Leave blank
  * **OAuth Client Secret:** Leave blank

Replace `YOUR_API_KEY` in the URL with your actual [Firecrawl API key](https://www.firecrawl.dev/app/api-keys). Your API key is embedded directly in the URL, so no additional authentication fields are needed. Click **Add** to save the connector.
**Prefer not to put your API key in the URL?** Use the keyless endpoint `https://mcp.firecrawl.dev/v2/mcp` instead (still leaving the OAuth fields blank). Claude.ai will open a browser window for you to sign in to Firecrawl and authorize the connector. See [Connect MCP Clients with OAuth](https://docs.firecrawl.dev/developer-guides/mcp-setup-guides/oauth) for details.
###  3. Enable in Conversation
In any Claude.ai conversation, click the **+** button at the bottom left, go to **Connectors** , and enable the Firecrawl connector.
##  Quick Demo
With the Firecrawl connector enabled, try these prompts: **Search the web:**
```
Search for the latest Next.js 15 features

```

**Scrape a page:**
```
Scrape firecrawl.dev and tell me what it does

```

**Get documentation:**
```
Find and scrape the Stripe API docs for payment intents

```

Claude will automatically use Firecrawl’s search and scrape tools to get the information.
[Suggest edits](https://github.com/firecrawl/firecrawl-docs/edit/main/developer-guides/mcp-setup-guides/claude-ai.mdx)[Raise issue](https://github.com/firecrawl/firecrawl-docs/issues/new?title=Issue%20on%20docs&body=Path:%20/developer-guides/mcp-setup-guides/claude-ai)
[ MCP Web Search & Scrape in ChatGPT Previous ](https://docs.firecrawl.dev/developer-guides/mcp-setup-guides/chatgpt)[ MCP Web Search & Scrape in Factory AI Next ](https://docs.firecrawl.dev/developer-guides/mcp-setup-guides/factory-ai)
⌘I
