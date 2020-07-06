from pie import *


def requires_compose_project_name():
    """Using this means we don't have to define COMPOSE_PROJECT_NAME for `docs.` tasks"""
    COMPOSE_PROJECT_NAME=env.get('COMPOSE_PROJECT_NAME',None)
    if not COMPOSE_PROJECT_NAME:
        print('COMPOSE_PROJECT_NAME environment variable is required')
        exit(1)
    return COMPOSE_PROJECT_NAME
