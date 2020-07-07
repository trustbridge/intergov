import json
from io import BytesIO
from urllib.parse import urljoin

import requests

from intergov.domain.country import Country
from intergov.loggers import logging
from intergov.monitoring import statsd_timer

logger = logging.getLogger(__name__)


class RetrieveAndStoreForeignDocumentsUseCase:
    """
    Processes single request from the queue to download
    some remote document.

    The process is recursive.
    If an object has sub-objects,
    add more jobs to download them later.

    .. admonition:: Note

       * returns None if the object has already been downloaded
       * returns True in case of success
       * raises exceptions for errors
    """

    def __init__(
            self,
            country,
            object_retrieval_repo,
            object_lake_repo,
            object_acl_repo):
        self.country = country
        self.object_retrieval = object_retrieval_repo
        self.object_lake = object_lake_repo
        self.object_acl_repo = object_acl_repo

    def execute(self):
        retrieval_task = self.object_retrieval.get_job()
        if not retrieval_task:
            return False
        (job_id, job) = retrieval_task
        return self.process(job_id, job)

    @statsd_timer("usecase.RetrieveAndStoreForeignDocumentsUseCase.process")
    def process(self, job_id, job):
        logger.info(
            "[%s] Running the RetrieveAndStoreForeignDocumentsUseCase for job %s",
            self.country,
            job
        )
        multihash = job['object']
        sender = Country(job['sender'])
        # 1. check if this object is not in the object lake yet
        # 2. if not - download it to the object lake
        if not self._is_in_object_lake(multihash):
            self._download_remote_obj(sender, multihash)
        # 3. Give receiver access to the object
        self.object_acl_repo.allow_access_to(
            multihash,
            self.country.name
        )
        # 4. Delete the job as completed
        # 4.1. Schedule downloads of sub-documents
        self.object_retrieval.delete(job_id)
        return True

    def _is_in_object_lake(self, multihash):
        try:
            # TODO: replace by just exist check instead of reading the whole file
            # maybe create and use an '.exists(multihash)' method on object_lake
            self.object_lake.get_body(multihash)
        except Exception as e:
            if e.__class__.__name__ == 'NoSuchKey':
                return False
            else:
                raise e
        return True

    def _download_remote_obj(self, sender, multihash):
        logger.info("Downloading %s from %s as %s", multihash, sender, self.country)
        remote_doc_api_url = sender.object_api_base_url()
        url = urljoin(remote_doc_api_url, multihash)

        doc_resp = requests.get(
            url,
            {
                "as_country": self.country.name,
            },
            # TODO: cognito JWT and other auth methods
            headers={
                'Authorization': 'JWTBODY {}'.format(
                    json.dumps({
                        "sub": "documents-api",
                        "party": "spider",
                        "country": self.country.name,
                    })
                )
            }
        )
        logger.info("GET %s: status %s", url, doc_resp.status_code)
        # TODO: we should process various response codes differently:
        # e.g. if 5xx, rescuedule for later
        # if 429, rescuedule for later with increasing wait times
        # different 4xx, different strategies
        # (put thought into logging/monitoring)
        assert doc_resp.status_code in (200, 201), "{} {}".format(doc_resp, doc_resp.content)
        # logger.info("For URL %s we got resp %s", remote_doc_api_url, doc_resp)
        self.object_lake.post_from_file_obj(
            multihash,
            BytesIO(doc_resp.content)
        )

        # try to parse the downloaded documents for `links` section
        try:
            json_document = json.loads(doc_resp.content)
        except Exception:
            # not a json, which is fine
            pass
            logger.info("Downloaded object %s is not JSON file", multihash)
        else:
            # TODO: security: document spider will blindly download any multihash
            # (including links in links in links).
            # not sure what negative impact is has.
            links = json_document.get('links')
            if isinstance(links, list):
                for link in links:
                    # {"TYPE1": "document", "TYPE2": "Exporters Information Form Update",
                    # "name": "hmmm_6W4jRRG.png",
                    # "ct": "binary/octet-stream",
                    # "link": "QmZxJAJhq98T683RQSk3T2wkLBH2nFV4y43iCHRk3DZyWn"}
                    if 'link' in link:
                        link_qmhash = link['link']
                        assert '/' not in link_qmhash
                        assert ':' not in link_qmhash
                        logger.info("Posting sub-job to retrieve %s", link_qmhash)
                        self.object_retrieval.post_job(
                            {
                                'action': 'download-object',
                                'sender': sender.name,
                                'object': link_qmhash,
                                'parent': multihash
                            }
                        )
