# https://docs.firecrawl.dev/api-reference/endpoint/activity

> ## Documentation Index
> Fetch the complete documentation index at: [/llms.txt](https://docs.firecrawl.dev/llms.txt)
> Use this file to discover all available pages before exploring further.
[Skip to main content](https://docs.firecrawl.dev/api-reference/endpoint/activity#content-area)
List recent API activity
cURL
```
curl --request GET \
  --url https://api.firecrawl.dev/v2/team/activity \
  --header 'Authorization: Bearer <token>'
```

200
```

  "success": true,
  "data": [

      "id": "<string>",
      "api_version": "v1",
      "created_at": "2023-11-07T05:31:56Z",
      "target": "<string>"

  ],
  "cursor": "<string>",
  "has_more": true

```

GET
/
team
/
activity
Try it
List recent API activity
cURL
```
curl --request GET \
  --url https://api.firecrawl.dev/v2/team/activity \
  --header 'Authorization: Bearer <token>'
```

200
```

  "success": true,
  "data": [

      "id": "<string>",
      "api_version": "v1",
      "created_at": "2023-11-07T05:31:56Z",
      "target": "<string>"

  ],
  "cursor": "<string>",
  "has_more": true

```

Lists your recent API activity from the last 24 hours. Use this to discover job IDs, then retrieve results with the corresponding GET endpoint.
Endpoint | Retrieval Endpoint  
---|---  
`scrape` | `GET /v2/scrape/{id}`  
`crawl` | `GET /v2/crawl/{id}`  
`batch_scrape` | `GET /v2/batch/scrape/{id}`  
`agent` | `GET /v2/agent/{jobId}`  
#### Authorizations
Authorization
string
header
required
Bearer authentication header of the form `Bearer <token>`, where `<token>` is your auth token.
#### Query Parameters
endpoint
enum<string>
Filter by endpoint
Available options: 
`scrape`, 
`crawl`, 
`batch_scrape`, 
`search`, 
`extract`, 
`llmstxt`, 
`deep_research`, 
`map`, 
`agent`, 
`browser`, 
`interact`
limit
integer
default:50
Maximum number of results per page
Required range: `1 <= x <= 100`
cursor
string
Cursor for pagination. Use the cursor value from the previous response.
#### Response
200 - application/json
Successful response
success
boolean
Example:
`true`
data
object[]
Show child attributes
cursor
string | null
Cursor to use for the next page. Null if there are no more results.
has_more
boolean
Whether there are more results available
[Suggest edits](https://github.com/firecrawl/firecrawl-docs/edit/main/api-reference/endpoint/activity.mdx)[Raise issue](https://github.com/firecrawl/firecrawl-docs/issues/new?title=Issue%20on%20docs&body=Path:%20/api-reference/endpoint/activity)
[ Docs Search Previous ](https://docs.firecrawl.dev/api-reference/endpoint/docs-search)[ Credit Usage Next ](https://docs.firecrawl.dev/api-reference/endpoint/credit-usage)
⌘I
