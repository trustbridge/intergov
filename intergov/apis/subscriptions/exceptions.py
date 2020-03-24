from http import HTTPStatus as StatusCode
from intergov.apis.common.errors import (
    ValidationError,
    InternalServerError,
    GenericHTTPError
)
from . import constants


class TopicValidationError(ValidationError):

    detail = '"{}" attribute is invalid'.format(constants.TOPIC_ATTR_KEY)

    @property
    def source(self):
        return list(self.args)


class CallbackURLValidationError(ValidationError):
    detail = '"{}" attribute is invalid'.format(constants.CALLBACK_ATTR_KEY)

    @property
    def source(self):
        return list(self.args)


class LeaseSecondsValidationError(ValidationError):
    detail = '"{}" attribute is invalid. Must be integer in range {}-{}'.format(
        constants.LEASE_SECONDS_ATTR_KEY,
        constants.LEASE_SECONDS_MIN_VALUE,
        constants.LEASE_SECONDS_MAX_VALUE
    )

    @property
    def source(self):
        got, = self.args
        return [
            {
                "value": int(got),
                "min": constants.LEASE_SECONDS_MIN_VALUE,
                "max": constants.LEASE_SECONDS_MAX_VALUE
            }
        ]


class UnknownModeError(ValidationError):
    @property
    def detail(self):
        got, = self.args
        return 'Uknown "{}" attribute value: "{}". Accepted:{}.'.format(
            constants.MODE_ATTR_KEY,
            got,
            [
                constants.MODE_ATTR_SUBSCRIBE_VALUE,
                constants.MODE_ATTR_UNSUBSCRIBE_VALUE
            ]
        )

    @property
    def source(self):
        got, = self.args
        return [
            {
                'key': constants.MODE_ATTR_KEY,
                'value': got,
                'expected': [
                    constants.MODE_ATTR_SUBSCRIBE_VALUE,
                    constants.MODE_ATTR_UNSUBSCRIBE_VALUE
                ]
            }
        ]


def SubscriptionExistsError():
    return GenericHTTPError(
        StatusCode.CONFLICT,
        detail='Subscription with given parameters exists'
    )


def SubscriptionNotFoundError():
    return GenericHTTPError(
        StatusCode.NOT_FOUND,
        detail='Subscription with given parameters not found'
    )


def UnableToPostSubscriptionError():
    return InternalServerError(
        detail='Unable to post data to repository',
    )
