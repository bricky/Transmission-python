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

from pybindgen import ReturnValue, Parameter

from pybindgen.typehandlers.base import PointerReturnValue, PointerParameter


class IntPtrReturn(PointerReturnValue):
    CTYPES = ['int *']

    def __init__(self, ctype, is_const=None, array_length=None):
        self.array_length = array_length
        super(IntPtrReturn, self).__init__(ctype, is_const)
    
    def convert_python_to_c(self, wrapper):
        name = wrapper.declarations.declare_variable('int',"tmp", array="[%i]" % self.array_length)
        if self.array_length is None:
            wrapper.parse_params.add_parameter("i", [name])
        else:
            wrapper.parse_params.add_parameter(
                '['+'i'*self.array_length+']',
                ['%s+%d'%(self.value,i) for i in range(self.array_length)],
                prepend=True)

    def convert_c_to_python(self, wrapper):
        if self.array_length is None:
            wrapper.build_params.add_parameter("i", [self.value], prepend=True)
        else:
            wrapper.build_params.add_parameter(
                '['+'i'*self.array_length+']',
                ['%s[%d]'%(self.value,i) for i in range(self.array_length)],
                prepend=True)


class CharPtrPtrReturn(PointerReturnValue):
    CTYPES = ['char **']

    def __init__(self, ctype, is_const=None, array_length=None):
        self.array_length = array_length
        super(CharPtrPtrReturn, self).__init__(ctype, is_const)

    def convert_c_to_python(self, wrapper):
        idx = wrapper.declarations.declare_variable("int", "idx")
        py_list = wrapper.declarations.declare_variable("PyObject *", "py_list")
        wrapper.after_call.write_code("%s = PyList_New(0);" % (py_list))
        wrapper.after_call.write_code("for(%s = 0; %s < %s; %s++) {"
                                       % (idx, idx, str(self.array_length), idx))
        wrapper.after_call.indent()
        wrapper.after_call.write_code("PyList_Append(%s, PyUnicode_FromString(%s[%s]));"
                                       % (py_list, self.value, idx))
        wrapper.after_call.unindent()
        wrapper.after_call.write_code("}")
        wrapper.build_params.add_parameter("N", [py_list], prepend=True)


class NewCharReturn(ReturnValue):
    CTYPES = []

    def get_c_error_return(self):
        return "return NULL;"
    
    def convert_python_to_c(self, wrapper):
        wrapper.parse_params.add_parameter("s", ['&'+self.value])

    def convert_c_to_python(self, wrapper):
        tmp = wrapper.declarations.declare_variable("char *", "tmp", self.value)
        wrapper.build_params.add_parameter("s", [tmp])
        wrapper.after_call.add_cleanup_code("tr_free(%s);" % (tmp))


class CharPtrLenParam(PointerParameter):

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = []

    def convert_python_to_c(self, wrapper):
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        name_len = wrapper.declarations.declare_variable("Py_ssize_t", self.name+'_len')
        wrapper.parse_params.add_parameter('s#', ['&'+name, '&'+name_len], self.value)
        wrapper.call_params.append(name)
        wrapper.call_params.append(name_len)


class BencReturn(PointerReturnValue):
    CTYPES = ['tr_benc *']
    BENC_TYPES = ['Bool', 'Int', 'Real', 'String', 'List', 'Dict']

    def convert_c_to_python(self, wrapper):
        if self.call_owns_return:
            raise NotImplementedError
        py_benc = wrapper.declarations.declare_variable("PyObject *", "py_benc", "NULL")

        wrapper.after_call.write_code("if (!(%s)) {\n"
                                      "    Py_INCREF(Py_None);\n"
                                      "    return Py_None;\n"
                                      "}" % self.value)
        for t in self.BENC_TYPES:
            wrapper.after_call.write_code('else if (tr_bencIs%s(%s)) {' % (t, self.value))
            wrapper.after_call.indent()
            wrapper.after_call.write_code('PyBenc%s *value;' % t)
            wrapper.after_call.write_code('value = PyObject_New(PyBenc%s, &PyBenc%s_Type);' % (t, t))
            wrapper.after_call.write_code('value->obj = %s;\n' % self.value)
            wrapper.after_call.write_code('value->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;')
            wrapper.after_call.unindent()
            wrapper.after_call.write_code('%s = (PyObject*)value;' % py_benc)
            wrapper.after_call.write_code('}')

        wrapper.after_call.write_error_check('%s == NULL' % py_benc,
                                             'PyErr_SetString(PyExc_ValueError, "Unable to get Benc");')

        wrapper.build_params.add_parameter("N", [py_benc])


