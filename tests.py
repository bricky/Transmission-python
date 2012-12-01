import unittest
import os.path

import transmission as tr

_torrent = os.path.realpath('OpenBSD_songs_mp3-2012-10-15-0236.torrent')


'''
import os.path
import transmission as tr
session = tr.Session('', tr.default_config_dir(), True, tr.default_settings())
ctor = tr.TorrentConstructor(session)
torrent_file = os.path.realpath('OpenBSD_songs_mp3-2012-10-15-0236.torrent')
ctor.set_metainfo_from_file(torrent_file)
ctor.parse()
torrent = session.torrent_new(ctor)
stats = torrent.stats()
stats.start_date
'''

class TestBenc(unittest.TestCase):
    def test_benc_bool_value(self):
        benc = tr.bencode.BencBool(True)
        self.assertEqual(benc.value, True)

    def test_benc_int_value(self):
        benc = tr.bencode.BencInt(7)
        self.assertEqual(benc.value, 7)

    def test_benc_real_value(self):
        benc = tr.bencode.BencReal(3.14)
        self.assertEqual(benc.value, 3.14)

    def test_benc_string_value(self):
        benc = tr.bencode.BencString('foo')
        self.assertEqual(benc.value, 'foo')

    def test_benc_dict_value(self):
        benc = tr.bencode.BencDict(0)
        self.assertIsNone(benc.value)

    def test_benc_dict_add_bool(self):
        benc = tr.bencode.BencDict(1)
        val = benc.add_bool('foo', True)

        self.assertEqual(type(val), tr.bencode.BencBool)
        self.assertEqual(val.value, True)
        self.assertEqual(benc['foo'], True)

    def test_benc_dict_add_int(self):
        benc = tr.bencode.BencDict(1)
        val = benc.add_int('foo', 7)

        self.assertEqual(type(val), tr.bencode.BencInt)
        self.assertEqual(val.value, 7)
        self.assertEqual(benc['foo'], 7)

    def test_benc_dict_add_real(self):
        benc = tr.bencode.BencDict(1)
        val = benc.add_real('foo', 3.14)

        self.assertEqual(type(val), tr.bencode.BencReal)
        self.assertEqual(val.value, 3.14)
        self.assertEqual(benc['foo'], 3.14)

    def test_benc_dict_add_string(self):
        benc = tr.bencode.BencDict(1)
        val = benc.add_string('foo', 'bar')

        self.assertEqual(type(val), tr.bencode.BencString)
        self.assertEqual(val.value, 'bar')
        self.assertEqual(benc['foo'], 'bar')

    def test_benc_dict_add_dict(self):
        benc = tr.bencode.BencDict(1)
        val = benc.add_dict('foo', 1)

        self.assertEqual(type(val), tr.bencode.BencDict)

    def test_benc_dict_add_list(self):
        benc = tr.bencode.BencDict(1)
        val = benc.add_list('foo', 1)

        self.assertEqual(type(val), tr.bencode.BencList)

    def test_benc_dict_indexing(self):
        benc = tr.bencode.BencDict(1)
        for i in range(10):
            benc.add_int('foo%i' % i, i)
            self.assertEqual(benc[i], i)

        self.assertEqual(len(benc), 10)

    def test_benc_list_value(self):
        benc = tr.bencode.BencList(0)
        self.assertIsNone(benc.value)

    def test_benc_list_add_bool(self):
        benc = tr.bencode.BencList(0)
        val = benc.add_bool(True)

        self.assertEqual(type(val), tr.bencode.BencBool)
        self.assertEqual(val.value, True)
        self.assertEqual(benc[0], True)

    def test_benc_list_add_int(self):
        benc = tr.bencode.BencList(1)
        val = benc.add_int(7)

        self.assertEqual(type(val), tr.bencode.BencInt)
        self.assertEqual(val.value, 7)
        self.assertEqual(benc[0], 7)

    def test_benc_list_add_real(self):
        benc = tr.bencode.BencList(1)
        val = benc.add_real(3.14)

        self.assertEqual(type(val), tr.bencode.BencReal)
        self.assertEqual(val.value, 3.14)
        self.assertEqual(benc[0], 3.14)

    def test_benc_list_add_string(self):
        benc = tr.bencode.BencList(1)
        val = benc.add_string('foo')

        self.assertEqual(type(val), tr.bencode.BencString)
        self.assertEqual(val.value, 'foo')
        self.assertEqual(benc[0], 'foo')

    def test_benc_list_add_dict(self):
        benc = tr.bencode.BencList(1)
        val = benc.add_dict(1)

        self.assertEqual(type(val), tr.bencode.BencDict)

        with self.assertRaises(NotImplementedError):
            benc[0] = val

    def test_benc_list_add_list(self):
        benc = tr.bencode.BencList(1)
        val = benc.add_list(1)

        self.assertEqual(type(val), tr.bencode.BencList)

        with self.assertRaises(NotImplementedError):
            benc[0] = val

    def test_benc_list_indexing(self):
        benc = tr.bencode.BencList(1)
        for i in range(10):
            benc.add_int(i)
            self.assertEqual(benc[i], i)

        self.assertEqual(len(benc), 10)

        for i, v in enumerate(benc):
            self.assertEqual(i, v)

    def test_benc_list_assign(self):
        benc = tr.bencode.BencList(1)
        benc.add_int(1)

        benc[0] = 7
        self.assertEqual(benc[0], 7)

        with self.assertRaises(ValueError):
            benc[0] = 'foo'

        with self.assertRaises(NotImplementedError):
            benc[1] = 'foo'


