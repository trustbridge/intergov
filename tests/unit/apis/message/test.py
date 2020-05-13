from http import HTTPStatus

from unittest import mock

from intergov.domain.wire_protocols.generic_discrete import Message

from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_dict as generate_message,
    # _encode_message_dict as encode_message,
    # _remove_message_params as remove_message_params,
    _diff_message_dicts as diff_message_dicts
)

# apis of message rx regarding first three test cases are identical
from tests.unit.apis.message_rx.test import (
    _test_post_message_validation_failed,
    _test_post_message_received_empty_body,
    _test_post_message_missing_required_attr,
    _test_post_message_received_unsupported_mimetype
)
from intergov.apis.common.errors import (
    InternalServerError
)
from intergov.apis.common.errors.handlers import (
    error_response_json_template
)
from intergov.apis.common.errors.api.message import (
    UnableWriteToInboxError,
    MessageDataEmptyError,

)
from intergov.apis.message.exceptions import (
    MessageNotFoundError,
    UnexpectedMessageStatusError
)
from intergov.apis.common.utils.routing import (
    UnsupportedMediaTypeError
)


MESSAGE_LAKE_REPO = 'intergov.apis.message.message.MessageLakeRepo'
BC_INBOX_REPO = 'intergov.apis.message.message.BCInboxRepo'
MESSAGE_CLASS = 'intergov.apis.message.message.Message'
NOTIFICATIONS_REPO = 'intergov.apis.message.message.NotificationsRepo'

PATCH_MESSAGE_METADATA_USE_CASE = 'intergov.apis.message.message.PatchMessageMetadataUseCase'


MESSAGE_RETURN = {
    'test': True
}

MESSAGE_REFERENCE = 'AU:00000000-1111-2222-3333-4445555666ff'

POST_URL = '/message'
GET_URL = '/message/{}'
PATCH_URL = '/message/{}'

VALID_MESSAGE_DATA_DICT = generate_message()
VALID_MESSAGE_DATA_DICT['sender_ref'] = '00000000-1111-2222-3333-4445555666ff'

VALID_PATCH_STATUSES = [
    "accepted",
    "rejected"
]


VALID_REQUEST_MIMETYPE = 'application/json'
VALID_RESPONSE_MIMETYPE = VALID_REQUEST_MIMETYPE


class NoSuchKey(Exception):
    pass


class RandomException(Exception):
    pass


def test_errors():
    assert MessageNotFoundError(MESSAGE_REFERENCE).to_dict() == {
        'code': 'generic-http-error',
        'status': 'Not Found',
        'title': 'Message Not Found Error',
        'detail': 'No message with that reference can be found for this auth',
        'source': [
            {
                'reference': MESSAGE_REFERENCE
            }
        ]
    }
    assert UnexpectedMessageStatusError('a', ['b', 'c']).to_dict() == {
        'code': 'unexpected-message-status-error',
        'status': 'Bad Request',
        'title': 'Unexpected Message Status Error',
        'detail': 'Unexpected message status value: a',
        'source': [
            {
                'value': 'a',
                'expected': ['b', 'c']
            }
        ]
    }


@mock.patch(MESSAGE_LAKE_REPO)
def test_get_success(RepoMock, client):

    instance = RepoMock.return_value
    instance.get.return_value = MESSAGE_RETURN

    resp = client.get(GET_URL.format(MESSAGE_REFERENCE))
    instance.get.assert_called()
    assert resp.mimetype == VALID_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.CREATED
    assert resp.get_json() == MESSAGE_RETURN, resp.get_json()


@mock.patch(MESSAGE_LAKE_REPO)
def test_get_error(RepoMock, client):

    instance = RepoMock.return_value
    instance.get.side_effect = NoSuchKey()

    resp = client.get(GET_URL.format(MESSAGE_REFERENCE))
    instance.get.assert_called_once()
    assert resp.mimetype == VALID_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.get_json() == error_response_json_template(
        MessageNotFoundError(MESSAGE_REFERENCE)
    )

    instance.get.reset_mock()

    instance.get.side_effect = RandomException()
    resp = client.get(GET_URL.format(MESSAGE_REFERENCE))
    instance.get.assert_called_once()
    assert resp.mimetype == VALID_RESPONSE_MIMETYPE
    assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert resp.get_json() == error_response_json_template(
        InternalServerError(instance.get.side_effect)
    )


@mock.patch(MESSAGE_LAKE_REPO)
@mock.patch(NOTIFICATIONS_REPO)
def test_patch_success(NotificationsRepoMock, MessageLakeRepoMock, client):

    notifications_repo = NotificationsRepoMock.return_value
    message_lake_repo = MessageLakeRepoMock.return_value

    # testing update without status, possible but not really
    # doing something usefull yet
    data = {**VALID_MESSAGE_DATA_DICT}
    try:
        del data['status']
    except KeyError:
        pass
    message = Message.from_dict(data)

    message_lake_repo.get.return_value = message

    resp = client.patch(
        PATCH_URL.format(MESSAGE_REFERENCE),
        json=VALID_MESSAGE_DATA_DICT
    )

    assert resp.status_code == HTTPStatus.OK
    assert resp.content_type == VALID_RESPONSE_MIMETYPE
    assert resp.get_json() == message.to_dict()

    assert message_lake_repo.get.call_count == 1
    message_lake_repo.update_metadata.assert_not_called()
    notifications_repo.post_job.assert_not_called()

    # testing status update
    sender, sender_ref = MESSAGE_REFERENCE.split(':', 1)
    for status in VALID_PATCH_STATUSES:
        notifications_repo.reset_mock()
        message_lake_repo.reset_mock()

        data = {**VALID_MESSAGE_DATA_DICT}
        message_old = Message.from_dict(data)
        data['status'] = status
        message_patched = Message.from_dict(data)

        message_lake_repo.get.side_effect = (message_old, message_patched,)

        resp = client.patch(
            PATCH_URL.format(MESSAGE_REFERENCE),
            json=data
        )

        assert resp.status_code == HTTPStatus.OK
        assert resp.content_type == VALID_RESPONSE_MIMETYPE
        assert resp.get_json() == message_patched.to_dict()

        assert message_lake_repo.get.call_count == 2
        message_lake_repo.update_metadata.assert_called_once_with(sender, sender_ref, {'status': status})
        notifications_repo.post_job.call_count == 3  # 3 types of msg notifications for each one


