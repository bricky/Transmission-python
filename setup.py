from distutils.core import setup, Extension

tr_build_dir = '../Transmission'

module = Extension('transmission',
                   include_dirs = ['src', 'include', '/usr/include',
                                   tr_build_dir+'/libtransmission'],
                   libraries = ['event', 'ssl', 'curl', 'z', 'pthread'],
                   library_dirs = ['/usr/lib64', '/usr/lib'],
                   extra_objects = [tr_build_dir+'/libtransmission/libtransmission.a',
                                    tr_build_dir+'/third-party/miniupnp/libminiupnp.a',
                                    tr_build_dir+'/third-party/libnatpmp/libnatpmp.a',
                                    tr_build_dir+'/third-party/dht/libdht.a',
                                    tr_build_dir+'/third-party/libutp/libutp.a'],
                   sources = ['src/tr_benc.cc',
                              'src/tr_info.cc',
                              'src/tr_module.cc',
                              'src/tr_session.cc',
                              'src/tr_torrent.cc',
                              'src/tr_tracker.cc'])

setup (name = 'transmission',
       version = '0.1',
       description = 'Python bindings for Transmission',
       ext_modules = [module])
