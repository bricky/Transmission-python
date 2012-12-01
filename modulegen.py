import sys
import os.path

sys.path.append('/usr/local/lib/python2.7/site-packages/')

from pybindgen import Module, FileCodeSink, ReturnValue, param, retval, cppclass, typehandlers, Parameter, CppClass

from pybindgen.module import SubModule, MultiSectionFactory

from pybindgen.typehandlers.base import PointerReturnValue, PointerParameter

import pybindgen.settings
import warnings

class ErrorHandler(pybindgen.settings.ErrorHandler):
    def handle_error(self, wrapper, exception, traceback_):
        warnings.warn("exception %r in wrapper %s" % (exception, wrapper))
        return True

pybindgen.settings.error_handler = ErrorHandler()
pybindgen.settings.min_python_version = (3, 0)
pybindgen.settings.unblock_threads = True

SHA_DIGEST_LENGTH = 20

_header = """/*
 *
 * Copyright (c) 2012 Dan Eicher
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 *
 */
"""

class TrMultiSectionFactory(MultiSectionFactory):

    def __init__(self, main_file_name):
        self.main_file_name = main_file_name
        self.main_sink = FileCodeSink(open('src/'+main_file_name, "wt"))
        self.header_name = "tr_module.h"
        header_file_name = os.path.join(os.path.dirname(self.main_file_name), self.header_name)
        self.header_sink = FileCodeSink(open('src/'+header_file_name, "wt"))
        self.section_sinks = {}

        self.main_sink.writeln(_header)
        self.header_sink.writeln(_header)

    def get_section_code_sink(self, section_name):
        if section_name == '__main__':
            return self.main_sink
        try:
            return self.section_sinks[section_name]
        except KeyError:
            file_name = os.path.join(os.path.dirname(self.main_file_name), "src/%s.cc" % section_name)
            sink = FileCodeSink(open(file_name, "wt"))
            self.section_sinks[section_name] = sink
            sink.writeln(_header)
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

def tr_instance_creation_function(cpp_class, code_block, lvalue,
                                       parameters, construct_type_name):
    code_block.write_code("%s = (%s*)tr_memdup(&%s, sizeof(%s));"
                           % (lvalue, construct_type_name, parameters, construct_type_name))


class TrFreeFunctionPolicy(cppclass.MemoryPolicy):
    def __init__(self, free_function):
        super(TrFreeFunctionPolicy, self).__init__()
        self.free_function = free_function

    def get_delete_code(self, cpp_class):
        delete_code = ("if (self->obj) {\n"
                       "    %stmp = self->obj;\n"
                       "    self->obj = NULL;\n"
                       "    if (!(self->flags & PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED))\n"
                       "        %s(tmp);\n"
                       "}"
                       % (self.get_pointer_type(cpp_class.full_name), self.free_function))
        return delete_code

    def get_instance_creation_function(self):
        return tr_instance_creation_function

    def __repr__(self):
        return 'TrFreeFunctionPolicy(%r)' % self.free_function


def tr_benc_instance_creation_function(cpp_class, code_block, lvalue,
                                       parameters, construct_type_name):
    code_block.write_code("%s = tr_new0(%s, 1);" % (lvalue, cpp_class.full_name))

class BencMemoryPolicy(cppclass.MemoryPolicy):
    def get_delete_code(self, cpp_class):
        return ("if (self->obj) {\n"
                "    tr_benc *tmp = self->obj;\n"
                "    self->obj = NULL;\n"
                "    if (!(self->flags & PYBINDGEN_WRAPPER_FLAG_OBJECT_NOT_OWNED)) {\n"
                "        tr_bencFree(tmp);\n"
                "        tr_free(tmp);\n"
                "    }\n"
                "}")

    def get_pointer_type(self, class_full_name):
        return "tr_benc *"

    def get_instance_creation_function(self):
        return tr_benc_instance_creation_function

    def __repr__(self):
        return 'BencMemoryPolicy()'

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


