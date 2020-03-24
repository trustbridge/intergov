import pycountry

from .conf import Config


class Country:
    """
    Helper class representing a country, with validations
    and extra parameters like readable name.

    Usage:

        from intergov.domain.contry import Country
        c = Country("US")
        c.object_api_base_url()
    """

    def __init__(self, name):
        # https://www.unece.org/cefact/locode/service/location.html
        assert isinstance(name, str), type(name)
        if len(name) != 2 or name.upper() != name:
            raise TypeError("Please use short 2-characters uppercase country name", name)
        self.country_object = pycountry.countries.get(alpha_2=name)
        if not self.country_object:
            raise ValueError("Unknown country name", name)
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}:{self.name}"

    def __eq__(self, other):
        if not isinstance(other, Country):
            return False
        return self.name == other.name

    def object_api_base_url(self):
        result = Config.DOCUMENT_REPOS.get(self.name)
        if not result:
            # In our test case it means misconfiguration
            # in the real world it may mean some systems offline/down or so,
            # and theoretically it should be handled gracefully, sending message/
            # doing whatever other job a little later.
            # For demo it's enough just to complain.
            raise ValueError(f"Unable to determine document repo for {self.name}")
        return result
