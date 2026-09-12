import re
from typing import Optional, Dict, Any, List

# Bengali <-> English translation tables
BENGALI_TO_ENGLISH = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
ENGLISH_TO_BENGALI = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

TERMINATORS = ("।", ".", "!", "?", ":", ";", "—", '"', "'", "”", "’")


def convert_digits_to_english(text: str) -> str:
    """
    Converts all Bengali numeral characters (০-৯) to standard Arabic numerals (0-9).
    100% deterministic, zero LLM calls, zero latency.
    """
    if not text:
        return ""
    return text.translate(BENGALI_TO_ENGLISH)


def convert_digits_to_bengali(text: str) -> str:
    """
    Converts all standard Arabic numerals (0-9) to Bengali numeral characters (০-৯).
    100% deterministic, zero LLM calls, zero latency.
    """
    if not text:
        return ""
    return text.translate(ENGLISH_TO_BENGALI)


def unwrap_broken_lines(text: str) -> str:
    """
    Unwraps artificial line breaks introduced by narrow columns, newspaper margins,
    or scanner edge clipping, joining sentences while preserving headings, lists,
    table structures, and blank paragraph breaks.
    """
    if not text:
        return ""

    lines = text.splitlines()
    out: List[str] = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            out.append("")
            i += 1
            continue

        stripped = line.strip()
        is_special = (
            stripped.startswith(("#", "|", ">", "```", "---", "===", "***"))
            or bool(re.match(r"^[-*+•]\s+", stripped))
            or bool(re.match(r"^\d+[\.\)]\s+", stripped))
        )

        if is_special:
            out.append(line)
            i += 1
            continue

        # Lookahead for normal prose continuation
        while i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if not next_line:
                break

            is_next_special = (
                next_line.startswith(("#", "|", ">", "```", "---", "===", "***"))
                or bool(re.match(r"^[-*+•]\s+", next_line))
                or bool(re.match(r"^\d+[\.\)]\s+", next_line))
            )
            if is_next_special:
                break

            # If current line ends with a sentence terminator, do not join
            if line.rstrip().endswith(TERMINATORS):
                break

            # Join continuation line with a single space
            line = line + " " + next_line
            i += 1

        out.append(line)
        i += 1

    return "\n".join(out)


def clean_whitespace_and_margins(text: str) -> str:
    """
    Normalizes excessive whitespace, trims trailing margin spaces,
    and collapses 3+ redundant blank lines down to clean paragraph breaks.
    """
    if not text:
        return ""

    lines = [l.rstrip() for l in text.splitlines()]
    joined = "\n".join(lines)
    # Collapse 3 or more blank lines down to 2
    joined = re.sub(r"\n{3,}", "\n\n", joined)

    out_lines: List[str] = []
    for line in joined.splitlines():
        # Preserve table pipes spacing
        if line.strip().startswith("|") and line.strip().endswith("|"):
            out_lines.append(line)
        else:
            # Collapse multiple inline spaces/tabs to a single space
            out_lines.append(re.sub(r"[ \t]{2,}", " ", line))

    return "\n".join(out_lines).strip()


