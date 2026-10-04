import pytest

from src.config.config_chunking import (
    CHUNKER_V2_SOFT_LIMIT,
    CHUNKER_V2_HARD_LIMIT,
)
from src.ingestion.chunking import (
    ChunkerV1,
    ChunkerV2,
    _segment,
    CODE_BLOCK,
    LIST,
    PROSE,
    TABLE,
)


def make_chunker(soft: int, hard: int) -> ChunkerV2:
    """Small limits keep test inputs readable; production uses the config values."""
    chunker = ChunkerV2()
    chunker.soft_limit = soft
    chunker.hard_limit = hard
    return chunker


def texts(chunks):
    return [chunk["text"] for chunk in chunks]


def non_whitespace(text: str) -> str:
    return "".join(text.split())


# ── Contract ────────────────────────────────────────────────

def test_defaults_come_from_config():
    chunker = ChunkerV2()
    assert chunker.soft_limit == CHUNKER_V2_SOFT_LIMIT
    assert chunker.hard_limit == CHUNKER_V2_HARD_LIMIT
    assert chunker.version == "v2"


@pytest.mark.parametrize("text", ["", "   ", "\n\n\t\n"])
def test_empty_or_whitespace_text_returns_no_chunks(text):
    assert ChunkerV2().chunk_document(text) == []


def test_output_shape_matches_v1():
    text = "First paragraph.\n\nSecond paragraph."
    v1_chunk = ChunkerV1().chunk_document(text, source="doc.md")[0]
    chunks = make_chunker(soft=20, hard=40).chunk_document(text, source="doc.md")

    for index, chunk in enumerate(chunks):
        assert chunk.keys() == v1_chunk.keys()
        assert chunk["metadata"].keys() == v1_chunk["metadata"].keys()
        assert chunk["metadata"] == {
            "source": "doc.md",
            "chunk_index": index,
            "chunk_length": len(chunk["text"]),
            "chunker_version": "v2",
        }


def test_short_text_is_single_stripped_chunk():
    chunks = ChunkerV2().chunk_document("\n  Just one sentence.  \n")
    assert texts(chunks) == ["Just one sentence."]


# ── Level 2: paragraphs ─────────────────────────────────────

def test_paragraphs_are_packed_up_to_soft_limit():
    a, b, c = "A" * 10, "B" * 10, "C" * 10
    text = f"{a}\n\n{b}\n\n{c}"
    # a + "\n\n" + b = 22 chars fits; adding c would be 34.
    chunks = make_chunker(soft=25, hard=50).chunk_document(text)
    assert texts(chunks) == [f"{a}\n\n{b}", c]


def test_paragraph_between_soft_and_hard_limit_is_kept_whole():
    paragraph = "One sentence here. Another sentence here. A third one here."
    chunks = make_chunker(soft=20, hard=100).chunk_document(paragraph)
    assert texts(chunks) == [paragraph]


def test_chunks_never_end_mid_paragraph_when_paragraphs_fit():
    paragraphs = [f"Paragraph {i} has some words in it." for i in range(10)]
    text = "\n\n".join(paragraphs)
    chunks = make_chunker(soft=80, hard=120).chunk_document(text)
    for chunk in chunks:
        for part in chunk["text"].split("\n\n"):
            assert part in paragraphs


def test_extra_blank_lines_and_crlf_are_paragraph_breaks():
    text = "First.\r\n\r\nSecond.\n \n\n\nThird."
    chunks = make_chunker(soft=5, hard=10).chunk_document(text)
    assert texts(chunks) == ["First.", "Second.", "Third."]


def test_internal_whitespace_is_preserved():
    text = "line one\n    indented line\nline three"
    assert texts(ChunkerV2().chunk_document(text)) == [text]


# ── Level 3: sentences ──────────────────────────────────────

def test_oversized_paragraph_splits_at_sentence_boundaries():
    sentences = [f"Sentence number {i} is here." for i in range(6)]
    paragraph = " ".join(sentences)
    chunks = make_chunker(soft=60, hard=80).chunk_document(paragraph)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk["text"]) <= 60
        assert chunk["text"].endswith(".")
        assert chunk["text"].startswith("Sentence")


