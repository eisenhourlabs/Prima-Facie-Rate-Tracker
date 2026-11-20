# Prima Facie Rate Tracker

An unofficial, personal compilation of state prima facie rate changes for credit life,
credit disability and involuntary unemployment insurance, built from public sources only.

A scheduled job checks state insurance department and regulation pages twice a month and
flags possible rate changes for review. Only reviewed, confirmed records are published.
Every record links to its official source, and the linked source governs. This is not
legal or actuarial advice.

Status: under construction. See [docs/plan.md](docs/plan.md) for the design and build plan
and [docs/decisions.md](docs/decisions.md) for decisions made.

## Quick start (local)

```
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pfrt config check
pytest
```
