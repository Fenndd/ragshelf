import json

import pytest

from ragshelf.eval.gold import ABSTAIN, GoldSetError, check_gold, load_gold, main
from ragshelf.parse import content_hash
from ragshelf.parse.cache import parser_key, seal_bundle

# Synthetic records only: the real set lives untracked in data/eval/.
SECRET = "Synthetic-marker-7f3a"


def answerable(number, **overrides):
    record = {
        "id": f"q{number:03d}",
        "type": "factual",
        "queries": {
            "ru": f"Сколько участников было в синтетическом исследовании {number}?",
            "sk": f"Koľko účastníkov malo syntetické štúdium {number}?",
            "en": f"How many participants did synthetic study {number} have?",
        },
        "answerable": True,
        "evidence": [{"doc_id": "alpha.pdf", "pages": [1, 2], "section": "Method"}],
        "reference_answer": "The synthetic study had 40 participants.",
    }
    record.update(overrides)
    return record


def unanswerable(number, **overrides):
    record = answerable(number, answerable=False, evidence=[], reference_answer=ABSTAIN,
                        unanswerable_reason="No synthetic document reports this.")
    record.update(overrides)
    return record


def gold_set(size=10, unanswerable_count=1):
    return [unanswerable(n) if n <= unanswerable_count else answerable(n) for n in range(1, size + 1)]


def write(path, records):
    path.write_text("".join(
        (r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)) + "\n" for r in records), encoding="utf-8")
    return path


def check(tmp_path, records, **options):
    options.setdefault("min_intents", 1)
    return check_gold(write(tmp_path / "gold.jsonl", records), **options)


def problems(report):
    return {(v.line, v.field) for v in report.violations}


def parsed(cache, original, page_indexes):
    descriptor = {"name": "fake", "version": 1}
    bundle = cache / content_hash(original) / parser_key(descriptor)
    bundle.mkdir(parents=True)
    (bundle / "markdown.md").write_text("Synthetic", encoding="utf-8")
    (bundle / "content_list.json").write_text(json.dumps(
        [{"type": "text", "text": "Synthetic", "page_idx": i} for i in page_indexes]), encoding="utf-8")
    seal_bundle(bundle, content_hash(original), descriptor)
    return bundle


@pytest.fixture
def library(tmp_path):
    """Synthetic originals: alpha has three parsed pages (one without text), beta one, unparsed none."""
    root = tmp_path / "library"
    (root / "sub").mkdir(parents=True)
    cache = tmp_path / "cache" / "parse"
    for name, payload, pages in (("alpha.pdf", b"synthetic alpha", (0, 2)),
                                 ("sub/beta.pdf", b"synthetic beta", (0,)),
                                 ("unparsed.pdf", b"synthetic unparsed", None)):
        (root / name).write_bytes(payload)
        if pages is not None:
            parsed(cache, root / name, pages)
    return root, cache


def test_valid_set_loads_and_reports_counts(tmp_path, library):
    root, cache = library
    records = gold_set()
    records[-1] = answerable(10, type="comparison", evidence=[
        {"doc_id": "alpha.pdf", "pages": [3]}, {"doc_id": "sub/beta.pdf", "pages": [1]}])
    intents = load_gold(write(tmp_path / "gold.jsonl", records), library=root, parse_cache=cache, min_intents=10)
    assert [i.id for i in intents] == [f"q{n:03d}" for n in range(1, 11)]
    assert intents[0].answerable is False and intents[1].evidence[0].pages == [1, 2]

    stats = check_gold(tmp_path / "gold.jsonl", min_intents=10).stats()
    assert stats == {"intents": 10, "unanswerable": 1, "unanswerable_share": 0.1,
                     "non_empty_queries": {"ru": 10, "sk": 10, "en": 10},
                     "types": {"comparison": 1, "factual": 9}, "documents": 2,
                     "multi_document": 1, "multi_page": 8}


@pytest.mark.parametrize(("change", "field"), [
    (lambda r: r["queries"].pop("sk"), "queries.sk"),
    (lambda r: r["queries"].update(en="   "), "queries.en"),
    (lambda r: r["queries"].update(ru="How many participants?"), "queries.ru"),
    (lambda r: r["queries"].update(sk="Сколько?"), "queries.sk"),
    (lambda r: r["queries"].update(sk=r["queries"]["en"]), "queries.sk"),
    (lambda r: r["queries"].update(de="Wie viele?"), "queries.de"),
])
def test_every_intent_needs_three_distinct_languages(tmp_path, change, field):
    records = gold_set()
    change(records[4])
    assert problems(check(tmp_path, records)) == {(5, field)}