@pytest.mark.parametrize("terminator", ["!", "?"])
def test_exclamation_and_question_marks_are_boundaries(terminator):
    paragraph = f"aaaa bbbb{terminator} cccc dddd{terminator} eeee ffff"
    chunks = make_chunker(soft=12, hard=20).chunk_document(paragraph)
    assert texts(chunks) == [
        f"aaaa bbbb{terminator}",
        f"cccc dddd{terminator}",
        "eeee ffff",
    ]


def test_period_before_lowercase_is_not_a_boundary():
    # "e.g. the" must not split; ". Then" must.
    paragraph = "Use a tool e.g. the hammer. Then hit it."
    chunks = make_chunker(soft=10, hard=30).chunk_document(paragraph)
    assert texts(chunks) == ["Use a tool e.g. the hammer.", "Then hit it."]


# ── Level 4: hard-limit fallback ────────────────────────────

def test_oversized_sentence_is_cut_at_whitespace_within_hard_limit():
    words = ["word"] * 30  # one 149-char sentence, no terminators
    sentence = " ".join(words)
    chunks = make_chunker(soft=20, hard=32).chunk_document(sentence)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk["text"]) <= 32
        assert set(chunk["text"].split()) == {"word"}  # no word was cut
    assert non_whitespace("".join(texts(chunks))) == non_whitespace(sentence)


def test_oversized_text_without_whitespace_is_cut_exactly_at_hard_limit():
    blob = "x" * 25
    chunks = make_chunker(soft=5, hard=10).chunk_document(blob)
    assert texts(chunks) == ["x" * 10, "x" * 10, "x" * 5]


# ── Invariants ──────────────────────────────────────────────

MIXED_DOCUMENT = "\n\n".join([
    "# Title",
    "Short intro paragraph.",
    " ".join(f"Long paragraph sentence {i} goes on." for i in range(40)),
    "z" * 300,
    "Middle paragraph? Yes! It has mixed punctuation. Done.",
    " ".join(["unterminated"] * 60),
    "Final words.",
])


@pytest.mark.parametrize("soft, hard", [(50, 80), (100, 200), (200, 250)])
def test_no_chunk_exceeds_hard_limit(soft, hard):
    chunks = make_chunker(soft, hard).chunk_document(MIXED_DOCUMENT)
    assert all(len(chunk["text"]) <= hard for chunk in chunks)


@pytest.mark.parametrize("soft, hard", [(50, 80), (100, 200), (200, 250)])
def test_content_is_preserved_without_overlap(soft, hard):
    chunks = make_chunker(soft, hard).chunk_document(MIXED_DOCUMENT)
    joined = "".join(texts(chunks))
    assert non_whitespace(joined) == non_whitespace(MIXED_DOCUMENT)


