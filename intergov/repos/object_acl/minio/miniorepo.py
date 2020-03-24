import json

from intergov.domain.country import Country
from intergov.loggers import logging  # NOQA
from intergov.serializers import generic_discrete_message as ser
from intergov.repos.base.minio import miniorepo


class ObjectACLRepo(miniorepo.MinioRepo):

    DEFAULT_BUCKET = 'acl'

    def post(self, message):
        """
        A message implies
        that the sender believes
        the recipient is entitled
        to access the object of the message.

        The message tells us
        who sender and receiver are,
        and what the object is.
        We can more-or-less ignore everything else
        """
        # TODO: This procedure has never been run yet
        logging.info("Saving message %s to ObjectACLRepo", message)

        message_is_already_there = False
        # TODO: implement such check
        if message_is_already_there:  # pragma: no cover
            # the file and path exist in the repo:
            return True
        else:
            message_content = json.dumps(message, cls=ser.MessageJSONEncoder)
            # will save it as `/QmLa/lalala/CN.json`
            path = f"{message.obj}/{message.receiver}.json"
            self.put_object(
                clean_path=path,
                content_body=message_content
            )
            # self.put_message_related_object(
            #     sender=message.sender,
            #     sender_ref=message.sender_ref,
            #     rel_path=f"/{message.receiver}.json",
            #     content_body=content
            # )
        # TODO (psudocode): add timestamp to the filename
        # if collission, wait 1 second and try again
        # make sure one process wins the race
        # - how? lockfile with PID-like worker identifier?
        # /{message_path}/{timestamp}.lockfile
        # (content = HOSTNAME.PID)
        return True

    def allow_access_to(self, obj, receiver):
        path = f"{obj}/{receiver}"
        return self.put_object(
            clean_path=path,
            content_body=""
        )

    def search(self, filters=None):
        """
        # TODO: we may do a faster version of it just to check if given country
        # may do this operation
        Because post() stores each message
        at the location representing the object,
        with a name representing the recipient
        (not implemented) (plus a timestamp, in case they received
                          messages about the same object more than once)
        , we are able to scan that location
        to see who has been granted access to the object.
        """
        # if filters is None:
        #     return False
        assert filters  # shoudln't be used without filters, it's a programming error
        # we only support one filter for now
        allowed_filters = ('object__eq',)
        for f in filters.keys():
            if f not in allowed_filters:
                # TODO ?
                raise Exception("unsupported filter {} (not in {})".format(
                    f, allowed_filters
                ))
        found_objects = self.client.list_objects(
            Bucket=self.bucket,
            Prefix=miniorepo.slash_chunk(filters['object__eq']) + '/',
            # recursive=True
        )

        if not found_objects.get('Contents', []):
            return []
        else:
            uniq_countries = set()
            for obj in found_objects.get('Contents', []):
                pure_filename = obj['Key'].split('/')[-1]
                if obj['Key'].endswith('.json'):
                    # based on rx_message, there is message in this file
                    # oname is something like /QmXx/xxx/xxxx/CN.json
                    country_name = pure_filename.split('.')[0]
                else:
                    # based on uploaded document, the file is empty
                    country_name = pure_filename
                uniq_countries.add(country_name)
            return [Country(c) for c in uniq_countries]
