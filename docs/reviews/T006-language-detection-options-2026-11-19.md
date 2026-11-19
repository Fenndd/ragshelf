# T006 document-language detection: options for the user's decision

Date: 2026-11-19. Status: analysis and recommendation only; **no option has been accepted**. Scope: document metadata, not query-language detection. This report is the only file changed by this analysis. Existing implementation and other unfinished changes were preserved.

## Recommendation

If automatic document-language labels are useful to you, retaining `langdetect` as an **advisory metadata fallback after the sidecar** is the most proportionate option on the evidence available. It is already installed, works locally on the tested prose, and does not require a GPU or another downloaded model. Keeping it requires an explicit amendment to accepted ADR 0002. The proposed safeguards below matter more than changing the package name.

If language is currently only a rarely consulted descriptive field, **sidecar-only plus unknown otherwise is equally defensible and simpler**. It sacrifices automatic coverage without sacrificing the multilingual requirement itself. A hand-written ru/sk/en heuristic is the least attractive default: it replaces a small dependency with project-owned classification rules and a new, unconfirmed restriction on languages. No measured need currently justifies adding another detector.

The underlying product choice is how much automatic coverage is worth compared with wrong labels and manual corrections. The repository does not specify an accuracy target, supported document-language whitelist, or the meaning of one language label for a multilingual document. Those remain your decisions.

## Confirmed contract and current behavior

- [Requirements R2 and R6](../requirements.md): documents and queries may be multilingual; Russian and Slovak queries over mostly English documents must work. R6 explicitly requires automatic title, authors, year and DOI extraction, but does **not** explicitly require automatic language detection or restrict documents to ru/sk/en.
- [T006](../../tasks/T006-document-model-and-metadata.md) includes language in document metadata. [ADR 0002](../decisions/0002-pipeline-architecture.md), accepted on 2026-11-16, includes language in index metadata and explicitly schedules removal of `langdetect`. Its prototype review ties that removal to the old chunker dropping non-English chunks. That documented rationale is not evidence that the detector itself is unsuitable for descriptive metadata; equally, it does not authorize ignoring the accepted removal decision.
- [`detect_language`](../../src/ragshelf/documents/metadata.py) accepts body paragraph/list texts, skips each text shorter than 80 characters, and takes consecutive eligible blocks until their total reaches 5,000 characters. Whole blocks are appended, so 5,000 is not a hard character limit. The installed detector internally considers at most the first 10,000 input characters after its initial cleaning. An early section can therefore dominate the document label.
- [`build_document`](../../src/ragshelf/documents/build.py) calls detection after running-text removal and reference separation, excluding headings/tables/code/captions from its input. It does not discard body text based on the detected language. Reference separation does not depend on this language value. Query translation uses its own LLM reply in [`retrieve/translate.py`](../../src/ragshelf/retrieve/translate.py).
- The wrapper sets `DetectorFactory.seed = 0`, returns the top language, and returns `None` for insufficient text or `LangDetectException`. It has no confidence threshold or mixed-language outcome. Seeding makes repeated results reproducible in the tested environment; it does not make them correct or guarantee identical results across versions/environments.
- The sidecar wins when values are merged, but detection still runs first even when a sidecar supplies language. A missing detector import would still fail for eligible text. Sidecar-only is therefore a small implementation change, not merely deleting the dependency.
- [`Metadata`](../../src/ragshelf/documents/model.py) allows `language=None` and records provenance. The source label `langdetect` also appears in model constants, candidates/precedence, tests and documentation. Although the detector call is isolated, a clean replacement is not literally a one-file change. `normalize_language` preserves unrecognized nonempty strings lowercased; sidecar entries are not validated against a complete language-code registry. Empty sidecar values currently do not suppress inference.

## Local checks and what they establish

No library document contents were read or sent anywhere. No external service, model download or dependency installation was used. Measurements below use synthetic text and the installed project environment.

Command: `venv/Scripts/python.exe -m pytest tests/documents/test_metadata.py -k 'language or sidecar' -q` — **58 passed, 134 deselected, 1.12 s**. The existing deterministic test checks one long prose example each for en/ru/sk/de/fr, five calls apiece. This verifies those fixtures and sidecar behavior, not corpus-wide accuracy.

An additional inline Python probe called the actual `detect_language` wrapper five times per case. All five outputs agreed in each case. The en/ru/sk prose came from the existing committee-proposal fixtures; additional cs/uk/bg prose expressed the same synthetic scenario.

| Synthetic case | Observed result | Interpretation |
| --- | --- | --- |
| Long en, ru, sk prose; analogous cs, uk, bg prose | Correct respective label in these six examples | Neighboring-language examples work; six sentences are not an accuracy benchmark. |
| Slovak fixture with diacritics removed | `sk` | A rule requiring Slovak-specific accented characters would miss this case. |
| `The experiment continues.`, `Эксперимент продолжается.`, `Experiment pokračuje.` as individual blocks | `None` each | Current wrapper rejects short blocks before calling the detector. |
| Forty separate `The experiment continues.` blocks, 1,000 total characters | `None` | Enough aggregate text does not help if every block is under 80 characters. Parser segmentation affects coverage. |
| One block containing `API CPU GPU JSON SQL HTTP XML DNA RNA ` repeated ten times | `so` | Acronyms received a Somali label. This has no defensible single natural-language ground truth; it demonstrates a false assignment on non-prose. |
| One Russian and one English fixture paragraph, 366 total characters | `en` | One returned label loses the other language. |
| One Slovak and one English fixture paragraph, 364 total characters | `en` | A mixed result is not represented. Neither mixed case has an agreed single-label ground truth. |
| Thirty English fixture paragraphs followed by 300 Russian ones | `en` | Opening sample wins despite the much larger Russian body. |
| Thirty Russian fixture paragraphs followed by 300 English ones | `ru` | Symmetric sampling failure; replacing the classifier alone would not fix it. |
| Russian or Slovak prose containing API/JSON/SQL/HTTP/GPU/CPU | `ru` / `sk` respectively | Technical terms need not break detection when sufficient contextual prose exists. |
| Digits only | `None` | No usable features. |

