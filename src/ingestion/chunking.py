import re
from typing import List, Dict, Any, Iterator, NamedTuple, Optional, Tuple

from src.config.config_chunking import (
    CHUNKER_V1_SIZE,
    CHUNKER_V1_OVERLAP,
    CHUNKER_V1_VERSION,
    CHUNKER_V2_SOFT_LIMIT,
    CHUNKER_V2_HARD_LIMIT,
    CHUNKER_V2_VERSION,
)

# (start, end) character offsets into the original document text.
Span = Tuple[int, int]

# A blank line (optionally containing spaces/tabs/CR) separates paragraphs.
_BLANK_LINE = re.compile(r"[ \t\r]*")
# Candidate sentence ends; "." additionally requires an uppercase letter next.
_SENTENCE_END = re.compile(r"[.!?]\s+")

# Markdown structure detection (common forms only, not full CommonMark/GFM).
_FENCE_OPEN = re.compile(r" {0,3}(`{3,}|~{3,})")
_LIST_ITEM = re.compile(r"( {0,3})(?:[-*+]|\d{1,9}[.)])(?:[ \t]|\r?$)")
_TABLE_SEPARATOR = re.compile(
    r"[ \t]*\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t\r]*"
)
_HEADING = re.compile(r" {0,3}#")

# Block kinds produced by structural segmentation.
PROSE = "prose"
CODE_BLOCK = "code_block"
LIST = "list"
TABLE = "table"


class _Block(NamedTuple):
    kind: str
    span: Span
    # Safe split points for structures: code lines, list items, table rows.
    # Empty for prose, which uses sentence splitting instead.
    parts: List[Span]
    # True when no blank line separates this block from the previous one
    # (e.g. a lead-in line directly above a list).
    joined: bool = False


class ChunkerV1:
    """
    V1 baseline chunking strategy.

    Algorithm : sliding-window character splitter
    Chunk size : 1000 characters
    Overlap    : 100 characters

    Do NOT modify these parameters to experiment.
    Create ChunkerV2 for any new strategy so results stay comparable.
    """

    chunk_size: int = CHUNKER_V1_SIZE
    overlap: int = CHUNKER_V1_OVERLAP
    version: str = CHUNKER_V1_VERSION

    def chunk_document(
        self,
        text: str,
        source: str = "unknown",
    ) -> List[Dict[str, Any]]:
        """
        Splits *text* into overlapping character slices.

        Returns a list of chunk dicts, each containing:
            text            – the raw chunk string
            metadata        – source, chunk_index, chunk_length, chunker_version
        """
        if not text:
            return []

        chunks: List[Dict[str, Any]] = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size
            slice_ = text[start:end]

            chunks.append({
                "text": slice_,
                "metadata": {
                    "source": source,
                    "chunk_index": index,
                    "chunk_length": len(slice_),
                    "chunker_version": self.version,
                },
            })

            start += max(1, self.chunk_size - self.overlap)
            index += 1

        return chunks


