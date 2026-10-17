from datetime import datetime
import re

from app.schemas.application import ApplicationData, Person

EMAIL_FIELDS = {"email", "employment_email"}
DATE_FIELDS = {"birthday"}
PHONE_FIELDS = {"contact_no", "home_tel", "employment_contact_no"}
UPPERCASE_FIELDS = {
    "last_name", "first_name", "middle_name", "citizenship", "birth_place", "address",
    "housing_status", "civil_status", "main_bank", "bank_branch", "employment_name",
    "position", "employment_address", "monthly_income", "bank_depositor", "relationship",
}
VALID_HOUSING_STATUSES = {"OWNED", "RENTED", "LIVING W/PARENTS", "LIVING WITH PARENTS"}


def _is_not_applicable(value: str) -> bool:
    return value.strip().upper() in {"N/A", "NA", "NONE", "NOT APPLICABLE"}


def correct_value_format(field: str, value: str) -> str:
    """Normalize a recognized field without hiding values that need validation."""
    value = re.sub(r"\s+", " ", str(value)).strip()
    if not value:
        return ""
    if field in EMAIL_FIELDS:
        return value.lower()
    if field in DATE_FIELDS:
        date_value = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", value, flags=re.IGNORECASE)
        for date_format in (
            "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
            "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
            "%d %B %Y", "%d %b %Y", "%Y-%m-%d",
        ):
            try:
                return datetime.strptime(date_value, date_format).strftime("%m/%d/%Y")
            except ValueError:
                continue
    if field == "tin_number":
        digits = re.sub(r"\D", "", value)
        if len(digits) == 9:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    if field in PHONE_FIELDS:
        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and digits.startswith("0"):
            return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
    if field in {"length_of_stay", "years_of_service"}:
        value = re.sub(r"\s*(?:YEARS?|YRS?)\.?\s*$", "YRS", value, flags=re.IGNORECASE)
        value = re.sub(r"\s+TO\s+", " TO ", value, flags=re.IGNORECASE)
    if field in UPPERCASE_FIELDS or field not in EMAIL_FIELDS:
        return value.upper()
    return value


def normalize_person(person: Person) -> Person:
    values = person.model_dump()
    return Person(**{field: correct_value_format(field, value) for field, value in values.items()})


def normalize_application(data: ApplicationData) -> ApplicationData:
    values = data.model_dump()
    values.update({field: correct_value_format(field, values[field]) for field in ("unit", "color_first", "color_second")})
    values["applicant"] = normalize_person(data.applicant)
    values["spouse"] = normalize_person(data.spouse)
    if not values["spouse"].housing_status:
        values["spouse"].housing_status = "N/A"
    return ApplicationData(**values)


def validate_application(data: ApplicationData) -> list[str]:
    data = normalize_application(data)
    issues: list[str] = []
    for label, person in (("Applicant", data.applicant), ("Spouse/co-maker", data.spouse)):
        if person.birthday and not _is_not_applicable(person.birthday):
            try:
                datetime.strptime(person.birthday, "%m/%d/%Y")
            except ValueError:
                issues.append(f"{label} birthdate must use MM/DD/YYYY and be a real date.")
        if person.housing_status and not _is_not_applicable(person.housing_status) and person.housing_status not in VALID_HOUSING_STATUSES:
            issues.append(f"{label} housing status is not recognized.")
    return issues
