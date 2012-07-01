
# var X = 4  ; Var(Name("X"), Num(4))            # ==> adds 'x = 4' to env
# X          ; Chain([Name("X")])                # ==> 4
# Y.Z        ; Chain([Name("Y"), Name("Z")])     # lookup in dict
# W(Z=4)     ; Chain([Name("Y"), Dict({"Z":4})]) # function call
# (Z=4)["Z"] ; Chain([Dict({"Z":4})])            # lookup of literal
# 4.toStr[]  ; Chain([Num(4), Name("toStr"), List([])]) # call literal
# "hello{x}".format(x="dave")


# Statement
#   var           Var(Name, Chain?)
#   def           Def(Name, Chain)
#   set           Set(Name, Chain)
#   inc           Inc(Name)
#   Value
#     name        Name(string)
#     num         Number(num)
#     string      String(string)
#     dict        Dict(dict: Name -> Chain)
#     list        List(list: Chain)
#     code-block  Code(list: Statement)
#     data-type   ??
#  call-chain     Chain(list: Value)


class Statement(object):
    def __init__(self, kind):
        super(Statement, self).__init__()
        self.kind = kind # string

    def as_string(self, indent):
        raise Exception("cannot stringify: " + self.kind)

    def call(self, this, args, env):
        raise Exception("cannot call: " + self.kind)

    def evaluate(self, env):
        raise Exception("cannot evaluate: " + self.kind)

    def lookup(self, key):
        raise Exception("cannot lookup: " + self.kind)


class Var(Statement):
    def __init__(self, name, chain):
        super(Var, self).__init__("var")
        self.name = name   # chain
        self.chain = chain # chain | none

    def as_string(self, indent):
        if self.chain:
            return "var " + self.name + " = " + self.chain.as_string(indent)
        else:
            return "var " + self.name
            
    def evaluate(self, env):
        assert self.name not in env.data.keys()
        if self.chain:
            res = self.chain.evaluate(env)
            env.data[self.name] = res
            return res
        else:
            env.data[self.name] = None
            return None


class Def(Statement):
    def __init__(self, name, chain):
        super(Def, self).__init__("def")
        self.name = name   # chain
        self.chain = chain # chain

    def as_string(self, indent):
        return "def " + self.name + " = " + self.chain.as_string(indent)

    def evaluate(self, env):
        assert self.name not in env.data.keys()
        res = self.chain.evaluate(env)
        env.data[self.name] = res
        return res

class Set(Statement):
    def __init__(self, name, chain):
        super(Set, self).__init__("set")
        self.name = name   # name
        self.chain = chain # chain

    def as_string(self, indent):
        return "set " + self.name + " = " + self.chain.as_string(indent)

    def evaluate(self, env):
        assert self.name in env.data.keys()
        res = self.chain.evaluate(env)
        env.data[self.name] = res
        return res


class Inc(Statement):
    def __init__(self, name):
        super(Inc, self).__init__("inc")
        self.name = name # name

    def as_string(self, indent):
        return "inc " + self.name

    def evaluate(self, env):
        raise NotImplementedError() # TODO: Inc.evaluate


class Name(Statement):
    def __init__(self, data):
        super(Name, self).__init__("name")
        self.data = data # string

    def as_string(self, indent):
        return self.data

    def evaluate(self, env):
        return env.lookup(self.data)


class Number(Statement):
    def __init__(self, data):
        super(Number, self).__init__("number")
        self.data = int(data) # integer

    def as_string(self, indent):
        return str(self.data)

    def evaluate(self, env):
        return self


class String(Statement):
    def __init__(self, data):
        super(String, self).__init__("string")
        self.data = data # string

    def as_string(self, indent):
        return "\"" + self.data + "\""

    def evaluate(self, env):
        return self


class Dict(Statement):
    def __init__(self, data):
        super(Dict, self).__init__("dict")
        self.data = data # {name => chain}

    def as_string(self, indent):
        ret = ", ".join(key.as_string(indent) + " = " + val.as_string(indent) for key,val in self.data.items())
        return "(" + ret + ")"

    def evaluate(self, env):
        ret = {}
        for key,val in self.data.items():
            ret[key] = val.evaluate(env)
        return Dict(ret)

    def call(self, this, args, env):

        # e.g. (a=1, b=2)[a] --> 1
        # e.g. (a=1, b=2)(x=a) --> 1
        if args.kind == "list":
            val = args.data[0]
            assert val.kind == "name"
            return self.data[val.data]
        else:
            assert args.kind == "dict"
            val = args.data["x"]
            assert val.kind == "name"
            return self.data[val.data]

    def lookup(self, key):
        if key in self.data:
            return self.data[key]
        assert "_parent" in self.data, "failed lookup of " + key
        return self.data["_parent"].lookup(key)

