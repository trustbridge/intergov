import random
import time

from intergov.conf import env, env_s3_config, env_queue_config
from intergov.domain.country import Country
from intergov.repos.object_lake import ObjectLakeRepo
from intergov.repos.object_retrieval import ObjectRetrievalRepo
from intergov.repos.object_acl import ObjectACLRepo
from intergov.use_cases import RetrieveAndStoreForeignDocumentsUseCase

from intergov.loggers import logging

logger = logging.getLogger('obj_spider')


class ObjectSpider(object):
    """
    Iterate over the RetrieveAndStoreForeignDocumentUseCase.
    """
    def __init__(self):
        self._prepare_repos_confs()
        self._prepare_repos()
        self._prepare_use_case()

    def _prepare_repos_confs(self):
        self.repo_conf = {
            'object_lake': env_s3_config('PROC_OBJ_SPIDER_OBJ_LAKE'),
            'object_retrieval': env_queue_config('PROC_OBJ_SPIDER_OBJ_RETRIEVAL'),
            'object_acl': env_s3_config('PROC_OBJ_SPIDER_OBJ_ACL'),
        }

    def _prepare_repos(self):
        self.repos = {
            'object_lake_repo': ObjectLakeRepo(self.repo_conf['object_lake']),
            'object_retrieval_repo': ObjectRetrievalRepo(self.repo_conf['object_retrieval']),
            'object_acl_repo': ObjectACLRepo(self.repo_conf['object_acl']),
        }

    def _prepare_use_case(self):
        self.use_case = RetrieveAndStoreForeignDocumentsUseCase(
            country=Country(env("IGL_COUNTRY", default='AU')),
            **self.repos
        )

    def __iter__(self):
        logger.info("Starting the Object Spider")
        return self

    def __next__(self):
        try:
            result = self.use_case.execute()
        except Exception as e:
            logger.exception(e)
            result = None
        return result


if __name__ == '__main__':   # pragma: no cover
    # To start it manually, from the base dir:
    # PYTHONPATH="`pwd`" python intergov/processors/obj_spider/__init__.py
    for result in ObjectSpider():
        if result is None:
            time.sleep(random.randint(1, 5))
