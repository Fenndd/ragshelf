"""Strict loader and validator for the gold evaluation set.

The format is defined in docs/evaluation/gold-set-format.md. Validation
collects every violation instead of stopping at the first one, so a reviewer
can fix a whole file in one pass. Messages name lines and fields but never
repeat record values: the real set quotes copyrighted documents and must not
leak into logs or reports.

Run `python -m ragshelf.eval.gold` to check `data/eval/gold.jsonl` against the
configured library and parse cache.
"""

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError

LANGUAGES = ("ru", "sk", "en")
QUERY_TYPES = ("factual", "comparison", "definition", "method")
# The reference answer of an unanswerable intent: the system must abstain.
ABSTAIN = "NO_ANSWER"
MIN_INTENTS = 50
UNANSWERABLE_SHARE = (0.10, 0.20)

_CYRILLIC = re.compile("[Ѐ-ӿ]")


def _not_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _relative_posix(value: str) -> str:
    # Same form as T005's doc_id: a path relative to data/library/ with
    # forward slashes. Anything else could never match a scanned document.
    path = PurePosixPath(value)
    if "\\" in value or path.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("must be a relative path with forward slashes, as produced by the library scan")
    return value


def _ascending(pages: list[int]) -> list[int]:
    if any(a >= b for a, b in zip(pages, pages[1:])):
        raise ValueError("pages must be in ascending order without duplicates")
    return pages


Text = Annotated[str, AfterValidator(_not_blank)]


class _Record(BaseModel):
    # Strict: no coercion ("3" is not a page, 1 is not true), unknown keys are errors.
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Queries(_Record):
    ru: Text
    sk: Text
    en: Text


class Evidence(_Record):
    doc_id: Annotated[str, AfterValidator(_not_blank), AfterValidator(_relative_posix)]
    # 1-based physical pages of the file: page n is content-list page_idx n - 1.
    pages: Annotated[list[Annotated[int, Field(ge=1)]], Field(min_length=1), AfterValidator(_ascending)]
    section: Text | None = None


class GoldIntent(_Record):
    id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_.-]{0,63}$")]
    type: Literal[QUERY_TYPES]
    queries: Queries
    answerable: bool
    evidence: list[Evidence]
    reference_answer: Text
    unanswerable_reason: Text | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    notes: Text | None = None

    @property
    def doc_ids(self) -> list[str]:
        return [item.doc_id for item in self.evidence]


@dataclass(frozen=True)
class Violation:
    line: int | None  # None for rules about the whole set
    field: str
    message: str

    def __str__(self) -> str:
        where = "set" if self.line is None else f"line {self.line}"
        return f"{where}: {self.field}: {self.message}" if self.field else f"{where}: {self.message}"


class GoldSetError(ValueError):
    def __init__(self, violations: list[Violation]):
        self.violations = violations
        super().__init__(f"{len(violations)} gold-set violation(s):\n" + "\n".join(map(str, violations)))


@dataclass
class GoldReport:
    intents: list[GoldIntent] = field(default_factory=list)
    violations: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def stats(self) -> dict[str, Any]:
        """Content-free counts over the structurally valid intents."""
        unanswerable = sum(not item.answerable for item in self.intents)
        answerable = [item for item in self.intents if item.answerable]
        return {
            "intents": len(self.intents),
            "unanswerable": unanswerable,
            "unanswerable_share": unanswerable / len(self.intents) if self.intents else 0.0,
            "non_empty_queries": {lang: sum(bool(getattr(i.queries, lang).strip()) for i in self.intents)
                                  for lang in LANGUAGES},
            "types": dict(sorted(Counter(item.type for item in self.intents).items())),
            "documents": len({doc for item in self.intents for doc in item.doc_ids}),
            "multi_document": sum(len(set(item.doc_ids)) > 1 for item in answerable),
            "multi_page": sum(any(len(e.pages) > 1 for e in item.evidence) for item in answerable),
        }


