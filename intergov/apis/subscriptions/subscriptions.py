from urllib.parse import urlparse
from http import HTTPStatus as StatusCode
from flask import (
    Blueprint,
    request,
    Response
)

from libtrustbridge import errors
from libtrustbridge.utils import routing
from libtrustbridge.websub.repos import SubscriptionsRepo
from libtrustbridge.websub.constants import (
    TOPIC_ATTR_KEY,
    CALLBACK_ATTR_KEY,
    LEASE_SECONDS_ATTR_KEY,
    LEASE_SECONDS_MAX_VALUE,
    LEASE_SECONDS_MIN_VALUE,
    MODE_ATTR_KEY,
    REQUIRED_ATTRS,
    MODE_ATTR_SUBSCRIBE_VALUE,
    MODE_ATTR_UNSUBSCRIBE_VALUE,
    VALID_REQUEST_CONTENT_TYPE,
    SUPPORTED_CALLBACK_URL_SCHEMES,
    ATTRS_DEFAULTS
)
from libtrustbridge.websub.exceptions import (
    UnknownModeError,
    UnableToPostSubscriptionError,
    SubscriptionExistsError,
    SubscriptionNotFoundError,
    CallbackURLValidationError,
    TopicValidationError,
    LeaseSecondsValidationError
)

from intergov.monitoring import statsd_timer
from intergov.use_cases import (
    SubscriptionDeregisterUseCase,
    SubscriptionRegisterUseCase,
)
from intergov.use_cases.subscription_deregister import SubscriptionNotFound

from .conf import Config

blueprint = Blueprint('subscriptions', __name__)


def _deregister_subscription(form):
    repo = SubscriptionsRepo(Config.SUBSCR_REPO_CONF)
    use_case = SubscriptionDeregisterUseCase(repo)
    try:
        use_case.execute(form[CALLBACK_ATTR_KEY], form[TOPIC_ATTR_KEY])
    except SubscriptionNotFound as e:
        raise SubscriptionNotFoundError() from e
    return Response(
        status=StatusCode.ACCEPTED
    )


def _register_subscription(form):
    repo = SubscriptionsRepo(Config.SUBSCR_REPO_CONF)
    use_case = SubscriptionRegisterUseCase(repo)
    result = use_case.execute(form[CALLBACK_ATTR_KEY], form[TOPIC_ATTR_KEY], form[LEASE_SECONDS_ATTR_KEY])
    if result is None:
        raise UnableToPostSubscriptionError()
    elif not result:
        raise SubscriptionExistsError()
    return Response(
        status=StatusCode.ACCEPTED
    )


def _is_valid_lease_seconds(value):
    try:
        return LEASE_SECONDS_MIN_VALUE <= int(value) <= LEASE_SECONDS_MAX_VALUE
    except ValueError:
        return False


def _validate_topic(value):
    if not isinstance(value, str):
        return 'Predicate must be string'

    if not value:
        return 'Predicate must not be empty'

    splitted = value.split('.')

    for element in splitted:
        if not element:
            return 'Predicate must not contain empty elements'

    wildcard = '*'
    wildcard_found = False
    # tests: one or no wildcards in the predicate
    for element in splitted:
        if element == '*':
            if not wildcard_found:
                wildcard_found = True
            else:
                return 'Predicate may contain only one wildcard and only as the last element'
    # tests: wildcard is the last element of the predicate
    if wildcard_found and splitted[-1] != wildcard:
        return 'Only last element of a predicate can be a wildcard'

    if value.startswith('UN.'):
        # some validations are applicable only for message predicates
        if len(splitted) < 4 and not wildcard_found:
            return 'Predicates shorter than 4 elements must include wildcard as the last element'
        if len(splitted) < 2:
            return 'Predicate domain must consist of 1 or more elements'
    # no errors found
    return False


def _validate_url(value):
    if not isinstance(value, str):
        return 'URL must be string'
    parsed = urlparse(value)
    if not parsed.scheme:
        return 'URL must contain scheme'
    if parsed.scheme not in SUPPORTED_CALLBACK_URL_SCHEMES:
        return 'Unsupported url scheme: "{}". Must be one of: {}.'.format(
            parsed.scheme,
            SUPPORTED_CALLBACK_URL_SCHEMES
        )
    if not parsed.netloc:
        return 'URL must contain domain or ip'
    # no errors found
    return False


def _validate_data(form):
    url_validation_error = _validate_url(form[CALLBACK_ATTR_KEY])
    topic_validation_error = _validate_topic(form[TOPIC_ATTR_KEY])
    if url_validation_error:
        raise CallbackURLValidationError(url_validation_error)
    if topic_validation_error:
        raise TopicValidationError(topic_validation_error)
    if not _is_valid_lease_seconds(form[LEASE_SECONDS_ATTR_KEY]):
        raise LeaseSecondsValidationError(form[LEASE_SECONDS_ATTR_KEY])


def _check_form_key_exists(form, key, errors):
    try:
        form[key]
    except KeyError:
        errors.append(key)


def _check_required_attrs(form):
    errors = []
    for key in REQUIRED_ATTRS:
        _check_form_key_exists(form, key, errors)
    return errors


def _fill_attrs_defaults(form):
    for key, default in ATTRS_DEFAULTS.items():
        try:
            form[key]
        except KeyError:
            form[key] = default


def _recast_form(form):
    form[LEASE_SECONDS_ATTR_KEY] = int(form[LEASE_SECONDS_ATTR_KEY])


@blueprint.route('/subscriptions', methods=['POST'])
@routing.mimetype([VALID_REQUEST_CONTENT_TYPE])
@statsd_timer("api.subscriptions.endpoint.subscription_register")
def subscription_register():
    form = request.form.to_dict()
    missing = _check_required_attrs(form)
    _fill_attrs_defaults(form)
    if missing:
        raise errors.MissingAttributesError(missing)
    _validate_data(form)
    _recast_form(form)
    if form[MODE_ATTR_KEY] == MODE_ATTR_SUBSCRIBE_VALUE:
        return _register_subscription(form)
    elif form[MODE_ATTR_KEY] == MODE_ATTR_UNSUBSCRIBE_VALUE:
        return _deregister_subscription(form)
    else:
        raise UnknownModeError(form[MODE_ATTR_KEY])
