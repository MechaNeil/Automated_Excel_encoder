from app.schemas.application import ApplicationData, Person
from app.services.validators import validate_application


def test_validator_rejects_bad_email_and_age():
    data = ApplicationData(applicant=Person(email="bad", age="200"))
    issues = validate_application(data)
    assert len(issues) == 2