class TestSession(unittest.TestCase):
    def setUp(self):
        self.session = tr.Session('', tr.default_config_dir(), True, tr.default_settings())

    def test_session_active_speed_limit(self):
        self.assertEqual(self.session.active_speed_limit_up, -1)
        self.assertEqual(self.session.active_speed_limit_down, -1)

    def test_session_alt_speed(self):
        self.assertEqual(self.session.alt_speed_up, 50)
        self.assertEqual(self.session.alt_speed_down, 50)

        self.session.alt_speed_up = 100
        self.session.alt_speed_down = 100
        self.assertEqual(self.session.alt_speed_up, 100)
        self.assertEqual(self.session.alt_speed_down, 100)

    def test_session_alt_speed_begin(self):
        self.assertEqual(self.session.alt_speed_begin, 540)

    def test_session_alt_speed_end(self):
        self.assertEqual(self.session.alt_speed_end, 1020)

    def test_session_alt_speed_day(self):
        self.assertEqual(self.session.alt_speed_day, tr.scheduled_days.ALL)

    def test_session_blocklist(self):
        with open('/tmp/blocklist.txt', 'w') as f:
            f.write("RangeName:8.8.8.1-8.8.8.1\n")
            f.write("RangeName:8.8.8.1-8.8.8.1\n")
            f.write("RangeName:8.8.8.2-8.8.8.2\n")
            f.write("RangeName:8.8.8.10-8.8.8.20\n")
            f.write("foo")

        self.assertEqual(self.session.blocklist_set('/tmp/blocklist.txt'), 3)
        self.assertEqual(self.session.blocklist_rule_count, 3)
        self.assertEqual(self.session.blocklist_exists, True)

        self.assertEqual(self.session.blocklist_set(), 0)
        self.assertEqual(self.session.blocklist_rule_count, 0)

        self.session.blocklist_enabled = True
        self.assertEqual(self.session.blocklist_enabled, True)

        self.session.blocklist_enabled = False
        self.assertEqual(self.session.blocklist_enabled, False)

        self.assertEqual(self.session.blocklist_URL, "http://www.example.com/blocklist")

    def test_session_speed_limit_enabled(self):
        self.assertEqual(self.session.speed_limit_enabled_up, False)
        self.assertEqual(self.session.speed_limit_enabled_down, False)

    def test_session_speed_limit(self):
        self.assertEqual(self.session.speed_limit_up, 100)
        self.assertEqual(self.session.speed_limit_down, 100)

        self.session.speed_limit_up = 50
        self.session.speed_limit_down = 50
        self.assertEqual(self.session.speed_limit_up, 50)
        self.assertEqual(self.session.speed_limit_down, 50)

