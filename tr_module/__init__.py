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

import os.path

from pybindgen.module import SubModule, MultiSectionFactory

from pybindgen import Module, FileCodeSink, ReturnValue, param, cppclass, typehandlers

from . import typedefs
from . import tr_benc
from . import tr_info
from . import tr_session
from . import tr_torrent

from .memory_policy import (TrFreeFunctionPolicy, BencMemoryPolicy)

class TrMultiSectionFactory(MultiSectionFactory):
    _header = ("/* ** GENERATED CODE -- DO NOT EDIT **\n"
               " *\n"
               " * Copyright (c) 2012 Dan Eicher\n"
               " *\n"
               " * Permission is hereby granted, free of charge, to any person obtaining a\n"
               " * copy of this software and associated documentation files (the \"Software\"),\n"
               " * to deal in the Software without restriction, including without limitation\n"
               " * the rights to use, copy, modify, merge, publish, distribute, sublicense,\n"
               " * and/or sell copies of the Software, and to permit persons to whom the\n"
               " * Software is furnished to do so, subject to the following conditions:\n"
               " *\n"
               " * The above copyright notice and this permission notice shall be included in\n"
               " * all copies or substantial portions of the Software.\n"
               " *\n"
               " * THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
               " * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
               " * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
               " * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
               " * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING\n"
               " * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER\n"
               " * DEALINGS IN THE SOFTWARE.\n"
               " *\n"
               " */\n")

    def __init__(self, main_file_name):
        self.main_file_name = main_file_name
        self.main_sink = FileCodeSink(open('src/'+main_file_name, "wt"))
        self.header_name = "tr_module.h"
        header_file_name = os.path.join(os.path.dirname(self.main_file_name), self.header_name)
        self.header_sink = FileCodeSink(open('src/'+header_file_name, "wt"))
        self.section_sinks = {}

        self.main_sink.writeln(self._header)
        self.header_sink.writeln(self._header)

    def get_section_code_sink(self, section_name):
        if section_name == '__main__':
            return self.main_sink
        try:
            return self.section_sinks[section_name]
        except KeyError:
            file_name = os.path.join(os.path.dirname(self.main_file_name), "src/%s.cc" % section_name)
            sink = FileCodeSink(open(file_name, "wt"))
            self.section_sinks[section_name] = sink
            sink.writeln(self._header)
            return sink

    def get_main_code_sink(self):
        return self.main_sink

    def get_common_header_code_sink(self):
        return self.header_sink

    def get_common_header_include(self):
        return '"%s"' % self.header_name

    def close(self):
        self.header_sink.file.close()
        self.main_sink.file.close()
        for sink in self.section_sinks.itervalues():
            sink.file.close()

def module_init():
    root_module = Module('transmission')
    root_module.add_include('"transmission.h"')
    root_module.add_include('"bencode.h"')
    root_module.add_include('"utils.h"')
    #root_module.add_include('<datetime.h>')

    root_module.before_init.write_code('''/* init some stuff... */
/* PyDateTime_IMPORT; */
tr_formatter_speed_init(1000, "kBps", "MBps", "GBps", "TBps");
tr_formatter_size_init(1024, "kB", "MB", "GB", "TB");
tr_formatter_mem_init(1000, "KiB", "MiB", "GiB", "TiB");
''')

    root_module.header.writeln("/* stupid global variables so the closures don't segfault */\n"
                               "extern tr_direction tr_up;\n"
                               "extern tr_direction tr_down;\n"
                               "extern tr_ctorMode tr_force;\n")

    root_module.body.writeln("tr_direction tr_up = TR_UP;\n"
                             "tr_direction tr_down = TR_DOWN;\n"
                             "tr_ctorMode tr_force = TR_FORCE;\n")

    return root_module


