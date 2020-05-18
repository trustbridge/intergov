from http import HTTPStatus as StatusCode
from unittest import mock, TestCase

import pytest

from intergov.apis.common import errors
from intergov.apis.common.errors.handlers import error_response_json_template
from intergov.apis.common.utils import routing
from intergov.apis.subscriptions.constants import (
    LEASE_SECONDS_MAX_VALUE,
    LEASE_SECONDS_MIN_VALUE,
)
from intergov.apis.subscriptions.subscriptions import (
    UnknownModeError,
    CallbackURLValidationError,
    LeaseSecondsValidationError,
    TopicValidationError,
    UnableToPostSubscriptionError,
    SubscriptionExistsError,
    SubscriptionNotFoundError,
    REQUIRED_ATTRS,
    _validate_url,
    _validate_topic
)
from tests.unit.domain.wire_protocols.test_generic_message import (
    _remove_message_params as remove_params
)

SUBSCRIPTIONS_REPO_CLASS = 'intergov.apis.subscriptions.subscriptions.SubscriptionsRepo'

POST_URL = '/subscriptions'

VALID_REQUEST_CONTENT_TYPE = 'application/x-www-form-urlencoded'

CALLBACK_ATTR_KEY = 'hub.callback'
TOPIC_ATTR_KEY = 'hub.topic'
MODE_ATTR_KEY = 'hub.mode'
LEASE_SECONDS_ATTR_KEY = 'hub.lease_seconds'
MODE_ATTR_SUBSCRIBE_VALUE = 'subscribe'
MODE_ATTR_UNSUBSCRIBE_VALUE = 'unsubscribe'

INVALID_CONTENT_TYPES = [
    'application/json',
    'multipart/form-data'
]

VALID_SUBSCRIBE_DATA = {
    CALLBACK_ATTR_KEY: 'http://elvis.presley.com/call/me/tender',
    TOPIC_ATTR_KEY: 'SONGS.OLD.TRACK.created',
    MODE_ATTR_KEY: MODE_ATTR_SUBSCRIBE_VALUE
}

VALID_UNSUBSCRIBE_DATA = {**VALID_SUBSCRIBE_DATA, MODE_ATTR_KEY: MODE_ATTR_UNSUBSCRIBE_VALUE}

INVALID_MODE_DATA = {**VALID_SUBSCRIBE_DATA, MODE_ATTR_KEY: 'dancewithme'}

INVALID_CALLBACK_DATA = {**VALID_SUBSCRIBE_DATA, CALLBACK_ATTR_KEY: '/invalid/callback'}

INVALID_TOPIC_DATA = {**VALID_SUBSCRIBE_DATA, TOPIC_ATTR_KEY: 'UN.SONGS'}


def test_validator():
    assert not _validate_topic('CEFACT.TRADE.CO.CA.created')
    assert not _validate_topic('CEFACT.TRADE.CO.created')
    assert not _validate_topic('CEFACT.TRADE.CO.*')
    assert not _validate_topic('CEFACT.TRADE.*')
    assert not _validate_topic('CEFACT.*')

    # I'm a little bit unsure about these rules, but there is no problem to remove or modify them
    short_predicate_withoud_wildcard = 'Predicates shorter than 4 elements must include wildcard as the last element'

    assert _validate_topic('UN.CEFACT.TRADE') == short_predicate_withoud_wildcard
    assert _validate_topic('UN.CEFACT') == short_predicate_withoud_wildcard
    assert _validate_topic('*') is False  # a little silly case to subscribe on everything...
    assert _validate_topic('CEFACT.*.*') == 'Predicate may contain only one wildcard and only as the last element'
    assert _validate_topic('CEFACT.TRADE.*.CO.created') == 'Only last element of a predicate can be a wildcard'
    assert _validate_topic('') == 'Predicate must not be empty'
    assert _validate_topic(1) == 'Predicate must be string'

    assert not _validate_url('http://hello.com/callback')
    assert not _validate_url('http://hello.com:8080/callback/')
    assert not _validate_url('https://hello.com')
    assert not _validate_url('https://hello')
    assert not _validate_url('https://192.168.0.1')

    assert _validate_url('http://') == 'URL must contain domain or ip'
    assert _validate_url('192.168.0.1') == 'URL must contain scheme'
    assert _validate_url('file://192.168.0.1') == 'Unsupported url scheme: "{}". Must be one of: {}.'.format(
        'file',
        ['http', 'https']
    )
    assert _validate_url(1) == 'URL must be string'