@mock.patch(MESSAGE_LAKE_REPO)
@mock.patch(NOTIFICATIONS_REPO)
def test_patch_error(NotificationsRepoMock, MessageLakeRepoMock, client):

    invalid_mimetype = "application/x-www-form-urlencoded"

    resp = client.patch(
        PATCH_URL.format(MESSAGE_REFERENCE),
        data={},
        mimetype=invalid_mimetype
    )

    assert resp.status_code == HTTPStatus.UNSUPPORTED_MEDIA_TYPE
    assert resp.content_type == VALID_RESPONSE_MIMETYPE
    assert resp.get_json() == error_response_json_template(
        UnsupportedMediaTypeError(
            invalid_mimetype,
            ['application/json'],
            []
        )
    )

    resp = client.patch(
        PATCH_URL.format(MESSAGE_REFERENCE),
        json={}
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.content_type == VALID_RESPONSE_MIMETYPE
    assert resp.get_json() == error_response_json_template(
        MessageDataEmptyError()
    )

    invalid_status = "Clearly some invalid status"
    resp = client.patch(
        PATCH_URL.format(MESSAGE_REFERENCE),
        json={"status": invalid_status}
    )

    assert resp.status_code == HTTPStatus.BAD_REQUEST
    assert resp.content_type == VALID_RESPONSE_MIMETYPE
    assert resp.get_json() == error_response_json_template(
        UnexpectedMessageStatusError(
            invalid_status,
            VALID_PATCH_STATUSES + [None]
        )
    )

    message_lake_repo = MessageLakeRepoMock.return_value
    message_lake_repo.get.side_effect = NoSuchKey()
    resp = client.patch(
        PATCH_URL.format(MESSAGE_REFERENCE),
        json={"status": VALID_PATCH_STATUSES[0]}
    )

    message_lake_repo.get.assert_called_once()

    assert resp.status_code == HTTPStatus.NOT_FOUND
    assert resp.content_type == VALID_RESPONSE_MIMETYPE
    assert resp.get_json() == error_response_json_template(
        MessageNotFoundError(MESSAGE_REFERENCE)
    )

    # testing random exception from use case
    message_lake_repo.reset_mock()
    message_lake_repo.get.side_effect = None

    with mock.patch(PATCH_MESSAGE_METADATA_USE_CASE) as UseCase:
        uc = UseCase.return_value
        uc.execute.side_effect = RandomException()
        resp = client.patch(
            PATCH_URL.format(MESSAGE_REFERENCE),
            json={"status": VALID_PATCH_STATUSES[0]}
        )

        assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert resp.content_type == VALID_RESPONSE_MIMETYPE
        assert resp.get_json() == error_response_json_template(
            InternalServerError(uc.execute.side_effect)
        )
        uc.execute.assert_called_once()


@mock.patch(BC_INBOX_REPO)
def test_post_success(RepoMock, client):

    message = Message.from_dict(VALID_MESSAGE_DATA_DICT)
    post = RepoMock.return_value.post
    post.return_value = message

    resp = client.post(POST_URL, json=VALID_MESSAGE_DATA_DICT)

    post.assert_called_once()

    assert resp.status_code == HTTPStatus.CREATED
    assert resp.content_type == VALID_RESPONSE_MIMETYPE
    # checks all required attrs + sender_ref
    resp_json = resp.get_json()
    diff = diff_message_dicts(
        resp_json,
        VALID_MESSAGE_DATA_DICT,
        keys=Message.required_attrs + ['sender_ref']
    )
    assert not diff
    assert 'status' in resp_json.keys()


def test_post_error(client):

    # just to prevent creation of the actual repo
    with mock.patch(BC_INBOX_REPO) as RepoMock:
        _test_post_message_received_unsupported_mimetype(client, url=POST_URL)
        _test_post_message_received_empty_body(client, url=POST_URL)

        _test_post_message_missing_required_attr(client, VALID_MESSAGE_DATA_DICT, url=POST_URL)

        _test_post_message_validation_failed(
            Message,
            MESSAGE_CLASS,
            client,
            VALID_MESSAGE_DATA_DICT,
            url=POST_URL
        )

    with mock.patch(BC_INBOX_REPO) as RepoMock:
        # Repo exceptions may contain sensitive info.
        # Maybe their str should not be passed as message
        # and logged internally instead

        # testing random repo specific exception response
        post = RepoMock.return_value.post
        post.side_effect = Exception('Repo Specific Exception')

        resp = client.post(POST_URL, json=VALID_MESSAGE_DATA_DICT)

        post.assert_called_once()

        assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert resp.content_type == VALID_RESPONSE_MIMETYPE
        assert resp.get_json() == error_response_json_template(
            InternalServerError(post.side_effect)
        )
        # testing expected repo inablity to post message
        # when post returns None
        post.reset_mock()
        post.return_value = None
        post.side_effect = None

        resp = client.post(POST_URL, json=VALID_MESSAGE_DATA_DICT)

        post.assert_called_once()

        assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert resp.content_type == VALID_RESPONSE_MIMETYPE
        assert resp.get_json() == error_response_json_template(
            UnableWriteToInboxError()
        )