def register_types(module):
    root_module = module.get_root()

    submodule = SubModule('torrent_error_type', parent=root_module)
    submodule.add_enum('tr_stat_errtype',
                       [('OK', 'TR_STAT_OK'),
                        ('TRACKER_WARNING', 'TR_STAT_TRACKER_WARNING'),
                        ('TRACKER_ERROR', 'TR_STAT_TRACKER_ERROR'),
                        ('LOCAL_ERROR', 'TR_STAT_LOCAL_ERROR')])

    submodule = SubModule('torrent_activity', parent=root_module)
    submodule.add_enum('tr_torrent_activity',
                       [('STOPPED', 'TR_STATUS_STOPPED'),
                        ('CHECK_WAIT', 'TR_STATUS_CHECK_WAIT'),
                        ('CHECK', 'TR_STATUS_CHECK'),
                        ('DOWNLOAD_WAIT', 'TR_STATUS_DOWNLOAD_WAIT'),
                        ('DOWNLOAD', 'TR_STATUS_DOWNLOAD'),
                        ('SEED_WAIT', 'TR_STATUS_SEED_WAIT'),
                        ('SEED', 'TR_STATUS_SEED')])

    submodule = SubModule('tracker_state', parent=root_module)
    submodule.add_enum('tr_tracker_state',
                       [('INACTIVE', 'TR_TRACKER_INACTIVE'),
                        ('WAITING', 'TR_TRACKER_WAITING'),
                        ('QUEUED', 'TR_TRACKER_QUEUED'),
                        ('ACTIVE', 'TR_TRACKER_ACTIVE')])

    submodule = SubModule('scheduled_days', parent=root_module)
    submodule.add_enum('tr_sched_day',
                       [('SUN', 'TR_SCHED_SUN'),
                        ('MON', 'TR_SCHED_MON'),
                        ('TUES', 'TR_SCHED_TUES'),
                        ('WED', 'TR_SCHED_WED'),
                        ('THURS', 'TR_SCHED_THURS'),
                        ('FRI', 'TR_SCHED_FRI'),
                        ('SAT', 'TR_SCHED_SAT'),
                        ('WEEKDAY', 'TR_SCHED_WEEKDAY'),
                        ('WEEKEND', 'TR_SCHED_WEEKEND'),
                        ('ALL', 'TR_SCHED_ALL')])

    submodule = SubModule('encryption_mode', parent=root_module)
    submodule.add_enum('tr_encryption_mode',
                       [('CLEAR_PREFERRED', 'TR_CLEAR_PREFERRED'),
                        ('ENCRYPTION_PREFERRED', 'TR_ENCRYPTION_PREFERRED'),
                        ('ENCRYPTION_REQUIRED', 'TR_ENCRYPTION_REQUIRED')])

    submodule = SubModule('direction', parent=root_module)
    submodule.add_enum('tr_direction',
                       [('CLIENT_TO_PEER', 'TR_CLIENT_TO_PEER'),
                        ('UP', 'TR_UP'),
                        ('PEER_TO_CLIENT', 'TR_PEER_TO_CLIENT'),
                        ('DOWN', 'TR_DOWN')])

    submodule = SubModule('ratio_limit', parent=root_module)
    submodule.add_enum('tr_ratiolimit',
                       [('GLOBAL', 'TR_RATIOLIMIT_GLOBAL'),
                        ('SINGLE', 'TR_RATIOLIMIT_SINGLE'),
                        ('UNLIMITED', 'TR_RATIOLIMIT_UNLIMITED')])

    submodule = SubModule('idle_limit', parent=root_module)
    submodule.add_enum('tr_idlelimit',
                          [('GLOBAL', 'TR_IDLELIMIT_GLOBAL'),
                           ('SINGLE', 'TR_IDLELIMIT_SINGLE'),
                           ('UNLIMITED', 'TR_IDLELIMIT_UNLIMITED')])

    submodule = SubModule('preallocation_mode', parent=root_module)
    submodule.add_enum('tr_preallocation_mode',
                       [('NONE', 'TR_PREALLOCATE_NONE'),
                        ('SPARCE', 'TR_PREALLOCATE_SPARSE'),
                        ('FULL', 'TR_PREALLOCATE_FULL')])

    submodule = SubModule('completeness', parent=root_module)
    submodule.add_enum('tr_completeness',
                       [('LEECH', 'TR_LEECH'),
                        ('SEED', 'TR_SEED'),
                        ('PARTIAL_SEED', 'TR_PARTIAL_SEED')])

    submodule = SubModule('rpc_callback_type', parent=root_module)
    submodule.add_enum('tr_rpc_callback_type',
                       [('TORRENT_ADDED', 'TR_RPC_TORRENT_ADDED'),
                        ('TORRENT_STARTED', 'TR_RPC_TORRENT_STARTED'),
                        ('TORRENT_STOPPED', 'TR_RPC_TORRENT_STOPPED'),
                        ('TORRENT_REMOVING', 'TR_RPC_TORRENT_REMOVING'),
                        ('TORRENT_THRASHING', 'TR_RPC_TORRENT_TRASHING'),
                        ('TORRENT_CHANGED', 'TR_RPC_TORRENT_CHANGED'),
                        ('TORRENT_MOVED', 'TR_RPC_TORRENT_MOVED'),
                        ('SESSION_CHANGED', 'TR_RPC_SESSION_CHANGED'),
                        ('SESSION_QUEUE_POSITIONS_CHANGED', 'TR_RPC_SESSION_QUEUE_POSITIONS_CHANGED'),
                        ('SESSION_CLOSE', 'TR_RPC_SESSION_CLOSE')])

    submodule = SubModule('rpc_callback_status', parent=root_module)
    submodule.add_enum('tr_rpc_callback_status',
                       [('OK', 'TR_RPC_OK'),
                        ('NOREMOVE', 'TR_RPC_NOREMOVE')])

    submodule = SubModule('port_forwarding', parent=root_module)
    submodule.add_enum('tr_port_forwarding',
                       [('ERROR','TR_PORT_ERROR'),
                        ('UNMAPPED','TR_PORT_UNMAPPED'),
                        ('UNMAPPING','TR_PORT_UNMAPPING'),
                        ('MAPPING','TR_PORT_MAPPING'),
                        ('MAPPED','TR_PORT_MAPPED')])

    submodule = SubModule('msg_level', parent=root_module)
    submodule.add_enum('tr_msg_level',
                       [('ERROR','TR_MSG_ERR'),
                        ('INF','TR_MSG_INF'),
                        ('DEBUG','TR_MSG_DBG')])

    submodule = SubModule('parse_result', parent=root_module)
    submodule.add_enum('tr_parse_result',
                       [('OK','TR_PARSE_OK'),
                        ('ERROR','TR_PARSE_ERR'),
                        ('DUPLICATE','TR_PARSE_DUPLICATE')])

    submodule = SubModule('torrent_constructor_mode', parent=root_module)
    submodule.add_enum('tr_ctorMode',
                       [('FALLBACK', 'TR_FALLBACK'),
                        ('FORCE', 'TR_FORCE')])

    submodule = SubModule('location_state', parent=root_module)
    submodule.add_enum('',
                       [('MOVING', 'TR_LOC_MOVING'),
                        ('DONE', 'TR_LOC_DONE'),
                        ('ERROR', 'TR_LOC_ERROR')])

    submodule = SubModule('priority', parent=root_module)
    submodule.add_enum('', 
                       [('LOW', 'TR_PRI_LOW'),
                        ('NORMAL', 'TR_PRI_NORMAL'),
                        ('HIGH', 'TR_PRI_HIGH')])

    submodule = SubModule('peers_from_index', parent=root_module)
    submodule.add_enum('',
                       [('INCOMING', 'TR_PEER_FROM_INCOMING'),
                        ('LPD', 'TR_PEER_FROM_LPD'),
                        ('TRACKER', 'TR_PEER_FROM_TRACKER'),
                        ('DHT', 'TR_PEER_FROM_DHT'),
                        ('PEX', 'TR_PEER_FROM_PEX'),
                        ('RESUME', 'TR_PEER_FROM_RESUME'),
                        ('LTEP', 'TR_PEER_FROM_LTEP')])

    submodule = SubModule('benc_serialization_mode', parent=root_module)
    submodule.add_enum('tr_fmt_mode',
                       [('BENC', 'TR_FMT_BENC'),
                        ('JSON', 'TR_FMT_JSON'),
                        ('JSON_LEAN', 'TR_FMT_JSON_LEAN')])

    submodule = SubModule('benc_type', parent=root_module)
    submodule.add_enum('',
                       [('INT', 'TR_TYPE_INT'),
                        ('STRING', 'TR_TYPE_STR'),
                        ('LIST', 'TR_TYPE_LIST'),
                        ('DICT', 'TR_TYPE_DICT'),
                        ('BOOL', 'TR_TYPE_BOOL'),
                        ('REAL', 'TR_TYPE_REAL')])
    ## tr_info.cc
    module.begin_section('tr_info')
    module.add_struct('tr_info',
                      no_constructor=True,
                      no_copy=True,
                      memory_policy=TrFreeFunctionPolicy('tr_metainfoFree'),
                      custom_name='TorrentInfo')

    module.add_struct('tr_file',
                      no_constructor=True,
                      no_copy=True,
                      custom_name='File')

    module.add_struct('tr_piece',
                      no_constructor=True,
                      no_copy=True,
                      custom_name='FilePiece')

    module.add_struct('tr_tracker_info',
                      no_constructor=True,
                      no_copy=True,
                      custom_name='TrackerInfo')

    module.add_struct('tr_tracker_stat',
                      no_constructor=True,
                      no_copy=True,
                      free_function='tr_free',
                      custom_name='TrackerStats')
    module.end_section('tr_info')

    ## tr_torrent.cc
    module.begin_section('tr_torrent')
    torrent = module.add_struct('tr_torrent',
                                no_constructor=True,
                                no_copy=True,
                                memory_policy=TrFreeFunctionPolicy('tr_torrentFree'),
                                custom_name='Torrent')
    #torrent.cannot_be_constructed = "use factory function Session.torrent_new()"

    module.add_struct('tr_ctor',
                      no_constructor=True,
                      no_copy=True,
                      memory_policy=TrFreeFunctionPolicy('tr_ctorFree'),
                      custom_name='TorrentConstructor')

    module.add_struct('tr_stat',
                      no_constructor=True,
                      no_copy=True,
                      memory_policy=TrFreeFunctionPolicy('tr_free'),
                      custom_name='TorrentStats')

    module.add_struct('tr_peer_stat',
                      no_constructor=True,
                      no_copy=True,
                      memory_policy=TrFreeFunctionPolicy('tr_free'),
                      custom_name='PeerStats')

    module.add_struct('tr_file_stat',
                      no_constructor=True,
                      no_copy=True,
                      free_function='tr_free',
                      custom_name='FileStats')
    module.end_section('tr_torrent')

    ## tr_session.cc
    module.begin_section('tr_session')
    module.add_struct('tr_session',
                      no_constructor=True,
                      no_copy=True,
                      memory_policy=TrFreeFunctionPolicy('tr_sessionClose'),
                      custom_name='Session')

    module.add_struct('tr_session_stats',
                      no_constructor=True,
                      no_copy=True,
                      memory_policy=cppclass.FreeFunctionPolicy('tr_free'),
                      custom_name='SessionStats')

    module.add_struct('tr_msg_list',
                      no_constructor=True,
                      no_copy=True,
                      free_function='tr_freeMessageList',
                      custom_name='Message')
    module.end_section('tr_session')

    ## tr_benc.cc
    module.begin_section('tr_benc')
    submodule = SubModule('bencode', parent=root_module)
    benc = submodule.add_struct('Benc',
                                no_constructor=True,
                                no_copy=True,
                                memory_policy=BencMemoryPolicy())
    benc.full_name = 'tr_benc'

    submodule.add_struct('BencInt',
                         parent=benc,
                         no_constructor=True,
                         no_copy=True).full_name = 'tr_benc'

    submodule.add_struct('BencString',
                         parent=benc,
                         no_constructor=True,
                         no_copy=True).full_name = 'tr_benc'

    submodule.add_struct('BencList',
                         parent=benc,
                         no_constructor=True,
                         no_copy=True).full_name = 'tr_benc'

    submodule.add_struct('BencDict',
                         parent=benc,
                         no_constructor=True,
                         no_copy=True).full_name = 'tr_benc'

    submodule.add_struct('BencBool',
                         parent=benc,
                         no_constructor=True,
                         no_copy=True).full_name = 'tr_benc'

    submodule.add_struct('BencReal',
                         parent=benc,
                         no_constructor=True,
                         no_copy=True).full_name = 'tr_benc'
    module.end_section('tr_benc')

    typehandlers.add_type_alias('uint32_t', 'tr_piece_index_t')
    typehandlers.add_type_alias('uint32_t', 'tr_file_index_t')
    typehandlers.add_type_alias('uint32_t*', 'tr_file_index_t*')
    typehandlers.add_type_alias('long int', 'time_t')
    typehandlers.add_type_alias('int8_t', 'tr_priority_t')
    typehandlers.add_type_alias('uint16_t', 'tr_port')