class BencValueReturn(PointerReturnValue):
    CTYPES = []

    def __init__(self, ctype, is_const=None, key=None, index=None):
        self.key = key
        self.index = index
        super(BencValueReturn, self).__init__(ctype, is_const)

    def convert_c_to_python(self, wrapper):
        py_tmp = wrapper.declarations.declare_variable("PyObject *", "py_tmp", "NULL")
        sink = wrapper.after_call

        if self.key:
            sink.write_error_check('%s == NULL' % self.value,
                'PyErr_Format(PyExc_KeyError, "invalid key: \'%s\'", %s);' %
                              ('%s', self.key))
        elif self.index:
            sink.write_error_check('%s == NULL' % self.value,
                'PyErr_SetString(PyExc_IndexError, "index out of range");')
        else:
            sink.write_code('if (%s == NULL) {\n'
                            '    Py_RETURN_NONE;\n'
                            '}\n' % self.value)
        sink.write_code('else if (tr_bencIsBool(%s)) {\n'
                        '    bool value;\n'
                        '    if (tr_bencGetBool(%s, &value)) {\n'
                        '        %s = PyBool_FromLong(value);\n'
                        '    }\n'
                        '}'% (self.value, self.value, py_tmp))
        sink.write_code('else if (tr_bencIsInt(%s)) {\n'
                        '    int64_t value;\n'
                        '    if (tr_bencGetInt(%s, &value)) {\n'
                        '        %s = PyLong_FromLong(value);\n'
                        '    }\n'
                        '}'% (self.value, self.value, py_tmp))
        sink.write_code('else if (tr_bencIsReal(%s)) {\n'
                        '    double value;\n'
                        '    if (tr_bencGetReal(%s, &value)) {\n'
                        '        %s = PyFloat_FromDouble(value);\n'
                        '    }\n'
                        '}'% (self.value, self.value, py_tmp))
        sink.write_code('else if (tr_bencIsString(%s)) {\n'
                        '    const char *value;\n'
                        '    if (tr_bencGetStr(%s, &value)) {\n'
                        '        %s = Py_BuildValue((char *) "s", value);\n'
                        '        if (%s == NULL) {\n'
                        '            int len;\n'
                        '            value = tr_bencToStr(%s, TR_FMT_BENC, &len);\n'
                        '            %s = Py_BuildValue((char *) "y#", value, len);\n'
                        '        }\n'
                        '    }\n'
                        '}'% (self.value, self.value, py_tmp, py_tmp, self.value, py_tmp))
        sink.write_code('else if (tr_bencIsList(%s)) {\n'
                        '    PyBencList *value;\n'
                        '    value = PyObject_New(PyBencList, &PyBencList_Type);\n'
                        '    value->obj = %s;\n'
                        '    value->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;\n'
                        '    %s = (PyObject *)value;\n'
                        '}'% (self.value, self.value, py_tmp))
        sink.write_code('else if (tr_bencIsDict(%s)) {\n'
                        '    PyBencDict *value;\n'
                        '    value = PyObject_New(PyBencDict, &PyBencDict_Type);\n'
                        '    value->obj = %s;\n'
                        '    value->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;\n'
                        '    %s = (PyObject *)value;\n'
                        '}'% (self.value, self.value, py_tmp))
        sink.write_code('else {\n'
                        '    PyErr_SetString(PyExc_ValueError, "Unknown Benc type");\n'
                        '}\n')

        sink.write_error_check('%s == NULL' % py_tmp,
            'PyErr_SetString(PyExc_ValueError, "Unable to get Benc value");')

        wrapper.build_params.add_parameter("N", [py_tmp])


