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

## 3-year momentum filter (2023 → 2026)

A snapshot of who's hiring into what today doesn't show *direction*. This section adds that: headcount trajectory over the last three years per company, which is a much stronger signal than the job-ad snapshot above, because it comes from actual reported/estimated employee counts rather than search-indexed job listings (still subject to the same network limitation — see note below).

Legend: 🔺 strong growth (>15% cumulative) · ▲ modest growth · ● flat/stabilizing · ▼ contraction · ✕ cluster eliminated from the group · ★ new entrant, no 3-year baseline

| Company | Cluster | Headcount 2023 | Latest reported | 3-yr change | Momentum | What drove it |
|---|---|---|---|---|---|---|
| **Nscale** | AI infra / data centers | 42 | 578 (2026); 817 by Jul-2026 | ~+1,300%+ | 🔺 | Went from a small JV to Aker's largest single position (Mar 2026 roll-up), funded partly by Cognite sale proceeds |
| **Cognite** | Data, AI & software | 596 | 898 (2026) | +50.7% | 🔺 | Accelerating GenAI push — hiring velocity roughly doubled (40/mo in 2024 → 89/mo in 2026) even mid-sale to Schneider Electric |
| **Solstad Offshore** | Vessel ops / maritime | ~831 | 952 (2026) | +14.6% | ▲ | Steady, accelerating in 2026 as order backlog strengthens despite softer utilization |
| **Aker BP** | Oil & gas E&P | 2,567 | 3,115 (2025) | +21.3%¹ | ▲ | Continued production/asset-development ramp (e.g. Yggdrasil) |
| **Aker Solutions** | Oilfield engineering | 11,961 | 12,113 (2025) | +1.3% | ● | Stabilized after a sharp 2022–23 cut; order backlog grew far faster than headcount (NOK 60.9bn → 72bn+), i.e. growth without rehiring at the same pace |
| **Aker BioMarine** | Krill biotech | n/a² | 258 (2025) | net ▼ then ● | ▼ then ● | Shed its Feed Ingredients division (spun into Aker Qrill, Sept 2024), then stabilized/regrew slightly (+3.6% in 2025) around Human Health |
| **Aker Qrill Company** | Krill harvesting | — | — | — | ★ | Didn't exist 3 years ago — spun out of Aker BioMarine in Sept 2024 as its own JV |
| **Aker Horizons / Aker Carbon Capture / Mainstream Renewable Power / Aker Clean Hydrogen** | Renewables & carbon capture | one of 4 listed portfolio companies at end-2023 | wound down / dissolved | −100% of the cluster | ✕ | Aker Carbon Capture liquidated after selling its SLB Capturi stake (May 2025); Aker Horizons merged into Aker ASA (Sept 2025) and its shell dissolved (Feb 2026) |
| **Philly Shipyard, Ocean Yield, American Shipping Co., Kvaerner** | Shipbuilding / ship leasing | in the group | fully exited | — | ✕ | Sold, divested, or liquidated between 2020–2025 (Kvaerner merged into Aker Solutions 2020; Philly Shipyard sold to Hanwha Dec 2024; Ocean Yield long since with KKR; AMSC liquidated Oct 2025) |

¹ Aker BP's own reporting implies ~30% cumulative growth 2023→2026; 2026 figure wasn't available, so the 2025 figure is shown.
² No clean 2023 baseline was found for Aker BioMarine standalone headcount before its 2023–24 segment restructuring, so only the latest trend (+3.6% in 2025) is shown.

**Headline read:** the group's hiring momentum over the last three years has swung hard from *industrial/engineering* toward *AI infrastructure* — Nscale's growth curve (42 → ~800 people) and Cognite's accelerating GenAI hiring dwarf everything else in the portfolio, while the entire renewables/carbon-capture cluster that existed in 2023 has been eliminated. Oil & gas (Aker BP, Aker Solutions) shows real but comparatively modest growth, increasingly decoupled from headcount (revenue/backlog scaling faster than hiring). Maritime crewing (Solstad, Qrill, BioMarine) moves independently of all of the above, on its own steady cadence.

**Source note:** headcount figures above are third-party estimates (Revelio Labs, LinkedIn-derived) surfaced via web search, cross-checked against official order-backlog and business-segment disclosures where available (Aker Solutions, Aker BioMarine, Aker Carbon Capture). They are estimates, not audited company disclosures — useful for direction and magnitude, not exact headcounts. The same network restriction noted above meant these came from search snippets, not primary-source annual reports fetched directly.

## Sources consulted

Company career pages and category structures: akerbp.com/en/open-positions, careers.akerbp.com, akersolutions.com/careers/job-search, akerbiomarine.com/careers, careers.akerbiomarine.com (Teamtailor), cognite.com/en/company/careers, careers.aize.io, nscale.com/careers, job-boards.eu.greenhouse.io/nscaleoperationsukltd, solstad.com/opportunities, theqrillcompany.com/careers.
Aggregators (used only for role titles/snippets, not counts): Glassdoor, LinkedIn Jobs, Indeed, Built In.
Portfolio/ownership changes: Aker ASA press releases and coverage of the Nscale, Cognite/Schneider Electric, Aker BioMarine take-private, Aker Horizons merger/dissolution, and Aker Carbon Capture/SLB Capturi transactions.
