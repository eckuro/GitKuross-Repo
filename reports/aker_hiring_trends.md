# Aker ASA Portfolio — Hiring Trends Comparison

**Compiled:** September 2026
**Scope:** Companies in which Aker ASA (Oslo Børs: AKER) holds a significant or controlling stake, compared by which functional clusters they are currently visibly hiring into.

## Methodology & limitations

This session's network egress is restricted to a small allowlist (package registries, Anthropic's API) plus a server-side web-search tool; direct page fetches (`WebFetch`/`curl`) to company career sites, ATS platforms (Teamtailor, Greenhouse, Workday), and job boards (LinkedIn, Glassdoor, Indeed) were all blocked by the sandbox's egress policy. A full scrape of every open requisition — the original ask — was **not possible** in this environment.

What follows instead is a **signal-based comparison** built from search-engine snippets of each company's careers pages, job-board aggregator listings, and press coverage. Aggregator "open position counts" (Glassdoor/LinkedIn/Indeed) were found to disagree wildly for the same company in the same session (e.g. one company showed 2, 32, and 1000+ depending on the source) and are **not used as data** — they're noise from aggregator scraping/caching, not ground truth. Instead, each cell below reflects the strongest evidence actually found for that company hiring in that cluster: a named open requisition, a career-site job-family/category page, or a clearly stated department structure. Absence of a mark means **no public evidence was found in this session**, not confirmed zero hiring — smaller or JS-rendered career sites in particular are likely undercounted.

Treat this as directional intelligence on where each company's *visible* hiring emphasis sits, not an audited headcount plan. For a rigorous version, re-run with a tool that has real network access to each company's career site.

## Current Aker ASA portfolio (as of Sept 2026)

Aker's structure has moved a lot in the last two years. Confirmed via web search:

**In the group:** Aker BP (~40%), Aker Solutions (~39%, largest shareholder), Aker BioMarine (77.67%, in process of being taken fully private), Cognite (still Aker-owned pending its announced sale to Schneider Electric, not yet closed), Aize, Nscale (~22.8%, largest shareholder — new major position from the March 2026 Aker-Nscale JV roll-up), Solstad Offshore (~32.9%) and Solstad Maritime Holding (~42%), Aker Qrill Company (JV spun out of Aker BioMarine's feed-ingredients unit), Akastor (listed holding company), Mainstream Renewable Power, Aker Clean Hydrogen (Euronext Growth-listed), Aker Property Group.

**No longer in the group** (excluded from the comparison): Aker Horizons (merged into Aker ASA Sept 2025, shell dissolved Feb 2026), Aker Carbon Capture (wound down after selling its SLB Capturi stake, May 2025), Philly Shipyard (sold to Hanwha, Dec 2024), Kvaerner (merged into Aker Solutions, 2020), Ocean Yield (passed to KKR years ago; KKR reportedly selling to A.P. Moller Holding), American Shipping Company (liquidated Oct 2025).

**Excluded for lack of an independent careers presence:** Akastor (~18 corporate staff; hiring happens at its own portfolio companies, e.g. MHWirth, AKOFS Offshore — out of scope here), Aker Property Group, Aker Clean Hydrogen, Mainstream Renewable Power (no dedicated ATS/careers page surfaced).

## Comparison table

Legend: `●` core/defining hiring focus · `◐` active, multiple open roles found · `○` limited/single signal (a category name or one req) · blank = no evidence found

| Company | Oil & Gas Eng. | Data, AI & Software | AI Infra / Data Centers | Production & Vessel Crew | HSE | Commercial (Sales/CS/Mktg) | Finance | HR & Talent | Corporate / G&A | Early Career |
|---|---|---|---|---|---|---|---|---|---|---|
| **Aker BP** (E&P) | ● | | | | ○ | | | ○ | | ● |
| **Aker Solutions** (oilfield engineering) | ● | | | ○ | ○ | ○ | ◐ | | ○ | ● |
| **Aker BioMarine** (krill biotech) | | | | ● | ○ | | | | | |
| **Cognite** (industrial SaaS/AI) | | ● | | | | ● | | ● | ○ | |
| **Aize** (digital-twin software) | | ◐ | | | | | | | | ○ |
| **Nscale** (AI/GPU cloud & data centers) | | ● | ● | | | ● | | ● | ○ | |
| **Solstad Offshore** (offshore vessel ops) | | | | ○ | | | | | | |
| **Aker Qrill Company** (krill harvesting) | | | | ● | | | | | | |

## Reading the trends

- **AI & data is the one cluster growing across the whole portfolio, not just at the "tech" companies.** Nscale (AI/GPU cloud infrastructure) is Aker's newest and now single largest-weighted position, built by rolling the Aker-Nscale JV into a company where Aker took a ~22.8% stake in March 2026 — funded in part by proceeds from selling Cognite. Cognite itself is hiring specifically for LLM/GenAI product and program roles even while its sale to Schneider Electric is pending. Aize, the smallest of the digital-native names, is still visibly hiring data engineers and software staff. Read together, this is a group-level pivot: capital and hiring emphasis are moving from traditional oilfield engineering toward AI infrastructure and industrial software.
- **Legacy oil & gas engineering hiring (Aker BP, Aker Solutions) looks comparatively quiet in current public postings** — both maintain strong graduate/trainee pipelines (their clearest, most consistent signal) but showed little indexed evidence of large-scale open technical hiring at the time of this research. That may understate reality (their career sites are JS-rendered and not fully indexed) rather than reflect an actual slowdown — a caveat this methodology can't resolve without direct page access.
- **Maritime/vessel crew hiring is a distinct, separate track** from the white-collar clusters above it. Aker Qrill Company (deck crew, fishmates) and Aker BioMarine (production/QC/maintenance at its Antarctic harvesting and Houston manufacturing operations) show steady blue-collar operational hiring; Solstad Offshore's public listings were sparser than expected for a fleet operator of its size.
- **Commercial and People/Talent functions concentrate at the software-native companies** (Cognite, Nscale) — consistent with those being the two names actively scaling go-to-market and corporate functions teams, versus the industrial/engineering names where those functions barely surface in public postings.
- **HSE is present only as a weak signal everywhere it was found** (Aker BP, Aker Solutions, Aker BioMarine) — likely because safety roles are usually folded into operations postings rather than listed as a standalone career-site category, so this undercounts a function that's certainly larger in practice at the offshore/industrial names.

## Sources consulted

Company career pages and category structures: akerbp.com/en/open-positions, careers.akerbp.com, akersolutions.com/careers/job-search, akerbiomarine.com/careers, careers.akerbiomarine.com (Teamtailor), cognite.com/en/company/careers, careers.aize.io, nscale.com/careers, job-boards.eu.greenhouse.io/nscaleoperationsukltd, solstad.com/opportunities, theqrillcompany.com/careers.
Aggregators (used only for role titles/snippets, not counts): Glassdoor, LinkedIn Jobs, Indeed, Built In.
Portfolio/ownership changes: Aker ASA press releases and coverage of the Nscale, Cognite/Schneider Electric, Aker BioMarine take-private, Aker Horizons merger/dissolution, and Aker Carbon Capture/SLB Capturi transactions.
