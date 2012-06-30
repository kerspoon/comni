
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
        self.kind = kind

    def call(self, this, args, env):
        raise Exception("cannot call: " + self.kind)

    def eval(self, env):
        raise Exception("cannot eval: " + self.kind)

    def lookup(self, key):
        raise Exception("cannot lookup: " + self.kind)


class Var(Statement):
    def __init__(self, name, chain):
        super(Var, self).__init__("var")
        self.name = name
        self.chain = chain

    def as_string(self):
        if self.chain:
            return "var " + self.name + " = " + self.chain.to_string()
        else:
            return "var " + self.name
            
    def eval(self, env):
        raise NotImplementedError()


class Def(Statement):
    def __init__(self, name, chain):
        super(Def, self).__init__("def")
        self.name = name
        self.chain = chain

    def as_string(self):
        return "def " + self.name + " = " + self.chain.to_string()

    def eval(self, env):
        raise NotImplementedError()


class Set(Statement):
    def __init__(self, name, chain):
        super(Set, self).__init__("set")
        self.name = name
        self.chain = chain

    def as_string(self):
        return "set " + self.name + " = " + self.chain.to_string()

    def eval(self, env):
        raise NotImplementedError()


class Inc(Statement):
    def __init__(self, name):
        super(Inc, self).__init__("inc")
        self.name = name

    def as_string(self):
        return "inc " + self.name

    def eval(self, env):
        raise NotImplementedError()


class Name(Statement):
    def __init__(self, name):
        super(Name, self).__init__("name")
        self.name = name

    def as_string(self):
        return self.name

    def eval(self, env):
        return env.lookup(self.name)


class Number(Statement):
    def __init__(self, name):
        super(Number, self).__init__("number")
        self.name = name

    def as_string(self):
        return self.name

    def eval(self, env):
        return self


class String(Statement):
    def __init__(self, name):
        super(String, self).__init__("string")
        self.name = name

    def as_string(self):
        return "\"" + self.name + "\""

    def eval(self, env):
        return self


class Dict(Statement):
    def __init__(self, data):
        super(Dict, self).__init__("dict")
        self.data = data

    def as_string(self):
        ret = ", ".join(key.as_string() + " = " + val.as_string() for key,val in self.data.items())
        return "(" + ret + ")"

    def eval(self, env):
        ret = {}
        for key,val in self.data.items():
            ret[key] = val.eval(env)
        return Dict(ret)

    def call(self):
        # get the args[0] element of it
        # return self.data[args[0]]
        raise NotImplementedError()


class List(Statement):
    def __init__(self, data):
        super(List, self).__init__("list")
        self.data = data

    def as_string(self):
        return "[" + ", ".join(x.as_string() for x in self.data) + "]"

    def eval(self, env):
        return List([val.eval(env) for val in self.data])

    def call(self):
        # get the args[0] element of it
        # return self.data[args[0]]
        raise NotImplementedError()


class Code(Statement):
    def __init__(self, statements):
        super(Code, self).__init__("code")
        self.statements = statements

    def as_string(self):
        return "{\n" + ";\n".join(x.as_string() for x in self.statements) + ";\n}"

    def eval(self, env):
        return self

    def call(self):
        raise NotImplementedError()


class Chain(Statement):
    def __init__(self, parts):
        super(Chain, self).__init__("chain")
        # list of name list or dict
        self.parts = parts

    def as_string(self):
        ret = [self.parts[0].as_string()]
        for x in self.parts[1:]:
            if x.kind == "name":
                ret += "."
            ret += x.as_string()
        return "".join(ret)

    def eval(self, env):

        # x
        # 5
        # ("y"=9.add[4])

        part0 = self.parts[0]
        val0 = part0.eval(env)
        if len(self.parts) == 1:
            return val0

        # x.y             --> x must eval to lookupable
        # x[y]            --> x must eval to callable
        # x("y"=9.add[4]) --> x must eval to callable

        part1 = self.parts[1]
        if part1.isName():
            val1 = val0.lookup(part1)
        elif part1.isList() or part1.isDict():
            val1 = val0.call(None, part1.eval(env), env)
        else:
            raise "expected name list or dict"
        
        if len(self.parts) == 2:
            return val1

        # x.y.z        --> x and x.y must eval to lookupable
        # next.eq[":"] --> next must eval to lookupable, nex.eq must eval to callable
        # 4.add[7]     --> val1 => eval(4.add) => code
        # x[2][7]      --> 

        part2 = self.parts[2]
        if part2.isName():
            val2 = val1.lookup(part2)
        elif part2.isList() or part2.isDict():
            val2 = val1.call(val0, part2.eval(base), env)
        else:
            raise "expected name list or dict"

        if len(self.parts) == 3:
            return val2

        assert "not implemented" # TODO: eval long chains

