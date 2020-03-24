import pytest
from unittest import mock
from intergov.domain.country import Country


def test_country_object_initialization():
    # For now I don't see any other way to check proper initialization
    # initialization failure cases in this test are much more important
    assert Country('US').name == 'US'


def test_country_object_initialization_failure():

    # no argument
    with pytest.raises(TypeError):
        Country()

    # lowercase
    with pytest.raises(TypeError):
        Country('us')

    # more than 2 letters
    with pytest.raises(TypeError):
        Country('USA')

    # less than 2 letters
    with pytest.raises(TypeError):
        Country('U')

    # empty string
    with pytest.raises(TypeError):
        Country('')

    # not string argument
    with pytest.raises(AssertionError):
        Country(1)

    # unknown country
    with mock.patch('pycountry.countries.get', return_value=None) as get_country:
        with pytest.raises(ValueError):
            Country('US')
        get_country.assert_called()