class ChunkerV2:
    """
    V2 boundary-aware chunking strategy.

    Implements the split-priority subset of chunking_v2.md:

        Structures – fenced code blocks, lists and tables are recognised
                  before paragraph splitting. One that fits within the hard
                  limit is never split; a larger one is split only at its own
                  boundaries (code lines, list items, table rows). The table
                  header/separator stay with the first row, and code fences
                  with their neighbouring line.
        Level 2 – paragraphs (blank lines). A paragraph that fits within the
                  hard limit is never split.
        Level 3 – sentences. Only used for paragraphs above the hard limit.
                  A boundary is "." + whitespace + uppercase letter, or
                  "!" / "?" + whitespace.
        Level 4 – hard cut. Only used for a single sentence, code line or
                  table row above the hard limit: cut at the last whitespace
                  within the limit, or exactly at the limit if there is none.
                  A single list item above the hard limit falls back to
                  Level 3 then Level 4.

    The resulting units are packed greedily into chunks up to the soft limit.
    A single unit between the soft and hard limits becomes its own chunk, so
    every chunk is <= hard_limit.

    Chunk text is a slice of the original document, so content (including
    internal whitespace) is preserved exactly; only the whitespace between
    chunks is dropped. No overlap is applied.

    Not yet implemented: headings (Level 1), overlap, and the extended V2
    metadata schema.
    """

    soft_limit: int = CHUNKER_V2_SOFT_LIMIT
    hard_limit: int = CHUNKER_V2_HARD_LIMIT
    version: str = CHUNKER_V2_VERSION

    def chunk_document(
        self,
        text: str,
        source: str = "unknown",
    ) -> List[Dict[str, Any]]:
        """
        Splits *text* into boundary-aligned chunks.

        Returns a list of chunk dicts with the same shape as ChunkerV1:
            text            – the raw chunk string
            metadata        – source, chunk_index, chunk_length, chunker_version
        """
        if not text or text.isspace():
            return []

        units: List[Span] = []
        for block in _segment(text):
            start, end = block.span
            if end - start <= self.hard_limit:
                block_units = [block.span]
            elif block.kind == PROSE:
                block_units = self._prose_units(text, start, end)
            else:
                block_units = self._structure_units(text, block)

            # Blocks with no blank line between them read as one paragraph
            # (e.g. "Steps:" directly above a list); keep them together when
            # they fit, as the paragraph splitter would have.
            if block.joined and units and block_units[0][1] - units[-1][0] <= self.hard_limit:
                units[-1] = (units[-1][0], block_units.pop(0)[1])
            units.extend(block_units)

        chunks: List[Dict[str, Any]] = []
        for index, (start, end) in enumerate(self._pack(units)):
            slice_ = text[start:end]
            chunks.append({
                "text": slice_,
                "metadata": {
                    "source": source,
                    "chunk_index": index,
                    "chunk_length": len(slice_),
                    "chunker_version": self.version,
                },
            })

        return chunks

    def _pack(self, units: List[Span]) -> Iterator[Span]:
        """Greedily merges consecutive units while the merged span fits the soft limit."""
        current: Optional[Span] = None
        for start, end in units:
            if current and end - current[0] <= self.soft_limit:
                current = (current[0], end)
            else:
                if current:
                    yield current
                current = (start, end)
        if current:
            yield current

    def _prose_units(self, text: str, start: int, end: int) -> List[Span]:
        """Levels 3–4: splits an over-long span at sentences, then hard cuts."""
        units: List[Span] = []
        for sentence in self._sentence_spans(text, start, end):
            if sentence[1] - sentence[0] <= self.hard_limit:
                units.append(sentence)
            else:
                units.extend(self._hard_split(text, *sentence))
        return units

    def _structure_units(self, text: str, block: _Block) -> List[Span]:
        """
        Splits an over-long structure at its own boundaries.

        The parts are pre-packed so each group starts fresh at the structure,
        rather than being merged piecemeal into whatever chunk precedes it.
        """
        parts = block.parts
        if block.kind == CODE_BLOCK:
            # Keep each fence with its neighbouring line, not stranded alone.
            parts = self._join_if_fits(parts, len(parts) - 2, len(parts))
            parts = self._join_if_fits(parts, 0, 2)
        elif block.kind == TABLE:
            # Header + separator stay with the first data row.
            parts = self._join_if_fits(parts, 0, 3)

        pieces: List[Span] = []
        for start, end in parts:
            if end - start <= self.hard_limit:
                pieces.append((start, end))
            elif block.kind == LIST:
                pieces.extend(self._prose_units(text, start, end))
            else:
                pieces.extend(self._hard_split(text, start, end))
        return list(self._pack(pieces))

    def _join_if_fits(self, parts: List[Span], start: int, stop: int) -> List[Span]:
        """Merges parts[start:stop] into one span if it fits the hard limit."""
        start = max(start, 0)
        group = parts[start:stop]
        if len(group) < 2 or group[-1][1] - group[0][0] > self.hard_limit:
            return parts
        return parts[:start] + [(group[0][0], group[-1][1])] + parts[stop:]

    @staticmethod
    def _sentence_spans(text: str, start: int, end: int) -> Iterator[Span]:
        pos = start
        for match in _SENTENCE_END.finditer(text, start, end):
            # Spans are stripped, so match.end() < end and indexing is safe.
            if text[match.start()] == "." and not text[match.end()].isupper():
                continue
            yield (pos, match.start() + 1)
            pos = match.end()
        yield (pos, end)

    def _hard_split(self, text: str, start: int, end: int) -> Iterator[Span]:
        """Level 4 fallback: cuts an over-long span into pieces of <= hard_limit."""
        while end - start > self.hard_limit:
            limit = start + self.hard_limit
            cut = next(
                (i for i in range(limit, start, -1) if text[i].isspace()),
                limit,
            )
            span = _strip_span(text, start, cut)
            if span:
                yield span
            start = cut
            while text[start].isspace():
                start += 1
        yield (start, end)


