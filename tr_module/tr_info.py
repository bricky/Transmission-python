##
## Copyright (c) 2012 Dan Eicher
##
## Permission is hereby granted, free of charge, to any person obtaining a
## copy of this software and associated documentation files (the "Software"),
## to deal in the Software without restriction, including without limitation
## the rights to use, copy, modify, merge, publish, distribute, sublicense,
## and/or sell copies of the Software, and to permit persons to whom the
## Software is furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
## FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
## DEALINGS IN THE SOFTWARE.
##

from pybindgen import ReturnValue

SHA_DIGEST_LENGTH = 20

def register_methods(root_module):
    register_Tr_info_methods(root_module, root_module['tr_info'])
    register_Tr_file_methods(root_module, root_module['tr_file'])
    register_Tr_piece_methods(root_module, root_module['tr_piece'])
    register_Tr_tracker_info_methods(root_module, root_module['tr_tracker_info'])
    register_Tr_tracker_stat_methods(root_module, root_module['tr_tracker_stat'])

def register_Tr_info_methods(root_module, cls):
    cls.add_instance_attribute('comment', 'char *', is_const=True)
    cls.add_instance_attribute('creator', 'char *', is_const=True)
    cls.add_instance_attribute('dateCreated', 'time_t', is_const=True,
                               custom_name='date_created')
    cls.add_instance_attribute('fileCount', 'tr_file_index_t', is_const=True,
                               custom_name='file_count')
    cls.add_instance_attribute('files',
                               ReturnValue.new('tr_file **', 
                                               array_length="self->obj->fileCount",
                                               caller_owns_return=False),
                               is_const=True)
    cls.add_instance_attribute('hash',
                               ReturnValue.new('uint8_t *',
                                               is_const=True,
                                               array_length=SHA_DIGEST_LENGTH),
                               is_const=True)
    cls.add_instance_attribute('hashString', 'char *', is_const=True,
                               custom_name='hash_string')
    cls.add_instance_attribute('isMultifile', 'bool', is_const=True,
                               custom_name='multifile')
    cls.add_instance_attribute('isPrivate', 'bool', is_const=True,
                               custom_name='private')
    cls.add_instance_attribute('name', 'char *', is_const=True)
    cls.add_instance_attribute('pieceCount', 'tr_piece_index_t', is_const=True,
                               custom_name='piece_count')
    cls.add_instance_attribute('pieceSize', 'uint32_t', is_const=True,
                               custom_name='piece_size')
    cls.add_instance_attribute('pieces',
                               ReturnValue.new('tr_piece **',
                                               array_length="self->obj->pieceCount",
                                               caller_owns_return=False),
                               is_const=True)
    cls.add_instance_attribute('torrent', 'char *', is_const=True)
    cls.add_instance_attribute('totalSize', 'uint64_t', is_const=True,
                               custom_name='total_size')
    cls.add_instance_attribute('trackerCount', 'int', is_const=True,
                               custom_name='tracker_count')
    cls.add_instance_attribute('trackers',
                               ReturnValue.new('tr_tracker_info **',
                                               array_length="self->obj->trackerCount",
                                               caller_owns_return=False),
                               is_const=True)
    cls.add_instance_attribute('webseedCount', 'int', is_const=True,
                               custom_name='webseed_count')
    cls.add_instance_attribute('webseeds',
                               ReturnValue.new('char **',  array_length="self->obj->webseedCount"),
                               is_const=True)
    return

def register_Tr_file_methods(root_module, cls):
    cls.add_instance_attribute('dnd', 'bool', is_const=True, custom_name='do_not_download')
    cls.add_instance_attribute('firstPiece', 'tr_piece_index_t', is_const=True, custom_name='first_piece')
    cls.add_instance_attribute('lastPiece', 'tr_piece_index_t', is_const=True, custom_name='last_piece')
    cls.add_instance_attribute('length', 'uint64_t', is_const=True)
    cls.add_instance_attribute('name', 'char *', is_const=True)
    cls.add_instance_attribute('offset', 'uint64_t', is_const=True)
    cls.add_instance_attribute('priority', 'int8_t', is_const=True)
    return

