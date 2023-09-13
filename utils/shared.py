"""
MIT License

Copyright (c) 2021 Alexander Bilz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
import io
import sys

from ccl_chrome_indexeddb import ccl_chromium_localstorage, ccl_chromium_sessionstorage, ccl_chromium_indexeddb, ccl_v8_value_deserializer, ccl_blink_value_deserializer

TEAMS_DB_OBJECT_STORES = ['replychains', 'conversations', 'people', 'buddylist']


def parse_db(filepath, do_not_filter=False):
    # Open raw access to a LevelDB and deserialize the records.
    wrapper = ccl_chromium_indexeddb.WrappedIndexDB(filepath)
    blink_deserializer = ccl_blink_value_deserializer.BlinkV8Deserializer()

    def bad_deserializer_data_handler(key: ccl_chromium_indexeddb.IdbKey, buffer: bytes):
        print(f"Error reading IndexedDb record {key}", file=sys.stderr)

    extracted_values = []
    for database_id in wrapper.database_ids:
        database = wrapper[database_id.dbid_no]
        for obj_store_name in database.object_store_names:
            if obj_store_name in TEAMS_DB_OBJECT_STORES or do_not_filter:
                obj_store = database.get_object_store_by_name(obj_store_name)
  
                for rec in obj_store.iterate_records(
                        bad_deserializer_data_handler=bad_deserializer_data_handler):
                        # Initialize deserializer and try deserialization.
                        details =  {'key': rec.key, 'value': rec.value, 'origin_file': database_id.origin,
                                'store': obj_store_name, 'seq': rec.sequence_number}
                        extracted_values.append(details)

    return extracted_values


def parse_localstorage(filepath):
    local_store = ccl_chromium_localstorage.LocalStoreDb(filepath)
    extracted_values = []
    for record in local_store.iter_all_records():
        try:
            extracted_values.append(json.loads(record.value))
        except json.decoder.JSONDecodeError:
            continue
    return extracted_values


def parse_sessionstorage(filepath):
    session_storage = ccl_chromium_sessionstorage.SessionStoreDb(filepath)
    extracted_values = []
    for host in session_storage:
        print(host)
        # Hosts can have multiple sessions associated with them
        for session_store_values in session_storage.get_all_for_host(host).values():
            for session_store_value in session_store_values:
                # response is of type SessionStoreValue
                # Make a nice dictionary out of it
                entry = {'key': host, 'value': session_store_value.value, 'guid': session_store_value.guid,
                         'leveldb_sequence_number': session_store_value.leveldb_sequence_number}
                extracted_values.append(entry)
    return extracted_values


def write_results_to_json(data, outputpath):
    # Dump messages into a json file
    try:
        with open(outputpath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, sort_keys=True, default=str, ensure_ascii=False)
    except EnvironmentError as e:
        print(e)


def parse_json():
    # read data from a file. This is only for testing purpose.
    try:
        with open('teams.json') as json_file:
            data = json.load(json_file)
            return data
    except EnvironmentError as e:
        print(e)
