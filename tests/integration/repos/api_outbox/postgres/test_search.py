import re
from intergov.conf import env_postgres_config
from intergov.repos.api_outbox import postgresrepo

CONF = env_postgres_config('TEST')


def test_repository_search_without_filters(
        docker_setup, pg_data, pg_session):
    repo = postgresrepo.PostgresRepo(CONF)

    repo_messages = repo.search()

    assert set([m.sender for m in repo_messages]) == \
        set([m['sender'] for m in pg_data])
    assert set([m.receiver for m in repo_messages]) == \
        set([m['receiver'] for m in pg_data])
    assert set([m.predicate for m in repo_messages]) == \
        set([m['predicate'] for m in pg_data])
    assert set([m.subject for m in repo_messages]) == \
        set([m['subject'] for m in pg_data])
    assert set([m.obj for m in repo_messages]) == \
        set([m['obj'] for m in pg_data])


def test_repository_search_messages_with_sender_filter(
        docker_setup, pg_data, pg_session):
    repo = postgresrepo.PostgresRepo(CONF)
    for d in pg_data:
        sender = d["sender"]
        repo_messages = repo.search(
            filters={'sender__eq': sender}
        )
        for m in repo_messages:
            assert m.sender == sender


def test_repository_search_messages_with_receiver_filter(
        docker_setup, pg_data, pg_session):
    repo = postgresrepo.PostgresRepo(CONF)
    for d in pg_data:
        r = d["receiver"]
        repo_messages = repo.search(
            filters={'receiver__eq': r}
        )
        for m in repo_messages:
            assert m.receiver == r


def test_repository_search_messages_with_subject_filter(
        docker_setup, pg_data, pg_session):
    repo = postgresrepo.PostgresRepo(CONF)
    for d in pg_data:
        s = d["subject"]
        repo_messages = repo.search(
            filters={'subject__eq': s}
        )
        for m in repo_messages:
            assert m.subject == s


def test_repository_search_messages_with_object_filter(
        docker_setup, pg_data, pg_session):
    repo = postgresrepo.PostgresRepo(CONF)
    for d in pg_data:
        o = d["obj"]
        repo_messages = repo.search(
            filters={'object__eq': o}
        )
        for m in repo_messages:
            assert m.obj == o  # ugh! FIXME


def test_repository_search_messages_with_predicate_eq_filter(
        docker_setup, pg_data, pg_session):
    repo = postgresrepo.PostgresRepo(CONF)
    for d in pg_data:
        p = d["predicate"]
        repo_messages = repo.search(
            filters={'predicate__eq': p}
        )
        for m in repo_messages:
            assert m.predicate == p


def test_repository_search_messages_with_predicate_wild_filter(
        docker_setup, pg_data, pg_session):
    repo = postgresrepo.PostgresRepo(CONF)
    for d in pg_data:
        source_p = d["predicate"]
        # if predicate is "foo.bar.baz",
        # we want patterns "foo.*"
        # and "foo.bar.*" to match it
        chunks = source_p.split('.')
        patterns = []
        for x in range(len(chunks)-1):
            p = chunks[0]
            for y in range(0, x):
                p = '{}.{}'.format(p, chunks[y+1])
            patterns.append(p)

        assert patterns, d
        for i in patterns:
            repo_messages = repo.search(
                filters={'predicate__wild': i}
            )
            pred_pattern = re.compile("^{}[.].+".format(i))

            for m in repo_messages:
                found_predicate = str(m.predicate)
                assert pred_pattern.match(found_predicate) is not None
