import StringIO
from evaluate import Var, Def, Set, Inc, Name, Number, String, Dict, List, Code, Chain

# * Any literals (in quotes) or regexps (==>) can have any amount of
#   whitespace including none. Note that special statements have at
#   least one whitespace char after them. 
#
# * Names must not be 'var' 'def' 'inc' or 'set'
#
# statement ::=
#     "def" whitespace lookup = chain
#     "var" whitespace lookup (= chain)?
#     "set" whitespace lookup = chain
#     "inc" whitespace lookup
#     chain
#
# lookup ::= name ("." name)*
# chain  ::= (name | value) (list | dict | ("." name) )* 
# value  ::= num | string | dict | list | code
# 
# name   ==> [A-Za-z][A-Za-z_0-9\-]* # cannot be: var, def, set, inc
# num    ==> -?[0-9]+(\.[0-9]+)?
# string ==> \"[^\"]*\"
#
# list ::=
#     "[" "]"
#     "[" (chain ",")* chain? "]"
#
# dict ::= 
#     "(" ")"
#     "(" (string "=" chain ",")* (string "=" chain)? ")"
#
# code ::=
#     args? "{" "}"
#     args? "{" (statement ";")* statement? "}"
# 
# args ::=
#     "!" "[" "]"
#     "!" "[" (name ",")* name? "]"
#

protected_names = set("var def inc set".split())

class Parser():
    def __init__(self, tokens):
        self.tokens = [("LITERAL", "{")] + tokens + [("LITERAL", "}")]
        self.current_token = 0
        self.code = None

    def read_all(self):
        if self.code is None:
            self.code = self.read_code()
        return self.code

    def as_string(self):
        if self.code is None:
            self.read_all()
        return self.code.as_string("")

    def read(self):
        self.current_token += 1
        return self.tokens[self.current_token-1]

    def skip_literal(self, val):
        assert self.is_literal(val)
        self.read()

    def read_special(self):
        assert self.is_special()
        return self.read()[1]

    def peek(self):
        return self.tokens[self.current_token] 

    def is_literal(self, val):
        return self.peek()[0] == "LITERAL" and self.peek()[1] == val

    def is_special(self):
        return self.peek()[0] == "SPECIAL"

    def read_statement(self):
        if self.is_special():
            kind = self.read_special()

            name = self.read()
            assert name[0] == "NAME"

            if not self.is_literal("="):
                if kind == "var": 
                    return Var(name[1], None)
                else:
                    assert kind == "inc"
                    return Inc(name[1])
            else:
                self.skip_literal("=")
                chain = self.read_chain()
                if kind == "var":
                    return Var(name[1], chain)
                elif kind == "def":
                    return Def(name[1], chain)
                else:
                    assert kind == "set"
                    return Set(name[1], chain)
        else:
            return self.read_chain()

    def read_chain(self):
        chain = []

        if self.peek()[0] == "NAME":
            chain.append(Name(self.read()[1]))
        else:
            chain.append(self.read_value())

        while True:
            if self.is_literal("["):
                chain.append(self.read_list())
            elif self.is_literal("("):
                chain.append(self.read_dict())
            elif self.is_literal("."):
                self.skip_literal(".")
                chain.append(Name(self.read()[1]))
            else:
                break

        return Chain(chain)

    def read_value(self):
        tok = self.peek()
        if tok[0] == "NUMBER":
            return self.read_number()
        elif tok[0] == "STRING":
            return self.read_string()
        elif self.is_literal("["):
            return self.read_list()
        elif self.is_literal("("):
            return self.read_dict()
        else:
            return self.read_code()

    def read_name(self):
        tok = self.read()
        assert tok[0] == "NAME"
        assert tok[1] not in protected_names
        return Name(tok[1])

    def read_number(self):
        tok = self.read()
        assert tok[0] == "NUMBER"
        return Number(tok[1])

    def read_string(self):
        tok = self.read()
        assert tok[0] == "STRING"
        return String(tok[1])

    def read_list(self, names_only = False):
        self.skip_literal("[")
        ret = []
        while not self.is_literal("]"):
            if names_only:
                ret.append(self.read_name().data)
            else:
                ret.append(self.read_chain())
            if not self.is_literal(","):
                break
            else:
                self.skip_literal(",")
                continue

        if not self.is_literal("]"):
            if names_only:
                ret.append(self.read_name().data)
            else:
                ret.append(self.read_chain())
        self.skip_literal("]")

        if names_only:
            return ret
        else:
            return List(ret)

    def read_dict(self):
        self.skip_literal("(")
        ret = {}
        while not self.is_literal(")"):
            name = self.read_name()
            self.skip_literal("=")
            value = self.read_chain()
            ret[name.data] = value
            if not self.is_literal(","):
                break
            else:
                self.skip_literal(",")
                continue
        if not self.is_literal(")"):
            name = self.read_name()
            self.skip_literal("=")
            value = self.read_chain()
            ret[name.data] = value
        self.skip_literal(")")
        return Dict(ret)

    def read_code(self):
        
        if self.is_literal("!"):
            self.skip_literal("!")
            args = self.read_list(True)
        else:
            args = []
            
        self.skip_literal("{")
        ret = []
        while not self.is_literal("}"):
            ret.append(self.read_statement())
            if not self.is_literal(";"):
                break
            else:
                self.skip_literal(";")
                continue
        if not self.is_literal("}"):
            ret.append(self.read_statement())
        self.skip_literal("}")
        return Code(ret, args)


def test_parser():
    from lex import Tokenizer, mockfile

    test_list = """
# NEXT x;
# NEXT x.y;
# NEXT (x=1);
# NEXT x.y[5][{ inc bob; }, "hello"](x=6);
# NEXT (a=1, b=2)(x=a);
# NEXT ![x] { 4;};
# NEXT ![x, y] { x;};
""".split("# NEXT")

    print "-"*50
    for inputString in test_list:

        tokenizer = Tokenizer(mockfile(inputString), False)
        tokenList = tokenizer.read_all()
        tokenString = tokenizer.as_string()

        parser = Parser(tokenList)
        code = parser.read_all()
        codeString = parser.as_string()
        
        print inputString.strip()
        print tokenString
        print codeString
        print "-"*50


if __name__ == '__main__':
    test_parser()
