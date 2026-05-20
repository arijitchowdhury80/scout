# Scout Target Matrix

Scout uses a balanced target matrix so validation does not overfit to one type
of company or website.

## Primary Targets

| Segment | Company | Primary Use |
|---|---|---|
| Private B2B SaaS | Algolia | PRISM, company, careers, blogs, docs |
| Private B2B SaaS | Constructor | PRISM, competitor intel, company, careers, blogs/docs |
| Private retail commerce | L.L.Bean | ecommerce, product catalog, careers, company |
| Private retail commerce | Patagonia | ecommerce, product catalog, company, sustainability/blog content |
| Public company | Adobe | company, investor, careers, blogs/news |
| Public company | Home Depot | public retail, investor, careers, product catalog, news |
| Public / hard-site retail | Estée Lauder | hard-site product/category fallback and blocked-page handling |
| Public travel / airline | British Airways | travel company intel, careers, research, website-quality |

## Secondary Targets

| Company | Use |
|---|---|
| Nike | public retail product/catalog and brand validation |
| Amplience | alternate private B2B SaaS target |
| Salesforce | optional public SaaS investor/careers/company validation |
| Intuit | optional public careers/jobs validation |

## Coverage Rules

- Company/PRISM: all primary targets.
- Investor: Adobe, Home Depot, Estée Lauder if available through parent/public filings, British Airways if public-parent evidence is useful.
- Products: L.L.Bean, Patagonia, Home Depot, Estée Lauder, and Nike.
- Careers/jobs: all primary targets.
- News/blogs: all primary targets.
- Hard-site behavior: Estée Lauder.
- Travel/research/website-quality: British Airways.

The executable source of truth lives in `scout.core.platform.targets`.
