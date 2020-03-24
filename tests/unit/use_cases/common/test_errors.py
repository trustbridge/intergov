import pytest
from intergov.use_cases.common import errors


def test_props_validation():
    class InvalidStatusCustomError(errors.UseCaseError):
        status = -100

    class InvalidDetailCustomError(errors.UseCaseError):
        detail = ['Hey', 'I', 'am', 'detail']

    class InvalidSourceCustomError(errors.UseCaseError):
        source = "I'm a source of the error, ha ha"

    with pytest.raises(ValueError) as e:
        InvalidDetailCustomError()
        assert str(e) == f"detail must be valid HTTP status code, got {InvalidDetailCustomError.detail}"

    with pytest.raises(ValueError) as e:
        InvalidSourceCustomError()
        assert str(e) == f"source must be valid HTTP status code, got {InvalidSourceCustomError.source}"

    with pytest.raises(ValueError) as e:
        InvalidStatusCustomError()
        assert str(e) == f"status must be valid HTTP status code, got {InvalidStatusCustomError.status}"


def test_errors_customization():

    STATUS = 404
    DETAIL = "Hello custom error"
    SOURCE = ['Something really bad happened']

    class CustomError(errors.UseCaseError):
        status = STATUS
        detail = DETAIL
        source = SOURCE

    e = CustomError()

    assert e.status == STATUS
    assert e.detail == DETAIL
    assert e.source == SOURCE

    kwargs = {
        'source': ['Something strange happened'],
        'detail': 'Hello big new world!',
        'status': 201
    }

    e = CustomError(**kwargs)

    assert e.status == kwargs['status']
    assert e.detail == kwargs['detail']
    assert e.source == kwargs['source']
