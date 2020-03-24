# import hashlib
import multihash

from intergov.repos.base.minio import miniorepo


class ObjectLakeMinioRepo(miniorepo.MinioRepo):

    DEFAULT_BUCKET = 'objectlake'

    # def _get_file_multihash(self, file_path):
    #     h = hashlib.sha256()
    #     b = bytearray(128*1024)
    #     mv = memoryview(b)
    #     with open(file_path, 'rb', buffering=0) as f:
    #         for n in iter(lambda: f.readinto(mv), 0):
    #             h.update(mv[:n])
    #     return multihash.to_b58_string(multihash.encode(h.digest(), 'sha2-256'))

    # def post_from_file(self, file_path, delete_it=False):
    #     # TODO: I believe if we have some file then we may have this file
    #     # multihash already (it can be calculated by the API), so may not need
    #     # to do that

    #     # NOTE: never has been run, just written as a pseudocode
    #     # 0. check file_path is stored locally
    #     assert os.path.isfile(file_path)
    #     # 1. calculate the multihash
    #     mh = self._get_file_multihash(file_path)
    #     # 2. calculate slash_chunked path from multihash
    #     # 3. save to object store at slash_chunked path
    #     self.client.fput_object(
    #         bucket_name=self.bucket_name,
    #         object_name=miniorepo.slash_chunk(mh),
    #         file_path=file_path
    #     )
    #     if delete_it:
    #         raise NotImplementedError("it's not implemented yet, delete the source file yourself")
    #     return True

    def post_from_file_obj(self, multihash, file_obj):
        # ulgy way to handle files, but works fine for small ones and MVP
        blob = file_obj.read()
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=miniorepo.slash_chunk(multihash),
            Body=blob,
            ContentLength=len(blob)
        )

    def get_body(self, b58_multihash: str):
        # Note: not for a very big files
        assert multihash.is_valid(
            multihash.from_b58_string(b58_multihash)
        ), "A valid multihash must be provided"
        # 1. calculate slash_chunked path from multihash
        # 2. get multihash-named object from store (or return False)
        # 3. return retrieved object
        return self.client.get_object(
            Bucket=self.bucket_name,
            Key=miniorepo.slash_chunk(b58_multihash),
        )['Body'].read()
