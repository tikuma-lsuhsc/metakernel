# Copyright (c) Metakernel Development Team.
# Distributed under the terms of the Modified BSD License.

from metakernel import Magic, option
try:
    import jedi
except ImportError:
    jedi = None
else:
    from jedi import Interpreter
    from jedi.api.helpers import completion_parts
    from jedi.parser.user_context import UserContext


class PythonMagic(Magic):

    def __init__(self, kernel):
        super(PythonMagic, self).__init__(kernel)
        self.env = globals()['__builtins__']
        self.retval = None

    def line_python(self, *args):
        """
        %python CODE - evaluate code as Python

        This line magic will evaluate the CODE (either expression or
        statement) as Python code.

        Examples:
            %python x = 42
            %python import math
            %python x + math.pi

        """
        code = " ".join(args)
        self.retval = self.eval(code)

    def eval(self, code):
        self.env["kernel"] = self.kernel
        try:
            return eval(code.strip(), self.env)
        except:
            try:
                exec(code.strip(), self.env)
            except Exception as exc:
                return "Error: " + str(exc)
        if "retval" in self.env:
            return self.env["retval"]

    @option(
        "-e", "--eval_output", action="store_true", default=False,
        help="Use the retval value from the Python cell as code in the kernel language."
    )
    def cell_python(self, eval_output=False):
        """
        %%python - evaluate contents of cell as Python

        This cell magic will evaluate the cell (either expression or
        statement) as Python code.

        Unlike IPython's Python, this does not return the last expression.
        To do that, you need to assign the last expression to the special
        variable "retval".

        The -e or --eval_output flag signals that the retval value expression
        will be used as code for the cell to be evaluated by the host 
        language.

        Examples:
            %%python 
            x = 42

            %%python 
            import math
            retval = x + math.pi

            %%python -e
            retval = "'(this is code in the kernel language)"

            %%python -e
            "'(this is code in the kernel language)"

        """
        if self.code.strip():
            if eval_output:
                self.eval(self.code)
                self.code = str(self.env["retval"]) if ("retval" in self.env and 
                                                        self.env["retval"] != None) else ""
                self.retval = None
                self.env["retval"] = None
                self.evaluate = True
            else:
                self.retval = self.eval(self.code)
                self.env["retval"] = None
                self.evaluate = False

    def post_process(self, retval):
        if retval is not None:
            return retval
        else:
            return self.retval

    def get_completions(self, info):
        '''Get Python completions'''
        # https://github.com/davidhalter/jedi/blob/master/jedi/utils.py
        if jedi is None:
            return []

        text = info['code']
        interpreter = Interpreter(text, [self.env])

        position = (info['line_num'], info['column'])
        path = UserContext(text, position).get_path_until_cursor()
        path, dot, like = completion_parts(path)
        before = text[:len(text) - len(like)]

        completions = interpreter.completions()

        completions = [before + c.name_with_symbols for c in completions]

        return [c[info['start']:] for c in completions]

    def get_help_on(self, info, level=0, none_on_fail=False):
        """Implement basic help for functions"""

        if not info['code']:
            return None if none_on_fail else ''

        last = info['obj']

        default = None if none_on_fail else ('No help available for "%s"' % last)

        parts = last.split('.')

        obj = self.env.get(parts[0], None)

        if not obj:
            return default

        for p in parts[1:]:

            obj = getattr(obj, p, None)

            if not obj:
                return default

        if level == 0:
            return getattr(obj, '__doc__', str(help(obj)))
        else:
            return str(help(obj))


def register_magics(kernel):
    kernel.register_magics(PythonMagic)