class TestTorrentConstructor(unittest.TestCase):
    def setUp(self):
        self.session = tr.Session('', tr.default_config_dir(), True, tr.default_settings())
        self.ctor = tr.TorrentConstructor(self.session)

    def tearDown(self):
        del self.ctor

    def test_ctor_bandwidth_priority(self):
        self.assertEqual(self.ctor.bandwidth_priority, tr.priority.NORMAL)

        self.ctor.bandwidth_priority = 10
        self.assertNotEqual(self.ctor.bandwidth_priority, 10)

        self.ctor.bandwidth_priority = tr.priority.LOW
        self.assertEqual(self.ctor.bandwidth_priority, tr.priority.LOW)

        self.ctor.bandwidth_priority = tr.priority.HIGH
        self.assertEqual(self.ctor.bandwidth_priority, tr.priority.HIGH)

    def test_ctor_delete_source(self):
        self.assertEqual(self.ctor.delete_source, False)

        self.ctor.delete_source = True
        self.assertEqual(self.ctor.delete_source, True)

    def test_ctor_download_directory(self):
        self.assertEqual(self.ctor.download_directory, self.session.download_directory)

        self.ctor.download_directory = '/tmp'
        self.assertEqual(self.ctor.download_directory, '/tmp')
        self.assertNotEqual(self.ctor.download_directory, self.session.download_directory)

    def test_ctor_paused(self):
        self.assertEqual(self.ctor.paused, False)

        self.ctor.paused = True
        self.assertEqual(self.ctor.paused, True)

    def test_ctor_peer_limit(self):
        self.assertEqual(self.ctor.peer_limit, 0)

    def test_ctor_metainfo_from_file(self):
        err = self.ctor.set_metainfo_from_file(_torrent)
        self.assertEqual(err, 0)

        metainfo = self.ctor.metainfo()
        
        self.assertEqual(self.ctor.source_file, _torrent)

        self.assertEqual(type(metainfo), tr.bencode.BencDict)
        self.assertEqual(len(metainfo), 6)
        self.assertEqual(metainfo['announce'], 'http://OpenBSD.somedomain.net:6969/announce')
        self.assertEqual(metainfo['created by'], 'mktorrent 1.0')
        self.assertEqual(metainfo['creation date'], 1350268605)
        self.assertEqual(metainfo['url-list'], 'http://openbsd.somedomain.net/pub/')
        self.assertEqual(metainfo['comment'], 'mp3 files from OpenBSD/songs\n'
                                              'Created by andrew fresh (andrew@afresh1.com)\n'
                                              'http://OpenBSD.somedomain.net/')

        self.assertEqual(type(metainfo['info']), tr.bencode.BencDict)
        self.assertEqual(metainfo['info']['name'], 'OpenBSD_songs_mp3')
        self.assertEqual(metainfo['info']['piece length'], 262144)
        with self.assertRaises(UnicodeDecodeError):
            pieces = metainfo['info']['pieces']
            self.assertEqual(pieces, None)

class TestTorrent(unittest.TestCase):
    def setUp(self):
        self.session = tr.Session('', tr.default_config_dir(), True, tr.default_settings())
        self.ctor = tr.TorrentConstructor(self.session)
        self.ctor.set_metainfo_from_file(_torrent)
        self.ctor.parse()
        self.torrent = self.session.torrent_new(self.ctor)

    def test_torrent_type(self):
        self.assertEqual(type(self.torrent), tr.Torrent)

    def test_torrent_current_directory(self):
        self.assertEqual(self.torrent.current_directory, '')


if __name__ == '__main__':
    unittest.main()