def test_duplicate_ids_name_both_lines(tmp_path):
    records = gold_set()
    records[6]["id"] = records[2]["id"]
    report = check(tmp_path, records)
    assert problems(report) == {(7, "id")}
    assert "line 3" in report.violations[0].message


@pytest.mark.parametrize(("record", "fields"), [
    (answerable(2, evidence=[]), {"evidence"}),
    (answerable(2, reference_answer=ABSTAIN), {"reference_answer"}),
    (answerable(2, unanswerable_reason="Not needed."), {"unanswerable_reason"}),
    (unanswerable(2, evidence=[{"doc_id": "alpha.pdf", "pages": [1]}]), {"evidence"}),
    (unanswerable(2, reference_answer="An answer."), {"reference_answer"}),
    (unanswerable(2, unanswerable_reason=None), {"unanswerable_reason"}),
    (answerable(2, type="comparison"), {"evidence"}),
    (answerable(2, evidence=[{"doc_id": "alpha.pdf", "pages": [1]}, {"doc_id": "alpha.pdf", "pages": [2]}]),
     {"evidence[1].doc_id"}),
])
def test_evidence_must_match_answerability(tmp_path, record, fields):
    records = gold_set()
    records[1] = record
    assert problems(check(tmp_path, records)) == {(2, f) for f in fields}


@pytest.mark.parametrize(("size", "unanswered", "ok"), [
    (10, 0, False), (10, 1, True), (10, 2, True), (10, 3, False), (20, 3, True), (20, 5, False),
])
def test_unanswerable_share_bounds_are_inclusive(tmp_path, size, unanswered, ok):
    report = check(tmp_path, gold_set(size, unanswered))
    assert report.ok is ok
    if not ok:
        assert problems(report) == {(None, "answerable")}


def test_share_and_minimum_are_parameters(tmp_path):
    records = gold_set(10, 3)
    assert check(tmp_path, records, unanswerable_share=(0.0, 0.5)).ok
    report = check(tmp_path, records, min_intents=50, unanswerable_share=(0.0, 0.5))
    assert problems(report) == {(None, "")}
    assert "10 valid intents; at least 50" in str(report.violations[0])


def test_default_minimum_is_fifty(tmp_path):
    path = write(tmp_path / "gold.jsonl", gold_set())
    assert {(v.line, v.field) for v in check_gold(path).violations} == {(None, "")}
    assert check_gold(write(tmp_path / "big.jsonl", gold_set(50, 5))).ok


def test_unknown_doc_id_and_malformed_doc_id(tmp_path, library):
    root, cache = library
    records = gold_set()
    records[3]["evidence"] = [{"doc_id": "gamma.pdf", "pages": [1]}]
    records[5]["evidence"] = [{"doc_id": "sub\\beta.pdf", "pages": [1]}]
    records[6]["evidence"] = [{"doc_id": "../alpha.pdf", "pages": [1]}]
    report = check(tmp_path, records, library=root)
    assert problems(report) == {(4, "evidence[0].doc_id"), (6, "evidence[0].doc_id"), (7, "evidence[0].doc_id")}
    # Without a library only the form is checked.
    assert problems(check(tmp_path, records)) == {(6, "evidence[0].doc_id"), (7, "evidence[0].doc_id")}


def test_pages_are_positive_ascending_and_within_the_parsed_document(tmp_path, library):
    root, cache = library
    records = gold_set()
    records[2]["evidence"] = [{"doc_id": "alpha.pdf", "pages": [3, 4]}]
    records[3]["evidence"] = [{"doc_id": "alpha.pdf", "pages": [0]}]
    records[4]["evidence"] = [{"doc_id": "alpha.pdf", "pages": [2, 1]}]
    records[5]["evidence"] = [{"doc_id": "alpha.pdf", "pages": []}]
    records[6]["evidence"] = [{"doc_id": "unparsed.pdf", "pages": [1]}]
    report = check(tmp_path, records, library=root, parse_cache=cache)
    assert problems(report) == {(3, "evidence[0].pages[1]"), (4, "evidence[0].pages[0]"),
                                (5, "evidence[0].pages"), (6, "evidence[0].pages"), (7, "evidence[0].pages")}
    messages = [str(v) for v in report.violations]
    assert "line 3: evidence[0].pages[1]: page 4 is beyond the document's 3 parsed pages" in messages
    assert "line 7: evidence[0].pages: no valid parse bundle for this document; pages unchecked" in messages
    # Without a cache page 4 is not checked against anything.
    assert (3, "evidence[0].pages[1]") not in problems(check(tmp_path, records, library=root))


