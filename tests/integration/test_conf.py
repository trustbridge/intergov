import pytest

from intergov.conf import env_s3_config, env_postgres_config, env_queue_config


@pytest.mark.tryfirst
def test():

    s3 = env_s3_config('TEST')
    queue = env_queue_config('TEST')
    postgres = env_postgres_config('TEST')
    assert s3['bucket'] == 'test-bucket-1'
    assert queue['queue_name'] == 'test-queue-1'
    assert postgres['dbname'] == 'postgres_test'

    s3 = env_s3_config('TEST_1')
    queue = env_queue_config('TEST_1')
    assert s3['bucket'] == 'test-bucket-1'
    assert queue['queue_name'] == 'test-queue-1'

    s3 = env_s3_config('TEST_2')
    queue = env_queue_config('TEST_2')
    assert s3['bucket'] == 'test-bucket-2'
    assert queue['queue_name'] == 'test-queue-2'
