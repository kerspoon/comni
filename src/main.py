

import sys
from evaluate import Dict, List
from parse import Parser
from lex import Tokenizer, PeekableStream

from function import make_builtins


def main(fileObj):
    global_env = make_builtins()
    tokenizer = Tokenizer(PeekableStream(fileObj), False)
    tokenList = tokenizer.read_all()
    tokenString = tokenizer.as_string()
    # print tokenString

    parser = Parser(tokenList)
    code = parser.read_all()
    codeString = parser.as_string()
    # print codeString
        
    env = Dict(global_env)
    val = code.evaluate(env)
    result = val.call(None, List([]), env)

    if result is not None:
        print result.as_string("")
    else:
        print None
    print "-"*50

if __name__ == '__main__':
    file_name = sys.argv[1]
    main(open(file_name))