''' # need to figure out how to pass a PyDateTime_TZInfoType
class PyDateTimeParam(Parameter):
    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = ['time_t']

    def convert_python_to_c(self, wrapper):
        name = wrapper.declarations.declare_variable('PyObject *', self.value)
        tm_time = wrapper.declarations.declare_variable('struct tm', self.value+'_tm')
        wrapper.parse_params.add_parameter("0!", ['&PyDateTimeAPI->DateTimeType', '&'+name])
        wrapper.before_call.write_code('%s.tm_year = PyDateTime_GET_YEAR(%s);' % (tm_time, name))
        wrapper.before_call.write_code('%s.tm_mon  = PyDateTime_GET_MONTH(%s);' % (tm_time, name))
        wrapper.before_call.write_code('%s.tm_mday = PyDateTime_GET_DAY(%s);' % (tm_time, name))
        wrapper.before_call.write_code('%s.tm_hour = PyDateTime_DATE_GET_HOUR(%s);' % (tm_time, name))
        wrapper.before_call.write_code('%s.tm_min  = PyDateTime_DATE_GET_MINUTE(%s);' % (tm_time, name))
        wrapper.before_call.write_code('%s.tm_sec  = PyDateTime_DATE_GET_SECOND(%s);' % (tm_time, name))
        wrapper.call_params.append('mktime(&%s)' % tm_time)


class PyDateTimeReturn(PointerReturnValue):
    CTYPES = ['time_t']

    def get_c_error_return(self):
        return "return NULL;"
    
    def convert_c_to_python(self, wrapper):
        tmp = wrapper.declarations.declare_variable('PyObject *', 'tmp')
        py_time = wrapper.declarations.declare_variable('PyObject *', 'py_time')
        wrapper.after_call.write_code('if (%s) {' % self.value)
        wrapper.after_call.indent()
        wrapper.after_call.write_code('%s = Py_BuildValue((char *) "(l)", %s);'
                                       % (tmp, self.value))
        wrapper.after_call.write_code('%s = PyDateTime_FromTimestamp(%s);' % (py_time, tmp))
        wrapper.after_call.write_code('//Py_DECREF(%s);' % (tmp))
        wrapper.after_call.unindent()
        wrapper.after_call.write_code('}')
        wrapper.after_call.write_code('else {\n'
                                      '    %s = PyLong_FromLong(0);\n'
                                      '}' % py_time)
        wrapper.build_params.add_parameter("N", [py_time])
'''

class CharPtrLenParam(PointerParameter):

    DIRECTIONS = [Parameter.DIRECTION_IN]
    CTYPES = []

    def convert_python_to_c(self, wrapper):
        name = wrapper.declarations.declare_variable(self.ctype, self.name)
        name_len = wrapper.declarations.declare_variable("Py_ssize_t", self.name+'_len')
        wrapper.parse_params.add_parameter('s#', ['&'+name, '&'+name_len], self.value)
        wrapper.call_params.append(name)
        wrapper.call_params.append(name_len)


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
    module.end_section('tr_info')

    ## tr_tracker.cc
    module.begin_section('tr_tracker')
    module.add_struct('tr_tracker_info',
                      no_constructor=True,
                      no_copy=True,
                      custom_name='TrackerInfo')

    module.add_struct('tr_tracker_stat',
                      no_constructor=True,
                      no_copy=True,
                      free_function='tr_free',
                      custom_name='TrackerStats')
    module.end_section('tr_tracker')

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
    register_Tr_file_methods(root_module, root_module['tr_file'])
    register_Tr_file_stat_methods(root_module, root_module['tr_file_stat'])
    register_Tr_info_methods(root_module, root_module['tr_info'])
    register_Tr_msg_list_methods(root_module, root_module['tr_msg_list'])
    register_Tr_peer_stat_methods(root_module, root_module['tr_peer_stat'])
    register_Tr_piece_methods(root_module, root_module['tr_piece'])
    register_Tr_session_stats_methods(root_module, root_module['tr_session_stats'])
    register_Tr_stat_methods(root_module, root_module['tr_stat'])
    register_Tr_tracker_info_methods(root_module, root_module['tr_tracker_info'])
    register_Tr_tracker_stat_methods(root_module, root_module['tr_tracker_stat'])
    register_Tr_ctor_methods(root_module, root_module['tr_ctor'])
    register_Tr_session_methods(root_module, root_module['tr_session'])
    register_Tr_torrent_methods(root_module, root_module['tr_torrent'])
    register_Tr_benc_methods(root_module, root_module['Benc'])
    register_Tr_benc_bool_methods(root_module, root_module['BencBool'])
    register_Tr_benc_int_methods(root_module, root_module['BencInt'])
    register_Tr_benc_real_methods(root_module, root_module['BencReal'])
    register_Tr_benc_string_methods(root_module, root_module['BencString'])
    register_Tr_benc_list_methods(root_module, root_module['BencList'])
    register_Tr_benc_dict_methods(root_module, root_module['BencDict'])
    return

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