def test_plain_prose_with_production_limits():
    text = "\n\n".join(
        " ".join(f"Paragraph {p} sentence {s} is plain prose." for s in range(8))
        for p in range(20)
    )
    chunks = ChunkerV2().chunk_document(text, source="notes.md")

    assert len(chunks) > 1
    assert all(len(c["text"]) <= CHUNKER_V2_HARD_LIMIT for c in chunks)
    assert [c["metadata"]["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert non_whitespace("".join(texts(chunks))) == non_whitespace(text)


# ══ Markdown structures (Task 22) ═══════════════════════════


def kinds(text):
    return [block.kind for block in _segment(text)]


def part_texts(text):
    """Text of each structural split point (code line / list item / table row)."""
    (block,) = _segment(text)
    return [text[start:end] for start, end in block.parts]


def assert_valid(chunks, source_text, hard):
    """Shared invariants: hard limit respected, nothing lost or duplicated."""
    assert all(len(c["text"]) <= hard for c in chunks)
    assert non_whitespace("".join(texts(chunks))) == non_whitespace(source_text)


def code_block_of_length(length):
    return "```\n" + "a" * (length - 8) + "\n```"


# ── Code blocks ─────────────────────────────────────────────

CODE = '```python\ndef hello():\n    print("Hello")\n\n    return 42\n```'


def test_code_block_recognised_with_surrounding_prose_kept_separate():
    # No blank lines: prose must not be swallowed into the fence, or vice versa.
    text = f"Intro text.\n{CODE}\nOutro text."
    assert kinds(text) == [PROSE, CODE_BLOCK, PROSE]
    # hard = len(CODE) leaves no room to glue the adjacent prose on.
    chunks = make_chunker(soft=10, hard=len(CODE)).chunk_document(text)
    assert texts(chunks) == ["Intro text.", CODE, "Outro text."]


def test_code_block_that_fits_is_intact_with_whitespace_preserved():
    # Includes a blank line and indentation inside the fence.
    chunks = make_chunker(soft=10, hard=200).chunk_document(CODE)
    assert texts(chunks) == [CODE]


def test_code_block_is_not_sentence_split():
    # Same content as prose would be sentence-split, since it exceeds hard=40.
    code = "```\n# First step. Then the second! Why? Because.\nx = 1. \nY = 2\n```"
    assert len(make_chunker(soft=20, hard=40).chunk_document(code.strip("`\n"))) > 1
    chunks = make_chunker(soft=20, hard=100).chunk_document(code)
    assert texts(chunks) == [code]


def test_tilde_fences_and_longer_fences_are_supported():
    text = "~~~\nx = 1\n~~~"
    assert kinds(text) == [CODE_BLOCK]
    # A ``` line inside a ```` block is content, not a closing fence.
    nested = "````markdown\n```python\nx = 1\n```\n\n# Not a heading\n````"
    assert kinds(nested) == [CODE_BLOCK]
    assert texts(ChunkerV2().chunk_document(nested)) == [nested]


def test_markdown_inside_code_is_not_interpreted():
    code = "```\n- not a list\n| not | a table |\n|---|---|\n```"
    assert kinds(code) == [CODE_BLOCK]


def test_unclosed_fence_runs_to_end_of_document():
    text = "Intro.\n\n```\ncode line\n\nmore code"
    assert kinds(text) == [PROSE, CODE_BLOCK]


def test_inline_triple_backticks_are_not_a_fence():
    assert kinds("```inline``` code in prose") == [PROSE]


def test_multiple_code_blocks_are_independent():
    text = "```\na = 1\n```\nBetween them.\n```\nb = 2\n```"
    assert kinds(text) == [CODE_BLOCK, PROSE, CODE_BLOCK]
    chunks = make_chunker(soft=5, hard=15).chunk_document(text)
    assert texts(chunks) == ["```\na = 1\n```", "Between them.", "```\nb = 2\n```"]


def test_oversized_code_block_splits_at_line_boundaries():
    lines = [f"    value_{i:02d} = compute({i})  # step. Next" for i in range(30)]
    code = "```python\n" + "\n".join(lines) + "\n```"
    chunks = make_chunker(soft=150, hard=200).chunk_document(code)

    assert len(chunks) > 1
    assert_valid(chunks, code, hard=200)
    original_lines = set(code.split("\n"))
    for chunk in chunks:
        # Every line is a complete original line, indentation included.
        assert set(chunk["text"].split("\n")) <= original_lines
    # Fences are not stranded on their own.
    assert chunks[0]["text"].startswith("```python\n    value_00")
    assert chunks[-1]["text"].endswith("value_29 = compute(29)  # step. Next\n```")


def test_code_block_exactly_at_hard_limit_is_kept_whole():
    code = code_block_of_length(100)
    assert texts(make_chunker(soft=50, hard=100).chunk_document(code)) == [code]


def test_code_block_just_above_hard_limit_is_split_within_limit():
    code = "```\n" + "\n".join(["a" * 20] * 4) + "\n```"  # 91 chars
    chunks = make_chunker(soft=50, hard=90).chunk_document(code)
    assert len(chunks) == 2
    assert_valid(chunks, code, hard=90)


def test_code_line_longer_than_hard_limit_falls_back_to_hard_cut():
    code = "```\nshort\n" + "x" * 250 + "\nshort\n```"
    chunks = make_chunker(soft=50, hard=100).chunk_document(code)
    assert_valid(chunks, code, hard=100)


# ── Lists ───────────────────────────────────────────────────

def test_unordered_list_is_recognised():
    text = "- First item\n* Second item\n+ Third item"
    assert kinds(text) == [LIST]
    assert part_texts(text) == ["- First item", "* Second item", "+ Third item"]


def test_ordered_list_is_recognised():
    text = "1. First\n2. Second\n10) Tenth"
    assert kinds(text) == [LIST]
    assert part_texts(text) == ["1. First", "2. Second", "10) Tenth"]


def test_list_interrupting_prose_and_followed_by_prose():
    text = "Steps:\n1. One\n2. Two\n\nAfterwards, prose."
    assert kinds(text) == [PROSE, LIST, PROSE]


def test_list_item_with_multiple_sentences_is_not_sentence_split():
    text = "- First. Second sentence! Third?\n- Another. Item here."
    chunks = make_chunker(soft=20, hard=200).chunk_document(text)
    assert texts(chunks) == [text]


def test_list_with_blank_lines_between_items_stays_together():
    text = "- One\n\n- Two\n\n- Three"
    assert kinds(text) == [LIST]
    assert texts(make_chunker(soft=10, hard=100).chunk_document(text)) == [text]


def test_indented_continuation_stays_with_its_item():
    text = "- First item\n\n  Additional information.\n- Second item"
    assert part_texts(text) == [
        "- First item\n\n  Additional information.",
        "- Second item",
    ]


def test_lazy_continuation_line_stays_with_its_item():
    text = "- First item that wraps\nonto the next line\n- Second"
    assert part_texts(text) == ["- First item that wraps\nonto the next line", "- Second"]


def test_nested_list_stays_with_parent_item():
    text = "- Parent\n  - Child one\n  - Child two\n- Next parent"
    assert part_texts(text) == [
        "- Parent\n  - Child one\n  - Child two",
        "- Next parent",
    ]


def test_heading_after_list_ends_the_list():
    assert kinds("- item\n# Heading") == [LIST, PROSE]


def test_oversized_list_splits_between_items():
    items = [f"- Item {i}: some text. More text here." for i in range(10)]
    text = "\n".join(items)
    chunks = make_chunker(soft=100, hard=150).chunk_document(text)

    assert len(chunks) > 1
    assert_valid(chunks, text, hard=150)
    for chunk in chunks:
        assert all(line in items for line in chunk["text"].split("\n"))


def test_oversized_list_keeps_nested_children_with_parent():
    items = [f"- Parent {i}\n  - child a\n  - child b" for i in range(6)]
    text = "\n".join(items)
    chunks = make_chunker(soft=60, hard=80).chunk_document(text)
    assert_valid(chunks, text, hard=80)
    for chunk in chunks:
        assert chunk["text"].startswith("- Parent")
        assert chunk["text"].endswith("- child b")


def test_oversized_single_list_item_falls_back_to_sentences():
    long_item = "- " + " ".join(f"Sentence {i} of the item." for i in range(10))
    text = f"{long_item}\n- Short item."
    chunks = make_chunker(soft=60, hard=100).chunk_document(text)

    assert_valid(chunks, text, hard=100)
    assert chunks[0]["text"].startswith("- Sentence 0")
    assert all(c["text"].endswith(".") for c in chunks)
    assert chunks[-1]["text"].endswith("- Short item.")


# ── Tables ──────────────────────────────────────────────────

TABLE_TEXT = "| Name | Age |\n|------|-----|\n| John | 30 |\n| Jane | 28 |"


def test_table_is_recognised():
    assert kinds(TABLE_TEXT) == [TABLE]
    assert part_texts(TABLE_TEXT) == TABLE_TEXT.split("\n")


def test_table_without_outer_pipes_and_with_alignment():
    text = "Name | Age\n:--- | ---:\nJohn | 30"
    assert kinds(text) == [TABLE]


def test_pipes_without_separator_row_are_prose():
    assert kinds("a | b\nc | d") == [PROSE]


def test_table_that_fits_is_intact():
    text = f"Before.\n{TABLE_TEXT}\nAfter."
    assert kinds(text) == [PROSE, TABLE, PROSE]
    chunks = make_chunker(soft=10, hard=len(TABLE_TEXT)).chunk_document(text)
    assert texts(chunks) == ["Before.", TABLE_TEXT, "After."]


def test_table_cells_are_not_sentence_split():
    text = "| Q | A |\n|---|---|\n| Does it work? Yes. | Fine! Good. |"
    chunks = make_chunker(soft=20, hard=200).chunk_document(text)
    assert texts(chunks) == [text]


def test_oversized_table_splits_between_rows_with_header_kept():
    header = "| Name | Description |\n|------|-------------|"
    rows = [f"| row{i:02d} | Some value. Another! |" for i in range(12)]
    text = header + "\n" + "\n".join(rows)
    chunks = make_chunker(soft=120, hard=160).chunk_document(text)

    assert len(chunks) > 1
    assert_valid(chunks, text, hard=160)
    # Header and separator stay together, with at least the first data row.
    assert chunks[0]["text"].startswith(header + "\n" + rows[0])
    # No row is split internally.
    for chunk in chunks[1:]:
        assert all(line in rows for line in chunk["text"].split("\n"))


def test_table_row_longer_than_hard_limit_falls_back_to_hard_cut():
    text = "| a | b |\n|---|---|\n| " + "word " * 40 + "| x |\n| c | d |"
    chunks = make_chunker(soft=50, hard=80).chunk_document(text)
    assert_valid(chunks, text, hard=80)


# ── Adjacency, CRLF, mixed documents ────────────────────────

def test_adjacent_structures_without_blank_lines():
    text = f"{CODE}\n{TABLE_TEXT}\n- a\n- b"
    assert kinds(text) == [CODE_BLOCK, TABLE, LIST]


def test_crlf_structures():
    text = "Intro.\r\n\r\n```\r\nx = 1\r\n```\r\n- a\r\n- b\r\n\r\n| h |\r\n|---|\r\n| v |\r\n"
    assert kinds(text) == [PROSE, CODE_BLOCK, LIST, TABLE]
    chunks = make_chunker(soft=5, hard=19).chunk_document(text)
    assert texts(chunks) == ["Intro.", "```\r\nx = 1\r\n```", "- a\r\n- b", "| h |\r\n|---|\r\n| v |"]


# ── Blocks with no blank line between them ──────────────────

def test_lead_in_line_stays_with_following_list():
    # Same result as the foundation, which saw this as one paragraph.
    text = "Earlier paragraph.\n\nIdentified blockers:\n- one\n- two"
    chunks = make_chunker(soft=20, hard=100).chunk_document(text)
    assert texts(chunks) == ["Earlier paragraph.", "Identified blockers:\n- one\n- two"]


def test_prose_directly_after_code_stays_with_it_when_it_fits():
    text = f"Example:\n{CODE}\nThat prints Hello."
    assert kinds(text) == [PROSE, CODE_BLOCK, PROSE]
    assert texts(make_chunker(soft=10, hard=200).chunk_document(text)) == [text]


def test_lead_in_attaches_to_first_group_of_oversized_list():
    items = [f"- Item {i}: some text. More text here." for i in range(10)]
    text = "Steps:\n" + "\n".join(items)
    chunks = make_chunker(soft=100, hard=150).chunk_document(text)
    assert_valid(chunks, text, hard=150)
    assert chunks[0]["text"].startswith("Steps:\n- Item 0")


MIXED_MARKDOWN = """# Introduction

Normal prose. It has two sentences.

```python
def example():
    return 42
```

Some additional prose.

- First item
- Second item

| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |

Final prose."""


def test_mixed_document_segmentation():
    assert kinds(MIXED_MARKDOWN) == [PROSE, PROSE, CODE_BLOCK, PROSE, LIST, TABLE, PROSE]


def test_mixed_document_fits_in_one_chunk_with_production_limits():
    assert texts(ChunkerV2().chunk_document(MIXED_MARKDOWN)) == [MIXED_MARKDOWN]


def test_mixed_document_with_small_limits_keeps_structures_intact():
    chunks = make_chunker(soft=40, hard=120).chunk_document(MIXED_MARKDOWN)
    assert_valid(chunks, MIXED_MARKDOWN, hard=120)
    assert texts(chunks) == [
        "# Introduction",
        "Normal prose. It has two sentences.",
        "```python\ndef example():\n    return 42\n```",
        "Some additional prose.",
        "- First item\n- Second item",
        "| Name | Value |\n|------|-------|\n| A    | 1     |\n| B    | 2     |",
        "Final prose.",
    ]


LARGE_MARKDOWN = "\n\n".join([
    MIXED_MARKDOWN,
    "```\n" + "\n".join(f"line_{i} = {i}" for i in range(80)) + "\n```",
    "\n".join(f"{i}. Step {i}. Do the thing! Check it?" for i in range(1, 40)),
    "| k | v |\n|---|---|\n" + "\n".join(f"| key{i} | val{i} |" for i in range(60)),
    " ".join(f"Prose sentence {i} here." for i in range(80)),
])


@pytest.mark.parametrize("soft, hard", [(60, 100), (200, 300), (1200, 2000)])
def test_large_markdown_document_invariants(soft, hard):
    chunks = make_chunker(soft, hard).chunk_document(LARGE_MARKDOWN)
    assert_valid(chunks, LARGE_MARKDOWN, hard=hard)
