import hashlib
import multihash

from intergov.monitoring import statsd_timer
from intergov.use_cases.common import BaseUseCase


class StoreObjectUseCase(BaseUseCase):
    """
    Used by the document API

    Accept object ACL and object lake repos
    Also accept file-like object with the document body to be saved

    * calculates multihash
    * tries to save this object to ACL and lake repos, using multihash as filename
    * adds receiving jurisdiction to the list of recipients able to use document
      API to retrieve the object
    * returns multihash on success or raises an exceptions if something is wrong
    """

    def __init__(self, object_acl_repo, object_lake_repo):
        self.object_acl = object_acl_repo
        self.object_lake = object_lake_repo

    def _get_file_multihash(self, fobj):
        fobj.seek(0)
        BLOCK_SIZE = 2**20
        hash_function = hashlib.sha256()
        while True:
            data = fobj.read(BLOCK_SIZE)
            if not data:
                break
            hash_function.update(data)
        fobj.seek(0)
        return multihash.to_b58_string(multihash.encode(
            hash_function.digest(), 'sha2-256'
        ))

    @statsd_timer("usecase.StoreObjectUseCase.execute")
    def execute(self, fname=None, fobj=None, target_jurisdiction=None):
        """
        If fname is received then saves object at given path
        If fboj is provided (file-like object) then saves it.
        """
        assert bool(fname) != bool(fobj)
        super().execute()
        if fname:
            # not sure we ever need it at all, but let this stub be here
            raise NotImplementedError("no fname save is supported yet")

        multihash = self._get_file_multihash(fobj)

        self.object_acl.allow_access_to(
            multihash,
            target_jurisdiction.name
        )

        # assuming it will raise errors if any
        # TODO: do not upload existing objects, just update their object_acl
        self.object_lake.post_from_file_obj(multihash, fobj)
        return multihash