def clean_table_formatting(text: str) -> str:
    """
    Detects markdown tables and aligns all vertical pipes (|) into a clean,
    well-spaced ASCII grid with uniform column widths.
    """
    if not text:
        return ""

    lines = text.splitlines()
    out: List[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and line.strip().endswith("|"):
            # Gather consecutive table lines
            table_lines: List[str] = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            rows: List[List[str]] = []
            max_cols = 0
            for tl in table_lines:
                raw_cells = tl.strip("|").split("|")
                cells = [c.strip() for c in raw_cells]
                max_cols = max(max_cols, len(cells))
                rows.append(cells)

            # Pad rows to have uniform column counts
            for r in rows:
                while len(r) < max_cols:
                    r.append("")

            # Calculate required column widths
            col_widths = [0] * max_cols
            for r in rows:
                for c_idx, cell in enumerate(r):
                    if set(cell).issubset({"-", ":", " "}) and cell:
                        continue
                    col_widths[c_idx] = max(col_widths[c_idx], len(cell))
            col_widths = [max(w, 3) for w in col_widths]

            # Reconstruct table with aligned pipes
            for r in rows:
                is_sep = any(set(c).issubset({"-", ":", " "}) and len(c) > 0 for c in r)
                formatted_cells: List[str] = []
                for c_idx, cell in enumerate(r):
                    w = col_widths[c_idx]
                    if is_sep:
                        formatted_cells.append("-" * (w + 2))
                    else:
                        formatted_cells.append(f" {cell.ljust(w)} ")
                out.append("|" + "|".join(formatted_cells) + "|")
        else:
            out.append(line)
            i += 1

    return "\n".join(out)


def _parse_numeric(val: str) -> Optional[float]:
    """Extracts first numeric value from a cell, supporting Bengali & comma separators."""
    cleaned = val.translate(BENGALI_TO_ENGLISH).replace(",", "").strip()
    m = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    return float(m.group(0)) if m else None


def check_invoice_math(text: str) -> Optional[Dict[str, Any]]:
    """
    Deterministically parses tables in text to locate line items, subtotal, tax/VAT, and totals.
    Calculates arithmetic sum and verifies whether items match the stated total.
    100% local, zero tokens, zero latency.

    Returns:
        dict with keys:
            'matched': bool
            'total': float
            'calculated': float
            'difference': float
            'currency_hint': str
        or None if no table or total line was found.
    """
    if not text:
        return None

    lines = [l.strip() for l in text.splitlines() if l.strip().startswith("|") and l.strip().endswith("|")]
    if not lines or len(lines) < 3:
        return None

    total_val: Optional[float] = None
    subtotal_val: Optional[float] = None
    tax_val: float = 0.0
    discount_val: float = 0.0
    item_vals: List[float] = []

    TOTAL_KEYWORDS = ["grand total", "net payable", "net total", "total amount", "total", "সর্বমোট", "মোট টাকা", "মোট"]
    SUBTOTAL_KEYWORDS = ["subtotal", "sub total", "উপমোট", "মোট মূল্য"]
    TAX_KEYWORDS = ["vat", "tax", "gst", "ভ্যাট", "কর", "ট্যাক্স"]
    DISCOUNT_KEYWORDS = ["discount", "ছাড়", "কমিশন"]

    for l in lines:
        cells = [c.strip() for c in l.strip("|").split("|")]
        # Skip separator rows
        if all(set(c).issubset({"-", ":", " "}) for c in cells if c):
            continue

        row_str = " ".join(cells).lower().translate(BENGALI_TO_ENGLISH)

        # 1. Total row
        if any(k in row_str for k in TOTAL_KEYWORDS):
            for c in reversed(cells):
                n = _parse_numeric(c)
                if n is not None:
                    total_val = n
                    break
        # 2. Subtotal row
        elif any(k in row_str for k in SUBTOTAL_KEYWORDS):
            for c in reversed(cells):
                n = _parse_numeric(c)
                if n is not None:
                    subtotal_val = n
                    break
        # 3. Tax row
        elif any(k in row_str for k in TAX_KEYWORDS):
            for c in reversed(cells):
                n = _parse_numeric(c)
                if n is not None:
                    tax_val = n
                    break
        # 4. Discount row
        elif any(k in row_str for k in DISCOUNT_KEYWORDS):
            for c in reversed(cells):
                n = _parse_numeric(c)
                if n is not None:
                    discount_val = n
                    break
        # 5. Regular line item row
        else:
            nums = [_parse_numeric(c) for c in cells if _parse_numeric(c) is not None]
            if nums:
                # Typically the line total is the last number in an item row
                item_vals.append(nums[-1])

    if total_val is not None:
        items_sum = sum(item_vals)
        if subtotal_val is not None:
            expected = subtotal_val + tax_val - discount_val
        else:
            expected = items_sum + tax_val - discount_val

        diff = round(abs(expected - total_val), 2)
        matched = diff < 0.05 or round(abs(items_sum - total_val), 2) < 0.05

        return {
            "matched": matched,
            "total": total_val,
            "calculated": expected,
            "difference": diff,
            "items_count": len(item_vals),
        }

    return None
