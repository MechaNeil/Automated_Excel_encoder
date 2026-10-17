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
VALID_CIVIL_STATUSES = {"SINGLE", "MARRIED", "WIDOWED", "SEPARATED", "DIVORCED"}


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
        for date_format in ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y"):
            try:
                return datetime.strptime(value, date_format).strftime("%m/%d/%Y")
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
    return ApplicationData(**values)


def validate_application(data: ApplicationData) -> list[str]:
    data = normalize_application(data)
    issues: list[str] = []
    for label, person in (("Applicant", data.applicant), ("Spouse/co-maker", data.spouse)):
        if person.email and not _is_not_applicable(person.email) and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", person.email):
            issues.append(f"{label} email address is not valid.")
        if person.employment_email and not _is_not_applicable(person.employment_email) and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", person.employment_email):
            issues.append(f"{label} employment email address is not valid.")
        if person.birthday and not _is_not_applicable(person.birthday):
            try:
                datetime.strptime(person.birthday, "%m/%d/%Y")
            except ValueError:
                issues.append(f"{label} birthdate must use MM/DD/YYYY and be a real date.")
        if person.age and (not person.age.isdigit() or not 0 < int(person.age) < 120):
            issues.append(f"{label} age should be a number between 1 and 119.")
        if person.tin_number and not _is_not_applicable(person.tin_number) and not re.fullmatch(r"\d{3}-\d{3}-\d{3}", person.tin_number):
            issues.append(f"{label} TIN must contain 9 digits in XXX-XXX-XXX format.")
        if person.housing_status and person.housing_status not in VALID_HOUSING_STATUSES:
            issues.append(f"{label} housing status is not recognized.")
        if person.civil_status and person.civil_status not in VALID_CIVIL_STATUSES:
            issues.append(f"{label} marital status is not recognized.")
        for field, value in (("cell phone", person.contact_no), ("home telephone", person.home_tel), ("employment telephone", person.employment_contact_no)):
            if value and not _is_not_applicable(value) and not re.fullmatch(r"[TLMt lm+()\d./-]{7,}", value):
                issues.append(f"{label} {field} contains unexpected characters.")
    return issues
