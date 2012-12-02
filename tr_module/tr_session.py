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

from pybindgen import ReturnValue, param, retval

from .typedefs import (BencOutParam, CountParam, TorrentErrorParam)

def register_methods(root_module):
    register_Tr_session_methods(root_module, root_module['tr_session'])
    register_Tr_session_stats_methods(root_module, root_module['tr_session_stats'])
    register_Tr_msg_list_methods(root_module, root_module['tr_msg_list'])

def register_Tr_session_methods(root_module, cls):
    cls.docstring = ('Class that manages the Transmission session\\n'
                     '\\n'
                     'Args:\\n'
                     '    tag (str): \'gtk\', \'macosx\', \'daemon\', etc...\\n'
                     '               this is only for pre-1.30 resume files\\n'
                     '    config_dir (str): directory for configuration files\\n'
                     '    message_queueing (bool): if True, messages will be queued\\n'
                     '    settings (BencDict): session settings')

    con = cls.add_function_as_constructor("tr_sessionInit",
                                          ReturnValue.new("tr_session *", caller_owns_return=True),
                                          [param('const char *', 'tag'),
                                           param('const char *', 'config_dir'),
                                           param('bool', 'message_queueing'),
                                           param('BencDict *', 'settings', transfer_ownership=False)])

    root_module.header.writeln("double _wrap_tr_sessionGetActiveSpeedLimit(const tr_session *session,\n"
                               "                                           tr_direction dir);")
    root_module.body.writeln("double _wrap_tr_sessionGetActiveSpeedLimit(const tr_session *session,\n"
                             "                                           tr_direction dir)\n"
                             "{\n"
                             "    double speed;\n"
                             "    if (tr_sessionGetActiveSpeedLimit_KBps(session, dir, &speed))\n"
                             "        return speed;\n"
                             "    return -1;\n"
                             "}")

    cls.add_instance_attribute('active_speed_limit_up', 'double',
                               is_const=True,
                               is_pure_c=True,
                               getter='_wrap_tr_sessionGetActiveSpeedLimit',
                               closure='&tr_up', closure_cast='*(tr_direction*)',
                               docstring="Get the active upload speed limit")

    cls.add_instance_attribute('active_speed_limit_down', 'double',
                               is_const=True,
                               is_pure_c=True,
                               getter='_wrap_tr_sessionGetActiveSpeedLimit',
                               closure='&tr_down', closure_cast='*(tr_direction*)',
                               docstring="Get the active download speed limit")

    cls.add_instance_attribute('alt_speed_up', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetAltSpeed_KBps',
                               setter='tr_sessionSetAltSpeed_KBps',
                               closure='&tr_up', closure_cast='*(tr_direction*)',
                               docstring="Get/set the upload alternate speed limit")

    cls.add_instance_attribute('alt_speed_down', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetAltSpeed_KBps',
                               setter='tr_sessionSetAltSpeed_KBps',
                               closure='&tr_down', closure_cast='*(tr_direction*)',
                               docstring="Get/set the download alternate speed limit")

    cls.add_instance_attribute('alt_speed_begin', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetAltSpeedBegin',
                               setter='tr_sessionSetAltSpeedBegin',
                               docstring="Get/set the time (in minutes since midnight) to begin the alt speed")

    cls.add_instance_attribute('alt_speed_end', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetAltSpeedEnd',
                               setter='tr_sessionSetAltSpeedEnd',
                               docstring="Get/set the time (in minutes since midnight) to end the alt speed")

    cls.add_instance_attribute('alt_speed_day', 'tr_sched_day',
                               is_pure_c=True,
                               getter='tr_sessionGetAltSpeedDay',
                               setter='tr_sessionSetAltSpeedDay',
                               docstring="Get/set the alt speed transmission.scheduled_days")

    cls.add_instance_attribute('blocklist_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_blocklistIsEnabled',
                               setter='tr_blocklistSetEnabled',
                               docstring="Get/set whether or not to use the peer blocklist")

    cls.add_instance_attribute('blocklist_exists', 'bool',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_blocklistExists',
                               docstring="Check if the blocklist exists")

    cls.add_instance_attribute('blocklist_rule_count', 'int',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_blocklistGetRuleCount',
                               docstring="Get/set the number of rules in the blocklist")

    cls.add_instance_attribute('blocklist_URL', 'char const *',
                               is_pure_c=True,
                               getter='tr_blocklistGetURL',
                               setter='tr_blocklistSetURL',
                               docstring="Get/set the blocklist URL")

    cls.add_instance_attribute('cache_limit', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetCacheLimit_MB',
                               setter='tr_sessionSetCacheLimit_MB',
                               docstring="Get/set the cache limit in MB")

    cls.add_instance_attribute('config_directory', 'char const *',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_sessionGetConfigDir',
                               docstring="Get the directory used for configuration files")

    root_module.header.writeln("tr_session_stats *_wrap_tr_sessionGetCumulativeStats(const tr_session * session);")
    root_module.body.writeln("tr_session_stats *_wrap_tr_sessionGetCumulativeStats(const tr_session * session)\n"
                             "{\n"
                             "    tr_session_stats *stats = tr_new0(tr_session_stats, 1);\n"
                             "    tr_sessionGetCumulativeStats(session, stats);\n"
                             "    return stats;\n"
                             "}")

    cls.add_instance_attribute('cumulative_stats', 
                               ReturnValue.new("tr_session_stats *", caller_owns_return=True),
                               is_pure_c=True,
                               is_const=True,
                               getter='_wrap_tr_sessionGetCumulativeStats',
                               docstring="Get the total (cumulative) session stats")

    cls.add_instance_attribute('delete_source', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionGetDeleteSource',
                               setter='tr_sessionSetDeleteSource',
                               docstring="")

    cls.add_instance_attribute('download_directory', 'char const *',
                               is_pure_c=True,
                               getter='tr_sessionGetDownloadDir',
                               setter='tr_sessionSetDownloadDir',
                               docstring="Get/set the download directory")

    cls.add_instance_attribute('download_directory_free_space', 'int64_t',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_sessionGetDownloadDirFreeSpace',
                               docstring="Get the download directory free space")

    cls.add_instance_attribute('encryption_mode', 'tr_encryption_mode',
                               is_pure_c=True,
                               getter='tr_sessionGetEncryption',
                               setter='tr_sessionSetEncryption',
                               docstring="Get/set the session transmission.encryption_mode")

    cls.add_instance_attribute('idle_limit', 'uint16_t',
                               is_pure_c=True,
                               getter='tr_sessionGetIdleLimit',
                               setter='tr_sessionSetIdleLimit',
                               docstring="Get/set the torrent idle limit in minutes")

    cls.add_instance_attribute('incomplete_directory', 'char const *',
                               is_pure_c=True,
                               getter='tr_sessionGetIncompleteDir',
                               setter='tr_sessionSetIncompleteDir',
                               docstring="Get/set the directory for incomplete torrents")

    cls.add_instance_attribute('paused', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionGetPaused',
                               setter='tr_sessionSetPaused',
                               docstring="Pause/unpause the session")

    cls.add_instance_attribute('peer_limit', 'uint16_t',
                               is_pure_c=True,
                               getter='tr_sessionGetPeerLimit',
                               setter='tr_sessionSetPeerLimit',
                               docstring="Get/set the peer limit per session")

    cls.add_instance_attribute('peer_limit_per_torrent', 'uint16_t',
                               is_pure_c=True,
                               getter='tr_sessionGetPeerLimitPerTorrent',
                               setter='tr_sessionSetPeerLimitPerTorrent',
                               docstring="Get/set the peer limit per torrent")

    cls.add_instance_attribute('peer_port', 'tr_port',
                               is_pure_c=True,
                               getter='tr_sessionGetPeerPort',
                               setter='tr_sessionSetPeerPort',
                               docstring="Get/set the peer port")

    cls.add_instance_attribute('peer_port_random_on_start', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionGetPeerPortRandomOnStart',
                               setter='tr_sessionSetPeerPortRandomOnStart',
                               docstring="Get/set whether or not to use a random peer port on start")

    cls.add_instance_attribute('port_forwarding', 'tr_port_forwarding',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_sessionGetPortForwarding',
                               docstring="Get the session transmission.port_forwarding value")

    cls.add_instance_attribute('queue_enabled_up', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionGetQueueEnabled',
                               setter='tr_sessionSetQueueEnabled',
                               closure='&tr_up', closure_cast='*(tr_direction*)',
                               docstring="Get/set whether or not to limit how many torrents can upload")

    cls.add_instance_attribute('queue_enabled_down', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionGetQueueEnabled',
                               setter='tr_sessionSetQueueEnabled',
                               closure='&tr_down', closure_cast='*(tr_direction*)',
                               docstring="Get/set whether or not to limit how many torrents can download")

    cls.add_instance_attribute('queue_size_up', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetQueueSize',
                               setter='tr_sessionSetQueueSize',
                               closure='&tr_up', closure_cast='*(tr_direction*)',
                               docstring="Get/set the number of torrents allowed to upload")

    cls.add_instance_attribute('queue_size_down', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetQueueSize',
                               setter='tr_sessionSetQueueSize',
                               closure='&tr_down', closure_cast='*(tr_direction*)',
                               docstring="Get/set the number of torrents allowed to download")

    cls.add_instance_attribute('queue_stalled_minutes', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetQueueStalledMinutes',
                               setter='tr_sessionSetQueueStalledMinutes',
                               docstring="Set whether or not to count torrents idle for over N minutes as `stalled\'")

    cls.add_instance_attribute('queue_stalled_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionGetQueueStalledEnabled',
                               setter='tr_sessionSetQueueStalledEnabled')

    cls.add_instance_attribute('RPC_bind_address', 'char const *',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_sessionGetRPCBindAddress',
                               docstring="Get/set RPC bind address")

    cls.add_instance_attribute('RPC_password', 'char const *',
                               is_pure_c=True,
                               getter='tr_sessionGetRPCPassword',
                               setter='tr_sessionSetRPCPassword',
                               docstring="Get/set RPC password")

    cls.add_instance_attribute('RPC_port', 'tr_port',
                               is_pure_c=True,
                               getter='tr_sessionGetRPCPort',
                               setter='tr_sessionSetRPCPort',
                               docstring="Get/set RPC port")

    cls.add_instance_attribute('RPC_url', 'char const *',
                               is_pure_c=True,
                               getter='tr_sessionGetRPCUrl',
                               setter='tr_sessionSetRPCUrl',
                               docstring="Get/set RPC URL")

    cls.add_instance_attribute('RPC_username', 'char const *',
                               is_pure_c=True,
                               getter='tr_sessionGetRPCUsername',
                               setter='tr_sessionSetRPCUsername',
                               docstring="Get/set RPC username")

    cls.add_instance_attribute('RPC_whitelist', 'char const *',
                               is_pure_c=True,
                               getter='tr_sessionGetRPCWhitelist',
                               setter='tr_sessionSetRPCWhitelist',
                               docstring="Get/set RPC Access Control List filename")

    cls.add_instance_attribute('RPC_whitelist_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionGetRPCWhitelistEnabled',
                               setter='tr_sessionSetRPCWhitelistEnabled',
                               docstring="Get/set if session uses the RPC whitelist for allowing/denying RPC requests")

    cls.add_instance_attribute('ratio_limit', 'double',
                               is_pure_c=True,
                               getter='tr_sessionGetRatioLimit',
                               setter='tr_sessionSetRatioLimit',
                               docstring="Get/set the session ratio limit")

    cls.add_instance_attribute('raw_speed_up', 'double',
                               is_pure_c=True,
                               is_const=True,
                               getter='tr_sessionGetRawSpeed_KBps',
                               closure='&tr_up', closure_cast='*(tr_direction*)',
                               docstring="Get the raw upload speed limit in KBps")

    cls.add_instance_attribute('raw_speed_down', 'double',
                               is_pure_c=True,
                               is_const=True,
                               getter='tr_sessionGetRawSpeed_KBps',
                               closure='&tr_up', closure_cast='*(tr_direction*)',
                               docstring="Get the raw download speed limit in KBps")

    cls.add_instance_attribute('speed_limit_up', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetSpeedLimit_KBps',
                               setter='tr_sessionSetSpeedLimit_KBps',
                               closure='&tr_up', closure_cast='*(tr_direction*)',
                               docstring="Get/set the upload speed limit in KBps")

    cls.add_instance_attribute('speed_limit_down', 'int',
                               is_pure_c=True,
                               getter='tr_sessionGetSpeedLimit_KBps',
                               setter='tr_sessionSetSpeedLimit_KBps',
                               closure='&tr_down', closure_cast='*(tr_direction*)',
                               docstring="Get/set the download speed limit in KBps")

    root_module.header.writeln("tr_session_stats *_wrap_tr_sessionGetStats(const tr_session * session);")
    root_module.body.writeln("tr_session_stats *_wrap_tr_sessionGetStats(const tr_session * session)\n"
                             "{\n"
                             "    tr_session_stats *stats = tr_new0(tr_session_stats, 1);\n"
                             "    tr_sessionGetStats(session, stats);\n"
                             "    return stats;\n"
                             "}")

    cls.add_instance_attribute('stats',
                               ReturnValue.new("tr_session_stats *", caller_owns_return=True),
                               is_const=True,
                               is_pure_c=True,
                               getter='_wrap_tr_sessionGetStats',
                               docstring="Get session stats")

    cls.add_instance_attribute('torrent_done_script', 'char const *',
                               is_pure_c=True,
                               getter='tr_sessionGetTorrentDoneScript',
                               setter='tr_sessionSetTorrentDoneScript',
                               docstring="Get/set filename of script to be called on torrent completion")

    cls.add_instance_attribute('DHT_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsDHTEnabled',
                               setter='tr_sessionSetDHTEnabled',
                               docstring="Check/set if session uses DHT")

    cls.add_instance_attribute('idle_limited_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsIdleLimited',
                               setter='tr_sessionSetIdleLimited',
                               docstring="Check/set if session suspends torrent if idle limit is exceded")

    cls.add_instance_attribute('incomplete_directory_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsIncompleteDirEnabled',
                               setter='tr_sessionSetIncompleteDirEnabled',
                               docstring="Check/set if session uses incomplete directory until download is complete")

    cls.add_instance_attribute('incomplete_file_naming_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsIncompleteFileNamingEnabled',
                               setter='tr_sessionSetIncompleteFileNamingEnabled',
                               docstring="Check/set if session appends `.part\' to files until download is complete")

    cls.add_instance_attribute('LPD_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsLPDEnabled',
                               setter='tr_sessionSetLPDEnabled',
                               docstring="Check/set if session uses LPD")

    cls.add_instance_attribute('pex_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsPexEnabled',
                               setter='tr_sessionSetPexEnabled',
                               docstring="Check/set if session uses Pex")

    cls.add_instance_attribute('port_forwarding_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsPortForwardingEnabled',
                               setter='tr_sessionSetPortForwardingEnabled',
                               docstring="Check/set if session uses port forwarding")

    cls.add_instance_attribute('RPC_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsRPCEnabled',
                               setter='tr_sessionSetRPCEnabled',
                               docstring="Check/set if session uses RPC server")

    cls.add_instance_attribute('RPC_password_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsRPCPasswordEnabled',
                               setter='tr_sessionSetRPCPasswordEnabled',
                               docstring="Check/set if RPC server requires password")

    cls.add_instance_attribute('ratio_limit_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsRatioLimited',
                               setter='tr_sessionSetRatioLimited',
                               docstring="Check/set if session is ratio limited")

    cls.add_instance_attribute('speed_limit_enabled_up', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsSpeedLimited',
                               setter='tr_sessionLimitSpeed',
                               closure='&tr_up', closure_cast='*(tr_direction*)',
                               docstring="Check/set if session limits upload speed")

    cls.add_instance_attribute('speed_limit_enabled_down', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsSpeedLimited',
                               setter='tr_sessionLimitSpeed',
                               closure='&tr_down', closure_cast='*(tr_direction*)',
                               docstring="Check/set if session limits download speed")

    cls.add_instance_attribute('torrent_done_script_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsTorrentDoneScriptEnabled',
                               setter='tr_sessionSetTorrentDoneScriptEnabled',
                               docstring="Check/set if session uses calls Session.torrent_done_script")

    cls.add_instance_attribute('UTP_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionIsUTPEnabled',
                               setter='tr_sessionSetUTPEnabled',
                               docstring="Check/set if session uses UTP")

    cls.add_instance_attribute('alt_speed_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionUsesAltSpeed',
                               setter='tr_sessionUseAltSpeed',
                               docstring="Check/set if session uses alt speed")

    cls.add_instance_attribute('alt_speed_time_enabled', 'bool',
                               is_pure_c=True,
                               getter='tr_sessionUsesAltSpeedTime',
                               setter='tr_sessionUseAltSpeedTime',
                               docstring="Check/set if session uses alt speed time")

    cls.add_function_as_method('tr_sessionReloadBlocklists',
                               'void',
                               [param('tr_session *', 'session', transfer_ownership=False)],
                               custom_name='blocklists_reload',
                               docstring="Reload blocklists")

    cls.add_function_as_method('tr_blocklistSetContent', 
                               'int', 
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('char const *', 'filename', default_value='NULL')],
                               custom_name='blocklist_set',
                              docstring="Set blocklist content\\n\\n"
                                        "Args:\\n"
                                        "    filename (str): blocklist filename or nothing to clear\\n"
                                        "Returns:\\n"
                                        "    number of entries added")

    cls.add_function_as_method('tr_sessionClearStats', 
                               'void', 
                               [param('tr_session *', 'session', transfer_ownership=False)],
                               custom_name='stats_clear',
                               docstring="Clear session stats")

    cls.add_function_as_method('tr_sessionSetPeerPortRandom', 
                               'tr_port', 
                               [param('tr_session *', 'session',
                                              transfer_ownership=False)],
                               custom_name='peer_port_set_random',
                               docstring="Set incoming peer port to a random port\\n\\n"
                                         "Returns:\\n"
                                         "    the port number")

    root_module.header.writeln("""void _wrap_alt_speed_callback(tr_session *session, bool active, bool userDriven, void *data);""")
    root_module.body.writeln("""
void _wrap_alt_speed_callback(tr_session *session, bool active, bool userDriven, void *data)
{
    PyObject *callback = (PyObject*) data;

    PyTr_session *py_session = PyObject_New(PyTr_session, &PyTr_session_Type);
    py_session->obj = session;
    py_session->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;

    PyObject_CallFunction(callback, (char*)"Obb", (PyObject*)py_session, active, userDriven);

    Py_DECREF(py_session);
}
""")

    cls.add_function_as_method('tr_sessionSetAltSpeedFunc', 
                               'void', 
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('tr_altSpeedFunc *', 'callback',
                                      callback_func="_wrap_alt_speed_callback")],
                               custom_name='alt_speed_function_set',
                               docstring=
                                   "Function to be called when alternate speed is enabled/disabled\\n\\n"
                                   "Args:\\n"
                                   "    callback (function): callable object or function\\n"
                                   "                         pass `None\' to clear existing callback")

    root_module.header.writeln("""tr_rpc_callback_status _wrap_rpc_callback(tr_session *session, tr_rpc_callback_type type, struct tr_torrent *tor, void *data);""")
    root_module.body.writeln("""
tr_rpc_callback_status _wrap_rpc_callback(tr_session *session, tr_rpc_callback_type type,
                                      struct tr_torrent *tor, void *data)
{
    PyObject *py_torrent, *py_retval;
    PyObject *callback = (PyObject*) data;
    int retval = 0;
    PyTr_session *py_session = PyObject_New(PyTr_session, &PyTr_session_Type);
    py_session->obj = session;
    py_session->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;

    if (tor) {
        PyTr_torrent *tmp = PyObject_New(PyTr_torrent, &PyTr_torrent_Type);
        tmp->obj = tor;
        tmp->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;
        py_torrent = (PyObject *)tmp;
    } else {
        Py_INCREF(Py_None);
        py_torrent = Py_None;
    }

    py_retval = PyObject_CallFunction(callback, (char*)"OiO", (PyObject*)py_session, type, py_torrent);

    if (py_retval && PyLong_Check(py_retval))
        retval = PyLong_AsLong(py_retval);

    Py_DECREF(py_session);
    Py_DECREF(py_torrent);
    Py_DECREF(py_retval);

    return retval == (int)TR_RPC_NOREMOVE ? TR_RPC_NOREMOVE : TR_RPC_OK;
}
""")

    cls.add_function_as_method('tr_sessionSetRPCCallback', 
                               'void',
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('tr_rpc_func', 'callback', callback_func="_wrap_rpc_callback")],
                               custom_name='RPC_callback',
                               docstring=
                                   "Function to be called whenever something is changed via RPC\\n\\n"
                                   "Args:\\n"
                                   "    callback (function): callable object or function\\n"
                                   "                         pass `None\' to clear existing callback")

    cls.add_function_as_method('tr_sessionGetSettings', 
                               'void',
                               [param('tr_session *', 'session', transfer_ownership=False),
                                BencOutParam('BencDict *', 'dict')],
                               custom_name='settings',
                               docstring="Get a `BencDict\' of session settings")

    cls.add_function_as_method('tr_sessionLoadTorrents', 
                               retval("tr_torrent **",
                                      array_length='count',
                                      reference_existing_object=True),
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('tr_ctor *', 'torrent_constructor', transfer_ownership=False),
                                CountParam('int', 'count')],
                                custom_name='load_torrents',
                                docstring="Load all the torrents in the torrent directory")

    root_module.header.writeln("#define _wrap_tr_torrentNew(s, ctor, err) tr_torrentNew(ctor, err)")
    cls.add_function_as_method("_wrap_tr_torrentNew",
                               ReturnValue.new("tr_torrent *", reference_existing_object=True),
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('tr_ctor *', 'ctor', transfer_ownership=False),
                                TorrentErrorParam('int', 'setmeError')],
                               custom_name='torrent_new')

    root_module.header.writeln("#define _wrap_tr_torrentFree(s, tor) tr_torrentFree(tor)")
    cls.add_function_as_method('_wrap_tr_torrentFree', 
                               'void', 
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('tr_torrent *', 'torrent', transfer_ownership=True)],
                               unblock_threads=True,
                               custom_name='torrent_free')

    root_module.header.writeln("#define _wrap_tr_torrentRemove(s, tor, rem, fn) tr_torrentRemove(tor, rem, fn)")
    cls.add_function_as_method('_wrap_tr_torrentRemove', 
                               'void', 
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('tr_torrent *', 'torrent', transfer_ownership=True),
                                param('bool', 'remove_local_data', default_value='0'),
                                param('NULL', 'removeFunc')],
                               custom_name='torrent_remove')

    cls.add_custom_method_wrapper('torrents',
                                  '_wrap_tr_torrentList',
                                  flags=["METH_NOARGS"],
                                  wrapper_body="""
static PyObject* _wrap_tr_torrentList(PyTr_session *self, PyObject **return_exception)
{
    tr_torrent *torrent = NULL;
    PyObject *py_list = PyList_New(0);

    while ((torrent = tr_torrentNext(self->obj, torrent)) != NULL) {
        PyTr_torrent *elem = PyObject_New(PyTr_torrent, &PyTr_torrent_Type);
        elem->obj = torrent;
        elem->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;
        PyList_Append(py_list, (PyObject*)elem);
    }

    return py_list;
}
""")

    cls.add_function_as_method('tr_sessionSaveSettings', 
                               'void', 
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('char const *', 'directory'),
                                param('BencDict const *', 'settings', transfer_ownership=False)],
                               custom_name='settings_save',
                               docstring="Save `settings\' to `directory\'")

    cls.add_function_as_method('tr_sessionSet', 
                               'void', 
                               [param('tr_session *', 'session', transfer_ownership=False),
                                param('BencDict *', 'settings', transfer_ownership=False)],
                               custom_name='update',
                               docstring="Update session settings from `BencDict\'")
    return

def register_Tr_session_stats_methods(root_module, cls):
    cls.add_instance_attribute('downloadedBytes', 'uint64_t',
                               is_const=True,
                               custom_name='downloaded_bytes')
    cls.add_instance_attribute('filesAdded', 'uint64_t',
                               is_const=True,
                               custom_name='files_added')
    cls.add_instance_attribute('ratio', 'float', is_const=True)
    cls.add_instance_attribute('secondsActive', 'uint64_t',
                               is_const=True,
                               custom_name='seconds_active')
    cls.add_instance_attribute('sessionCount', 'uint64_t',
                               is_const=True,
                               custom_name='session_count')
    cls.add_instance_attribute('uploadedBytes', 'uint64_t',
                               is_const=True,
                               custom_name='uploaded_bytes')
    return

def register_Tr_msg_list_methods(root_module, cls):
    cls.add_instance_attribute('file', 'char const *', is_const=True)
    cls.add_instance_attribute('level', 'tr_msg_level', is_const=True)
    cls.add_instance_attribute('line', 'int', is_const=True)
    cls.add_instance_attribute('message', 'char *', is_const=True)
    cls.add_instance_attribute('name', 'char *', is_const=True)
    cls.add_instance_attribute('when', 'time_t', is_const=True)
    return

