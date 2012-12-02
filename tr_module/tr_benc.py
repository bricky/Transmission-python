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

from .typedefs import (BencValueReturn, BencOutParam, CharPtrLenParam)

def register_methods(root_module):
    register_Tr_benc_methods(root_module, root_module['Benc'])
    register_Tr_benc_bool_methods(root_module, root_module['BencBool'])
    register_Tr_benc_int_methods(root_module, root_module['BencInt'])
    register_Tr_benc_real_methods(root_module, root_module['BencReal'])
    register_Tr_benc_string_methods(root_module, root_module['BencString'])
    register_Tr_benc_list_methods(root_module, root_module['BencList'])
    register_Tr_benc_dict_methods(root_module, root_module['BencDict'])

def register_Tr_benc_methods(root_module, cls):
    root_module.header.writeln("tr_benc *_wrap_tr_bencGetValue(tr_benc * benc);")
    root_module.body.writeln("tr_benc *_wrap_tr_bencGetValue(tr_benc * benc)\n"
                             "{\n"
                             "    if (!benc || tr_bencIsList(benc) || tr_bencIsDict(benc))\n"
                             "        return NULL;\n"
                             "    return benc;\n"
                             "}")

    cls.add_instance_attribute('value',
                               BencValueReturn('tr_benc *'), 
                               is_const=True,
                               is_pure_c=True,
                               getter='_wrap_tr_bencGetValue')

    cls.add_function_as_method('tr_bencToStr',
                               'char *', 
                               [param('Benc *', 'benc', transfer_ownership=False),
                                param('tr_fmt_mode', 'mode'),
                                param('NULL', 'len')],
                               custom_name='string')

    return

def register_Tr_benc_bool_methods(root_module, cls):
    root_module.header.writeln("tr_benc *_wrap_tr_bencNewBool(int value);")
    root_module.body.writeln("""
tr_benc *_wrap_tr_bencNewBool(int value)
{
    tr_benc *benc = tr_new0(tr_benc, 1);
    tr_bencInitBool(benc, value);
    return benc;
}
""")

    cls.add_function_as_constructor("_wrap_tr_bencNewBool",
                                    ReturnValue.new("tr_benc*", caller_owns_return=True),
                                    [param('bool', 'value')])
    return

def register_Tr_benc_int_methods(root_module, cls):
    root_module.header.writeln("tr_benc *_wrap_tr_bencNewInt(int64_t value);")
    root_module.body.writeln("""
tr_benc *_wrap_tr_bencNewInt(int64_t value)
{
    tr_benc *benc = tr_new0(tr_benc, 1);
    tr_bencInitInt(benc, value);
    return benc;
}
""")

    cls.add_function_as_constructor("_wrap_tr_bencNewInt",
                                    ReturnValue.new("tr_benc*", caller_owns_return=True),
                                    [param('int64_t', 'value')])
    return

def register_Tr_benc_real_methods(root_module, cls):
    root_module.header.writeln("tr_benc *_wrap_tr_bencNewReal(double value);")
    root_module.body.writeln("""
tr_benc *_wrap_tr_bencNewReal(double value)
{
    tr_benc *benc = tr_new0(tr_benc, 1);
    tr_bencInitReal(benc, value);
    return benc;
}
""")

    cls.add_function_as_constructor("_wrap_tr_bencNewReal",
                                    ReturnValue.new("tr_benc*", caller_owns_return=True),
                                    [param('double', 'value')])
    return

def register_Tr_benc_string_methods(root_module, cls):
    root_module.header.writeln("tr_benc *_wrap_tr_bencNewStr(const void *str, int str_len);")
    root_module.body.writeln("""
tr_benc *_wrap_tr_bencNewStr(const void *str, int str_len)
{
    tr_benc *benc = tr_new0(tr_benc, 1);
    tr_bencInitStr(benc, str, str_len);
    return benc;
}
""")

    cls.add_function_as_constructor("_wrap_tr_bencNewStr",
                                    ReturnValue.new("tr_benc*", caller_owns_return=True),
                                    [CharPtrLenParam('const char *', 'value')])
    return

