from http import HTTPStatus
from unittest import mock

from intergov.apis.common.errors.api.message import (
    MessageValidationError,
    MessageDeserializationError,
    MessageDataEmptyError,
)
from intergov.apis.common.errors.handlers import (
    error_response_json_template
)
from intergov.apis.common.utils.routing import (
    UnsupportedMediaTypeError
)
from intergov.domain.wire_protocols.generic_discrete import Message
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_dict as generate_message,
    _remove_message_params as remove_message_params
)

MESSAGE_CLASS = 'intergov.apis.message_rx.message.Message'
BC_INBOX_REPO_CLASS = 'intergov.apis.message_rx.message.BCInboxRepo'
ENQUEUE_MESSAGE_USE_CASE_CLASS = 'intergov.apis.message_rx.message.EnqueueMessageUseCase'

VALID_MESSAGE_DATA_DICT = generate_message()
VALID_MESSAGE_DATA_DICT['sender_ref'] = '00000000-1111-2222-3333-4445555666ff'

POST_URL = '/messages'

VALID_REQUEST_MIMETYPE = 'application/json'
VALID_RESPONSE_MIMETYPE = VALID_REQUEST_MIMETYPE

INVALID_REQUEST_MIMETYPE = 'application/x-www-form-urlencoded'


def _test_post_message_missing_required_attr(client, valid_data, url=POST_URL):
    for key in Message.required_attrs:

        data = remove_message_params(valid_data, keys=[key])
        resp = client.post(url, json=data)

        assert resp.mimetype == VALID_RESPONSE_MIMETYPE
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.get_json() == error_response_json_template(
            MessageDeserializationError(
                source=[
                    '\'{}\''.format(key)
                ]
            )
        )


def _test_post_message_received_unsupported_mimetype(client, url=POST_URL):
    resp = client.post(url, mimetype=INVALID_REQUEST_MIMETYPE, data={})
    assert resp.mimetype == VALID_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert resp.get_json() == error_response_json_template(
        UnsupportedMediaTypeError(
            INVALID_REQUEST_MIMETYPE,
            [VALID_REQUEST_MIMETYPE],
            []
        )
    )


def _test_post_message_received_empty_body(client, url=POST_URL):
    resp = client.post(url, mimetype=VALID_REQUEST_MIMETYPE)
    assert resp.mimetype == VALID_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.get_json() == error_response_json_template(
        MessageDataEmptyError()
    )

    resp = client.post(url, json={})
    assert resp.mimetype == VALID_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.get_json() == error_response_json_template(
        MessageDataEmptyError()
    )


def _test_post_message_validation_failed(
        message_class,
        message_class_path,
        client,
        valid_data,
        url=POST_URL,
        api=""
):
    # it's pretty much impossible yet to get around from_dict validation without mocking
    require_allowed = ["sender_ref"] if api == "rx" else []
    message = message_class.from_dict(valid_data, require_allowed=require_allowed)
    message.kwargs['spurious_attr'] = 'Something suspicious'
    remove_message_params(message.kwargs, keys=message_class.required_attrs, copy_data=False, set_none=True)

    with mock.patch(message_class_path + '.from_dict') as from_dict:
        from_dict.return_value = message

        resp = client.post(url, json=valid_data)
        from_dict.assert_called_once()

        assert resp.mimetype == VALID_RESPONSE_MIMETYPE
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.get_json() == error_response_json_template(
            MessageValidationError(
                source=[
                    'spurious attr: spurious_attr',
                    'sender is not a country: None',
                    'receiver is not a country: None',
                    'subject is empty',
                    'obj is not a URI: None',
                    'predicate is not a URI: None'
                ]
            )
        )