def test_a_damaged_bundle_does_not_count(tmp_path, library):
    root, cache = library
    (next((cache / content_hash(root / "alpha.pdf")).iterdir()) / "content_list.json").write_text("[]")
    report = check(tmp_path, gold_set(), library=root, parse_cache=cache)
    assert len(report.violations) == 9  # every answerable intent cites alpha
    assert all("no valid parse bundle" in v.message for v in report.violations)


def test_parse_cache_requires_library(tmp_path, library):
    with pytest.raises(ValueError, match="requires library"):
        check(tmp_path, gold_set(), parse_cache=library[1])


def test_malformed_lines_are_numbered_and_do_not_stop_validation(tmp_path):
    records = gold_set(12)
    records[2] = '{"id": "q003", '
    records[4] = "   "
    records[6] = "[1, 2]"
    records[8] = json.dumps(answerable(9))[:-1] + ', "id": "again"}'
    records[10] = json.dumps(answerable(11)).replace('"answerable": true', '"answerable": NaN')
    report = check(tmp_path, records, unanswerable_share=(0.0, 1.0))
    assert problems(report) == {(3, ""), (5, ""), (7, ""), (9, ""), (11, "")}
    assert [i.id for i in report.intents] == [f"q{n:03d}" for n in (1, 2, 4, 6, 8, 10, 12)]
    assert "duplicate key 'id'" in str(report.violations[3])


def test_byte_order_mark_and_invalid_utf8_are_reported(tmp_path):
    path = tmp_path / "gold.jsonl"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(answerable(1)).encode() + b"\n\xff\n")
    report = check_gold(path, min_intents=1, unanswerable_share=(0.0, 1.0))
    assert problems(report) == {(1, ""), (2, "")}
    assert len(report.intents) == 1


def test_values_are_not_coerced_and_unknown_fields_are_errors(tmp_path):
    records = gold_set()
    records[1]["answerable"] = 1
    records[2]["evidence"][0]["pages"] = ["1"]
    records[3]["confidence"] = 0.9
    records[4]["type"] = "opinion"
    records[5]["id"] = "Q 6"
    records[7]["difficulty"] = "trivial"
    assert problems(check(tmp_path, records, unanswerable_share=(0.0, 1.0))) == {
        (2, "answerable"), (3, "evidence[0].pages[0]"), (4, "confidence"), (5, "type"), (6, "id"),
        (8, "difficulty")}


def test_messages_never_repeat_record_text(tmp_path, library):
    root, cache = library
    records = gold_set()
    records[1]["queries"]["ru"] = SECRET
    records[2]["type"] = SECRET
    records[3]["evidence"] = [{"doc_id": SECRET + ".pdf", "pages": [9]}]
    records[4] = '{"id": "' + SECRET + '"'
    report = check(tmp_path, records, library=root, parse_cache=cache)
    assert len(report.violations) == 4
    assert all(SECRET not in str(v) for v in report.violations)


def test_load_gold_raises_with_every_violation(tmp_path):
    records = gold_set()
    records[1]["queries"].pop("ru")
    records[3]["evidence"] = []
    with pytest.raises(GoldSetError) as caught:
        load_gold(write(tmp_path / "gold.jsonl", records), min_intents=1)
    assert {(v.line, v.field) for v in caught.value.violations} == {(2, "queries.ru"), (4, "evidence")}
    assert "line 2: queries.ru" in str(caught.value)


def test_command_line_exit_status(tmp_path, library, capsys):
    root, cache = library
    path = write(tmp_path / "gold.jsonl", gold_set())
    args = [str(path), "--library", str(root), "--parse-cache", str(cache), "--min-intents", "10"]
    assert main(args) == 0
    assert capsys.readouterr().out.rstrip().endswith("OK")
    assert main(args[:-1] + ["11"]) == 1
    assert "FAILED: 1 violation(s)" in capsys.readouterr().out
