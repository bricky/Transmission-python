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

from .typedefs import (AllocedReturn, IdleLimitReturn, NewCharReturn, RatioModeReturn,
                       BoolCountParam, FloatCountParam, AllocedListReturn, CountParam,
                       TrackerInfoListParam, DummyParam, BencOutParam)

def register_methods(root_module):
    register_Tr_torrent_methods(root_module, root_module['tr_torrent'])
    register_Tr_ctor_methods(root_module, root_module['tr_ctor'])
    register_Tr_stat_methods(root_module, root_module['tr_stat'])
    register_Tr_peer_stat_methods(root_module, root_module['tr_peer_stat'])
    register_Tr_file_stat_methods(root_module, root_module['tr_file_stat'])

def register_Tr_torrent_methods(root_module, cls):
    cls.add_instance_attribute('can_manual_update', 'bool',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentCanManualUpdate',
                               setter=None)

    cls.add_instance_attribute('bytes_left_to_allocate', 'uint64_t',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentGetBytesLeftToAllocate',
                               setter=None)

    cls.add_instance_attribute('current_directory', 'char const *',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentGetCurrentDir',
                               setter=None)

    cls.add_instance_attribute('download_directory', 'char const *',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentGetDownloadDir')

    cls.add_instance_attribute('file_priorities', 
                               AllocedReturn('tr_priority_t *',
                                             array_length="tr_torrentInfo(self->obj)->fileCount"),
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentGetFilePriorities')

    cls.add_instance_attribute('idle_limit', 'uint16_t',
                               is_pure_c=True,
                               getter='tr_torrentGetIdleLimit',
                               setter='tr_torrentSetIdleLimit')

    cls.add_instance_attribute('idle_mode', IdleLimitReturn('tr_idlelimit'),
                               is_pure_c=True,
                               getter='tr_torrentGetIdleMode',
                               setter='tr_torrentSetIdleMode')

    cls.add_instance_attribute('magnet_link', NewCharReturn('char *'),
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentGetMagnetLink',
                               setter=None)

    cls.add_instance_attribute('peer_limit', 'uint16_t',
                               is_pure_c=True,
                               getter='tr_torrentGetPeerLimit',
                               setter='tr_torrentSetPeerLimit')

    cls.add_instance_attribute('priority', 'tr_priority_t',
                               is_pure_c=True,
                               getter='tr_torrentGetPriority',
                               setter='tr_torrentSetPriority')

    cls.add_instance_attribute('queue_position', 'int',
                               is_pure_c=True,
                               getter='tr_torrentGetQueuePosition',
                               setter='tr_torrentSetQueuePosition')

    cls.add_instance_attribute('ratio_limit', 'double',
                               is_pure_c=True,
                               getter='tr_torrentGetRatioLimit',
                               setter='tr_torrentSetRatioLimit')

    cls.add_instance_attribute('ratio_mode', RatioModeReturn('tr_ratiolimit'),
                               is_pure_c=True,
                               getter='tr_torrentGetRatioMode',
                               setter='tr_torrentSetRatioMode')

    cls.add_instance_attribute('seed_idle', 'bool',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentGetSeedIdle',
                               closure_cast='(uint16_t *)')

    root_module.header.writeln("uint16_t _wrap_tr_torrentGetSeedIdleMinutes(const tr_torrent * tor);")
    root_module.body.writeln("uint16_t _wrap_tr_torrentGetSeedIdleMinutes(const tr_torrent * tor)\n"
                             "{\n"
                             "    uint16_t idleMinutes;\n"
                             "    return tr_torrentGetSeedIdle(tor, &idleMinutes) ? idleMinutes : 0;\n"
                             "}")

    cls.add_instance_attribute('seed_idle_minutes', 'uint16_t',
                               is_const=True,
                               is_pure_c=True,
                               getter='_wrap_tr_torrentGetSeedIdleMinutes')

    root_module.header.writeln("double _wrap_tr_torrentGetSeedRatio(const tr_torrent * tor);")
    root_module.body.writeln("double _wrap_tr_torrentGetSeedRatio(const tr_torrent * tor)\n"
                             "{\n"
                             "    double ratio;\n"
                             "    return tr_torrentGetSeedRatio(tor, &ratio) ? ratio : 0;\n"
                             "}")

    cls.add_instance_attribute('seed_ratio', 'double',
                               is_const=True,
                               is_pure_c=True,
                               getter='_wrap_tr_torrentGetSeedRatio')

    cls.add_instance_attribute('speed_limit_up', 'uint8_t',
                               is_pure_c=True,
                               getter='tr_torrentGetSpeedLimit_KBps',
                               setter='tr_torrentSetSpeedLimit_KBps',
                               closure='&tr_up', closure_cast='*(tr_direction*)')

    cls.add_instance_attribute('speed_limit_down', 'uint8_t',
                               is_pure_c=True,
                               getter='tr_torrentGetSpeedLimit_KBps',
                               setter='tr_torrentSetSpeedLimit_KBps',
                               closure='&tr_down', closure_cast='*(tr_direction*)')

    cls.add_instance_attribute('use_speed_limit_up', 'bool',
                               is_pure_c=True,
                               getter='tr_torrentUsesSpeedLimit',
                               setter='tr_torrentUseSpeedLimit',
                               closure='&tr_up', closure_cast='*(tr_direction*)')

    cls.add_instance_attribute('use_speed_limit_down', 'bool',
                               is_pure_c=True,
                               getter='tr_torrentUsesSpeedLimit',
                               setter='tr_torrentUseSpeedLimit',
                               closure='&tr_down', closure_cast='*(tr_direction*)')

    cls.add_instance_attribute('has_metadata', 'bool',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentHasMetadata',
                               setter=None)

    cls.add_instance_attribute('id', 'int',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentId',
                               setter=None)

    cls.add_instance_attribute('info',
                               ReturnValue.new("tr_info *", return_internal_reference=True, is_const=True),
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentInfo')

    cls.add_instance_attribute('name', 'char const *',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_torrentName')

    cls.add_instance_attribute('use_session_limits', 'bool',
                               is_pure_c=True,
                               getter='tr_torrentUsesSessionLimits',
                               setter='tr_torrentUseSessionLimits')

    cls.add_instance_attribute('web_speeds',
                               AllocedReturn('double *',
                                             array_length="tr_torrentInfo(self->obj)->webseedCount"),
                               is_pure_c=True,
                               is_const=True,
                               getter='tr_torrentWebSpeeds_KBps',
                               setter=None)

    cls.add_function_as_method('tr_torrentStart', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False)],
                               custom_name='start')

    cls.add_function_as_method('tr_torrentStartNow', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False)],
                               custom_name='start_now')

    cls.add_function_as_method('tr_torrentStop', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False)],
                               custom_name='stop')

    cls.add_function_as_method('tr_torrentStat', 
                               'tr_stat const *', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False)],
                               custom_name='stats')

    cls.add_function_as_method('tr_torrentStatCached', 
                               'tr_stat const *', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False)],
                               custom_name='stats_cached')

    cls.add_function_as_method('tr_torrentVerify', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False)],
                               custom_name='verify')

    cls.add_function_as_method('tr_torrentAmountFinished', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                FloatCountParam('int', 'size')],
                               custom_name='amount_finished')

    cls.add_function_as_method('tr_torrentAvailability', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                BoolCountParam('int', 'size')],
                               custom_name='availability')

    cls.add_function_as_method('tr_torrentFiles', 
                               AllocedListReturn('tr_file_stat *', array_length='count'),
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                CountParam('tr_file_index_t', 'count')],
                               custom_name='files')

    cls.add_function_as_method('tr_torrentFindFile', 
                               'char *', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('tr_file_index_t', 'file_number')],
                               custom_name='find_file')

    cls.add_function_as_method('tr_torrentPeers', 
                               AllocedListReturn("tr_peer_stat *", array_length='count'),
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                CountParam('int', 'count')],
                               custom_name='peers')

    cls.add_function_as_method('tr_torrentSetAnnounceList', 
                               'bool', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                TrackerInfoListParam('tr_tracker_info', 'trackers')],
                               custom_name='set_announce_list')

    cls.add_function_as_method('tr_torrentSetFileDLs', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('tr_file_index_t const *', 'files'),
                                DummyParam('1', 'fileCount'),
                                param('bool', 'download')],
                               custom_name='file_set_download')

    cls.add_function_as_method('tr_torrentSetFilePriorities', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('tr_file_index_t *', 'index'),
                                DummyParam('1', 'fileCount'),
                                param('tr_priority_t', 'priority')],
                               custom_name='file_set_priority')

    cls.add_function_as_method('tr_torrentSetLocation', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('char const *', 'location'),
                                param('bool', 'move'),
                                param('NULL', 'progress'),
                                param('NULL', 'state')],
                               custom_name='set_location')

    cls.add_function_as_method('tr_torrentTrackers', 
                               AllocedListReturn('tr_tracker_stat *', array_length='count'),
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                CountParam('int', 'count')],
                               custom_name='trackers')

    root_module.header.writeln("""void _wrap_completeness_callback(tr_torrent *torrent, tr_completeness completeness, bool wasRunning, void *data);""")
    root_module.body.writeln("""
void _wrap_completeness_callback(tr_torrent *torrent, tr_completeness completeness, bool wasRunning, void *data)
{
    PyObject *callback = (PyObject*) data;
    PyGILState_STATE __py_gil_state;

    __py_gil_state = (PyEval_ThreadsInitialized() ? PyGILState_Ensure() : (PyGILState_STATE) 0);

    PyTr_torrent *py_torrent = PyObject_New(PyTr_torrent, &PyTr_torrent_Type);
    py_torrent->obj = torrent;
    py_torrent->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;

    PyObject_CallFunction(callback, (char*)"Oib", (PyObject*)py_torrent, completeness, wasRunning);

    Py_DECREF(py_torrent);

    if (PyEval_ThreadsInitialized())
        PyGILState_Release(__py_gil_state);
}
""")

    cls.add_function_as_method('tr_torrentSetCompletenessCallback', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('tr_torrent_completeness_func *', 'func',
                                      callback_func="_wrap_completeness_callback")],
                               custom_name='completeness_callback_set')

    root_module.header.writeln("""void _wrap_no_call_args_callback(tr_torrent *torrent, void *data);""")
    root_module.body.writeln("""
void _wrap_no_call_args_callback(tr_torrent *torrent, void *data)
{
    PyObject *callback = (PyObject*) data;

    PyTr_torrent *py_torrent = PyObject_New(PyTr_torrent, &PyTr_torrent_Type);
    py_torrent->obj = torrent;
    py_torrent->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;

    PyObject_CallFunction(callback, (char*)"O", (PyObject*)py_torrent);

    Py_DECREF(py_torrent);
}
""")

    cls.add_function_as_method('tr_torrentSetIdleLimitHitCallback', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('tr_torrent_idle_limit_hit_func *', 'func',
                                      callback_func="_wrap_no_call_args_callback")],
                               custom_name='idle_limit_hit_callback')

    cls.add_function_as_method('tr_torrentSetMetadataCallback', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('tr_torrent_metadata_func *', 'func',
                                      callback_func="_wrap_no_call_args_callback")],
                               custom_name='metadata_callback')

    root_module.header.writeln("""typedef void (tr_torrent_queue_start_func)(tr_torrent *torrent, void *data);""")
    cls.add_function_as_method('tr_torrentSetQueueStartCallback', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('tr_torrent_queue_start_func *', 'func',
                                      callback_func="_wrap_no_call_args_callback")],
                               custom_name='queue_start_callback')

    cls.add_function_as_method('tr_torrentSetRatioLimitHitCallback', 
                               'void', 
                               [param('tr_torrent *', 'torrent', transfer_ownership=False),
                                param('tr_torrent_ratio_limit_hit_func *', 'func',
                                      callback_func="_wrap_no_call_args_callback")],
                               custom_name='ratio_limit_hit_callback')
    return

