from pathlib import Path

from pie import *
from pie_docker_compose import *


ROOT_DIR = Path('.').absolute()
INTERGOV_DIR = ROOT_DIR


DEMO_DOCKER_COMPOSE = DockerCompose('demo-dc.yml')

@task
def build():
    with cd(INTERGOV_DIR):
        DEMO_DOCKER_COMPOSE.cmd('build')


@task
def start():
    with cd(INTERGOV_DIR):
        DEMO_DOCKER_COMPOSE.cmd('up', options=['-d'])


@task
def stop():
    with cd(INTERGOV_DIR):
        DEMO_DOCKER_COMPOSE.cmd('down')

@task
def destroy():
    with cd(INTERGOV_DIR):
        DEMO_DOCKER_COMPOSE.cmd('down',options=['-v', '--rmi all'])



@task
def tests__unit():
    with cd(INTERGOV_DIR):
        DEMO_DOCKER_COMPOSE.service('tests-unit').cmd('run')

@task
def tests__integration():
    with cd(INTERGOV_DIR):
        DEMO_DOCKER_COMPOSE.service('tests-integration').cmd('run')