One fresh-process first detection took **294 ms**, including lazy detector import/profile initialization but excluding Python process startup and the earlier import of the project module. Warm median times over five calls per case were approximately **1.4–17.1 ms** for nonempty labels in this probe. These are local observations, not service-level guarantees; process-wide RAM and concurrent initialization were not measured. Repetition-heavy samples intentionally expose sampling behavior and are not representative corpus data.

## Options and trade-offs

| Option | Benefit | Cost / failure mode | When it makes sense |
| --- | --- | --- | --- |
| Retain seeded `langdetect` | Existing offline implementation, broad installed profiles, sidecar correction and provenance | Wrong top labels on ambiguous/non-prose inputs; sampling and mixed-language limitations; accepted ADR needs amendment | Automatic labels are useful as advisory metadata. |
| Stdlib script/stopword heuristic | No detector package; explicit rules and cheap abstention can be simple | Cyrillic is not synonymous with Russian: Ukrainian and Bulgarian use it too. Latin script does not distinguish English/Slovak/Czech. Short/no-diacritic text, shared words and terminology need rules and evaluation. Restricting output to ru/sk/en can silently mislabel other languages. | You explicitly choose a small supported language set and prefer unknown over guesses; maintain a measured rule set. |
| Sidecar-only, otherwise `None` | No automatic false assignments; minimal runtime; preserves explicit user authority | Manual labels may themselves be wrong/stale; unlabeled documents stay unknown; extra work if many labels are wanted | Language is optional descriptive metadata and automated coverage has little immediate value. |
| Same detector with bounded, distributed sampling and abstention | Targets demonstrated weaknesses without introducing another engine | More code and calibration; confidence scores are not established real-world correctness probabilities; multilingual aggregation needs defined semantics | A measured need for better label reliability emerges. This is a proposed refinement, not implemented behavior. |
| Another local statistical detector or existing parser-provided language | Potentially different accuracy/runtime characteristics or reuse of existing information | No comparative benchmark or reliable parser-language contract was verified here. Current `PdfInfo` has no language field. Package/model size, Windows/Python 3.14 support and licenses would need checking before selection. | Current detector fails agreed examples after sampling is fixed, or a trustworthy parser field is established. |

An LLM call solely for document-language metadata is not justified by these results. It would introduce runtime/model coordination and, for a remote service, a new document-data transfer. The existing query-translation LLM is not evidence that document metadata should use that route.

### Dependency and licensing evidence

`pyproject.toml` directly declares `langdetect`; `requirements.txt` and installed metadata identify version **1.0.9**. Installed metadata declares only `six` as a required dependency. Its recorded installed files total **2,309,011 bytes (about 2.20 MiB)**, include 55 language profiles, and contain no `.dll`, `.pyd` or `.so` files. Inspected detection code uses local profiles and Python computation, with no network request or GPU path. These facts support “small installed local dependency”; they do not establish current upstream maintenance or future compatibility. The local tests demonstrate operation in the existing environment, not a clean reinstall.

**License metadata discrepancy:** installed package metadata says `MIT`, while `venv/Lib/site-packages/langdetect-1.0.9.dist-info/licenses/LICENSE` and `NOTICE` state Apache License 2.0 (the latter identifies the underlying Cybozu language-detection work). Do not describe it as unambiguously MIT based on metadata alone. Preserve the license/notice evidence and resolve the attribution record during dependency/release review if retained. This is an inventory finding, not a legal conclusion. No public-package freshness or alternative-package licensing research was performed.

## Proportionate decision and follow-up checks

Before implementation, choose whether the field means “best-effort primary document language,” “explicit user label only,” or something that represents multiple languages. A single optional string already supports the first two; a structured multilingual result would be a separate contract change. Also choose whether inference is allowed to stay unknown and whether any future retrieval/filtering component may rely on it. The recommendation is to keep inferred language advisory and never exclude content solely on that label.

For retention, the proportionate next step is an agreed small regression set covering en/ru/sk plus cs/uk/bg distractors, short-block segmentation, missing accents, OCR-like noise, multilingual openings, acronym-only content, and sidecar precedence. Test body preservation independently of language. If sampling changes, bound the actual characters processed and test the beginning/middle/end cases. If a confidence threshold is added, select it on labeled examples rather than assuming a probability such as 0.9 means 90% accuracy.

For sidecar-only, verify that unknown language does not prevent build/inspect or later ingestion, that explicit language retains sidecar provenance, and that `langdetect` is no longer called. Remove the package only when the remaining legacy chunker import is retired or otherwise resolved under the existing task plan.

For a heuristic or replacement engine, compare against the same fixtures before adoption. Record **coverage** (nonempty labels / all eligible documents), **error rate among assigned labels**, confusion pairs, mixed/non-prose false assignments, and cold/warm runtime. The acceptable error-versus-unknown trade-off must be set by the user; this report supplies no invented product threshold. A content-free user-labeled corpus check would be more informative than expanding synthetic examples indefinitely.

Unverified: real-library language distribution and accuracy; acceptable quality thresholds; multilingual label semantics; performance/memory at scale; current upstream maintenance; competing engines. No source, dependency, ADR, task status or acceptance decision was changed.