def register_Tr_file_methods(root_module, cls):
    cls.add_instance_attribute('dnd', 'int8_t', is_const=True, custom_name='do_not_download')  # XXX: bool?
    cls.add_instance_attribute('firstPiece', 'tr_piece_index_t', is_const=True, custom_name='first_piece')
    cls.add_instance_attribute('lastPiece', 'tr_piece_index_t', is_const=True, custom_name='last_piece')
    cls.add_instance_attribute('length', 'uint64_t', is_const=True)
    cls.add_instance_attribute('name', 'char *', is_const=True)
    cls.add_instance_attribute('offset', 'uint64_t', is_const=True)
    cls.add_instance_attribute('priority', 'int8_t', is_const=True)
    return

def register_Tr_file_stat_methods(root_module, cls):
    cls.add_instance_attribute('bytesCompleted', 'uint64_t', is_const=True, custom_name='bytes_completed')
    cls.add_instance_attribute('progress', 'float', is_const=True)
    return

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
    cls.add_instance_attribute('hash', ReturnValue.new('uint8_t *', is_const=True,
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
                               ReturnValue.new('char **', 
                                               array_length="self->obj->webseedCount"),
                               is_const=True)
    return

def register_Tr_msg_list_methods(root_module, cls):
    cls.add_instance_attribute('file', 'char const *', is_const=True)
    cls.add_instance_attribute('level', 'tr_msg_level', is_const=True)
    cls.add_instance_attribute('line', 'int', is_const=True)
    cls.add_instance_attribute('message', 'char *', is_const=True)
    cls.add_instance_attribute('name', 'char *', is_const=True)
    cls.add_instance_attribute('when', 'time_t', is_const=True)
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

def register_Tr_piece_methods(root_module, cls):
    cls.add_instance_attribute('timeChecked', 'time_t', is_const=True, custom_name='time_checked')
    cls.add_instance_attribute('hash', ReturnValue.new('uint8_t *', is_const=True,
                                                       array_length=SHA_DIGEST_LENGTH),
                               is_const=True)
    cls.add_instance_attribute('priority', 'int8_t', is_const=True)
    cls.add_instance_attribute('dnd', 'int8_t', is_const=True, custom_name='do_not_download')
    return

def register_Tr_session_stats_methods(root_module, cls):
    cls.add_instance_attribute('downloadedBytes', 'uint64_t', is_const=True, custom_name='downloaded_bytes')
    cls.add_instance_attribute('filesAdded', 'uint64_t', is_const=True, custom_name='files_added')
    cls.add_instance_attribute('ratio', 'float', is_const=True)
    cls.add_instance_attribute('secondsActive', 'uint64_t', is_const=True, custom_name='seconds_active')
    cls.add_instance_attribute('sessionCount', 'uint64_t', is_const=True, custom_name='session_count')
    cls.add_instance_attribute('uploadedBytes', 'uint64_t', is_const=True, custom_name='uploaded_bytes')
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



def register_functions(root_module):
    module = root_module

    module.add_function('tr_sessionLoadSettings', 
                        ErrorCheckReturn('bool', exception='PyExc_ValueError',
                                         error_string='"unable to load settings"',
                                         error_cleanup='Py_DECREF(py_dictionary);\n'),
                        [BencOutParam('BencDict *', 'dictionary'),
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
                        [BencOutParam('BencDict *', 'dictionary')],
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
                        [ListParam('Torrent', 'torrents')],
                        custom_name='queue_move_up',
                        docstring="Move Torrents up in download queue\\n\\n"
                                  "Args:\\n"
                                  "    torrents (list): Torrents to move\\n")

    module.add_function('tr_torrentsQueueMoveDown', 
                        'void', 
                        [ListParam('Torrent', 'torrents')],
                        custom_name='queue_move_down',
                        docstring="Move Torrents down in download queue\\n\\n"
                                  "Args:\\n"
                                  "    torrents (list): Torrents to move\\n")

    module.add_function('tr_torrentsQueueMoveTop', 
                        'void', 
                        [ListParam('Torrent', 'torrents')],
                        custom_name='queue_move_top',
                        docstring="Move Torrents to top of download queue\\n\\n"
                                  "Args:\\n"
                                  "    torrents (list): Torrents to move\\n")

    module.add_function('tr_torrentsQueueMoveBottom', 
                        'void', 
                        [ListParam('Torrent', 'torrents')],
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

def main():
    out = TrMultiSectionFactory('tr_module.cc')
    root_module = module_init()
    register_types(root_module)
    register_methods(root_module)
    register_functions(root_module)
    root_module.generate(out)

if __name__ == '__main__':
    main()
