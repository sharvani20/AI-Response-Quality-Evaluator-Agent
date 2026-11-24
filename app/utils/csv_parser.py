import csv
import io
from typing import List, Tuple


def parse_csv(content: str) -> Tuple[List[dict], List[str]]:
    """Parse CSV content and validate required columns.

    Args:
        content: Raw CSV string content.

    Returns:
        Tuple of (list of row dicts, list of error messages).
    """
    errors = []
    rows = []

    try:
        reader = csv.DictReader(io.StringIO(content))

        # Validate headers
        if not reader.fieldnames:
            return [], ["CSV file is empty or has no headers."]

        headers = [h.strip().lower() for h in reader.fieldnames]

        # Check required columns
        required = ["question", "ai_response"]
        missing = [col for col in required if col not in headers]
        if missing:
            return [], [f"Missing required columns: {', '.join(missing)}. "
                        f"Found columns: {', '.join(headers)}"]

        # Parse rows
        for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            # Normalize keys
            normalized = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}

            question = normalized.get("question", "").strip()
            ai_response = normalized.get("ai_response", "").strip()
            reference = normalized.get("reference_answer", "").strip() or normalized.get("reference", "").strip()

            if not question:
                errors.append(f"Row {i}: Missing 'question' value.")
                continue
            if not ai_response:
                errors.append(f"Row {i}: Missing 'ai_response' value.")
                continue

            rows.append({
                "question": question,
                "ai_response": ai_response,
                "reference": reference if reference else None,
            })

        if not rows and not errors:
            errors.append("CSV file contains no data rows.")

    except Exception as e:
        errors.append(f"Failed to parse CSV: {str(e)}")

    return rows, errors
