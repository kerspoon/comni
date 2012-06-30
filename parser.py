import StringIO


class Statement():
    def __init__(self, kind):
        self.kind = kind
        pass

    def call(self, this, args, env):
        pass

    def eval(self, env):
        pass

class Chain():
    def __init__(self, parts):
        self.kind = "chain"
        self.parts = parts

    def eval(self, env):

        # x
        # x.y
        # x[y]
        # x.y.z
        # next.eq[":"]

        val = self.parts[0].eval(env)  # "next"

        if len(self.parts) == 1:
            return val
        elem = self.parts[1]

        if elem.isName():
            evald = val.lookup(elem) # aka eval # function eq(){..}
        elif elem.isList() or elem.isDict():
            evald = val.call(None, elem, env)
        else:
            raise "expected name list or dict"

        if len(self.parts) == 2:
            return evald
        elem = self.parts[2] # list [":"]
        
        if elem.isName():
            evald = elem.lookup(evald) # aka eval
        elif elem.isList() or elem.isDict():
            evald = evald.call(val, elem, env)  # fn_equal("next", [":"], env) 
        else:
            raise "expected name list or dict"
        


        # val = parts[0].eval(env) --> Value
        # parts[1] is Name, List, Dict, Nil
        # if Nil return
        # if List val.call(this=env, args=parts[1], env=env)
        # if Dict val.call(this=env, args=parts[1], env=env)
        # if Name 
        #   newVal = val.lookup(parts[1]) --> Value
        #   if no more parts: return newVal

        #   if Nil return
        #   if List val.call(this=env, args=parts[1], env=env)
        #   if Dict val.call(this=env, args=parts[1], env=env)
        #   



        n = 0
        elem = self.parts[n]
        evald = elem.eval(env)
        while(len(self.parts) != n+1):
            n += 1
            elem = self.parts[n]
            if elem.isList() or elem.isDict():
                evald = evald.call(elem, env)
            else:
                assert elem.isName()
                evald = elem.eval(evald)
        return evald


# var X = 4 ; Var(Name("X"), Num(4))            # ==> adds 'x = 4' to env
# X         ; Chain([Name("X")])                # ==> 4
# Y.Z       ; Chain([Name("Y"), Name("Z")])     # lookup in dict
# W(Z=4)    ; Chain([Name("Y"), Dict({"Z":4})]) # function call
# (Z=4).Z   ; Chain([Dict({"Z":4})])            # lookup of literal
# 4.toStr[] ; Chain([Num(4), Name("toStr"), List([])]) # call literal


class Number():
    def eval(self, env):
        return self



whitespace = set("\n\t ")
number_chars = set("1234567890-")
name_start_chars = set("qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM")
name_chars = name_start_chars | number_chars | set("_")
value_start_chars = number_chars | set("\"[(!{:")


class PeekableStream():
    
    def __init__(self, stream):
        self.stream = stream

    def read(self, n):
        return self.stream.read(n)

    def peek(self, n):
        loc = self.stream.tell()
        tmp = self.stream.read(n)
        self.stream.seek(loc)
        return tmp


