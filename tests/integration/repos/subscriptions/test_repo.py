# TODO: write tests for the subscription repo
# mocking the underlying minio stuff
from unittest import mock
from datetime import datetime, timedelta
from intergov.repos.subscriptions import SubscriptionsRepo


ROOT_PREDICATE_LAYERS = [
    "OOOO",
    "BBBB",
    "CCCC",
    "DDDD"
]

PREDICATE_ROOT = ".".join(ROOT_PREDICATE_LAYERS)

SUBSCRIPTIONS_POSTS = [
    (1, f"{PREDICATE_ROOT}.a", 3600 * 1),
    (2, f"{PREDICATE_ROOT}.b", 3600 * 2),
    (3, f"{PREDICATE_ROOT}.c", 3600 * 3),
    (4, f"{PREDICATE_ROOT}.d", 3600 * 4),
]

CALLBACK = "http://receiver.com/callback"
TOPIC = "UN.CEFACT.CertificateOfOrigin.created"

NOW = datetime.utcnow()
NOW_DAY_AFTER = NOW + timedelta(days=1)
NOW_TEN_DAYS_AFTER = NOW + timedelta(days=10)
EXPIRATION_TWO_DAYS = 3600 * 2


@mock.patch('intergov.repos.subscriptions.minio.miniorepo.current_datetime')
@mock.patch('intergov.repos.subscriptions.minio.miniorepo.expiration_datetime')  # noqa
def test_post_update_search_delete(expiration_datetime, current_datetime, docker_setup):

    expiration_datetime.side_effect = lambda s: NOW + timedelta(seconds=s)
    current_datetime.return_value = NOW

    repo = SubscriptionsRepo(docker_setup['minio'])

    # testing broad deletion & cleanup before test
    for callback_id, topic, expiration in SUBSCRIPTIONS_POSTS:
        repo.delete(None, topic)
        assert len(repo.search(topic)) == 0

    # testing layered search
    def predicates_in_layers(layers):
        for i in range(len(layers)):
            yield ".".join(layers[0:i+1]), i

    callbacks_per_layer = 3
    for topic, i in predicates_in_layers(ROOT_PREDICATE_LAYERS):
        repo.delete(None, topic)
        for callback_index in range(callbacks_per_layer):
            callback = f"http://callback/{i*callbacks_per_layer+callback_index}/"
            repo.post(callback, topic, EXPIRATION_TWO_DAYS)

    for topic, i in predicates_in_layers(ROOT_PREDICATE_LAYERS):
        expect = (i+1) * callbacks_per_layer
        assert len(repo.search(topic, layered=True)) == expect, f"Layer:{topic}"

    for topic, i in predicates_in_layers(ROOT_PREDICATE_LAYERS):
        assert repo.delete(None, topic) == 3

    for step in range(1, 2):
        for callback_id, topic, expiration in SUBSCRIPTIONS_POSTS:

            callbacks = [f"http://callback/{callback_id}/{step}/{char}" for char in "abcdef"]

            # creating
            repo.post(callbacks[0], topic, expiration)
            # testing get and creation result
            subscription = repo.get(callbacks[0], topic)
            assert subscription == {
                'c': callbacks[0],
                'e': expiration_datetime(expiration)
            }
            # updating
            expiration = expiration * step
            repo.post(callbacks[0], topic, expiration)
            # testing get and update result
            subscription = repo.get(callbacks[0], topic)
            assert subscription == {
                'c': callbacks[0],
                'e': expiration_datetime(expiration)
            }
            # testing narrow search
            assert repo.search(topic, url=callbacks[0])
            # testing broad search
            search_results = repo.search(topic)
            assert len(search_results) == 1
            assert callbacks[0] in search_results
            # testing deletion
            assert repo.delete(callbacks[0], topic) == 1
            assert not repo.search(topic, url=callbacks[0])

            # testing two deletion modes with multiply subsriptions to the same topic
            for delete in ["narrow", "broad", "wild"]:
                for callback in callbacks:
                    repo.post(callback, topic, expiration)
                    search_results = repo.search(topic)
                    assert callback in search_results
                assert len(search_results) == len(callbacks)
                if delete == "narrow":
                    left = len(callbacks) - 1
                    for callback in callbacks:
                        assert repo.delete(callback, topic) == 1
                        search_results = repo.search(topic)
                        assert callback not in search_results
                        assert len(search_results) == left
                        left -= 1
                elif delete == "broad":
                    assert repo.delete(None, topic) == len(callbacks)
                    assert len(repo.search(topic)) == 0
                elif delete == "wild":
                    assert repo.delete(None, PREDICATE_ROOT, recursive=True) == len(callbacks)
                    assert len(repo.search(PREDICATE_ROOT, recursive=True)) == 0

    # testing that all topics have no subscriptions left
    for callback_id, topic, expiration in SUBSCRIPTIONS_POSTS:
        assert len(repo.search(topic)) == 0

    # testing discarding expired subscriptions
    repo.delete(None, PREDICATE_ROOT, recursive=True)
    assert not repo.search(PREDICATE_ROOT, recursive=True)

    def create_callback(id):
        return f"http://callback/{id}/"

    test_broad_wild_search = True
    for method in ["delete", "search", "get"]:
        current_datetime.return_value = NOW
        for callback_id, topic, expiration in SUBSCRIPTIONS_POSTS:
            callback = create_callback(callback_id)
            expiration = EXPIRATION_TWO_DAYS
            repo.post(callback, topic, expiration)

        # testing broad wild search
        if test_broad_wild_search:
            search_result = repo.search(PREDICATE_ROOT, recursive=True)
            assert len(search_result) == len(SUBSCRIPTIONS_POSTS)
            for callback_id, *rest in SUBSCRIPTIONS_POSTS:
                assert create_callback(callback_id) in search_result
            test_broad_wild_search = False

        current_datetime.return_value = NOW_TEN_DAYS_AFTER
        if method == 'delete':
            assert repo.delete(None, PREDICATE_ROOT, recursive=True) == 0
        elif method == 'search':
            assert len(repo.search(PREDICATE_ROOT, recursive=True)) == 0
        elif method == 'get':
            for callback_id, topic, expiration in SUBSCRIPTIONS_POSTS:
                callback = create_callback(callback_id)
                assert not repo.get(callback, topic)


def test_repo_utils(docker_setup):
    repo = SubscriptionsRepo(docker_setup['minio'])
    assert repo._pattern_to_layers("a.b.c.d.event") == [
        "A/",
        "A/B/",
        "A/B/C/",
        "A/B/C/D/",
        "A/B/C/D/EVENT/"
    ]

    assert repo._pattern_to_layers("a.b.c.d.*") == [
        "A/",
        "A/B/",
        "A/B/C/",
        "A/B/C/D/"
    ]

    assert repo._pattern_to_layers("a.b.*") == [
        "A/",
        "A/B/"
    ]

    assert repo._pattern_to_layers("a") == [
        "A/"
    ]

    assert repo._pattern_to_layers("a.*") == [
        "A/"
    ]
