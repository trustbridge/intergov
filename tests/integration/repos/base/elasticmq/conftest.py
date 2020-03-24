import pytest
import boto3


QUEUE_NAME = 'dummy'


def elasticmq_is_responsive(docker_setup):
    connection_data = docker_setup["elasticmq"]
    if connection_data["use_ssl"]:
        endpoint_tmplt = 'https://{}:{}'
    else:
        endpoint_tmplt = 'http://{}:{}'
    endpoint_url = endpoint_tmplt.format(
        connection_data['host'],
        connection_data['port'])
    client = boto3.client(
        'sqs',
        endpoint_url=endpoint_url,
        region_name=connection_data['region'],
        aws_secret_access_key=connection_data['secret_key'],
        aws_access_key_id=connection_data['access_key'],
        use_ssl=connection_data['use_ssl']
    )
    try:
        # this is the test
        print(client.list_queues())
        # client.get_queue_by_name(QueueName=QUEUE_NAME)
        return True

    except Exception:  # except what?
        # print(QUEUE_NAME)
        return False


@pytest.fixture(scope='session')
def elasticmq_client(docker_setup):
    # docker_services.wait_until_responsive(
    #     timeout=30.0, pause=0.1,
    #     check=lambda: elasticmq_is_responsive(docker_setup)
    # )
    connection_data = docker_setup["elasticmq"]
    if connection_data["use_ssl"]:
        endpoint_tmplt = 'https://{}:{}'
    else:
        endpoint_tmplt = 'http://{}:{}'
    endpoint_url = endpoint_tmplt.format(
        connection_data['host'],
        connection_data['port'])
    client = boto3.client(
        'sqs',
        endpoint_url=endpoint_url,
        region_name=connection_data['region'],
        aws_secret_access_key=connection_data['secret_key'],
        aws_access_key_id=connection_data['access_key'],
        use_ssl=connection_data['use_ssl']
        )
    yield client
