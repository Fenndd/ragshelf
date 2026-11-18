# Gold evaluation set format

The gold set measures retrieval and answers independently of chunking ([ADR 0002, Evaluation](../decisions/0002-pipeline-architecture.md); [research §4](../research/reports/Production%20RAG%20architecture.md)). It covers requirement R2 (the same intent asked in Russian, Slovak, and English over mostly English documents) and R3 (answers cite a document and its location; when the library holds no evidence, the system abstains).

The set lives in `data/eval/gold.jsonl`, which is not tracked: its queries and reference answers paraphrase copyrighted documents. Everything shown in this file is synthetic.

## File

- One JSON object per line (JSON Lines), encoded as UTF-8 without a byte-order mark. Non-ASCII characters are written as themselves, not as `\u` escapes (both parse; literal characters keep the file reviewable).
- Lines end with LF; a CR before the LF is tolerated. The final newline is optional. Blank lines, comments, duplicate keys within an object, and `NaN`/`Infinity` are errors.
- Each line is one *intent*: one information need, asked in all three languages, with one set of labels.
- Unknown fields are errors. Values are never coerced: `"3"` is not a page and `1` is not `true`.

## Fields

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable intent ID, unique in the file. Lowercase letters, digits, `_`, `.`, `-`; starts with a letter or digit; at most 64 characters. Convention: `q001`, `q002`, … in file order. IDs are never reused for a different intent. |
| `type` | string | yes | One of `factual`, `comparison`, `definition`, `method` (see [Query types](#query-types)). |
| `queries` | object | yes | Exactly the keys `ru`, `sk`, `en`, each a non-blank string (see [Queries](#queries)). |
| `answerable` | boolean | yes | `true` when the library contains evidence that answers the intent; `false` when the system should abstain. |
| `evidence` | array | yes | The relevant locations (see [Evidence](#evidence)). At least one item when `answerable` is `true`; exactly `[]` when it is `false`. |
| `reference_answer` | string | yes | For an answerable intent, a short English answer of 1–3 sentences that is fully supported by the cited pages. For an unanswerable intent, exactly the abstention marker `NO_ANSWER`, which answerable intents must not use. |
| `unanswerable_reason` | string | when unanswerable | Why the corpus does not answer the intent, and how this was established (for example, which key terms were searched for in the parsed text). Absent or `null` for answerable intents. |
| `difficulty` | string | no | `easy`, `medium`, or `hard`: the labeller's estimate of how hard retrieval is (for example, `hard` when the wording differs strongly from the document, the evidence is one sentence in a book, or the intent is a near-miss unanswerable). |
| `notes` | string | no | Free-text labelling notes: ambiguity, why a page was chosen, review corrections. |

`null` is accepted for the optional fields and means the same as leaving them out.

### Query types

These are the kinds of questions the user asks of the library (task T010):

- `factual` — a specific fact stated in a document: a sample size, a result, a percentage, who proposed something.
- `comparison` — a comparison across documents: how two or more documents differ or agree on a point. An answerable comparison cites at least two different documents.
- `definition` — what a term or construct means, as defined in a document.
- `method` — how a study was done: design, sample, instruments, analysis, procedure.

### Queries

- Each of `ru`, `sk`, and `en` expresses the same intent as a researcher would naturally ask it in that language. They are independent phrasings, not word-for-word translations, so that the evaluation exercises query translation (ADR 0001) rather than lexical overlap.
- Technical terms are written as speakers of that language use them; an English term may stay English where that is natural (for example an instrument's acronym).
- Queries do not name the page, and name a document only when a user would (for example "in the Replika study").
- Validation checks that `ru` contains Cyrillic script, that `sk` and `en` contain none, and that `sk` is not a copy of `en`. It does not check language quality; the user's review does.

### Evidence

Each evidence item is an object:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `doc_id` | string | yes | The document's identity as defined in T005 and ADR 0002: its path relative to `data/library/`, with forward slashes, exactly as `ragshelf.parse.scan.scan_library` reports it (for a file at the library root, its file name, for example `Some Article.pdf`). Sidecar `.metadata.json` files are not documents. |
| `pages` | array of integers | yes | The pages that hold the supporting text, ascending, without duplicates, at least one. |
| `section` | string | no | The heading under which the evidence appears, as written in the document, to help a reviewer find it. Not used for scoring. |

**Page convention.** `pages` are **1-based physical page numbers of the file**: page 1 is the first page of the PDF as it is stored in `data/library/`, regardless of the page numbers printed on the page (journal pagination, roman-numeral front matter, or a book's printed page numbers). Page *n* corresponds to the parse-cache content items with `page_idx` *n − 1* in `data/cache/parse/<content-sha256>/<parser-key>/content_list.json`. A plain-text or Markdown document has only page 1 (its logical `page_idx` is 0).

Rules for choosing evidence:

- Cite every page a reader needs to verify the reference answer, and only those. When a sentence runs across a page break, cite both pages.
- One item per document: put all of a document's pages in one item.
- An intent may cite several documents (always for `comparison`; also when several documents state the same fact). A retrieval hit on any cited page counts as relevant; T015 defines the metrics.
- Prefer the page where the content is stated over the abstract that summarises it, and add the abstract's page when it answers the intent on its own.
- A document cited for an answerable intent must be parsed; its pages must not exceed the parsed page count (last `page_idx` + 1).

### Unanswerable intents

An unanswerable intent is a plausible question in the library's subject area that no document answers. It has `answerable: false`, `evidence: []`, `reference_answer: "NO_ANSWER"`, and an `unanswerable_reason`. The labeller establishes that the answer is absent by searching the parsed text of all documents for the intent's key terms and their variants, not by assumption, and records the search in the reason. Some unanswerable intents should be *near misses*: they mention a construct, population, or instrument the library does discuss, but ask for something the documents do not report; say so in `notes`.

## Set-level rules

- At least 50 intents (`MIN_INTENTS`).
- Between 10% and 20% unanswerable, inclusive (`UNANSWERABLE_SHARE`).
- Both thresholds are parameters of the validator, so a smaller set (for example a smoke subset) can be checked with other bounds.

## Validation

`src/ragshelf/eval/gold.py` loads and validates the file. It reports every violation with its line number (or `set` for set-level rules) and the field path, for example `line 12: evidence[0].pages[1]: page 31 is beyond the document's 23 parsed pages`. Messages never repeat record text.

```
python -m ragshelf.eval.gold                                  # data/eval/gold.jsonl, configured library and parse cache
python -m ragshelf.eval.gold path/to/gold.jsonl --no-library  # structure and set rules only
```

Defaults come from the configured `paths.eval`, `paths.library`, and `paths.cache`. With a library, every `doc_id` must name a scanned document; with the parse cache as well, every page must be within that document's parsed page count, taken from its valid parse bundle (the largest count when several parser versions are cached). The command prints content-free statistics and exits with status 0 when the set is valid and 1 otherwise. Code reads the set with `ragshelf.eval.gold.load_gold`, which raises `GoldSetError` listing every violation.

## Synthetic example

Three lines of a file (wrapped here for reading; in the file each object is on one line):

```json
{"id": "q001", "type": "method", "queries": {"ru": "Сколько участников было в исследовании о сне студентов и как их набирали?", "sk": "Koľko účastníkov mala štúdia o spánku študentov a ako ich získali?", "en": "How many participants were in the student sleep study, and how were they recruited?"}, "answerable": true, "evidence": [{"doc_id": "studies/Example Sleep Study.pdf", "pages": [3, 4], "section": "2.1 Participants"}], "reference_answer": "The study included 120 undergraduates recruited through a university participant pool.", "difficulty": "easy"}
{"id": "q002", "type": "comparison", "queries": {"ru": "Чем различаются выводы двух обзоров о влиянии кофеина на память?", "sk": "V čom sa líšia závery dvoch prehľadov o vplyve kofeínu na pamäť?", "en": "How do the two reviews differ in their conclusions about caffeine and memory?"}, "answerable": true, "evidence": [{"doc_id": "Example Review A.pdf", "pages": [9]}, {"doc_id": "Example Review B.pdf", "pages": [2, 11]}], "reference_answer": "Review A finds a small benefit for recall, while Review B finds no reliable effect once sleep is controlled."}
{"id": "q003", "type": "factual", "queries": {"ru": "Какова распространённость бессонницы среди студентов в Словакии?", "sk": "Aká je prevalencia nespavosti medzi študentmi na Slovensku?", "en": "What is the prevalence of insomnia among university students in Slovakia?"}, "answerable": false, "evidence": [], "reference_answer": "NO_ANSWER", "unanswerable_reason": "No document reports data from Slovakia; searched the parsed text for Slovakia/Slovak and for prevalence figures.", "difficulty": "hard", "notes": "Near miss: the sleep study reports insomnia, but in another country."}
```
