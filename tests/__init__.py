# -*- coding: utf-8 -*-
import os
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

from kinto import main as kinto_main
from kinto.core.testing import get_user_headers, BaseWebTest as CoreWebTest


here = os.path.abspath(os.path.dirname(__file__))


class BaseWebTest(CoreWebTest):
    api_prefix = "v1"
    entry_point = kinto_main
    config = 'config.ini'

    def __init__(self, *args, **kwargs):
        super(BaseWebTest, self).__init__(*args, **kwargs)
        self.headers.update(get_user_headers('mat'))
        self.headers.update({'Origin': 'http://localhost:9999'})

    def get_app_settings(self, extras=None):
        ini_path = os.path.join(here, self.config)
        config = configparser.ConfigParser()
        config.read(ini_path)
        settings = dict(config.items('app:main'))
        return settings

    def setUp(self):
        super(BaseWebTest, self).setUp()
        self.create_collection('blocklists', 'certificates')

    def create_collection(self, bucket_id, collection_id):
        bucket_uri = '/buckets/%s' % bucket_id
        self.app.put_json(bucket_uri,
                          {},
                          headers=self.headers)
        collection_uri = bucket_uri + '/collections/%s' % collection_id
        self.app.put_json(collection_uri,
                          {},
                          headers=self.headers)

    def get_record_uri(self, bucket_id, collection_id, record_id):
        return ('/buckets/{bucket_id}/collections/{collection_id}'
                '/records/{record_id}').format(**locals())