def register_Tr_ctor_methods(root_module, cls):
    cls.add_function_as_constructor("tr_ctorNew",
                                    ReturnValue.new("tr_ctor*", caller_owns_return=True),
                                    [param('tr_session const *', 'session', null_ok=True)])

    cls.add_instance_attribute('bandwidth_priority', 'tr_priority_t',  #XXX: check for value in tr.priority
                               is_pure_c=True,
                               getter='tr_ctorGetBandwidthPriority',
                               setter='tr_ctorSetBandwidthPriority')

    root_module.header.writeln("bool _wrap_tr_ctorGetDeleteSource(const tr_ctor * ctor);")
    root_module.body.writeln("bool _wrap_tr_ctorGetDeleteSource(const tr_ctor * ctor)\n"
                             "{\n"
                             "    bool setme = 0;\n"
                             "    tr_ctorGetDeleteSource(ctor, &setme);\n"
                             "    return setme;\n"
                             "}")

    cls.add_instance_attribute('delete_source', 'bool',
                               is_pure_c=True,
                               getter='_wrap_tr_ctorGetDeleteSource',
                               setter='tr_ctorSetDeleteSource')

    cls.add_instance_attribute('session',
                               ReturnValue.new("tr_session *", reference_existing_object=True),
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_ctorGetSession')

    cls.add_instance_attribute('source_file', 'char const *',
                               is_const=True,
                               is_pure_c=True,
                               getter='tr_ctorGetSourceFile')

    root_module.header.writeln("uint16_t _wrap_tr_ctorGetPeerLimit(const tr_ctor * ctor, tr_ctorMode mode);")
    root_module.body.writeln("uint16_t _wrap_tr_ctorGetPeerLimit(const tr_ctor * ctor, tr_ctorMode mode)\n"
                             "{\n"
                             "    uint16_t count = 0;\n"
                             "    if (tr_ctorGetPeerLimit(ctor, mode, &count))\n"
                             "        return count;\n"
                             "    else if (tr_ctorGetPeerLimit(ctor, TR_FALLBACK, &count)) \n"
                             "        return count;\n"
                             "    return 0;\n"
                             "}")

    cls.add_instance_attribute('peer_limit', 'uint16_t',
                               is_pure_c=True,
                               getter='_wrap_tr_ctorGetPeerLimit',
                               setter='tr_ctorSetPeerLimit',
                               closure='&tr_force', closure_cast='*(tr_ctorMode*)')

    root_module.header.writeln("const char *_wrap_tr_ctorGetDownloadDir(const tr_ctor * ctor, tr_ctorMode mode);")
    root_module.body.writeln("const char *_wrap_tr_ctorGetDownloadDir(const tr_ctor * ctor, tr_ctorMode mode)\n"
                             "{\n"
                             "    const char *dir;\n"
                             "    if (tr_ctorGetDownloadDir(ctor, mode, &dir) == 0)\n"
                             "        return dir;\n"
                             "    else if (tr_ctorGetDownloadDir(ctor, TR_FALLBACK, &dir) == 0)\n"
                             "        return dir;\n"
                             "    return NULL;\n"
                             "}")

    cls.add_instance_attribute('download_directory', 'char const *',
                               is_pure_c=True,
                               getter='_wrap_tr_ctorGetDownloadDir',
                               setter='tr_ctorSetDownloadDir',
                               closure='&tr_force', closure_cast='*(tr_ctorMode*)')

    root_module.header.writeln("uint16_t _wrap_tr_ctorGetPaused(const tr_ctor * ctor, tr_ctorMode mode);")
    root_module.body.writeln("uint16_t _wrap_tr_ctorGetPaused(const tr_ctor * ctor, tr_ctorMode mode)\n"
                             "{\n"
                             "    bool paused = 0;\n"
                             "    if (tr_ctorGetPaused(ctor, mode, &paused) == 0)\n"
                             "        return paused;\n"
                             "    tr_ctorGetPaused(ctor, TR_FALLBACK, &paused); \n"
                             "    return paused;\n"
                             "}")

    cls.add_instance_attribute('paused', 'bool',
                               is_pure_c=True,
                               getter='_wrap_tr_ctorGetPaused',
                               setter='tr_ctorSetPaused',
                               closure='&tr_force', closure_cast='*(tr_ctorMode*)')

    cls.add_function_as_method('tr_ctorGetMetainfo', 
                               'void', 
                               [param('tr_ctor *', 'ctor', transfer_ownership=False),
                                BencOutParam('const tr_benc **', 'dict', merge_dict=True)],
                               custom_name='metainfo')

    cls.add_function_as_method('tr_torrentParse', 
                               'tr_parse_result',
                               [param('tr_ctor *', 'ctor', transfer_ownership=False),
                                param('NULL', 'info')],
                               custom_name='parse')

    cls.add_function_as_method('tr_ctorSetMetainfoFromMagnetLink', 
                               'int', 
                               [param('tr_ctor *', 'ctor', transfer_ownership=False),
                                param('char const *', 'magnet')],
                               custom_name='set_metainfo_from_magnet')

    cls.add_function_as_method('tr_ctorSetMetainfoFromFile', 
                               'int', 
                               [param('tr_ctor *', 'ctor', transfer_ownership=False),
                                param('char const *', 'filename')],
                               custom_name='set_metainfo_from_file')

    cls.add_function_as_method('tr_ctorSetMetainfoFromHash', 
                               'int', 
                               [param('tr_ctor *', 'ctor', transfer_ownership=False),
                                param('char const *', 'hash_tag')],
                               custom_name='set_metainfo_from_hash')
    return

def register_Tr_stat_methods(root_module, cls):
    cls.add_instance_attribute('activity', 'tr_torrent_activity', is_const=True)
    cls.add_instance_attribute('activityDate', 'time_t', is_const=True,
                               custom_name='activity_date')
    cls.add_instance_attribute('addedDate', 'time_t', is_const=True,
                               custom_name='added_date')
    cls.add_instance_attribute('corruptEver', 'uint64_t', is_const=True,
                               custom_name='corrupt_ever')
    cls.add_instance_attribute('desiredAvailable', 'uint64_t', is_const=True,
                               custom_name='desired_available')
    cls.add_instance_attribute('doneDate', 'time_t', is_const=True,
                               custom_name='done_date')
    cls.add_instance_attribute('downloadedEver', 'uint64_t', is_const=True,
                               custom_name='downloaded_ever')
    cls.add_instance_attribute('error', 'tr_stat_errtype', is_const=True)
    cls.add_instance_attribute('errorString', 'char *', is_const=True,
                               custom_name='error_string')
    cls.add_instance_attribute('eta', 'int', is_const=True)
    cls.add_instance_attribute('etaIdle', 'int', is_const=True,
                               custom_name='eta_idle')
    cls.add_instance_attribute('finished', 'bool', is_const=True)
    cls.add_instance_attribute('haveUnchecked', 'uint64_t', is_const=True,
                               custom_name='have_unchecked')
    cls.add_instance_attribute('haveValid', 'uint64_t', is_const=True,
                               custom_name='have_valid')
    cls.add_instance_attribute('id', 'int', is_const=True)
    cls.add_instance_attribute('idleSecs', 'int', is_const=True,
                               custom_name='idle_seconds')
    cls.add_instance_attribute('isStalled', 'bool', is_const=True,
                               custom_name='is_stalled')
    cls.add_instance_attribute('leftUntilDone', 'uint64_t', is_const=True,
                               custom_name='left_until_done')
    cls.add_instance_attribute('manualAnnounceTime', 'time_t', is_const=True,
                               custom_name='manual_announce_time')
    cls.add_instance_attribute('metadataPercentComplete', 'float', is_const=True,
                               custom_name='metadata_percent_complete')
    cls.add_instance_attribute('peersConnected', 'int', is_const=True,
                               custom_name='peers_connected')
    cls.add_instance_attribute('peersFrom',
                               retval('int *', array_length=7),  # TR_PEER_FROM__MAX
                               is_const=True,
                               custom_name='peers_from')
    cls.add_instance_attribute('peersGettingFromUs', 'int', is_const=True,
                               custom_name='peers_getting_from_us')
    cls.add_instance_attribute('peersSendingToUs', 'int', is_const=True,
                               custom_name='peers_sending')
    cls.add_instance_attribute('percentComplete', 'float', is_const=True,
                               custom_name='percent_complete')
    cls.add_instance_attribute('percentDone', 'float', is_const=True,
                               custom_name='percent_done')
    cls.add_instance_attribute('pieceDownloadSpeed_KBps', 'float', is_const=True,
                               custom_name='piece_download_speed')
    cls.add_instance_attribute('pieceUploadSpeed_KBps', 'float', is_const=True,
                               custom_name='piece_upload_speed')
    cls.add_instance_attribute('queuePosition', 'int', is_const=True,
                               custom_name='queue_position')
    cls.add_instance_attribute('ratio', 'float', is_const=True)
    cls.add_instance_attribute('rawDownloadSpeed_KBps', 'float', is_const=True,
                               custom_name='raw_download_speed')
    cls.add_instance_attribute('rawUploadSpeed_KBps', 'float', is_const=True,
                               custom_name='raw_upload_speed')
    cls.add_instance_attribute('recheckProgress', 'float', is_const=True,
                               custom_name='recheck_progress')
    cls.add_instance_attribute('secondsDownloading', 'int', is_const=True,
                               custom_name='seconds_downloading')
    cls.add_instance_attribute('secondsSeeding', 'int', is_const=True,
                               custom_name='seconds_seeding')
    cls.add_instance_attribute('seedRatioPercentDone', 'float', is_const=True,
                               custom_name='seed_ratio_percent_done')
    cls.add_instance_attribute('sizeWhenDone', 'uint64_t', is_const=True,
                               custom_name='size_when_done')
    cls.add_instance_attribute('startDate', 'time_t', is_const=True,
                               custom_name='start_date')
    cls.add_instance_attribute('uploadedEver', 'uint64_t', is_const=True,
                               custom_name='uploaded_ever')
    cls.add_instance_attribute('webseedsSendingToUs', 'int', is_const=True,
                               custom_name='webseeds_sending_to_us')
    return

def register_Tr_peer_stat_methods(root_module, cls):
    cls.add_instance_attribute('addr', 'char *', is_const=True,
                               custom_name='address')
    cls.add_instance_attribute('blocksToClient', 'uint32_t', is_const=True,
                               custom_name='blocks_to_client')
    cls.add_instance_attribute('blocksToPeer', 'uint32_t', is_const=True,
                               custom_name='blocks_to_peer')
    cls.add_instance_attribute('cancelsToClient', 'uint32_t', is_const=True,
                               custom_name='cancels_to_client')
    cls.add_instance_attribute('cancelsToPeer', 'uint32_t', is_const=True,
                               custom_name='cancles_to_peer')
    cls.add_instance_attribute('client', 'char *', is_const=True)
    cls.add_instance_attribute('clientIsChoked', 'bool', is_const=True,
                               custom_name='client_is_choked')
    cls.add_instance_attribute('clientIsInterested', 'bool', is_const=True,
                               custom_name='client_is_interested')
    cls.add_instance_attribute('flagStr', 'char *', is_const=True,
                               custom_name='flag_string')
    cls.add_instance_attribute('from', 'uint8_t', is_const=True)
    cls.add_instance_attribute('isDownloadingFrom', 'bool', is_const=True,
                               custom_name='is_downloading_from')
    cls.add_instance_attribute('isEncrypted', 'bool', is_const=True,
                               custom_name='is_encrypted')
    cls.add_instance_attribute('isIncoming', 'bool', is_const=True,
                               custom_name='is_incoming')
    cls.add_instance_attribute('isSeed', 'bool', is_const=True,
                               custom_name='is_seed')
    cls.add_instance_attribute('isUTP', 'bool', is_const=True,
                               custom_name='is_UTP')
    cls.add_instance_attribute('isUploadingTo', 'bool', is_const=True,
                               custom_name='is_downloading_to')
    cls.add_instance_attribute('peerIsChoked', 'bool', is_const=True,
                               custom_name='peer_is_choked')
    cls.add_instance_attribute('peerIsInterested', 'bool', is_const=True,
                               custom_name='peer_is_interested')
    cls.add_instance_attribute('pendingReqsToClient', 'int', is_const=True,
                               custom_name='pending_requests_to_client')
    cls.add_instance_attribute('pendingReqsToPeer', 'int', is_const=True,
                               custom_name='pending_requests_to_peer')
    cls.add_instance_attribute('port', 'tr_port', is_const=True)
    cls.add_instance_attribute('progress', 'float', is_const=True)
    cls.add_instance_attribute('rateToClient_KBps', 'double', is_const=True,
                               custom_name='rate_to_client')
    cls.add_instance_attribute('rateToPeer_KBps', 'double', is_const=True,
                               custom_name='rate_to_peer')
    return

def register_Tr_file_stat_methods(root_module, cls):
    cls.add_instance_attribute('bytesCompleted', 'uint64_t', is_const=True,
                               custom_name='bytes_completed')
    cls.add_instance_attribute('progress', 'float', is_const=True)
    return

