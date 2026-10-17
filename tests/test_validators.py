from app.schemas.application import ApplicationData, Person
from app.services.validators import validate_application


def test_validator_ignores_unrelated_email_and_age_values():
    data = ApplicationData(applicant=Person(email="bad", age="200"))
    issues = validate_application(data)
    assert issues == []


def test_validator_normalizes_named_dates_and_spouse_housing():
    data = ApplicationData(
        applicant=Person(birthday="JULY 5, 1996", employment_contact_no="0977 039 8157"),
        spouse=Person(birthday="5 July 1996"),
    )
    from app.services.validators import normalize_application

    normalized = normalize_application(data)
    assert normalized.applicant.birthday == "07/05/1996"
    assert normalized.applicant.employment_contact_no == "0977 039 8157"
    assert normalized.spouse.birthday == "07/05/1996"
    assert normalized.spouse.housing_status == "N/A"
    assert validate_application(data) == []