class List(Statement):
    def __init__(self, data):
        super(List, self).__init__("list")
        self.data = data  # [chain]

    def as_string(self, indent):
        return "[" + ", ".join(x.as_string(indent) for x in self.data) + "]"

    def evaluate(self, env):
        return List([val.evaluate(env) for val in self.data])

    def call(self, this, args, env):

        # list.call = function(x) { return data[x] }
        # e.g. ["a", "b"][0] --> "a"
        # e.g. ["a", "b"](x=1) --> "b"

        if args.kind == "list":
            val = args.data[0]
            assert val.kind == "number"
            return self.data[val.data]
        else:
            assert args.kind == "dict"
            val = args.data["x"]
            assert val.kind == "number"
            return self.data[val.data]


class Code(Statement):
    def __init__(self, statements, arg_list=None, arg_rest=None):
        super(Code, self).__init__("code")
        self.statements = statements # [statement]
        self.arg_list = arg_list     # [name]
        self.arg_rest = arg_rest     # name 

    def as_string(self, indent):
        if self.arg_list is None and self.arg_rest is None:
            if len(self.statements) == 0:
                return "{}"
            ret = "{\n" + indent + "  "
        else:
            raise NotImplementedError() # TODO: print code with args
        string_args = [x.as_string(indent + "  ") for x in self.statements]
        ret += (";\n" + indent + "  ").join(string_args)
        ret += ";\n" + indent + "}"
        return ret

    def evaluate(self, env):
        return self

    def call(self, this, args, env):

        # make a new environment with some special entries
        newEnv = Dict({
                "__parent": env,
                "__this": this,
                "__args": args
                })
        newEnv.data["__frame"] = newEnv
        # TODO: add 'this' to newEnv so we dont have to do the gay
        # python thing of self.x everywhere

        if self.arg_list is None and self.arg_rest is None:

            res = None
            for statement in self.statements:
                res = statement.evaluate(newEnv)
            return res

        else:
            raise NotImplementedError() # TODO: call code with args
        

class Chain(Statement):
    def __init__(self, parts):
        super(Chain, self).__init__("chain")
        self.parts = parts # value|vame + [name|list|dict]

    def as_string(self, indent):
        ret = [self.parts[0].as_string(indent)]
        for x in self.parts[1:]:
            if x.kind == "name":
                ret += "."
            ret += x.as_string(indent)
        return "".join(ret)

    def evaluate(self, env):

        # x
        # 5
        # ("y"=9.add[4])

        part0 = self.parts[0]
        val0 = part0.evaluate(env)
        if len(self.parts) == 1:
            return val0

        # x.y             --> x must evaluate to lookupable
        # x[y]            --> x must evaluate to callable
        # x("y"=9.add[4]) --> x must evaluate to callable

        part1 = self.parts[1]
        if part1.kind == "name":
            val1 = val0.lookup(part1)
        elif part1.kind == "list" or part1.kind == "dict":
            val1 = val0.call(None, part1.evaluate(env), env)
        else:
            raise "expected name list or dict"
        
        if len(self.parts) == 2:
            return val1

        # x.y.z        --> x and x.y must evaluate to lookupable
        # next.eq[":"] --> next must evaluate to lookupable, nex.eq must evaluate to callable
        # 4.add[7]     --> val1 => evaluate(4.add) => code
        # x[2][7]      --> 

        part2 = self.parts[2]
        if part2.kind == "name":
            val2 = val1.lookup(part2)
        elif part2.kind == "list" or part2.kind == "dict":
            val2 = val1.call(val0, part2.evaluate(base), env)
        else:
            raise "expected name list or dict"

        if len(self.parts) == 3:
            return val2

        raise NotImplementedError() # TODO: evaluate long chains


def test_evaluator():
    from parse import Parser
    from lex import Tokenizer, mockfile

    test_list = """
# NEXT 4;
# NEXT def x = 4; x;
# NEXT def x = ["a", "b"]; x;
# NEXT def x = ["a", "b"]; x[0];
# NEXT ["a", "b"][0];
""".split("# NEXT")

    print "-"*50
    for inputString in test_list:

        tokenizer = Tokenizer(mockfile(inputString), False)
        tokenList = tokenizer.read_all()
        tokenString = tokenizer.as_string()

        parser = Parser(tokenList)
        code = parser.read_all()
        codeString = parser.as_string()

        env = Dict({Name("y"): Number("7")})
        result = code.call(None, None, env)

        print inputString.strip()
        print tokenString
        print codeString
        if result is not None:
            print result.as_string("")
        else:
            print None
        print "-"*50


if __name__ == '__main__':
    test_evaluator()