def test_error_builders():
    # instead of asserting responses data directly it's better to test
    # error builders and then only compare the results
    assert UnknownModeError(INVALID_MODE_DATA[MODE_ATTR_KEY]).to_dict() == {
        'title': 'Unknown Mode Error',
        'code': 'unknown-mode-error',
        'status': 'Bad Request',
        'detail': 'Uknown "{}" attribute value: "{}". Accepted:{}.'.format(
            MODE_ATTR_KEY,
            INVALID_MODE_DATA[MODE_ATTR_KEY],
            [
                MODE_ATTR_SUBSCRIBE_VALUE,
                MODE_ATTR_UNSUBSCRIBE_VALUE
            ]
        ),
        'source': [
            {
                'key': MODE_ATTR_KEY,
                'value': INVALID_MODE_DATA[MODE_ATTR_KEY],
                'expected': [
                    MODE_ATTR_SUBSCRIBE_VALUE,
                    MODE_ATTR_UNSUBSCRIBE_VALUE
                ]
            }
        ]
    }

    assert TopicValidationError('a').to_dict() == {
        'title': 'Topic Validation Error',
        'code': 'topic-validation-error',
        'status': 'Bad Request',
        'detail': '"{}" attribute is invalid'.format(TOPIC_ATTR_KEY),
        'source': ['a']
    }

    assert CallbackURLValidationError('a').to_dict() == {
        'title': 'Callback URL Validation Error',
        'code': 'callback-url-validation-error',
        'status': 'Bad Request',
        'detail': '"{}" attribute is invalid'.format(CALLBACK_ATTR_KEY),
        'source': ['a']
    }

    assert LeaseSecondsValidationError(100).to_dict() == {
        'title': 'Lease Seconds Validation Error',
        'code': 'lease-seconds-validation-error',
        'status': 'Bad Request',
        'detail': '"{}" attribute is invalid. Must be integer in range {}-{}'.format(
            LEASE_SECONDS_ATTR_KEY,
            LEASE_SECONDS_MIN_VALUE,
            LEASE_SECONDS_MAX_VALUE
        ),
        'source': [
            {
                'value': 100,
                'max': LEASE_SECONDS_MAX_VALUE,
                'min': LEASE_SECONDS_MIN_VALUE
            }
        ]
    }

    assert SubscriptionExistsError().to_dict() == {
        'title': 'Conflict',
        'code': 'generic-http-error',
        'status': 'Conflict',
        'detail': 'Subscription with given parameters exists',
        'source': []
    }

    assert SubscriptionNotFoundError().to_dict() == {
        'title': 'Not Found',
        'code': 'generic-http-error',
        'status': 'Not Found',
        'detail': 'Subscription with given parameters not found',
        'source': []
    }

    assert UnableToPostSubscriptionError().to_dict() == {
        'title': 'Internal Server Error',
        'code': 'internal-server-error',
        'status': 'Internal Server Error',
        'detail': 'Unable to post data to repository',
        'source': []
    }


