# Place custom exceptions here
# All shared stuff should go to intergov.apis.common.errors.api.message
from http import HTTPStatus
from intergov.apis.common.errors import GenericHTTPError, ValidationError


class UnexpectedMessageStatusError(ValidationError):

    @property
    def detail(self):
        got, *rest = self.args
        return f'Unexpected message status value: {got}'

    @property
    def source(self):
        got, expected = self.args
        return [
            {
                'value': got,
                'expected': list(expected)
            }
        ]


def MessageNotFoundError(reference):
    return GenericHTTPError(
        title='Message Not Found Error',
        status=HTTPStatus.NOT_FOUND,
        detail='No message with that reference can be found for this auth',
        source=[
            {
                'reference': reference
            }
        ]
    )
