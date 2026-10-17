import re

from app.schemas.application import ApplicationData, ParseResponse, Person
from app.services.field_map import FIELD_ALIASES
from app.services.validators import correct_value_format

SECTION_MARKERS = {
    "applicant details": "applicant",
    "borrower primary": "applicant",
    "borrowerprimary": "applicant",
    "spouse or co maker": "spouse",
    "spouse/co maker": "spouse",
    "coborrower comaker": "spouse",
    "coborrowercomaker": "spouse",
    "co borrower co maker": "spouse",
}


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" \t:-")


def _canonical(label: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", " ", label.lower()).strip()
    for field, aliases in FIELD_ALIASES.items():
        if normalized in {re.sub(r"[^a-z0-9]+", " ", alias).strip() for alias in aliases}:
            return field
    return None


def parse_text(raw_text: str) -> ParseResponse:
    people = {"applicant": {}, "spouse": {}}
    application: dict[str, str] = {}
    source_values: dict[str, str] = {}
    warnings: list[str] = []
    conflicts: list[str] = []
    current = "applicant"
    current_field: str | None = None

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        marker = re.sub(r"[^a-z0-9 ]+", "", line.lower()).strip()
        if marker in SECTION_MARKERS:
            current = SECTION_MARKERS[marker]
            current_field = None
            continue
        match = re.match(r"^\s*([^:]{2,60})\s*:\s*(.*)$", line)
        if not match:
            if current_field:
                target = application if current == "application" else people[current]
                target[current_field] = correct_value_format(
                    current_field,
                    _clean(f"{target.get(current_field, '')} {line}"),
                )
            continue
        field = _canonical(match.group(1))
        value = _clean(match.group(2))
        if not field:
            warnings.append(f"Unrecognized field label: {match.group(1).strip()}.")
            current_field = None
            continue
        if not value:
            continue
        target = application if field in {"unit", "color_first", "color_second"} else people[current]
        current = "application" if field in {"unit", "color_first", "color_second"} else current
        if target.get(field) and target[field] != value:
            conflicts.append(f"Conflicting values for {current}.{field}: {target[field]!r} and {value!r}")
        target[field] = correct_value_format(field, value)
        source_values[f"{current}.{field}"] = value
        current_field = field

    if not application.get("unit"):
        warnings.append("Vehicle unit is missing.")
    for section in ("applicant", "spouse"):
        if not people[section].get("first_name") and not people[section].get("last_name"):
            warnings.append(f"{section.title()} identity is missing or uncertain.")
    if application.get("unit") and not application.get("color_first"):
        warnings.append("First-choice color is missing.")

    return ParseResponse(
        data=ApplicationData(applicant=Person(**people["applicant"]), spouse=Person(**people["spouse"]), **application),
        warnings=warnings,
        conflicts=conflicts,
        source_values=source_values,
    )
