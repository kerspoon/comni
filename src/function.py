

from evaluate import Statement, Var, Def, Set, Inc, Name, Number, String, Dict, List, Function, Code, Chain, bool_true, bool_false, File
import operator

def number_two_number(name, func):
    def inner(this, args, env):
        return Number(func(this.data, args["x"].data))
    Statement.builtins["number"][name] = Function(inner, ["x"], name)

def number_asString(this, args, env):
    return String(this.as_string(""))

def boolean_ifTrue(this, args, env):
    # args = [Code, Code?]
    if this is bool_true:
        return args["cons"].call(None, List([]), env)
    else:
        assert this is bool_false
        if "alt" in args:
            return args["alt"].call(None, List([]), env)
        return Name("None")


def file_open(this, args, env):
    return File(args["name"].data)

def file_close(this, args, env):
    this.file_obj.close()
    return bool_true

def file_read(this, args, env):
    return String(this.file_obj.read(args["n"].data))

def file_peek(this, args, env):
    loc = self.stream.tell()
    tmp = self.stream.read(args["n"].data)
    self.stream.seek(loc)
    return String(tmp)

def make_builtins():
    Statement.builtins["number"] = {
        "asString": Function(number_asString, [], "asString"),
        }

    number_two_number("add", operator.add)
    number_two_number("div", operator.div)
    number_two_number("mod", operator.mod)
    number_two_number("mul", operator.mul)
    number_two_number("sub", operator.sub)
    number_two_number("sub", operator.sub)
    number_two_number("abs", operator.abs)

    Statement.builtins["string"] = {
        "asString": Function(number_asString, [], "asString"),
        }

    Statement.builtins["boolean"] = {
        "ifTrue": Function(boolean_ifTrue, ["cons", "alt"], "ifTrue"),
        }
    
    Statement.builtins["file"] = {
        "close": Function(file_close, [], "close"),
        "read": Function(file_read, ["n"], "read"),
        "peek": Function(file_peek, ["n"], "peek"),
        }
    
    global_env = {
        "true" : bool_true,
        "false": bool_false,
        "File": Function(file_open, ["name"], "File")
        }

    return global_env

# number:
#  eq

# string :
#  startsWith ( string ) -> Bool
#  endsWith   ( string ) -> Bool
#  contains   ( string ) -> Bool
#  cat ( string) -> String
#  slice  ( number, number?, number? ) -> String
#  strip () -> String
#  len () -> Number
#  split  ( string ) -> List String
#  eq

# list:
#  join ( string ) -> String
#  str ( ) -> String
#  len ( ) -> Number
#  push ( ) -> List
#  pop  ( ) -> List
#  eq
#  for

# dict:
#  has/in
#  eq
#  for

# global:
#  whileTrue
#  print

make_builtins()



