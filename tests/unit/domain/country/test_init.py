import pytest
from unittest import mock
from intergov.domain.jurisdiction import Jurisdiction


def test_jurisdiction_object_initialization():
    # For now I don't see any other way to check proper initialization
    # initialization failure cases in this test are much more important
    assert Jurisdiction('US').name == 'US'


def test_jurisdiction_object_initialization_failure():

    # no argument
    with pytest.raises(TypeError):
        Jurisdiction()

    # lowercase
    with pytest.raises(TypeError):
        Jurisdiction('us')

    # more than 2 letters
    with pytest.raises(TypeError):
        Jurisdiction('USA')

    # less than 2 letters
    with pytest.raises(TypeError):
        Jurisdiction('U')

    # empty string
    with pytest.raises(TypeError):
        Jurisdiction('')

    # not string argument
    with pytest.raises(AssertionError):
        Jurisdiction(1)

    # unknown jurisdiction
    with mock.patch('pycountry.countries.get', return_value=None) as get_country:
        with pytest.raises(ValueError):
            Jurisdiction('US')
        get_country.assert_called()