def register_methods(root_module):
    tr_benc.register_methods(root_module)
    tr_info.register_methods(root_module)
    tr_session.register_methods(root_module)
    tr_torrent.register_methods(root_module)

    return

def register_functions(root_module):
    module = root_module

    module.add_function('tr_sessionLoadSettings', 
                        typedefs.ErrorCheckReturn('bool', exception='PyExc_ValueError',
                                                  error_string='"unable to load settings"',
                                                  error_cleanup='Py_DECREF(py_dictionary);\n'),
                        [typedefs.BencOutParam('BencDict *', 'dictionary'),
                         param('char *', 'config_dir', default_value='NULL'),
                         param('char *', 'app_name',
                               default_value='(char*)"Transmission"')],
                        custom_name='user_settings',
                        docstring="Load settings from the configuration directory's settings.json file "
                                  "using Transmission's default settings as fallbacks for missing keys\\n\\n"
                                  "Args:\\n"
                                  "    config_dir (str): configuration directory or None\\n"
                                  "    app_name (str): used to find default configuration directory if "
                                  "config_dir is None\\n"
                                  "Returns:\\n"
                                  "    (BencDict) user settings")

    module.add_function('tr_sessionGetDefaultSettings', 
                        'void',
                        [typedefs.BencOutParam('BencDict *', 'dictionary')],
                        custom_name='default_settings',
                        docstring="Get Transmission's default settings\\n\\n"
                                  "Returns:\\n"
                                  "    (BencDict) default settings")

    module.add_function('tr_getDefaultConfigDir', 
                        'char const *', 
                        [param('char const *', 'app_name', default_value='"Transmission"')],
                        custom_name='default_config_dir',
                        docstring="Get the default configuration directory\\n\\n"
                                  "Returns:\\n"
                                  "    (str) default configuration directory")

    module.add_function('tr_getDefaultDownloadDir', 
                        'char const *', 
                        [],
                        custom_name='default_download_dir',
                        docstring="Get the default download directory\\n\\n"
                                  "Returns:\\n"
                                  "    (str) default download directory")

    module.add_function('tr_getMessageQueuing', 
                        'bool', 
                        [],
                        custom_name='message_queuing_enabled',
                        docstring="Check if message queuing is enabled\\n\\n"
                                  "Returns:\\n"
                                  "    (bool) queuing is enabled")

    module.add_function('tr_setMessageQueuing', 
                        'void', 
                        [param('bool', 'enabled')],
                        custom_name='message_queuing_set',
                        docstring="If enabled logging messages will be queued instead of going to stderr\\n\\n"
                                  "Args:\\n"
                                  "    enabled (bool): turn on/off message queuing\\n")

    module.add_function('tr_getQueuedMessages', 
                        ReturnValue.new('tr_msg_list *',
                                        caller_owns_return=True), 
                        [],
                        custom_name='queued_messages',
                        docstring="Retrieve a list of queued messaged\\n\\n"
                                  "Returns:\\n"
                                  "    (list) logged messages")

    module.add_function('tr_torrentsQueueMoveUp', 
                        'void', 
                        [typedefs.ListParam('Torrent', 'torrents')],
                        custom_name='queue_move_up',
                        docstring="Move Torrents up in download queue\\n\\n"
                                  "Args:\\n"
                                  "    torrents (list): Torrents to move\\n")

    module.add_function('tr_torrentsQueueMoveDown', 
                        'void', 
                        [typedefs.ListParam('Torrent', 'torrents')],
                        custom_name='queue_move_down',
                        docstring="Move Torrents down in download queue\\n\\n"
                                  "Args:\\n"
                                  "    torrents (list): Torrents to move\\n")

    module.add_function('tr_torrentsQueueMoveTop', 
                        'void', 
                        [typedefs.ListParam('Torrent', 'torrents')],
                        custom_name='queue_move_top',
                        docstring="Move Torrents to top of download queue\\n\\n"
                                  "Args:\\n"
                                  "    torrents (list): Torrents to move\\n")

    module.add_function('tr_torrentsQueueMoveBottom', 
                        'void', 
                        [typedefs.ListParam('Torrent', 'torrents')],
                        custom_name='queue_move_bottom',
                        docstring="Move Torrents to bottom of download queue\\n\\n"
                                  "Args:\\n"
                                  "    torrents (list): Torrents to move\\n")

    submodule = SubModule('formatter', parent=module,
                          docstring="Utility functions for setting the unit formatting strings for printing")
    submodule.add_function('tr_formatter_mem_init', 
                           'void', 
                           [param('unsigned int', 'kilo', default_value='1000'),
                            param('const char *', 'kb', default_value='"KiB"'),
                            param('const char *', 'mb', default_value='"MiB"'),
                            param('const char *', 'gb', default_value='"GiB"'),
                            param('const char *', 'tb', default_value='"TiB"')],
                           custom_name='memory_units',
                           docstring="Set the multiplier and formatting strings for memory units\\n\\n"
                                  "Args:\\n"
                                  "    kilo (int): Thousands multiplier\\n"
                                  "    kb (str): Kilobytes string representation\\n"
                                  "    mb (str): Megabytes string representation\\n"
                                  "    gb (str): Gigabytes string representation\\n"
                                  "    tb (str): Terabytes string representation\\n")

    submodule.add_function('tr_formatter_size_init', 
                           'void', 
                           [param('unsigned int', 'kilo'),
                            param('const char *', 'kb'),
                            param('const char *', 'mb'),
                            param('const char *', 'gb'),
                            param('const char *', 'tb')],
                           custom_name='size_units',
                           docstring="Set the multiplier and formatting strings for file size units\\n\\n"
                                  "Args:\\n"
                                  "    kilo (int): Thousands multiplier\\n"
                                  "    kb (str): Kilobytes string representation\\n"
                                  "    mb (str): Megabytes string representation\\n"
                                  "    gb (str): Gigabytes string representation\\n"
                                  "    tb (str): Terabytes string representation\\n")

    submodule.add_function('tr_formatter_speed_init', 
                           'void', 
                           [param('unsigned int', 'kilo'),
                            param('const char *', 'kb'),
                            param('const char *', 'mb'),
                            param('const char *', 'gb'),
                            param('const char *', 'tb')],
                           custom_name='speed_units',
                           docstring="Set the multiplier and formatting strings for network speed units\\n\\n"
                                  "Args:\\n"
                                  "    kilo (int): Thousands multiplier\\n"
                                  "    kb (str): Kilobytes string representation\\n"
                                  "    mb (str): Megabytes string representation\\n"
                                  "    gb (str): Gigabytes string representation\\n"
                                  "    tb (str): Terabytes string representation\\n")
    return

