from http import HTTPStatus
from intergov.apis.common.errors import (
    ValidationError,
    GenericHTTPError,
)


class BadCountryNameError(ValidationError):

    detail = 'Received invalid/unknown country name'

    @property
    def source(self):
        try:
            error, = self.args
            return [str(error)]
        except ValueError:
            return []


class NoInputFileError(ValidationError):
    detail = 'Received no input file'


class TooManyFilesError(ValidationError):

    detail = 'Too many files. Only one file must be provided.'

    @property
    def source(self):
        try:
            files, = self.args
            return [
                {
                    'files': int(files)
                }
            ]
        except ValueError:
            return []


class InvalidURIError(ValidationError):
    detail = 'URI is not multihash'


def DocumentNotFoundError(uri, country):
    return GenericHTTPError(
        HTTPStatus.NOT_FOUND,
        detail='Document with uri:{} for country:{} not found'.format(
            uri, country
        ),
        source=[
            {
                'uri': uri,
                'country': str(country)
            }
        ]
    )
