import json
import hashlib
from datetime import datetime, timedelta
from io import BytesIO

import dateutil
from botocore.client import ClientError

from intergov.repos.base.minio import miniorepo
from intergov.loggers import logging  # NOQA

logger = logging.getLogger(__name__)

CALLBACK_KEY = 'c'
EXPIRATION_KEY = 'e'


# used to mock datetime now in the tests
def current_datetime():
    return datetime.utcnow()


def expiration_datetime(seconds):
    return current_datetime() + timedelta(seconds=seconds)


def url_to_filename(url):
    return hashlib.md5(url.encode('utf-8')).hexdigest()


class SubscriptionExpired(Exception):
    pass


class InvalidSubscriptionFormat(Exception):
    pass


class SubscriptionsRepo(miniorepo.MinioRepo):

    DEFAULT_BUCKET = 'subscriptions'

    def _pattern_to_key(self, predicate_pattern):
        # logging.info(predicate_pattern)
        if not predicate_pattern:
            raise ValueError("non-empty predicate is required")
        if '/' in predicate_pattern:
            # predicate is a topic
            topic_pattern = predicate_pattern
            predicate_pattern = None
        else:
            # predicate is a predicate
            topic_pattern = None
        if predicate_pattern:
            if predicate_pattern.endswith('.'):
                # drop the pointless dot at the end
                predicate_pattern = predicate_pattern[:-1]
            if predicate_pattern.endswith('*'):
                predicate_pattern = predicate_pattern[:-1]
                assert predicate_pattern.endswith('.'), "* character is supported only in the last part"
            predicate_parts = predicate_pattern.upper().split('.')
            return '/'.join([p for p in predicate_parts if p]) + '/'
        elif topic_pattern:
            topic_pattern = topic_pattern.strip("/")
            if topic_pattern.endswith('*'):
                topic_pattern = topic_pattern[:-1]
                assert topic_pattern.endswith('/'), "* character is supported only in the last part"
            return topic_pattern

    def _pattern_to_layers(self, predicate_pattern):
        layers = []
        key = self._pattern_to_key(predicate_pattern)
        split_layers = [layer for layer in key.split("/") if layer]
        for i in range(0, len(split_layers)):
            layers.append("/".join(split_layers[0:i+1])+"/")
        return layers

    def _predicate_url_to_key(self, predicate_pattern, url):
        return self._pattern_to_key(predicate_pattern) + url_to_filename(url)

    def _encode_obj(self, callback, expiration):
        data = {
            CALLBACK_KEY: callback,
            EXPIRATION_KEY: expiration.isoformat()
        }
        return json.dumps(data).encode('utf-8')

    def _decode_obj(self, obj, name=None, now=None, invalids_list=None):
        try:
            json_data = None
            try:
                json_data = obj['Body'].read()
                data = json.loads(json_data.decode('utf-8'))
            except UnicodeError as e:
                raise InvalidSubscriptionFormat("data is not UTF-8") from e
            except ValueError as e:
                logging.warning("Tried to decode JSON data %s but failed", json_data)
                raise InvalidSubscriptionFormat("data is not a valid JSON") from e

            try:
                data[CALLBACK_KEY]
                data[EXPIRATION_KEY] = dateutil.parser.parse(data[EXPIRATION_KEY])
            except KeyError as e:
                raise InvalidSubscriptionFormat(
                    f"data missing required key:{str(e)}"
                ) from e
            except (TypeError, ValueError) as e:
                raise InvalidSubscriptionFormat(
                    f"expiration invalid format:{str(data[EXPIRATION_KEY])}"
                ) from e

            if now and data[EXPIRATION_KEY] < now:
                raise SubscriptionExpired()
            return data

        except (InvalidSubscriptionFormat, SubscriptionExpired) as e:
            # logging various invalid subscription format errors
            if isinstance(e, InvalidSubscriptionFormat):
                logger.warning(f"Deleting invalid subscription:{name}. Reason:[{str(e)}]")
            # autoremove invalid objects on decoding
            if invalids_list is None:
                if name:
                    self.client.delete_objects(
                        Bucket=self.bucket,
                        Delete={
                            'Objects': [
                                {'Key': name}
                            ],
                            'Quiet': True,  # |False
                        },
                    )
            else:
                # to support bulk deletion
                invalids_list.append(name)
        return None

    def _search_objects(self, storage_key, recursive=False):
        found_objects = set()

        listed_objects = self.client.list_objects(
            Bucket=self.bucket,
            Prefix=storage_key,
            # recursive=recursive  TODO: it's recursive :-(
        )
        # Warning: this is very dumb way to iterate S3-like objects
        # works only on small datasets
        for obj in listed_objects.get('Contents', []):
            full_url = obj['Key']
            rel_url = full_url[len(storage_key):]
            if not recursive and '/' in rel_url:
                # returned a file in subdirectory, ignore
                continue
            found_objects.add(obj['Key'])

        return found_objects

    def get(self, url, predicate_pattern):
        now = current_datetime()
        object_name = self._predicate_url_to_key(predicate_pattern, url)
        try:
            obj = self.client.get_object(
                Bucket=self.bucket,
                Key=object_name
            )
            return self._decode_obj(obj, object_name, now)
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'NoSuchKey':
                return None
            else:
                raise

    def post(self, url, predicate_pattern, expiration):
        """
        Save or update this url, expiration for this predicate
        Note: aa.bb.cc != aa.bb.ccc, so "aa.bb.cc" means any string which start
        with "aa.bb.cc." and the 'aa.bb.cc' itself, but not 'aa.bb.ccc'
        """
        # logger.info("Subscribing url %s to %s expires in %s seconds", url, predicate_pattern, expiration)
        subscription = self._encode_obj(url, expiration_datetime(expiration))

        self.client.put_object(
            Bucket=self.bucket,
            Key=self._predicate_url_to_key(predicate_pattern, url),
            Body=BytesIO(subscription),
            ContentLength=len(subscription)
        )
        return True

    def search(self, predicate_pattern, url=None, recursive=False, layered=False):
        """
        predicate pattern parameter is the primary search filter
        technically aaaa.bbbb.cccc.* == aaaa.bbbb.cccc
        This can be used for verbosity

        recursive parameter is used primarily for testing purposes, to check state of the bucket.
        Don't use it unless you want to get results from subdirectories.

        layered parameter will enable search like
        predicate: a.b.c.d
        1. a = files in A/
        2. a.b = files in A/B/
        3. a.b.c = files in A/B/C/
        4. a.b.c.d files in A/B/C/D/

        Note: layered != recursive because it searches only in directories which are in the predicate

        Important: subscription AA.BB.CCCC is not equal to AA.BB.CC but includes
        AA.BB.CCCC.EE, and doesn't include AA.BB.CC.GG
        """
        now = current_datetime()
        if url:
            return self.get(url, predicate_pattern)
        else:
            invalids_list = []
            subscribed_urls = set()
            if layered:
                if recursive:
                    raise ValueError("Can't perform layered recursive search")
                layers = self._pattern_to_layers(predicate_pattern)
            else:
                layers = [self._pattern_to_key(predicate_pattern)]
            for storage_key in layers:
                found_objects = self._search_objects(storage_key, recursive=recursive)
                for found_obj_name in found_objects:
                    obj = self.client.get_object(
                        Bucket=self.bucket,
                        Key=found_obj_name,
                    )
                    data = self._decode_obj(obj, found_obj_name, now, invalids_list)
                    if not data:
                        continue
                    subscribed_urls.add(data[CALLBACK_KEY])
                if invalids_list:
                    self.client.delete_objects(
                        Bucket=self.bucket,
                        Delete={
                            'Objects': [
                                {'Key': key} for key in invalids_list
                            ],
                            'Quiet': True,  # |False
                        },
                    )
            return subscribed_urls

    def delete(self, url, predicate_pattern, recursive=False):
        now = current_datetime()
        deleted = 0
        if url:
            try:
                name = self._predicate_url_to_key(predicate_pattern, url)
                self.client.delete_objects(
                    Bucket=self.bucket,
                    Delete={
                        'Objects': [
                            {'Key': name}
                        ],
                        'Quiet': True,  # |False
                    },
                )
                return 1
            except ClientError as ex:
                if ex.response['Error']['Code'] == 'NoSuchKey':
                    return 0
                else:
                    raise
        else:
            invalids_list = []
            found_objects = self._search_objects(
                self._pattern_to_key(predicate_pattern), recursive=recursive
            )
            for found_obj_name in found_objects:
                obj = self.client.get_object(
                    Bucket=self.bucket,
                    Key=found_obj_name
                )
                data = self._decode_obj(obj, found_obj_name, now, invalids_list)
                if not data:
                    continue
                deleted += 1
                self.client.delete_objects(
                    Bucket=self.bucket,
                    Delete={
                        'Objects': [
                            {'Key': found_obj_name}
                        ],
                        'Quiet': True,  # |False
                    },
                )
            if invalids_list:
                self.client.delete_objects(
                    Bucket=self.bucket,
                    Delete={
                        'Objects': [
                            {'Key': key} for key in invalids_list
                        ],
                        'Quiet': True,  # |False
                    },
                )
        return deleted
