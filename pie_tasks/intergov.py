import sys
from pathlib import Path

from pie import *
from pie_docker_compose import *
from pie_env_ext import *

from .utils import requires_compose_project_name


ROOT_DIR = Path('.').absolute()
ENV_DIR = ROOT_DIR/'docker'
DOCKER_COMPOSE = DockerCompose('docker/node.docker-compose.yml')


def INSTANCE_ENVIRONMENT():
    COMPOSE_PROJECT_NAME=requires_compose_project_name()
    return env.from_files(
        ENV_DIR/'node.env',
        ENV_DIR/f'node.{COMPOSE_PROJECT_NAME}.env',
        ENV_DIR/f'node.{COMPOSE_PROJECT_NAME}-local.env')


@task
def build():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('build')


@task
def p():
    with INSTANCE_ENVIRONMENT():
        if len(sys.argv) == 2:
            print("Some parameters are required")
        else:
            DOCKER_COMPOSE.cmd(sys.argv[2], options=sys.argv[3:])


@task
def start():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('up', options=['-d'])


@task
def start_sync():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('up')


@task
def logs():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('logs', options=['--tail=40', '-f'])


@task
def stop():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down')

@task
def restart():
    stop()
    start()

@task
def destroy():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.cmd('down',options=['-v', '--rmi local'])



@task
def tests__unit():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.service('tests-unit').cmd('run')

@task
def tests__integration():
    with INSTANCE_ENVIRONMENT():
        DOCKER_COMPOSE.service('tests-integration').cmd('run')