class BencOutParam(Parameter):
    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT]
    CTYPES = []

    def __init__(self, ctype, name, direction=Parameter.DIRECTION_IN, is_const=False,
                 default_value=None, merge_dict=False):
        super(BencOutParam, self).__init__(ctype, name, direction, is_const, default_value)
        self.merge_dict = merge_dict

    def convert_python_to_c(self, wrapper):
        name = wrapper.declarations.declare_variable('tr_benc *', self.name, 'tr_new0(tr_benc, 1)')
        py_name = wrapper.declarations.declare_variable("PyBencDict *", "py_"+self.name)
        wrapper.before_parse.write_error_check('%s == NULL || tr_bencInitDict(%s, 0) != 0' % (name, name),
                "tr_free(%s);\n"
                "PyErr_SetNone(PyExc_MemoryError);" % name)

        if self.merge_dict:
            tmp = wrapper.declarations.declare_variable('tr_benc *', self.name+'_tmp')
            wrapper.call_params.append('(const tr_benc **)&%s' % (tmp))
            wrapper.after_call.write_code('tr_bencMergeDicts(%s, %s);' % (name, tmp))
        else:
            wrapper.call_params.append(name)

        wrapper.after_call.write_code("%s = PyObject_New(PyBencDict, &PyBencDict_Type);" % (py_name))
        wrapper.after_call.write_code("%s->obj = %s;" % (py_name, name))
        wrapper.after_call.write_code("%s->flags = PYBINDGEN_WRAPPER_FLAG_NONE;" % (py_name))

        wrapper.build_params.add_parameter("N", [py_name], prepend=True)


class MessagePtrReturn(PointerReturnValue):
    CTYPES = ['tr_msg_list *']

    def convert_c_to_python(self, wrapper):
        next = wrapper.declarations.declare_variable("tr_msg_list *", "next")
        py_list = wrapper.declarations.declare_variable("PyObject *", "py_list")
        py_name = wrapper.declarations.declare_variable("PyTr_msg_list *", "py_msg_list")

        wrapper.after_call.write_code("%s = PyList_New(0);" % (py_list))
        wrapper.after_call.write_code("while (%s != NULL) {" % (self.value))
        wrapper.after_call.indent()
        wrapper.after_call.write_code("%s = %s->next;" % (next, self.value))
        wrapper.after_call.write_code("%s->next = NULL;" % (self.value))
        wrapper.after_call.write_code("%s = PyObject_New(PyTr_msg_list, &PyTr_msg_list_Type);" % (py_name))
        wrapper.after_call.write_code("%s->obj = %s;" % (py_name, self.value))
        if self.call_owns_return:
            wrapper.after_call.write_code("%s->flags = PYBINDGEN_WRAPPER_FLAG_NONE;" % (py_name))
        else:
            wrapper.after_call.write_code("%s->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;" % (py_name))
        wrapper.after_call.write_code("PyList_Append(%s, (PyObject *)%s);" % (py_list, py_name))
        wrapper.after_call.write_code("%s = %s;" % (self.value, next))
        wrapper.after_call.unindent()
        wrapper.after_call.write_code("}")

        wrapper.build_params.add_parameter("N", [py_list], prepend=True)