def register_Tr_benc_list_methods(root_module, cls):
    root_module.header.writeln("tr_benc *_wrap_tr_bencNewList(size_t reserveCount);")
    root_module.body.writeln("""
tr_benc *_wrap_tr_bencNewList(size_t reserveCount)
{
    tr_benc *benc = tr_new0(tr_benc, 1);
    tr_bencInitList(benc, reserveCount);
    return benc;
}
""")

    cls.add_function_as_constructor("_wrap_tr_bencNewList",
                                    ReturnValue.new("tr_benc*", caller_owns_return=True),
                                    [param('size_t', 'reserve_count')])

    cls.add_function_as_method('tr_bencListAddBool', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencList *', 'benc', transfer_ownership=False),
                                param('bool', 'value')],
                               custom_name='add_bool')

    cls.add_function_as_method('tr_bencListAddInt', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencList *', 'benc', transfer_ownership=False),
                                param('int64_t', 'value')],
                               custom_name='add_int')

    cls.add_function_as_method('tr_bencListAddReal', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencList *', 'benc', transfer_ownership=False),
                                param('double', 'value')],
                               custom_name='add_real')

    cls.add_function_as_method('tr_bencListAddStr', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencList *', 'benc', transfer_ownership=False),
                                param('char const *', 'value')],
                               custom_name='add_string')

    cls.add_function_as_method('tr_bencListAddDict', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencList *', 'benc', transfer_ownership=False),
                                param('size_t', 'reserve')],
                               custom_name='add_dict')

    cls.add_function_as_method('tr_bencListAddList', 
                               'tr_benc *',
                               [param('BencList *', 'benc', transfer_ownership=False),
                                param('size_t', 'reserve')],
                               custom_name='add_list')

    cls.add_function_as_method('tr_bencListSize', 
                               'size_t', 
                               [param('BencList *', 'benc', transfer_ownership=False)],
                               custom_name='__len__')

    cls.add_function_as_method('tr_bencListChild', 
                               BencValueReturn('tr_benc *', index='index'), 
                               [param('BencList *', 'benc', transfer_ownership=False),
                                param('int', 'index')],
                               custom_name='__getitem__')

    cls.add_custom_method_wrapper('__setitem__',
                                  '_wrap_transmission_tr_bencListSet',
                                  flags=["METH_VARARGS", "METH_KEYWORDS"],
                                  wrapper_body="""
PyObject *
_wrap_transmission_tr_bencListSet(PyBencList *self, PyObject *args,
                                   PyObject *kwargs, PyObject **return_exception)
{
    PyObject *py_value = NULL;
    PyObject *exc_type, *traceback;
    tr_benc *retval;
    int index;
    const char *keywords[] = {"index", "value", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "iO", (char **) keywords, &index, &py_value)) {
        PyErr_Fetch(&exc_type, return_exception, &traceback);
        Py_XDECREF(exc_type);
        Py_XDECREF(traceback);
        return NULL;
    }

    retval = tr_bencListChild(self->obj, index);

    if (!retval) {
        PyErr_SetString(PyExc_NotImplementedError,
                        "adding new items through sequence methods currently not supported");        
        return NULL;
    }

    if (tr_bencIsBool(retval) && PyBool_Check(py_value)) {
        tr_bencInitBool(retval, (py_value == Py_True));
        Py_RETURN_NONE;
    }
    else if (tr_bencIsInt(retval) && PyLong_Check(py_value)) {
        tr_bencInitReal(retval, PyLong_AsLong(py_value));
        Py_RETURN_NONE;
    }
    else if (tr_bencIsReal(retval) && PyFloat_Check(py_value)) {
        tr_bencInitReal(retval, PyFloat_AsDouble(py_value));
        Py_RETURN_NONE;
    }
    else if (tr_bencIsString(retval) && PyUnicode_Check(py_value)) {
        tr_bencFree(retval);
        tr_bencInitStr(retval, PyUnicode_AsUTF8(py_value), -1);
        Py_RETURN_NONE;
    }
    else if (tr_bencIsDict(retval) || tr_bencIsList(retval)) {
        PyErr_SetString(PyExc_NotImplementedError,
                        "assigning to BencList and BencDict types currently not supported");
        return NULL;
    }

    PyErr_Format(PyExc_ValueError, "Unable to set index '%i'", index);
    return NULL;
}"""
    )
    return