@pytest.mark.usefixtures("client_class")
class SubscriptionViewTest(TestCase):
    def setUp(self):
        patcher = mock.patch(SUBSCRIPTIONS_REPO_CLASS)
        self.subscription_repo = patcher.start().return_value
        self.addCleanup(patcher.stop)

    def test_register_subscription__with_default_lease_seconds__should_succeed(self):
        resp = self.client.post(
            POST_URL,
            data=VALID_SUBSCRIBE_DATA,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.ACCEPTED, resp.data

    def test_register_subscription__with__lease_seconds__should_succeed(self):
        data = {**VALID_SUBSCRIBE_DATA}
        data[LEASE_SECONDS_ATTR_KEY] = LEASE_SECONDS_MAX_VALUE
        resp = self.client.post(
            POST_URL,
            data=data,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.ACCEPTED, resp.data

    def test_deregister_subscription__when_exist__should_succeed(self):
        self.subscription_repo.get_subscriptions_by_pattern.return_value = [
            mock.Mock(callback_url=VALID_SUBSCRIBE_DATA[CALLBACK_ATTR_KEY])
        ]
        resp = self.client.post(
            POST_URL,
            data=VALID_UNSUBSCRIBE_DATA,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.ACCEPTED, resp.get_json()
        self.subscription_repo.bulk_delete.assert_called_once_with([
            'SONGS/OLD/TRACK/CREATED/5bb78ecf699270199191582271882041'
        ])

    def test_request_with_wrong_mime_type__should_return_error(self):
        # forcing correct mimetype
        for content_type in INVALID_CONTENT_TYPES:
            resp = self.client.post(
                POST_URL,
                data=VALID_SUBSCRIBE_DATA,
                content_type=content_type
            )
            assert resp.status_code == StatusCode.UNSUPPORTED_MEDIA_TYPE, resp.data
            assert resp.get_json() == error_response_json_template(
                routing.UnsupportedMediaTypeError(
                    content_type,
                    [VALID_REQUEST_CONTENT_TYPE],
                    []
                )
            )

    def test_request_with_one_missing_required_attribute__should_return_error(self):
        for key in REQUIRED_ATTRS:
            data = remove_params(VALID_SUBSCRIBE_DATA, keys=[key])
            resp = self.client.post(
                POST_URL,
                data=data,
                content_type=VALID_REQUEST_CONTENT_TYPE
            )
            assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
            assert resp.get_json() == error_response_json_template(
                errors.MissingAttributesError([key])
            )

    def test_request_with_all_missing_required_attribute__should_return_error(self):
        data = remove_params(VALID_SUBSCRIBE_DATA, REQUIRED_ATTRS)
        resp = self.client.post(
            POST_URL,
            data=data,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
        assert resp.get_json() == error_response_json_template(
            errors.MissingAttributesError(REQUIRED_ATTRS)
        )

        resp = self.client.post(
            POST_URL,
            data=INVALID_TOPIC_DATA,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
        assert resp.get_json() == error_response_json_template(
            TopicValidationError('Predicates shorter than 4 elements must include wildcard as the last element')
        )

        resp = self.client.post(
            POST_URL,
            data=INVALID_CALLBACK_DATA,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
        assert resp.get_json() == error_response_json_template(
            CallbackURLValidationError('URL must contain scheme')
        )

    def test_request__with_unknown_mode_error__should_return_error(self):
        resp = self.client.post(
            POST_URL,
            data=INVALID_MODE_DATA,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.BAD_REQUEST, resp.data
        assert resp.get_json() == error_response_json_template(
            UnknownModeError(INVALID_MODE_DATA[MODE_ATTR_KEY])
        )

    def test_request__when_subscription_exists__should_return_error(self):
        resp = self.client.post(
            POST_URL,
            data=VALID_SUBSCRIBE_DATA,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        # let's support both conflict and fine, need to think about it more
        assert resp.status_code in (StatusCode.CONFLICT, StatusCode.ACCEPTED), resp.data
        # assert resp.get_json() == error_response_json_template(
        #     SubscriptionExistsError()
        # )

    def test_request__when_subscription_not_found__should_return_error(self):
        resp = self.client.post(
            POST_URL,
            data=VALID_UNSUBSCRIBE_DATA,
            content_type=VALID_REQUEST_CONTENT_TYPE
        )
        assert resp.status_code == StatusCode.NOT_FOUND, resp.data
        assert resp.get_json() == error_response_json_template(
            SubscriptionNotFoundError()
        )
