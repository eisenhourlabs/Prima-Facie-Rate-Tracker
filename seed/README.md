# Seed import

Past prima facie rate changes enter the tracker as seed batches. A batch is a CSV in this
folder (for example `batch_01.csv`) that follows `import_template.csv`. Design: `docs/plan.md`
section 7. Commands run from the repository folder with the project Python:
`.venv\Scripts\python.exe -m pfrt ...`

## The batch file

One row per rate item. Rows with the same `state`, `product` and `effective_date` become one
record. Fields that belong to the whole record (summary, source, legal basis and so on) may be
written on the first row of the record only; if two rows give different values, that is an error.

| Column | Required | Example |
|---|---|---|
| `state` | yes | `WI` |
| `product` | yes | `CL`, `CD` or `IUI` |
| `change_type` | yes | `change`, `no_change` or `initial` |
| `effective_date` | yes | `2021-01-01` |
| `date_communicated` | no | `2020-09-30`; blank allowed for old records (shown as "Not stated") |
| `source_url` | yes | Primary-source URL; `NONE` if no public source is known (record is unverified) |
| `source_title` | no | `Bulletin 2020-09-30` |
| `plan` | yes unless `no_change` | `Single premium, 12 months, 14-day retroactive` |
| `basis` | yes unless `no_change` | `per $100 of initial insured indebtedness` |
| `old_rate` | no | `0.50` |
| `new_rate` | yes unless `no_change` | `0.45` |
| `rate_table_note` | no | Where the full table is |
| `summary` | yes | Plain English, 20 to 600 characters |
| `legal_basis` | yes | Citation |
| `public_document_file` | no | File name in `seed/documents/` of the public document. Several names may be given, separated by `;`: the first is the copy of `source_url`, the others (such as a separate rate table) are saved too and listed in the rate table note |
| `notes` | no | Not shown on the site, but public in the repository |

Headline rates (owner's decision, A5): the 12-month and 60-month rates for each product, where
the state publishes rates by term. A "reviewed, no change" notice (A6) is one row with
`change_type` `no_change` and no rates; it shows in Historical only.

## Steps

1. Original work documents stay in `internal/seed_raw/` (git-ignored). They never leave it.
2. Copy only facts into the batch CSV. Do not copy sentences from internal documents.
3. For each record, find the public primary source and put its URL in `source_url`. Download
   the public copy from the official site into `seed/documents/`. That folder is git-ignored:
   import copies each file into `archive/`, which is what gets committed.
4. Work through the scrubbing checklist below.
5. `seed scan seed/` must pass.
6. `seed validate seed/batch_01.csv` lists errors and warnings by row. Fix every error.
7. `seed import seed/batch_01.csv` makes one candidate per record (origin `seed`). It refuses
   if there is any error or the scan fails.
8. Check each value against its saved document, then
   `review confirm --batch batch_01`. This confirms only the candidates with no warnings and
   leaves the rest open; confirm those one at a time with `review confirm ID`. A record that
   would be unverified is never confirmed in bulk.
9. `validate`, `build`, preview, commit, push.

## Scrubbing checklist (plan 7.3)

Before any seed file is committed:

- [ ] No employer, affiliate, client, vendor or colleague names, in text or in file names.
- [ ] No internal rates: deviated rates, filed company rates, account rates, commissions, loss
      ratios or experience data. Only state prima facie or presumptive rates.
- [ ] No filing identifiers, tracking numbers, system names, product codes or form numbers.
- [ ] No borrower, account or policy data.
- [ ] No internal commentary, opinions, deadlines or project names.
- [ ] `notes` column reviewed; it is not shown on the site but is public in the repository.
- [ ] Documents in `seed/documents/` were downloaded from the official public site, not taken
      from internal copies, so they carry no annotations, stamps, routing marks or highlights.
- [ ] Document properties checked: author, company, comments and tracked changes are absent.
- [ ] `seed scan seed/` passes. It searches file and folder names, CSV text, and the extracted
      text, metadata and comments of each PDF for the terms in `internal/blocklist.txt`. It
      prints file names only, never the terms. A file it cannot search (Word, Excel, a scanned
      PDF with no text) fails the scan: convert it to a text PDF, check it by hand, or remove it.
- [ ] A final read of `git diff --staged` before committing.