def check_gold(path: Path, *, library: Path | None = None, parse_cache: Path | None = None,
               min_intents: int = MIN_INTENTS,
               unanswerable_share: tuple[float, float] = UNANSWERABLE_SHARE) -> GoldReport:
    """Validate a gold JSONL file and return every violation.

    `library` (data/library/) enables the doc_id existence check;
    `parse_cache` (data/cache/parse/) additionally bounds page numbers by the
    parsed page count of each cited document and requires `library`.
    """
    if parse_cache is not None and library is None:
        raise ValueError("parse_cache requires library: page bounds are found through content hashes")
    report = GoldReport()
    lines: list[int] = []
    seen_ids: dict[str, int] = {}
    for number, raw in _read_records(path, report.violations):
        if isinstance(raw.get("id"), str):
            if raw["id"] in seen_ids:
                report.violations.append(Violation(number, "id", f"duplicate id, first used on line {seen_ids[raw['id']]}"))
            else:
                seen_ids[raw["id"]] = number
        try:
            intent = GoldIntent.model_validate(raw)
        except ValidationError as exc:
            for error in exc.errors(include_input=False, include_url=False):
                report.violations.append(Violation(number, _location(error["loc"]), error["msg"]))
            continue
        report.violations.extend(Violation(number, name, message) for name, message in _record_rules(intent))
        report.intents.append(intent)
        lines.append(number)

    _set_rules(report, min_intents, unanswerable_share)
    if library is not None:
        _library_rules(report, lines, library, parse_cache)
    return report


def load_gold(path: Path, **options: Any) -> list[GoldIntent]:
    """Return the intents of a valid set; raise `GoldSetError` listing every violation."""
    report = check_gold(path, **options)
    if not report.ok:
        raise GoldSetError(report.violations)
    return report.intents


