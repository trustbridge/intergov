from intergov.apis.common.errors import (
    ValidationError,
    InternalServerError
)


class MessageDataEmptyError(ValidationError):
    detail = 'A single non-empty JSON must be passed'
    source = []


class MessageDeserializationError(ValidationError):
    detail = 'Unable to deserialize the posted message'
    source = []


class MessageValidationError(ValidationError):
    detail = 'Unable to validate the posted message'
    source = []


class MessageAbsoluteURLError(ValidationError):
    detail = 'Unable to identify absolute URI of message'
    source = []


class UnableWriteToInboxError(InternalServerError):
    detail = 'Unexpected error, unable write to inbox'
    source = []
