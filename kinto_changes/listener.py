import hashlib
import six
from uuid import UUID
from pyramid.security import Everyone
from pyramid.settings import aslist
from cliquet.listeners import ListenerBase
from cliquet.storage import exceptions as storage_exceptions


class Listener(ListenerBase):
    def __init__(self, collections, changes_bucket, changes_collection):
        super(Listener, self).__init__()
        self.collections = set(collections)
        self.changes_bucket = changes_bucket
        self.changes_collection = changes_collection

    def __call__(self, event):
        registry = event.request.registry

        bucket = event.payload['bucket_id']
        collection = event.payload['collection_id']
        bucket_uri = '/buckets/%s' % bucket
        collection_uri = u'/buckets/%s/collections/%s' % (bucket,
                                                          collection)

        collections_uris = {bucket_uri, collection_uri}
        is_matching = collections_uris.intersection(self.collections)
        if self.collections and not is_matching:
            return

        bucket_id = '/buckets/%s' % self.changes_bucket
        collection_id = '/buckets/%s/collections/%s' % (
            self.changes_bucket, self.changes_collection)

        try:
            # Make sure the monitor bucket exists
            registry.storage.create(collection_id='bucket',
                                    parent_id='',
                                    record={'id': self.changes_bucket})
        except storage_exceptions.UnicityError:
            pass

        try:
            # Make sure the changes collection exists
            registry.storage.create(collection_id='collection',
                                    parent_id=bucket_id,
                                    record={'id': self.changes_collection})
            registry.permission.add_principal_to_ace(collection_id,
                                                     'read',
                                                     Everyone)
        except storage_exceptions.UnicityError:
            pass

        # Create the new record
        identifier = hashlib.md5(collection_uri.encode('utf-8')).hexdigest()
        record_id = six.text_type(UUID(identifier))
        last_modified = registry.storage.collection_timestamp(
            parent_id=collection_uri, collection_id='record')

        registry.storage.update(
            parent_id=collection_id,
            collection_id='record',
            object_id=record_id,
            record={
                'id': record_id,
                'last_modified': last_modified,
                'host': registry.settings.get('http_host'),
                'bucket': bucket,
                'collection': collection
            })


def load_from_config(config, prefix=''):
    settings = config.get_settings()

    collections = aslist(settings[prefix + 'collections'])

    changes_bucket = settings.get(prefix + 'bucket', 'monitor')
    changes_collection = settings.get(prefix + 'collection', 'changes')

    return Listener(collections, changes_bucket, changes_collection)
