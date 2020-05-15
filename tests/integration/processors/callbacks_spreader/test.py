from libtrustbridge.utils.conf import env_queue_config, env_s3_config
from libtrustbridge.websub import repos
from libtrustbridge.websub.domain import Pattern
from libtrustbridge.websub.processors import Processor

from intergov.use_cases import DispatchMessageToSubscribersUseCase
from tests.unit.domain.wire_protocols.test_generic_message import (
    _generate_msg_object
)

DELIVERY_OUTBOX_REPO_CONF = env_queue_config('TEST_1')
NOTIFICATIONS_REPO_CONF = env_queue_config('TEST_2')
SUBSCRIPTIONS_REPO_CONF = env_s3_config('TEST')

CALLBACK_URL = "http://dummy-test-helper-server:5001/response/200/{}"

DEFAULT_EXPIRATION = 3600 * 2

# predicates dont have common prefixes
SUBSCRIPTIONS = {
    'aaa.bbb.ccc.ddd': 2,
    'eee.fff.jjj': 3,
    'hhh.iii': 4,
    'ggg': 1
}


SUBSCRIPTIONS_WITH_COMMON_PREFIXES = {
    'ooo': {
        'ooo.aaa.bbb': 2,
        'ooo.aaa': 3,
    },
    'zzz': {
        'zzz.aaa.bbb': 5,
        'zzz.aaa': 3,
    }
}


def _fill_subscriptions_repo(repo, subscriptions):
    overall = 0
    for predicate, number in subscriptions.items():
        overall += number
        url_tail = predicate.replace('.', '-')+"-{}"
        url = CALLBACK_URL.format(url_tail)
        for i in range(number):
            print(f"subcribe predicate:{predicate}, url:{url.format(i)}")
            repo.subscribe_by_pattern(Pattern(predicate), url.format(i), DEFAULT_EXPIRATION)
    assert not repo._unsafe_is_empty_for_test()


def _is_predicate_in_url(url, predicate):
    return url.split('/')[-1].startswith(predicate.replace('.', '-'))


def test():
    # testing predicate in url search

    delivery_outbox_repo = repos.DeliveryOutboxRepo(DELIVERY_OUTBOX_REPO_CONF)
    notifications_repo = repos.NotificationsRepo(NOTIFICATIONS_REPO_CONF)
    subscriptions_repo = repos.SubscriptionsRepo(SUBSCRIPTIONS_REPO_CONF)

    delivery_outbox_repo._unsafe_clear_for_test()
    notifications_repo._unsafe_clear_for_test()
    subscriptions_repo._unsafe_clear_for_test()

    assert notifications_repo._unsafe_is_empty_for_test()
    assert delivery_outbox_repo._unsafe_is_empty_for_test()
    assert subscriptions_repo._unsafe_is_empty_for_test()

    use_case = DispatchMessageToSubscribersUseCase(notifications_repo, delivery_outbox_repo, subscriptions_repo)
    processor = Processor(use_case=use_case)

    # testing that iter returns processor
    assert iter(processor) is processor

    # assert processor has nothing to do
    assert next(processor) is None

    _fill_subscriptions_repo(subscriptions_repo, SUBSCRIPTIONS)
    for prefix, subscriptions in SUBSCRIPTIONS_WITH_COMMON_PREFIXES.items():
        _fill_subscriptions_repo(subscriptions_repo, subscriptions)

    for s in subscriptions_repo.get_subscriptions_by_pattern(Pattern('aaa.bbb.ccc.ddd')):
        print(s.__hash__())
        print(s.payload, s.key, s.now, s.data)
    # testing that subscriptions repod doesn't have side effect on processor
    assert next(processor) is None

    # testing callbacks spreading for predicates without common prefixes
    for predicate, number_of_subscribers in SUBSCRIPTIONS.items():
        # pushing notification
        message = _generate_msg_object(predicate=predicate)
        notifications_repo.post_job(message)
        # test proccessor received notification
        assert next(processor) is True

        # test processor created correct number of delivery jobs
        # each subscriptions group has unique topic/predicate
        for i in range(number_of_subscribers):
            job = delivery_outbox_repo.get_job()
            assert job, f"Call:{i+1}. Predicate:{predicate}"
            message_queue_id, payload = job
            # test that only direct subscribers received this message
            assert payload.get('payload', {}).get('predicate') == predicate
            # testing that only correct subscribers will receive notification
            url = payload.get('s', '')
            assert _is_predicate_in_url(url, predicate), {'url': url, 'predicate': predicate}
            assert delivery_outbox_repo.delete(message_queue_id)
        # test queue is empty

        print(delivery_outbox_repo.get_job())
        assert not delivery_outbox_repo.get_job()
    # processor completed the job
    assert next(processor) is None

    for prefix, subscriptions in SUBSCRIPTIONS_WITH_COMMON_PREFIXES.items():

        # finding longest predicate in the group + total number of expected
        # delivery jobs
        expect_jobs = 0
        longest_predicate = ""
        for predicate, number_of_subscribers in subscriptions.items():
            if len(longest_predicate) < len(predicate):
                longest_predicate = predicate
            expect_jobs += number_of_subscribers

        # posting notification
        message = _generate_msg_object(predicate=longest_predicate)
        assert notifications_repo.post_job(message)
        assert next(processor) is True

        # testing processor created the correct number of delivery jobs
        for i in range(expect_jobs):
            job = delivery_outbox_repo.get_job()
            assert job
            message_queue_id, payload = job
            # test that only direct subscribers received this message
            assert payload.get('payload', {}).get('predicate') == longest_predicate
            # testing that only correct subscribers will receive notification
            url = payload.get('s', '')
            assert _is_predicate_in_url(url, prefix), {'url': url, 'prefix': prefix}
            assert delivery_outbox_repo.delete(message_queue_id)
        assert next(processor) is None