def _read_records(path: Path, violations: list[Violation]):
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        violations.append(Violation(1, "", "file must be UTF-8 without a byte-order mark"))
        data = data[3:]
    rows = data.split(b"\n")
    if rows and rows[-1] == b"":
        rows.pop()  # the newline that ends the last record
    for number, row in enumerate(rows, 1):
        row = row.removesuffix(b"\r")
        try:
            text = row.decode("utf-8")
        except UnicodeDecodeError:
            violations.append(Violation(number, "", "line is not valid UTF-8"))
            continue
        if not text.strip():
            violations.append(Violation(number, "", "blank lines are not allowed"))
            continue
        try:
            value = json.loads(text, object_pairs_hook=_unique_keys, parse_constant=_reject_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            detail = f"{exc.msg} at column {exc.colno}" if isinstance(exc, json.JSONDecodeError) else str(exc)
            violations.append(Violation(number, "", f"invalid JSON: {detail}"))
            continue
        if not isinstance(value, dict):
            violations.append(Violation(number, "", "each line must be one JSON object"))
            continue
        yield number, value


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def _reject_constant(name: str) -> Any:
    raise ValueError(f"{name} is not valid JSON")


def _location(loc: tuple[int | str, ...]) -> str:
    text = ""
    for part in loc:
        text += f"[{part}]" if isinstance(part, int) else (f".{part}" if text else str(part))
    return text


def _record_rules(intent: GoldIntent) -> list[tuple[str, str]]:
    problems = []
    queries = intent.queries
    if not _CYRILLIC.search(queries.ru):
        problems.append(("queries.ru", "must be written in Cyrillic script"))
    for lang in ("sk", "en"):
        if _CYRILLIC.search(getattr(queries, lang)):
            problems.append((f"queries.{lang}", "must not contain Cyrillic script"))
    if queries.sk.strip().casefold() == queries.en.strip().casefold():
        problems.append(("queries.sk", "must be a Slovak query, not a copy of queries.en"))

    doc_ids = intent.doc_ids
    if intent.answerable:
        if not intent.evidence:
            problems.append(("evidence", "an answerable intent needs at least one evidence item"))
        if intent.reference_answer.strip() == ABSTAIN:
            problems.append(("reference_answer", f"{ABSTAIN} is reserved for unanswerable intents"))
        if intent.unanswerable_reason is not None:
            problems.append(("unanswerable_reason", "only unanswerable intents have a reason"))
        for index, doc_id in enumerate(doc_ids):
            if doc_id in doc_ids[:index]:
                problems.append((f"evidence[{index}].doc_id", "cite each document once; list all its pages there"))
        if intent.type == "comparison" and len(set(doc_ids)) < 2:
            problems.append(("evidence", "a comparison intent cites at least two documents"))
    else:
        if intent.evidence:
            problems.append(("evidence", "an unanswerable intent has no evidence"))
        if intent.reference_answer != ABSTAIN:
            problems.append(("reference_answer", f"an unanswerable intent's answer is exactly {ABSTAIN}"))
        if intent.unanswerable_reason is None:
            problems.append(("unanswerable_reason", "required for an unanswerable intent"))
    return problems


def _set_rules(report: GoldReport, min_intents: int, share: tuple[float, float]) -> None:
    count = len(report.intents)
    if count < min_intents:
        report.violations.append(Violation(None, "", f"{count} valid intents; at least {min_intents} required"))
    if count:
        actual = sum(not item.answerable for item in report.intents) / count
        low, high = share
        if not low <= actual <= high:
            report.violations.append(Violation(
                None, "answerable", f"unanswerable share {actual:.1%} is outside {low:.0%}-{high:.0%}"))


def _library_rules(report: GoldReport, lines: list[int], library: Path, parse_cache: Path | None) -> None:
    # Imported here so that loading a gold file never touches the parser registry.
    from ragshelf.parse.scan import scan_library

    hashes = {source.doc_id: source.content_hash for source in scan_library(library)}
    page_counts: dict[str, int | None] = {}
    for number, intent in zip(lines, report.intents):
        for index, item in enumerate(intent.evidence):
            if item.doc_id not in hashes:
                report.violations.append(Violation(number, f"evidence[{index}].doc_id", "not found in the library"))
                continue
            if parse_cache is None:
                continue
            if item.doc_id not in page_counts:
                page_counts[item.doc_id] = parsed_page_count(parse_cache / hashes[item.doc_id], hashes[item.doc_id])
            pages = page_counts[item.doc_id]
            if pages is None:
                report.violations.append(Violation(
                    number, f"evidence[{index}].pages", "no valid parse bundle for this document; pages unchecked"))
                continue
            for position, page in enumerate(item.pages):
                if page > pages:
                    report.violations.append(Violation(
                        number, f"evidence[{index}].pages[{position}]",
                        f"page {page} is beyond the document's {pages} parsed pages"))


def parsed_page_count(entry_root: Path, source_hash: str) -> int | None:
    """Pages in the parse bundle of one content hash: last page_idx + 1.

    Considers only sealed, checksum-valid bundles; with several parser
    versions cached, the largest count wins. None when nothing valid exists.
    """
    from ragshelf.parse.cache import cache_valid

    counts = []
    if not entry_root.is_dir():
        return None
    for entry in sorted(entry_root.iterdir()):
        # Work directories and quarantined bundles start with a dot.
        if entry.name.startswith(".") or not entry.is_dir():
            continue
        try:
            descriptor = json.loads((entry / "manifest.json").read_text(encoding="utf-8"))["parser"]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if not cache_valid(entry, source_hash, descriptor):
            continue
        content = json.loads((entry / "content_list.json").read_text(encoding="utf-8"))
        counts.append(max((item["page_idx"] for item in content), default=-1) + 1)
    return max(counts) if counts else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ragshelf.eval.gold",
                                     description="Validate the gold evaluation set.")
    parser.add_argument("gold", nargs="?", type=Path, help="default: <paths.eval>/gold.jsonl")
    parser.add_argument("--library", type=Path, help="default: paths.library")
    parser.add_argument("--parse-cache", type=Path, help="default: <paths.cache>/parse")
    parser.add_argument("--no-library", action="store_true", help="skip the doc_id and page checks")
    parser.add_argument("--min-intents", type=int, default=MIN_INTENTS)
    parser.add_argument("--unanswerable-min", type=float, default=UNANSWERABLE_SHARE[0])
    parser.add_argument("--unanswerable-max", type=float, default=UNANSWERABLE_SHARE[1])
    args = parser.parse_args(argv)

    if args.gold is None or (not args.no_library and (args.library is None or args.parse_cache is None)):
        from ragshelf.config import load_settings

        paths = load_settings().paths
        args.gold = args.gold or paths.eval / "gold.jsonl"
        args.library = args.library or paths.library
        args.parse_cache = args.parse_cache or paths.cache / "parse"
    library = None if args.no_library else args.library
    report = check_gold(args.gold, library=library, parse_cache=None if args.no_library else args.parse_cache,
                        min_intents=args.min_intents,
                        unanswerable_share=(args.unanswerable_min, args.unanswerable_max))
    for violation in report.violations:
        print(violation)
    print(json.dumps(report.stats(), indent=2))
    print("OK" if report.ok else f"FAILED: {len(report.violations)} violation(s)")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
