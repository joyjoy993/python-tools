#!/usr/bin/python
# -*- coding: UTF-8 -*-
from pymongo import *
import datetime
import logging

# MONGO_ADDRESS = {
#     'address1': 'localhost',
#     'address2': 'localhost'
# }
# MONGO_USER = {
#     'user1': 'username1',
#     'user2': 'username2'
# }
# MONGO_PWD = {
#     'password1': 'password1',
#     'password2': 'password2'
# }
# MONGO_PORT = 27017
# MONGO_BULK_INSERT_THRESHOLD = 1000


class Mongo:

    def __init__(self, db_address, database):
        try:
            self.client = MongoClient(MONGO_ADDRESS[db_type], MONGO_PORT, w=1)
            self.client[database].authenticate(MONGO_USER[database],
                                            MONGO_PWD[database],
                                            mechanism='SCRAM-SHA-1')
        except:
            logging.exception('when getting mongodb instance')
        self.db = self.client[database]
        self.bulk_insert_buffer = {}

    def __del__(self):
        self.clean_buffer()

    def get_update_operation(self, operation):
        return {
            '$set': operation,
            '$push': {
                '_changes': {
                    'date': datetime.datetime.utcnow(),
                    'author': AUTHOR,
                    'action': 'update',
                    'data': '$set: %s' % operation
                }
            }
        }

    def check_limit(self, collection):
        return len(self.bulk_insert_buffer[collection]) >= MONGO_BULK_INSERT_THRESHOLD

    def clean_buffer(self):
        for collection in self.bulk_insert_buffer:
            self.insert_many(collection, self.bulk_insert_buffer[collection])
            self.bulk_insert_buffer[collection] = []

    def insert(self, collection, data):
        if collection not in self.bulk_insert_buffer:
            self.bulk_insert_buffer[collection] = []
        if self.check_limit(collection):
            self.insert_many(collection, self.bulk_insert_buffer[collection])
            self.bulk_insert_buffer[collection] = []
        self.bulk_insert_buffer[collection].append(self.get_update_operation(data))

    def query(self, collection, condition, projection_condition=None):
        try:
            return self.db[collection].find(condition, projection_condition)
        except:
            logging.exception('when querying mongodb')

    def query_with_distinct_large_set(self, collection, condition, distinct_key):
        try:
            pipeline = [
                {"$group": {"_id": "$"+distinct_key}}
            ]
            return list(self.db[collection].aggregate(pipeline, allowDiskUse=True))
        except:
            logging.exception('when querying mongodb with distinct large set')
            
    def query_with_distinct(self, collection, condition, distinct_key):
        try:
            return self.query(collection, condition).distinct(distinct_key)
        except:
            logging.exception('when querying mongodb with distinct')

    def update_many(self, collection, query_condition, update_condition):
        return self.db[collection].update_many(query_condition, update_condition)

    def update_one(self, collection, query_condition, update_condition):
        return self.db[collection].update_one(query_condition, self.get_update_operation(update_condition))

    def insert_one(self, collection, data):
        return self.db[collection].insert_one(self.get_update_operation(data))

    def insert_many(self, collection, data):
        if len(data) != 0:
            return self.db[collection].insert_many(data)

    def delete_many(self, collection, delete_condition):
        return self.db[collection].delete_many(delete_condition)

    def delete_one(self, collection, delete_condition):
        return self.db[collection].delete_one(delete_condition)
        