class CountParam(PointerParameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = []

    def convert_python_to_c(self, wrapper):
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        wrapper.call_params.append('&'+name)

class FloatCountParam(PointerParameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = []

    def convert_python_to_c(self, wrapper):
        py_list = wrapper.declarations.declare_variable("PyObject*", "py_list")
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        idx = wrapper.declarations.declare_variable("int", "idx")

        wrapper.parse_params.add_parameter('i', ['&'+name], self.name)

        wrapper.before_call.write_code('float tab[%s];' % (name))

        wrapper.call_params.append('tab')
        wrapper.call_params.append(name)

        wrapper.after_call.write_code("%s = PyList_New(%s);" % (py_list, name))
        wrapper.after_call.write_code("for (%s = 0; %s < %s; %s++) {" % (idx, idx, name, idx))
        wrapper.after_call.indent()
        wrapper.after_call.write_code("PyList_SET_ITEM(%s, %s, PyFloat_FromDouble(tab[%s]));"
                                       % (py_list, idx, idx))
        wrapper.after_call.unindent()
        wrapper.after_call.write_code('}')

        wrapper.build_params.add_parameter("N", [py_list])

class BoolCountParam(PointerParameter):
    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT, Parameter.DIRECTION_INOUT]
    CTYPES = []

    def convert_python_to_c(self, wrapper):
        py_list = wrapper.declarations.declare_variable("PyObject*", "py_list")
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        idx = wrapper.declarations.declare_variable("int", "idx")

        wrapper.parse_params.add_parameter('i', ['&'+name], self.name)

        wrapper.before_call.write_code('int8_t tab[%s];' % (name))

        wrapper.call_params.append('tab')
        wrapper.call_params.append(name)

        wrapper.after_call.write_code("%s = PyList_New(%s);" % (py_list, name))
        wrapper.after_call.write_code("for (%s = 0; %s < %s; %s++) {" % (idx, idx, name, idx))
        wrapper.after_call.indent()
        wrapper.after_call.write_code("PyList_SET_ITEM(%s, %s, PyLong_FromLong(tab[%s]));"
                                       % (py_list, idx, idx))
        wrapper.after_call.unindent()
        wrapper.after_call.write_code('}')

        wrapper.build_params.add_parameter("N", [py_list])


class TrackerInfoListParam(Parameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = []

    def convert_python_to_c(self, wrapper):
        py_type = "Py"+self.ctype.capitalize()
        py_list = wrapper.declarations.declare_variable("int", "MAX_TRACKERS", "64")
        py_list = wrapper.declarations.declare_variable("PyObject *", "py_list")
        name = wrapper.declarations.declare_variable(self.ctype , self.name, array="[MAX_TRACKERS]")
        elem = wrapper.declarations.declare_variable("PyObject *", "element")
        idx = wrapper.declarations.declare_variable("int", "idx")
        n_params = wrapper.declarations.declare_variable("int", "n_params")
        wrapper.parse_params.add_parameter('O!', ['&PyList_Type', '&'+py_list], self.name)

        wrapper.before_call.write_error_check('(%s = PyList_Size(%s)) == 0' % (n_params, py_list),
            'PyErr_SetString(PyExc_TypeError, "argument `%s\' must be a list of %s types");'
            % (self.name, self.ctype))

        wrapper.before_call.write_code("for (%(idx)s = 0; %(idx)s < %(n_params)s; %(idx)s++) {" % vars())
        wrapper.before_call.indent()
        wrapper.before_call.write_code('if (%s < MAX_TRACKERS) {' % (idx))
        wrapper.before_call.indent()
        wrapper.before_call.write_code("%(elem)s = PyList_GET_ITEM(%(py_list)s, %(idx)s);" % vars())

        wrapper.before_call.write_code('if (!PyObject_IsInstance(%s, (PyObject*) &%s_Type)) {'
                                        % (elem, py_type))
        wrapper.before_call.indent()
        wrapper.before_call.write_code('PyErr_SetString(PyExc_TypeError, "argument `%s\' must be a list of %s types");'  % (self.name, self.ctype))
        wrapper.before_call.write_error_return()
        wrapper.before_call.unindent()
        wrapper.before_call.write_code("}")

        wrapper.before_call.write_code("memcpy(%s+%s, ((%s*)%s)->obj, sizeof(%s));" % (name, idx, py_type, elem, self.ctype))
        wrapper.before_call.unindent()
        wrapper.before_call.write_code('}')
        wrapper.before_call.unindent()
        wrapper.before_call.write_code('}')

        wrapper.call_params.append(name)
        wrapper.call_params.append(n_params)


class ListParam(Parameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = []

    def convert_python_to_c(self, wrapper):
        py_type = 'PyTr_'+self.ctype.lower()
        ctype = 'tr_'+self.ctype.lower()
        py_list = wrapper.declarations.declare_variable("PyObject *", "py_list")
        name = wrapper.declarations.declare_variable(ctype+' **', self.name)
        elem = wrapper.declarations.declare_variable("PyObject *", "element")
        idx = wrapper.declarations.declare_variable("int", "idx")
        n_params = wrapper.declarations.declare_variable("int", "n_params")
        wrapper.parse_params.add_parameter('O!', ['&PyList_Type', '&'+py_list], self.name)

        wrapper.before_call.write_code('if ((%s = PyList_Size(%s)) == 0) {\n'
                                       '    Py_RETURN_NONE;\n'
                                       '}' % (n_params, py_list))

        wrapper.before_call.write_code("%(name)s = tr_new0(%(ctype)s *, %(n_params)s);" % vars())
        wrapper.before_call.write_code("for (%(idx)s = 0; %(idx)s < %(n_params)s; %(idx)s++) {" % vars())
        wrapper.before_call.indent()
        wrapper.before_call.write_code("%(elem)s = PyList_GET_ITEM(%(py_list)s, %(idx)s);" % vars())

        wrapper.before_call.write_code('if (!PyObject_IsInstance(%s, (PyObject*) &%s_Type)) {'
                                        % (elem, py_type))
        wrapper.before_call.indent()
        wrapper.before_call.write_code('PyErr_SetString(PyExc_TypeError, "argument `%s\' must be a list of %s types");'  % (self.name, self.ctype))
        wrapper.before_call.write_code('tr_free(%s);' % (name))
        wrapper.before_call.write_error_return()
        wrapper.before_call.unindent()
        wrapper.before_call.write_code("}")

        wrapper.before_call.write_code("%(name)s[%(idx)s] = ((%(py_type)s*)%(elem)s)->obj;" % vars())
        wrapper.before_call.unindent()
        wrapper.before_call.write_code('}')

        wrapper.call_params.append(name)
        wrapper.call_params.append(n_params)

        wrapper.after_call.write_code('tr_free(%s);' % (name))


class ListReturn(PointerReturnValue):
    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT,
                  Parameter.DIRECTION_IN|Parameter.DIRECTION_OUT]
    CTYPES = ['tr_torrent **', 'tr_file **', 'tr_tracker_info **', 'tr_piece **']

    def __init__(self, ctype, is_const=None, array_length=None,
                 caller_owns_return=False, reference_existing_object=False):
        super(ListReturn, self).__init__(ctype, is_const)
        self.array_length = array_length
        self.call_owns_return = caller_owns_return
        self.reference_existing_object = reference_existing_object

    def convert_c_to_python(self, wrapper):
        tr_type = self.ctype.split(' ')[0]
        py_type = "Py"+tr_type.capitalize()
        idx = wrapper.declarations.declare_variable("int", "idx")
        elem = wrapper.declarations.declare_variable("%s *" % (py_type), "elem")
        py_list = wrapper.declarations.declare_variable("PyObject *", "py_list")
        wrapper.after_call.write_code("%s = PyList_New(%s);" % (py_list, str(self.array_length)))
        wrapper.after_call.write_code("for(%s = 0; %s < %s; %s++) {"
                                       % (idx, idx, str(self.array_length), idx))
        wrapper.after_call.indent()
        wrapper.after_call.write_code("%s = PyObject_New(%s, &%s_Type);"
                                       % (elem, py_type, py_type))

        if self.call_owns_return:
            wrapper.after_call.write_code("%s->obj = (%s)tr_memdup(%s+%s, sizeof(%s));" %
                                          (elem, tr_type, self.value, idx, tr_type))
            wrapper.after_call.write_code("%s->flags = PYBINDGEN_WRAPPER_FLAG_NONE;" % (elem))
        else:
            if self.reference_existing_object:  # hack for 'tr_torrent **'
                wrapper.after_call.write_code("%s->obj = %s[%s];" % (elem, self.value, idx))
            else:
                wrapper.after_call.write_code("%s->obj = %s+%s;" % (elem, self.value, idx))
            wrapper.after_call.write_code("%s->flags = PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED;" % (elem))
        wrapper.after_call.write_code("PyList_SetItem(%s, %s, (PyObject*)%s);" % (py_list, idx, elem))
        wrapper.after_call.unindent()
        wrapper.after_call.write_code("}")
        wrapper.build_params.add_parameter("N", [py_list], prepend=True)


class AllocedListReturn(PointerReturnValue):
    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT,
                  Parameter.DIRECTION_IN|Parameter.DIRECTION_OUT]
    CTYPES = []

    def __init__(self, ctype, array_length, is_const=None):
        super(AllocedListReturn, self).__init__(ctype, is_const)
        self.array_length = array_length

    def convert_c_to_python(self, wrapper):
        py_type = "Py"+str(self.type_traits.target).capitalize()
        idx = wrapper.declarations.declare_variable("int", "idx")
        elem = wrapper.declarations.declare_variable("%s *" % (py_type), "elem")
        py_list = wrapper.declarations.declare_variable("PyObject *", "py_list")
        wrapper.after_call.write_code("%s = PyList_New(%s);" % (py_list, str(self.array_length)))
        wrapper.after_call.write_code("for(%s = 0; %s < %s; %s++) {"
                                       % (idx, idx, str(self.array_length), idx))
        wrapper.after_call.indent()
        wrapper.after_call.write_code("%s = PyObject_New(%s, &%s_Type);"
                                       % (elem, py_type, py_type))
        wrapper.after_call.write_code("%s->obj = (%s)tr_memdup(%s+%s, sizeof(%s));"
                                      % (elem, self.ctype, self.value, idx, str(self.type_traits.target)))
        wrapper.after_call.write_code("%s->flags = PYBINDGEN_WRAPPER_FLAG_NONE;" % (elem))
        
        wrapper.after_call.write_code("PyList_SetItem(%s, %s, (PyObject*)%s);" % (py_list, idx, elem))
        wrapper.after_call.unindent()
        wrapper.after_call.write_code("}")
        wrapper.after_call.write_code("tr_free(%s);" % (self.value))
        wrapper.build_params.add_parameter("N", [py_list], prepend=True)


class AllocedReturn(PointerReturnValue):

    DIRECTIONS = [Parameter.DIRECTION_IN, Parameter.DIRECTION_OUT,
                  Parameter.DIRECTION_IN|Parameter.DIRECTION_OUT]
    CTYPES = []

    def __init__(self, ctype,
        is_const=None, default_value=None, transfer_ownership=None,
        array_length=None, py_func='PyFloat_FromDouble'):
        self.array_length = array_length
        self.py_func = py_func
        super(AllocedReturn, self).__init__(ctype, is_const)
    
    def convert_c_to_python(self, wrapper):
        tmp = wrapper.declarations.declare_variable(self.ctype, "tmp")
        length = wrapper.declarations.declare_variable("int", "length")
        idx = wrapper.declarations.declare_variable("int", "idx")
        py_list = wrapper.declarations.declare_variable("PyObject *", "py_list")
        wrapper.after_call.write_code("%s = %s;" % (length, str(self.array_length)))
        wrapper.after_call.write_code("%s = %s;" % (tmp, self.value))
        wrapper.after_call.write_code("%s = PyList_New(%s);" % (py_list, length))
        wrapper.after_call.write_code("for(%s = 0; %s < %s; %s++) {"
                                       % (idx, idx, length, idx))
        wrapper.after_call.indent()
        wrapper.after_call.write_code("PyList_SetItem(%s, %s, %s(%s[%s]));" % (py_list, idx, self.py_func, tmp, idx))
        wrapper.after_call.unindent()
        wrapper.after_call.write_code("}")
        wrapper.after_call.write_code("tr_free(%s);" % (tmp))
        wrapper.build_params.add_parameter("N", [py_list], prepend=True)


class CallbackParam(Parameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['tr_torrent_completeness_func *', 'tr_torrent_idle_limit_hit_func *',
              'tr_torrent_ratio_limit_hit_func *', 'tr_torrent_metadata_func *',
              'tr_torrent_queue_start_func *', 'tr_altSpeedFunc *', 'tr_rpc_func']

    def __init__(self, ctype, name, direction=Parameter.DIRECTION_IN, is_const=False,
                 default_value=None, callback_func=None):
        super(CallbackParam, self).__init__(ctype, name, direction, is_const, default_value)
        self.callback_func = callback_func

    def convert_python_to_c(self, wrapper):
        static_ptr = wrapper.declarations.declare_variable("static PyObject*",
                                                           'static_%s_ptr' % self.name,
                                                           'NULL')
        py_cb = wrapper.declarations.declare_variable("PyObject*", self.name)
        func = wrapper.declarations.declare_variable(self.ctype, self.name+'_ptr', 'NULL')
        wrapper.parse_params.add_parameter('O', ['&'+py_cb], self.name)

        wrapper.before_call.write_error_check('%s && !PyCallable_Check(%s) && (PyObject*)%s != Py_None'
                                               % (py_cb, py_cb, py_cb),
            'PyErr_SetString(PyExc_TypeError, "argument `%s\' must be a callable object or None");'
             % self.name)

        wrapper.before_call.write_code('if (%s && (PyObject*)%s != Py_None) {\n'
                                       '    %s = %s;\n'
                                       '    Py_INCREF(%s);\n'
                                       '}' % (py_cb, py_cb, func, self.callback_func, py_cb))

        wrapper.call_params.append(func)
        wrapper.call_params.append('(%s ? %s : NULL)' % (func, py_cb))

        wrapper.after_call.add_cleanup_code("\n"
            "// XXX: still gonna leak...\n"
            "// need a hook to call from libtransmission for destructors and whatnot\n"
            "Py_XDECREF(%s);\n"
            "%s = (PyObject*)%s != Py_None ? %s : NULL;\n" % (static_ptr, static_ptr, py_cb, py_cb))


class TorrentErrorParam(Parameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = []

    def convert_python_to_c(self, wrapper):
        name = wrapper.declarations.declare_variable(self.ctype, self.name, '0')
        wrapper.call_params.append('&'+name)

        wrapper.before_call.write_error_check(
            '!tr_ctorGetSession(ctor->obj)',
            'PyErr_SetString(PyExc_NotImplementedError, '
            '"unable to create a Torrent without a session");')
        
        wrapper.after_call.write_error_check('%s == TR_PARSE_ERR' % name,
                                            'PyErr_SetString(PyExc_ValueError, '
                                            '"error parsing torrent");')
        wrapper.after_call.write_error_check('%s == TR_PARSE_DUPLICATE' % name,
                                            'PyErr_SetString(PyExc_ValueError, '
                                            '"torrent already added to session");')


class IdleLimitReturn(ReturnValue):
    CTYPES = []

    def get_c_error_return(self):
        return "return INT_MIN;"
    
    def convert_python_to_c(self, wrapper):
        tmp = wrapper.declarations.declare_variable("int", "tmp")
        wrapper.parse_params.add_parameter("i", ["&"+tmp], prepend=True)

        wrapper.after_call.write_error_check(
            "!(%s==TR_IDLELIMIT_GLOBAL || %s==TR_IDLELIMIT_SINGLE || %s==TR_IDLELIMIT_UNLIMITED)" % (tmp, tmp, tmp),
            'PyErr_SetString(PyExc_ValueError, "must be a \'transmission.idle_limit\' value");')

        wrapper.after_call.write_code("%s = (%s)%s;" % (self.value, self.ctype, tmp))

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("i", [self.value], prepend=True)


class RatioModeReturn(ReturnValue):
    CTYPES = []

    def get_c_error_return(self):
        return "return INT_MIN;"
    
    def convert_python_to_c(self, wrapper):
        tmp = wrapper.declarations.declare_variable("int", "tmp")
        wrapper.parse_params.add_parameter("i", ["&"+tmp], prepend=True)

        wrapper.after_call.write_error_check(
            "!(%s==TR_RATIOLIMIT_GLOBAL || %s==TR_RATIOLIMIT_SINGLE || %s==TR_RATIOLIMIT_UNLIMITED)" % (tmp, tmp, tmp),
            'PyErr_SetString(PyExc_ValueError, "must be a \'transmission.ratio_limit\' value");')

        wrapper.after_call.write_code("%s = (%s)%s;" % (self.value, self.ctype, tmp))

    def convert_c_to_python(self, wrapper):
        wrapper.build_params.add_parameter("i", [self.value], prepend=True)


class ErrorCheckReturn(ReturnValue):
    CTYPES = []

    def __init__(self, ctype, exception, error_string=None, error_cleanup='',
                 is_const=False, caller_owns_return=None, negate=True):
        super(ErrorCheckReturn, self).__init__(ctype, is_const=is_const)
        self.exception = exception
        self.error_string = error_string
        self.error_cleanup = error_cleanup
        self.negate = negate

    def get_c_error_return(self):
        return "return NULL;"
    
    def convert_c_to_python(self, wrapper):
        if self.error_string:
            wrapper.after_call.write_error_check('%s%s' % ('!' if self.negate else '', self.value), 
                                                 '%sPyErr_SetString(%s, %s);' %
                                                      (self.error_cleanup, self.exception, self.error_string))
        else:
            wrapper.after_call.write_error_check('%s%s' % ('!' if self.negate else '', self.value),
                                                 '%sPyErr_SetNone(%s);' % (self.error_cleanup, self.exception))


class DummyParam(Parameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['NULL']

    def convert_python_to_c(self, wrapper):
        wrapper.call_params.append(self.ctype)


class NotImplementedParam(Parameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['NotImplementedError']

    def convert_python_to_c(self, wrapper):
        wrapper.before_call.write_error_check("1", 'PyErr_SetString(PyExc_NotImplementedError, '
                                                   '"function not yet implemented");')


