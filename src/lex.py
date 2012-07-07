import StringIO
import string

whitespace = set(string.whitespace)
number_chars = set(string.digits + "-")
name_start_chars = set(string.ascii_letters)
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

    # ---- public functions ----

    def __init__(self, stream, debug):
        self.stream = stream
        self.tokens = []
        self.debug = debug

    def read_all(self):
        self.skip_whitespace()
        while(self.stream.peek(1)):
            self.read_statement()
            self.skip_whitespace()
            self.read_literal(";")
            self.skip_whitespace()
        return self.tokens

    def as_string(self):
        if len(self.tokens) == 0:
            self.read_all()
        res = []
        for tok in self.tokens:
            if tok[0] == "STRING":
                res.append("\"" + tok[1] + "\"")
            else:
                res.append(tok[1])
        return " ".join(res)

    # ---- private functions ----

    def skip_whitespace(self):
        while True:
            while(self.stream.peek(1) in whitespace):
                self.stream.read(1)
            if self.stream.peek(2) == "/*":             
                self.stream.read(len("/*"))
                while(self.stream.peek(2) != "*/"):
                    self.stream.read(1)          
                self.stream.read(len("*/"))
            elif self.stream.peek(1) == "#":               
                self.stream.read(len("#"))
                while(self.stream.peek(1) != "\n"):
                    self.stream.read(1)             
                self.stream.read(len("\n"))
            else:
                return

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

        
    def read_statement(self):
        self.skip_whitespace()
        three = self.stream.peek(3);

        if (three == "var" or three == "def" or three == "set" or three == "inc"):
            self.read_special()
            self.skip_whitespace()
            self.read_name()
            self.skip_whitespace()
            # TODO: deal with datatypes
            if (self.stream.peek(1) == "="):
                self.read_literal("=")
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
        if (self.stream.peek(1) == "!"):
            self.read_literal("!")
            self.skip_whitespace()
            self.read_list(True)
            self.skip_whitespace()
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

    def read_list(self, names_only = False):
        self.read_literal("[")
        self.skip_whitespace()
        while(True):
            if (self.stream.peek(1) == "]"):
                self.read_literal("]")
                return
            if names_only:
                self.read_name()
            else:
                self.read_chain_or_value()
            self.skip_whitespace()
            if (self.stream.peek(1) == ","):
                self.read_literal(",")
                self.skip_whitespace()
            else:
                self.read_literal("]")
                return


def mockfile(text):
    return PeekableStream(StringIO.StringIO(text))

def test_tokenizer():

    test_list = """
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
# NEXT A.Z.q1.r-f;
# NEXT a[1][2].b(x=4)[5];
# NEXT a [ 1 ] [ 2 ] . b ( x = 4 ) [ 5 ] ;
# NEXT ![x, y] {x.plus[y];};
# NEXT ![x, y] {x.plus[y]};
# NEXT !  [   ] {  4  } ;
# NEXT ABC; /* comment */ DEF;
# NEXT ABC; # comment 
DEF;
""".split("# NEXT")

# NEXT inc y.x;
# TODO: get this working: 'set a.b = 4;'

    print "-"*50
    for inputString in test_list:

        tokenizer = Tokenizer(mockfile(inputString), False)
        tokenList = tokenizer.read_all()
        tokenString = tokenizer.as_string()
        
        print inputString.strip()
        print tokenString
        # print toks.tokens
        print "-"*50


if __name__ == '__main__':
    test_tokenizer()

