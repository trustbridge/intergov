from intergov.loggers import logging

from intergov.monitoring import statsd_timer
from intergov.use_cases.common import BaseUseCase


class AuthenticatedObjectAccessUseCase(BaseUseCase):
    """
    Used by the document/object retrieve API

    Receive ACL and object lake repos
    Receive URI which is a multihash of the file
    Receive auth_jurisdiction - a jurisdiction, which is trying to access this object
    Returns obj body or None or raises an Exception
    Checks if this jurisdiction can access this object and returns it if exists
    """

    def __init__(self, object_acl_repo, object_lake_repo):
        self.object_acl = object_acl_repo
        self.object_lake = object_lake_repo

    @statsd_timer("usecase.AuthenticatedObjectAccessUseCase.execute")
    def execute(self, uri, auth_jurisdiction):
        super().execute(uri, auth_jurisdiction)
        authenticated_jurisdictions = self.object_acl.search({'object__eq': uri})
        if auth_jurisdiction not in authenticated_jurisdictions:
            # it's not much of an error, just useful for debug to see what's wrong
            logging.error("Actor %s tried to access %s but can't", auth_jurisdiction, uri)
            return None
        try:
            obj = self.object_lake.get_body(uri)
        except Exception as e:
            if e.__class__.__name__ == 'NoSuchKey':
                obj = None
            else:
                raise e

        if not obj:
            logging.error(
                "For object %s the ACL record exists but object is not in the object lake",
                uri
            )
            return None
        else:
            return obj
