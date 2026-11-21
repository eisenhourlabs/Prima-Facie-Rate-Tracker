# Manual checks and data gaps

What the tracker cannot do automatically, and history it is missing. Each item says why and
what would close it. Update this file when an item is closed or a new one is found. Reasons
for each decision are in `docs/decisions.md`.

Last updated: 2026-11-20.

## States checked by hand (not monitored automatically)

These states appear on the page under "Not monitored automatically". A new notice there is
not detected by the scheduled check; it must be looked for by hand.

| State | Why | Where to look | What would close it |
|---|---|---|---|
| Arizona | difi.az.gov and publicmeetings.az.gov answer HTTP 403 to the tool (Cloudflare bot check). Getting past it is ruled out | Department of Insurance and Financial Institutions orders setting prima facie rates (A.A.C. R20-6-604.03 to .05; A.R.S. 20-1621.05), at least every three years; hearing notices on publicmeetings.az.gov | The site stops refusing the tool, or another official host of the orders is found. Seed history needs the orders saved by hand |
| West Virginia | Only the rules list and the 114-06 rule file are watched (lagging). The Commissioner's bulletins and informational letters index is built by JavaScript (the tool sees 245 characters and no links), so a triennial adjustment published there (114-6-8) would not be detected | Insurance Commissioner insurance bulletins (informational letters until 2020) on wvinsurance.gov | A fetchable index of bulletins, or a browser-based fetcher (plan Q7) |
| Virginia | www.scc.virginia.gov robots.txt admits named search engines only, deliberately; its web policy limits use to "intended purposes". Not overridden | State Corporation Commission orders for each triennium (Va. Code 38.2-3725, 38.2-3730) | An owner decision to override, or another official host. No seed records yet |

Until monitoring is enabled in Stage 6, every state other than the pilot sources is also
unmonitored (see the page and `config/sources.csv`). New Mexico and South Carolina have seed
records but their sources are still disabled.

## Missing history

| State | Missing | Why | What would close it |
|---|---|---|---|
| South Carolina | Rates for 2025 and earlier | The 2025 orders (Order Numbers 2024-04 and 2024-06) are scanned images with no text, which `seed scan` rejects; older orders are only on dc.statelibrary.sc.gov, which refuses the tool (robots.txt, then 403) | Hand-checked import of the scanned orders (see "Tool changes needed"); older orders saved by hand. SC-CD-2026-01-01-1 then gets its old rates |
| New Mexico | Rates before February 2022, and old rates for NM-CD-2022-02-01-1 | Bulletins 2017-012 and 2019-018 are scanned images; no earlier credit rate bulletin is listed on the site (its index reaches back to about 2015) | Hand-checked import of the two scanned bulletins; earlier rates from the pre-2025 rule text (13.18.2 NMAC as filed 2007) if needed |
| Arizona | All | See above | Orders saved by hand |
| Iowa | Any triennial adjustment since March 30, 2001 | 28.10 requires a triennial review published by bulletin, but the only credit rate bulletin in the Division's index (83 bulletins) is 00-04 (effective March 30, 2001), and the rule rates are unchanged since 2007 or earlier | None needed unless an adjustment is found |
| Oregon | Any adjustment published under OAR 836-060-0041 since 2001 | The rate rules (836-060-0026 and -0031) were last amended effective January 1, 2001; -0041 says the Director publishes adjusted rates "if published", and none was found. The Division's filing checklist points to the rates adopted in the rules | None needed unless an adjustment is found |
| West Virginia | Any triennial adjustment since July 1, 2011 | Rule series 114-06 took effect July 1, 2011 (just outside the window); no adjusted-rate letter or bulletin after it was found, but the index cannot be read by the tool (see above). The rule file is a scanned image | Check the bulletins index by hand; if an adjustment exists, save it and seed it |
| North Dakota | Any triennial adjustment since 2006 | 45-07-01.1-09 requires a triennial review beginning January 1, 2006 and publication of adjusted rates, but no credit rate bulletin after 2002 is listed and the rates in the rule are unchanged since 2003 (the 2021 amendment corrected formulas only) | None needed unless an adjustment is found published elsewhere |
| Utah | Confirmation that no rate changed in 2011-2026 | No revision order under R590-91-10 was found, and the disability data is dated 06/2008; the 2022 rule amendment (Utah State Bulletin 2022-07) was not read to confirm it left the $0.65 credit life rate unchanged | Read the 2022 filing in the Utah State Bulletin (rules.utah.gov); if a rate changed, seed that record |
| Virginia | All | See above | Owner decision or documents saved by hand |
| Indiana | Official copy of 760 IAC 1-5.1 | The disability bulletins do not state the rate unit; "per $100 of initial insured debt" rests on the owner's statement and 760 IAC 1-5.1-7 as described in search results. The legacy IAC PDF is gone, iar.iga.in.gov has an unreadable robots.txt, Justia answers 403 | Save an official copy of the rule when one can be fetched, and cite it in the six IN-CD records |
| Wisconsin | Old rates for the 2009 records | The 2005 bulletin and 2006 table were not saved. The 2009 records are outside the 15-year window and hidden | Low priority; save them only if the 2009 records are ever shown |
| Indiana | Bulletin 144 (2007) as a record | Outside the 15-year window; the 2009 record already carries its rates | Low priority |

## Open questions on recorded data

| Item | Note |
|---|---|
| Indiana effective dates | Bulletins 173 to 262 state no effective date; the records use the bulletin date. IN-CD-2025-07-01-1 uses the "no later than" date. Amend if another convention is preferred |
| South Carolina orders | The file named "Order No. 2025-003" is headed "Number 2025-004" (the 3-day order's number); Order 2026-04's opening says "for use during 2026" while its table is for 2027. Both noted in the records |

## Tool changes needed

| Change | Why | When |
|---|---|---|
| Hand-checked import of scanned PDFs | `seed scan` rejects PDFs with no text, by design. A reviewed exception (the owner checks the file, the decision is logged per file) would let the scanned SC and NM documents in; values would be read from page images | When the SC and NM gaps are filled |
| `review add --file` | `review add` can only download. Blocked sites (Arizona, Virginia) need a candidate made from a document saved by hand, keeping the official URL | Stage 6 |
| Enable monitoring for New Mexico and South Carolina | Their sources are in `config/sources.csv` but disabled; New Mexico now fetches under the robots override | Stage 6 |
| Idaho | Fetches work from GitHub Actions but not from the build computer; `must_contain` markers still to be chosen | Stage 6 (see `docs/status.md`) |

## Other deferred items

- Email and the backup GitHub issue are built but off (see `docs/status.md`). Until they are
  configured, a new candidate is seen only on the site or in the run summary.
- The scheduled run is off until Stage 8.
