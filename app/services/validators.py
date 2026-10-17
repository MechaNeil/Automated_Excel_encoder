import re

from app.schemas.application import ApplicationData


def validate_application(data: ApplicationData) -> list[str]:
    issues: list[str] = []
    for label, person in (("Applicant", data.applicant), ("Spouse/co-maker", data.spouse)):
        if person.email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", person.email):
            issues.append(f"{label} email address is not valid.")
        if person.age and (not person.age.isdigit() or not 0 < int(person.age) < 120):
            issues.append(f"{label} age should be a number between 1 and 119.")
        if person.tin_number and not re.fullmatch(r"[0-9-]+", person.tin_number):
            issues.append(f"{label} TIN contains unexpected characters.")
    return issues
