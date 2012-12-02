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

from pybindgen.cppclass import MemoryPolicy

class TrFreeFunctionPolicy(MemoryPolicy):
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
        def instance_creation_function(cpp_class, code_block, lvalue,
                                       parameters, construct_type_name):
            code_block.write_code("%s = (%s*)tr_memdup(&%s, sizeof(%s));"
                                  % (lvalue, construct_type_name,
                                     parameters, construct_type_name))

        return instance_creation_function

    def __repr__(self):
        return 'TrFreeFunctionPolicy(%r)' % self.free_function


class BencMemoryPolicy(MemoryPolicy):
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
        def instance_creation_function(cpp_class, code_block, lvalue,
                                       parameters, construct_type_name):
            code_block.write_code("%s = tr_new0(%s, 1);" %
                                  (lvalue, cpp_class.full_name))

        return instance_creation_function

    def __repr__(self):
        return 'BencMemoryPolicy()'