def _strip_span(text: str, start: int, end: int) -> Optional[Span]:
    """Narrows (start, end) to exclude surrounding whitespace; None if empty."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return (start, end) if start < end else None


# ── Structural segmentation (ChunkerV2) ─────────────────────

def _segment(text: str) -> List[_Block]:
    """
    Splits *text* into prose paragraphs and Markdown structures.

    Lines are scanned top to bottom. A fenced code block, table or list may
    start on any non-blank line (interrupting a paragraph); everything else
    is prose, grouped into paragraphs by blank lines exactly as before.
    """
    lines = _line_spans(text)
    blocks: List[_Block] = []
    paragraph: List[int] = []

    def add(block: _Block, first_line: int) -> None:
        joined = bool(blocks) and first_line > 0 and not _is_blank(text, lines[first_line - 1])
        blocks.append(block._replace(joined=joined))

    def flush_paragraph() -> None:
        if paragraph:
            span = _strip_span(text, lines[paragraph[0]][0], lines[paragraph[-1]][1])
            if span:
                add(_Block(PROSE, span, []), paragraph[0])
            paragraph.clear()

    i = 0
    while i < len(lines):
        if _is_blank(text, lines[i]):
            flush_paragraph()
            i += 1
            continue
        for scan in (_scan_code_block, _scan_table, _scan_list):
            found = scan(text, lines, i)
            if found:
                flush_paragraph()
                block, next_line = found
                add(block, i)
                i = next_line
                break
        else:
            paragraph.append(i)
            i += 1
    flush_paragraph()
    return blocks


def _scan_code_block(text: str, lines: List[Span], i: int) -> Optional[Tuple[_Block, int]]:
    """
    A ``` or ~~~ fence up to the matching closing fence (same character, at
    least as long). Contents are opaque: nothing inside is interpreted. An
    unclosed fence runs to the end of the document.
    """
    line = _line(text, lines[i])
    match = _FENCE_OPEN.match(line)
    if not match:
        return None
    fence = match.group(1)
    if fence[0] == "`" and "`" in line[match.end():]:
        return None  # inline code such as ```x```, not a fence
    closing = re.compile(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}[ \t\r]*")

    last = i + 1
    while last < len(lines) and not closing.fullmatch(_line(text, lines[last])):
        last += 1
    last = min(last, len(lines) - 1)
    return _structure_block(text, lines, CODE_BLOCK, i, last, range(i, last + 1)), last + 1


def _scan_table(text: str, lines: List[Span], i: int) -> Optional[Tuple[_Block, int]]:
    """A header row containing "|", a separator row, then non-blank rows containing "|"."""
    if "|" not in _line(text, lines[i]) or i + 1 >= len(lines):
        return None
    separator = _line(text, lines[i + 1])
    if "|" not in separator or not _TABLE_SEPARATOR.fullmatch(separator):
        return None

    last = i + 1
    while (
        last + 1 < len(lines)
        and not _is_blank(text, lines[last + 1])
        and "|" in _line(text, lines[last + 1])
    ):
        last += 1
    return _structure_block(text, lines, TABLE, i, last, range(i, last + 1)), last + 1


def _scan_list(text: str, lines: List[Span], i: int) -> Optional[Tuple[_Block, int]]:
    """
    A run of list items. A line belongs to the list if it is:
      - another item marker at the same or lower indent (a new item);
      - indented (continuation text or a nested list, even after blank lines);
      - unindented text directly after a list line (lazy continuation),
        unless it starts a heading or code fence.
    Items are split points only at the top level; nested content stays with
    its parent item.
    """
    match = _LIST_ITEM.match(_line(text, lines[i]))
    if not match:
        return None
    base_indent = len(match.group(1))

    item_starts = [i]
    last = i
    j = i + 1
    while j < len(lines):
        if _is_blank(text, lines[j]):
            j += 1
            continue
        line = _line(text, lines[j])
        item = _LIST_ITEM.match(line)
        if item and len(item.group(1)) <= base_indent:
            item_starts.append(j)
        elif line[0] in " \t":
            pass
        elif last == j - 1 and not (_HEADING.match(line) or _FENCE_OPEN.match(line)):
            pass
        else:
            break
        last = j
        j += 1

    item_ends = [start - 1 for start in item_starts[1:]] + [last]
    items = [
        _lines_span(text, lines, start, end)
        for start, end in zip(item_starts, item_ends)
    ]
    block = _Block(LIST, _lines_span(text, lines, i, last), items)
    return block, last + 1


def _structure_block(
    text: str, lines: List[Span], kind: str, first: int, last: int, part_lines: range,
) -> _Block:
    """A block whose split points are its individual non-blank lines."""
    parts = [
        _lines_span(text, lines, n, n)
        for n in part_lines
        if not _is_blank(text, lines[n])
    ]
    return _Block(kind, _lines_span(text, lines, first, last), parts)


def _line_spans(text: str) -> List[Span]:
    """(start, end) of every line, excluding the "\\n" (a trailing "\\r" is kept)."""
    spans: List[Span] = []
    pos = 0
    for match in re.finditer("\n", text):
        spans.append((pos, match.start()))
        pos = match.end()
    spans.append((pos, len(text)))
    return spans


def _lines_span(text: str, lines: List[Span], first: int, last: int) -> Span:
    """
    Lines first..last, keeping the first line's indentation but dropping
    trailing whitespace (blank lines, "\\r"). The first line must be non-blank.
    """
    start = lines[first][0]
    end = lines[last][1]
    while end > start and text[end - 1].isspace():
        end -= 1
    return (start, end)


def _line(text: str, span: Span) -> str:
    return text[span[0]:span[1]]


def _is_blank(text: str, span: Span) -> bool:
    return _BLANK_LINE.fullmatch(text, span[0], span[1]) is not None