def register_Tr_piece_methods(root_module, cls):
    cls.add_instance_attribute('timeChecked', 'time_t', is_const=True, custom_name='time_checked')
    cls.add_instance_attribute('hash',
                               ReturnValue.new('uint8_t *', array_length=SHA_DIGEST_LENGTH),
                               is_const=True)
    cls.add_instance_attribute('priority', 'int8_t', is_const=True)
    cls.add_instance_attribute('dnd', 'bool', is_const=True, custom_name='do_not_download')
    return

def register_Tr_tracker_info_methods(root_module, cls):
    cls.add_instance_attribute('announce', 'char *', is_const=True)
    cls.add_instance_attribute('id', 'uint32_t', is_const=True)
    cls.add_instance_attribute('scrape', 'char *', is_const=True)
    cls.add_instance_attribute('tier', 'int', is_const=True)
    return

def register_Tr_tracker_stat_methods(root_module, cls):
    cls.add_instance_attribute('announce', 'char *', is_const=True)
    cls.add_instance_attribute('announceState', 'tr_tracker_state', is_const=True,
                               custom_name='announce_state')
    cls.add_instance_attribute('downloadCount', 'int', is_const=True,
                               custom_name='download_count')
    cls.add_instance_attribute('hasAnnounced', 'bool', is_const=True,
                               custom_name='has_announced')
    cls.add_instance_attribute('hasScraped', 'bool', is_const=True,
                               custom_name='has_scraped')
    cls.add_instance_attribute('host', 'char *', is_const=True)
    cls.add_instance_attribute('id', 'uint32_t', is_const=True)
    cls.add_instance_attribute('isBackup', 'bool', is_const=True,
                               custom_name='is_backup')
    cls.add_instance_attribute('lastAnnouncePeerCount', 'int', is_const=True,
                               custom_name='last_announce_peer_count')
    cls.add_instance_attribute('lastAnnounceResult', 'char *', is_const=True,
                               custom_name='last_announce_result')
    cls.add_instance_attribute('lastAnnounceStartTime', 'time_t', is_const=True,
                               custom_name='last_announce_start_time')
    cls.add_instance_attribute('lastAnnounceSucceeded', 'bool', is_const=True,
                               custom_name='last_announce_succeeded')
    cls.add_instance_attribute('lastAnnounceTime', 'time_t', is_const=True,
                               custom_name='last_announce_time')
    cls.add_instance_attribute('lastAnnounceTimedOut', 'bool', is_const=True,
                               custom_name='last_announce_timed_out')
    cls.add_instance_attribute('lastScrapeResult', 'char *', is_const=True,
                               custom_name='last_scrape_result')
    cls.add_instance_attribute('lastScrapeStartTime', 'time_t', is_const=True,
                               custom_name='last_scrape_Start_time')
    cls.add_instance_attribute('lastScrapeSucceeded', 'bool', is_const=True,
                               custom_name='last_scrape_succeeded')
    cls.add_instance_attribute('lastScrapeTime', 'time_t', is_const=True,
                               custom_name='last_scrape_time')
    cls.add_instance_attribute('lastScrapeTimedOut', 'bool', is_const=True,
                               custom_name='last_scrape_timed_out')
    cls.add_instance_attribute('leecherCount', 'int', is_const=True,
                               custom_name='leecher_count')
    cls.add_instance_attribute('nextAnnounceTime', 'time_t', is_const=True,
                               custom_name='next_announce_time')
    cls.add_instance_attribute('nextScrapeTime', 'time_t', is_const=True,
                               custom_name='next_scrape_time')
    cls.add_instance_attribute('scrape', 'char *', is_const=True)
    cls.add_instance_attribute('scrapeState', 'tr_tracker_state', is_const=True,
                               custom_name='scrape_state')
    cls.add_instance_attribute('seederCount', 'int', is_const=True,
                               custom_name='seeder_count')
    cls.add_instance_attribute('tier', 'int', is_const=True)
    return