def register_Tr_benc_dict_methods(root_module, cls):
    root_module.header.writeln("tr_benc *_wrap_tr_bencNewDict(size_t reserveCount);")
    root_module.body.writeln("""
tr_benc *_wrap_tr_bencNewDict(size_t reserveCount)
{
    tr_benc *benc = tr_new0(tr_benc, 1);
    tr_bencInitDict(benc, reserveCount);
    return benc;
}
""")

    cls.add_function_as_constructor("_wrap_tr_bencNewDict",
                                    ReturnValue.new("tr_benc*", caller_owns_return=True),
                                    [param('size_t', 'reserve_count')])

    cls.add_function_as_method('tr_bencDictAddBool', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key'),
                                param('bool', 'value')],
                               custom_name='add_bool')

    cls.add_function_as_method('tr_bencDictAddBool', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key'),
                                param('bool', 'value')],
                               custom_name='add_bool')

    cls.add_function_as_method('tr_bencDictAddInt', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key'),
                                param('int64_t', 'value')],
                               custom_name='add_int')

    cls.add_function_as_method('tr_bencDictAddReal', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key'),
                                param('double', 'value')],
                               custom_name='add_real')

    cls.add_function_as_method('tr_bencDictAddStr', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key'),
                                param('char const *', 'value')],
                               custom_name='add_string')

    cls.add_function_as_method('tr_bencDictAddDict', 
                               ReturnValue.new('tr_benc *', caller_owns_return=False), 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key'),
                                param('size_t', 'reserve')],
                               custom_name='add_dict')

    cls.add_function_as_method('tr_bencDictAddList', 
                               'tr_benc *',
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key'),
                                param('size_t', 'reserve')],
                               custom_name='add_list')

    cls.add_function_as_method('tr_bencLoadFile', 
                               'int', 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('tr_fmt_mode', 'mode'),
                                param('char const *', 'filename')],
                               custom_name='load_file')

    cls.add_function_as_method('tr_bencToFile', 
                               'int', 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('tr_fmt_mode', 'mode'),
                                param('char const *', 'filename')],
                               custom_name='to_file')

    root_module.header.writeln("#define _wrap_BencDict_contains(benc, key) (tr_bencDictFind(benc, key) != NULL)")

    cls.add_function_as_method('_wrap_BencDict_contains', 
                               'bool', 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key')],
                               custom_name='__contains__')

    cls.add_custom_method_wrapper('keys',
                                  '_wrap_transmission_tr_benc_keys',
                                  flags=["METH_NOARGS"],
                                  wrapper_body="""
PyObject *
_wrap_transmission_tr_benc_keys(PyBencDict *self, PyObject **return_exception)
{
    int idx;
    int length = tr_bencDictSize(self->obj);

    PyObject *py_list = PyList_New(length);

    for(idx = 0; idx < length; ++idx) {
        const char * key;
        tr_benc * val;
        if(tr_bencDictChild(self->obj, idx, &key, &val)) {
            PyList_SetItem(py_list, idx, Py_BuildValue((char*)"s", key));
        }
    }
    return py_list;
}""")

    cls.add_function_as_method('tr_bencDictFind', 
                               'tr_benc *',
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key')],
                               custom_name='get')

    ## mapping methods
    cls.add_function_as_method('tr_bencDictSize', 
                               'size_t', 
                               [param('BencDict *', 'benc', transfer_ownership=False)],
                               custom_name='__maplen__')

    root_module.header.writeln("tr_benc *_wrap_tr_bencDictChild(tr_benc * benc, int i);")
    root_module.body.writeln("tr_benc *_wrap_tr_bencDictChild(tr_benc * benc, int i)\n"
                             "{\n"
                             "    const char *key;\n"
                             "    tr_benc *val;\n"
                             "    if (tr_bencDictChild(benc, i, &key, &val))\n"
                             "        return val;\n"
                             "    return NULL;\n"
                             "}")

    cls.add_function_as_method('_wrap_tr_bencDictChild', 
                               BencValueReturn('tr_benc *', index='index'), 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('int', 'index')],
                               custom_name='__mapget__')

    cls.add_function_as_method('tr_bencDictFind', 
                               BencValueReturn('tr_benc *', key='key'), 
                               [param('BencDict *', 'benc', transfer_ownership=False),
                                param('char const *', 'key')],
                               custom_name='__mapget__')

    cls.add_custom_method_wrapper('__mapset__',
                                  '_wrap_transmission_tr_bencDictSet',
                                  flags=["METH_VARARGS", "METH_KEYWORDS"],
                                  wrapper_body="""
PyObject *
_wrap_transmission_tr_bencDictSet(PyBencDict *self, PyObject *args,
                                   PyObject *kwargs, PyObject **return_exception)
{
    PyObject *py_value = NULL;
    PyObject *exc_type, *traceback;
    tr_benc *retval;
    char const *key;
    int index;
    const char *keywords[] = {"key", "value", NULL};

    if (PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "iO", (char **) keywords, &index, &py_value)) {
        if (!tr_bencDictChild(self->obj, index, &key, &retval)) {
            PyErr_SetString(PyExc_NotImplementedError,
                            "adding new items through mapping methods currently not supported");
            return NULL;
        }
    }
    else if (!PyArg_ParseTupleAndKeywords(args, kwargs, (char *) "sO", (char **) keywords, &key, &py_value)) {
        PyErr_Fetch(&exc_type, return_exception, &traceback);
        Py_XDECREF(exc_type);
        Py_XDECREF(traceback);
        return NULL;
    }

    /*
    if (!retval && !tr_bencDictFind(self->obj, key)) {
        PyErr_SetString(PyExc_NotImplementedError,
                        "adding new items through mapping methods currently not supported");        
        return NULL;
    }
    */
    if (PyBool_Check(py_value)) {
        if (tr_bencDictAddBool(self->obj, key, (py_value == Py_True)))
            Py_RETURN_NONE;
    }
    else if (PyLong_Check(py_value)) {
        if (tr_bencDictAddInt(self->obj, key, PyLong_AsLong(py_value)))
            Py_RETURN_NONE;
    }
    else if (PyFloat_Check(py_value)) {
        if (tr_bencDictAddReal(self->obj, key, PyFloat_AsDouble(py_value)))
            Py_RETURN_NONE;
    }
    else if (PyUnicode_Check(py_value)) {
        if (tr_bencDictAddStr(self->obj, key, PyUnicode_AsUTF8(py_value)))
            Py_RETURN_NONE;
    }
    else if (PyObject_IsInstance(py_value, (PyObject *)&PyBencDict_Type) ||
             PyObject_IsInstance(py_value, (PyObject *)&PyBencList_Type)) {
        PyErr_SetString(PyExc_NotImplementedError,
                        "assigning BencList and BencDict types currently not supported");
        return NULL;
    }

    PyErr_Format(PyExc_ValueError, "Unable to set '%s'", key);
    return NULL;
}"""
    )
    return