class Tokenizer():

    def __init__(self, stream, debug):
        self.stream = stream
        self.tokens = []
        self.debug = debug

    def skip_whitespace(self):
        # TODO: deal with comments
        while(self.stream.peek(1) in whitespace):
            self.stream.read(1)

    def read_literal(self, lit):
        tmp = self.stream.read(len(lit))
        assert tmp == lit, "Expected " + lit + " got " + tmp
        self.tokens.append(("LITERAL", tmp))
        if self.debug: print self.tokens

    def read_special(self):
        self.tokens.append(("SPECIAL", self.stream.read(3)))
        if self.debug: print self.tokens

    def read_name(self):
        tmp = [self.stream.read(1)]
        assert tmp[0] in name_start_chars, "expected " + "".join(name_start_chars) + " got " + tmp[0]
        while(self.stream.peek(1) in name_chars):
            tmp.append(self.stream.read(1))
        self.tokens.append(("NAME", "".join(tmp)))
        if self.debug: print self.tokens

    def read_number(self):
        # TODO: deal with non integers (see JSON spec)
        tmp = []
        while(self.stream.peek(1) in number_chars):
            tmp.append(self.stream.read(1))
        self.tokens.append(("NUMBER", "".join(tmp)))
        if self.debug: print self.tokens

    def read_string(self):
        # TODO: deal with escaping '"' with '\'
        tmp = []

        quote = self.stream.read(1)
        assert quote == "\"", "expected '\"' got " + quote
        while(self.stream.peek(1) != "\""):
            tmp.append(self.stream.read(1))
        quote = self.stream.read(1)
        assert quote == "\"", "expected '\"' got " + quote

        self.tokens.append(("STRING", "".join(tmp)))
        if self.debug: print self.tokens

    def read_tokens(self):
        self.skip_whitespace()
        while(self.stream.peek(1)):
            self.read_statement()
            self.skip_whitespace()
            self.read_literal(";")
            self.skip_whitespace()
        return self.tokens
        
    def read_statement(self):
        self.skip_whitespace()
        three = self.stream.peek(3);

        if (three == "var" or three == "def" or three == "set"):
            self.read_special()
            self.skip_whitespace()
            self.read_name()
            self.skip_whitespace()
            # TODO: deal with datatypes
            if (self.stream.peek(1) == "="):
                self.read_literal("=")
                self.skip_whitespace()
                self.read_chain_or_value()
        elif (three == "inc"):
            self.read_special()
            self.skip_whitespace()
            self.read_chain_or_value()
        else:
            self.read_chain_or_value()

    def read_chain_or_value(self):
        while(True):
            self.skip_whitespace()
            if (self.stream.peek(1) in value_start_chars):
                self.read_value()
            else:
                self.read_name()

            # optional (do we allow 'thing . other')?
            self.skip_whitespace() 

            # second loop to deal with: a[1] [2].b(x=4)[5]
            while(True):
                if (self.stream.peek(1) == "."):
                    self.read_literal(".")
                    break
                elif (self.stream.peek(1) == "("):
                    self.read_dict()
                    self.skip_whitespace() 
                elif (self.stream.peek(1) == "["):
                    self.read_list()
                    self.skip_whitespace()
                else:
                    return

    def read_value(self):
        self.skip_whitespace()
        char = self.stream.peek(1)
        assert char in value_start_chars, "expected " + value_start_chars + " got " + char
        if (char in number_chars):
            self.read_number()
        elif (char == "\""):
            self.read_string()
        elif (char == "{" or char == "!"):
            self.read_code_block()
        elif (char == "("):
            self.read_dict()
        elif (char == "["):
            self.read_list()
        else:
            assert char == ":"
            raise "TODO: implement datatypes"

    def read_code_block(self):
        self.read_literal("{")
        self.skip_whitespace()
        while(True):
            if (self.stream.peek(1) == "}"):
                self.read_literal("}")
                return
            self.read_statement()
            self.skip_whitespace()
            if (self.stream.peek(1) == ";"):
                self.read_literal(";")
                self.skip_whitespace()
            else:
                self.read_literal("}")
                return

    def read_dict(self):
        self.read_literal("(")
        self.skip_whitespace()
        while(True):
            if (self.stream.peek(1) == ")"):
                self.read_literal(")")
                return
            self.read_name()
            self.skip_whitespace()
            self.read_literal("=")
            self.skip_whitespace()
            self.read_chain_or_value()
            self.skip_whitespace()
            if (self.stream.peek(1) == ","):
                self.read_literal(",")
                self.skip_whitespace()
            else:
                self.read_literal(")")
                return

    def read_list(self):
        self.read_literal("[")
        self.skip_whitespace()
        while(True):
            if (self.stream.peek(1) == "]"):
                self.read_literal("]")
                return
            self.read_chain_or_value()
            self.skip_whitespace()
            if (self.stream.peek(1) == ","):
                self.read_literal(",")
                self.skip_whitespace()
            else:
                self.read_literal("]")
                return

    def to_string(self):
        if len(self.tokens) == 0:
            self.read_tokens()
        res = []
        for tok in self.tokens:
            if tok[0] == "STRING":
                res.append("\"" + tok[1] + "\"")
            else:
                res.append(tok[1])
        return " ".join(res)



def mockfile(text):
    return PeekableStream(StringIO.StringIO(text))


def test_tokenizer():

    testlist = """
# NEXT (Z=4).Z;
# NEXT "boo".startswith["b"];
# NEXT [config.Get["shoe-size"]];
# NEXT [config.Get[6]];
# NEXT "boo";
# NEXT [x.y[7]];
# NEXT [x.y[7]];
# NEXT [x.y[]];
# NEXT [x.y];
# NEXT [x, 4];
# NEXT [];
# NEXT def x;
# NEXT var 
x 
= 
-45;
# NEXT set y = 2;
# NEXT 3;
# NEXT inc y ;
# NEXT inc y.x;
# NEXT A.Z.q1.r-f;
# NEXT a[1][2].b(x=4)[5];
# NEXT a [ 1 ] [ 2 ] . b ( x = 4 ) [ 5 ] ;
""".split("# NEXT")

    for test in testlist:
        toks = Tokenizer(mockfile(test), False)
        print toks.to_string()
        print toks.tokens
        print "-"*50

test_tokenizer()


class Parser():
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = 0
        self.statements = []

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

    def is_special(self, val):
        return self.peek()[0] == "SPECIAL"




    def parse(self):
        while len(self.tokens) > self.current_token:
            pass



    def read_statement(self):
        if self.is_special():
            kind = self.read_special()
            name = self.read()
            assert name[0] == "NAME"


            if self.is_literal("="):
                self.skip_literal("=")
                return Var(name[1], self.read_chain())
            else:
                return Var(name[1], None)


    def read_chain(self):
        chain = Chain()
        chain.add(read_value())
        while not self.is_literal(";"):
            chain.add(read_value())
        self.skip_literal(";")
        return chain

    def read_value(self):
        currType = self.tokens[self.current_token][0]
        currVal = self.tokens[self.current_token][1]
        self.current_token += 1
        
        if currType == "NAME":
            return Name(currVal)
        elif currType == "NUMBER":
            return Number(currVal)
        elif currType == "STRING":
            return String(currVal)
        elif currType == "SPECIAL" and currVal == "[":
            pass
        elif currType == "SPECIAL" and currVal == "(":
            pass
        elif currType == "SPECIAL" and currVal == "{":
            pass
        elif currType == "SPECIAL" and currVal == ":":
            pass


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


# var X = 4 ; Var(Name("X"), Num(4))            # ==> adds 'x = 4' to env
# X         ; Chain([Name("X")])                # ==> 4
# Y.Z       ; Chain([Name("Y"), Name("Z")])     # lookup in dict
# W(Z=4)    ; Chain([Name("Y"), Dict({"Z":4})]) # function call
# (Z=4).Z   ; Chain([Dict({"Z":4})])            # lookup of literal
# 4.toStr[] ; Chain([Num(4), Name("toStr"), List([])]) # call literal

