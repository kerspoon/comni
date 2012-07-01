
Comni
====

Comni is a programming language. 

It is in somy ways quite similar to javascript and lua. The goals are as follows:

- A very simple syntax but more expressive than lisp.
- Supports higher order programing.
- As little concepts as possible.

The third point may need explaining. I have tried to unify things like prototypes/class definitions and objects into a single thing: the dictionary. The environment is also a dictionary and can be used like one. 

This means environment is a first class object. The return value of a function can be a dictionary of the items defined in that code block. This is how we do object oriented programming in comni.

There is also no difference between a file and a block of code and a block of code is simply a function without arguments. Before we get too bogged down in the philosophy lets start the tutorial...

Tutorial
====

There are six kinds of statements, these are:

1. Variable Definition ~ "var"
1. Semi-Constant Definition ~ "def"
1. Includes ~ "inc"
1. Assignment ~ "set"
1. A Value ~ quoted string, number, list, etc
1. A call or lookup.

All statements end with a semi-colon, You can tell which type of statement is on a line by looking at the first three characters, you can even tell which type of value it is. 

There are no special forms outside of the ones that define these. There are however predefined functions that allow you do to looping or conditional statements. 

The Environment, Lookups and Calls
----

The *environment* is the dictionary of all the defined things. There are many things defined in the top level environment. Every call or lookup must start with something defined in the current environment.

    True;       # ok, True is defined
    NotDefined; # error, "NotDefined" is not defined.
    
A lookup like `True` will return a value. These values can be other dictionaries. You can look into those using the `.` operator. 

    player.velocity; # ok, player is a dictionary with the slot `value`.

*Function calls* are simply a lookup followed by either a list or a dictionary:

    player.Turn[90];
    True.Not[];
    Socket.Connect{ "host"="google.com", "port"=80 };

This looks up the definition of the function and matches the arguments. More on this later.

You can also do lookups, and hence function calls, on values.

    1234.Add[5, 6, 7];
    "catalogue".StartsWith["cat"];

You can chain lookups and function calls together as follows:

    1.Add[2].Take[4];
    "bob".Contains["b"].Not[];
    socket[8080].inputStream.Read[1].Type;

The code is evaluated in the order:

1. The first name is looked for in the current environment.
1. If it is a function call. Its arguments are evaluated left to right, values don't need to be evaluated. 
1. The function is called extending its environment with the parameters passed.
1. If it exists, the next part of the call chain is evaluated as if the result of the last bit was there.

Functions are first class meaning they can return functions as so:

    var IncrementByFour = IncrementByNMaker[4];
    IncrementByFour[7]; # evaluates to 11.

This can be done in one line:

    IncrementByNMaker[4][7] # also evaluates to 11.

Code Blocks
----

Anything between curly brackets `{}` is a *code block*. These can contain any of the six possible statements. These are first class objects and can be used for a variety of things. The most common is probably as an argument for a function. Here is how we would use the conditional *if*, note that `IfTrue` is predefined.

    parser.hasError.ifTrue[{
      # ... any code goes here
    }];

Note that this isn't a special form `ifTrue` is a function that takes one argument. If it is called by something that is true then it will evaluate (call) the argument passed to it, otherwise it will not do anything. This is why we have to use both square and curly brackets. We could equally used a predefined code block rather than define one inline, remember a code block is a value just like `4` or `"hello"`. 

    var myCodeBlock = {
      # ... any code goes here
    };

    parser.hasError.ifTrue[myCodeBlock];

Loops are handled in a similar way. The `WhileFalse` function keeps calling its only argument until it returns something other than false. Note that there is no specific return statement. The result of the last statement is the result of the code block. 

    # process a stream, one word at a time.
    WhileFalse[{
      var word = stream.ReadUntil[Whitespace];
      # ... do something with word
      word.IsEmpty;
    }];

Each code block has it's own environment with all the things defined above it available to it. For instance in the following code the variable `x` is available in the code block passed to the `IfFalse` function.

    var x = 3;
    
    4.Equals[3].IfFalse[{
      var y = x;
    }];
    
Definitions - Variable and Constant
----

As you have probably guessed by now you can extend this set of defined things by using either `var` or `def` statements. For `var` statements you can optionally specify the initial value and the datatype (more on datatypes later). They are used like so:

    var w;
    var x : String;
    var y = 4;
    var z : String = "hello";
    
As you can see the data type is preceded with a colon and the value with an equals sign. The only difference between `var` and `def` statements is that you cannot change what is in a `def` slot. i.e `set` only works on things created with `var` not with those created with `def`. 

    def w;                    # error, initial value not specified
    def x : String;           # error, initial value not specified
    def y = 4;                # ok
    def z : String = "hello"; # ok

Any value can be used which brings us on to the question. What are valid values?

Values
----

There are 6 types of value, all are first class meaning they can be created stored in variables, passed and returned from and to code blocks.

1. Number     ~ starts with - or a number 
1. String     ~ starts with "
1. List       ~ starts with [
1. Dictionary ~ starts with (
1. Code block ~ starts with ! or {
1. Data type  ~ starts with :

They are mostly self explanitory. Lists and dictionaries are comma seperated, dictionaries have and equals separating the keys and values. Code blocks are a list of any of the 6 possible statement types with a semi-colon after them. 

*Numbers*

    1    # ok
    -2   # ok
    3.4  # ok
    -5.6 # ok
    7.   # error, it thinks its looking up something
    .8   # error, numbers must start with number or '-'
    0.0  # ok

*Strings*

    ""                            # ok
    "a"                           # ok
    "!£$%^&*()_+[]'#<>/,;/:@~{}"  # ok
    """                           # error, double quotes need to be escaped
    "\""                          # ok
    "'"                           # ok
    'a'                           # error, single quote not allowed
    "\"                           # error, backslashes need to be escaped
    "\\"                          # ok
    "\n"                          # ok

*Lists*

Lists can contain any values and are not homogeneous. They can also contain calls/lookup chains. 

But for a `def` statement the entire chain must be able to be evaluated at compile time. **TODO** I'm not sure if this is true, or should be.

    []             # ok
    [,]            # error
    [1]            # ok
    [1,2]          # ok
    [1 2]          # error, lists are comma separated
    [1,]           # ok, nothing wrong with trailing seperators
    [1,,2]         # error
    [1, "hi"]      # ok, list can contain different types
    [{True;}]      # ok, it's a list with a code block in it
    [config.Get["shoe-size"]]  # ok, it has a call in it

*Dictionaries*

The keys must start with a letter (upper or lower case) or an underscore.  The rest of the name can also contain dashes or numbers. There are conventions for naming (see later) and there are reserved words but other than that it is up to the user. It is the same as what is allowed for slots in `var` and `def` statements.

    ()          # ok
    (,)         # error
    (x = 4)     # ok, seperators are optional on the last one
    (x=4,)      # ok, nothing wrong with trailing seperators
    (x=4 y=2)   # error, needs separator
    (x=4, y=2)  # ok
    (x = config.Get["shoe-size"])  # ok, it has a call in it

Remember that the environment itself is a dictionary and can be accessed using `Frame`. 

*Code Blocks*

These are semi-colon separated statements surrounded by curly brackets. To be consistant with the list and dictionary the last semi-colon of a block is optional. The big difference with these is that they don't get evaluated when they are created they get evaluated when they are called. See the example in the section called *scope*. Code blocks that start with a `!` are special and dealt with later.

    {}     # ok
    {;}    # error
    {config.Get["shoe-size"]} # ok, seperators are optional on the last one

*Data Type*

There are certain things defined in the global environment that evaluate to datatypes. These are:

1. Number
1. String
1. List
1. Dict
1. Codeblock
1. Type
1. Any

`Any` is the default and is used when nothing else is specified.

    var w;                 # ok, type defaults to Any
    var x : Number;        # ok, `x` has the type Number
    def y : String = "hi"; # ok, `w` has the type String
    
The standard function `Type` returns the type of any slot hence it can be used as a type itself.

    var z : x.Type         # ok, `z` has the type Number
    var a : w.Type         # ok, `a` has the type Any

You can also combine datatypes using the `|` character. This means that either one of the two types is ok. To do this you must start it with the `:` character. This means if you are using to specify the type of a slot then you will have two semi-colons.

    var b :: Number | String; # ok, b can be either Number or String
    set b = 4;                # ok
    set b = "hello";          # ok
    set b = [1, 2, 3];        # error, `b` is of wrong type
    
Types don't automatically coerce:

    var d : String = "2";
    var e : Number = d;   # error, we don't automaticly coerce.

**TODO:** I could make it a compile time error to assign to something with a larger set of possible types. But that may get annoying. Otherwise it needs run time checks, which I wanted to avoid if possible.

    var c : Number;
    set b = 5;
    set c = b;     # ok
    set b = "hi"   # ok
    set c = b;     # error
    
Data types are first class meaning you can assign them to variables, pass them as parameters and return them from functions:

    # x is a data-type with the value Integer.
    var x : Type = Integer;
    
    # NameType is the same as string.
    def NameType : Type = String;
    
    # as it is fixed at compile time it can be used to 
    # specify the type of something else.
    def bob : NameType = "hello";
    
    var b : Number | String = 4;       # ok
    var c : Type = : Number | String;  # ok
    b.Type.Equals[c];                  # returns True
    
Although you can specify a list using the built in `List`, you can get more specific. For instance you can specify how many elements and what types of elements are allowed. The syntax is a list of things that evaluate to a datatype (at compile time if used as the type in a `var` or `def`) preceded by a colon. 

    var z : List;               # ok, accepts any list
    var a ::[];                 # ok, only accepts the empty list
    var b ::[String];           # ok, accepts one string
    var c ::[IfTrue];           # error, `IfTrue` is not a type.
    var d ::[String, Integer];  # ok, two elements: a string then integer.

The symbol `&` means all other elements must have the following type. It also means the list can be of any length.
    
    var e  ::[&String];          # ok, zero or more strings
    var f  ::[String &String];   # ok, one or more strings
    var g  ::[String, &String];  # ok, trailing commas are ok
    var g  ::[Integer, &String]; # ok, different types are fine
    var zz ::[&Any];            # ok, same as `z`, accepts any list

You can do the same treatment to dictionaries. By default they allow extra things in them. To match they must have at least the things specified and they all must be of the correct type.

    var h ::(x=Integer, y=String);

To make things a bit quicker you can use an existing code block to create a dict type using the pre defined function `ToType`:

    def w = {var y : Integer};     # ok
    def x : x.ToType = (y=4);      # ok
    def y : x.ToType = (y=4, z=3); # ok, no problem with extra args
    def z : x.ToType = (z=3);      # error, requires y 
    def a : x.ToType = (y="hi");   # error, requires y as Integer
    
**TODO:** Function type

must specify:

+ that is is a type
+ that it is for functions
+ the types and number of args
+ the names of args
+ the return type

    def addOne ::!(x=Integer) String = ![x]{ };

Scope
----

**TODO:** what should return here:

    var x = 4;
    var y = [x];
    var z = {x};
    x.Add[6];
    y;        # ???
    z[];      # ???

**TODO:** What about here:

    config.Set["x", 4];
    var y = [config.Get["x"]];
    var z = {config.Get["x"]};
    config.Set["x", 9];
    y;        # ???
    z[];      # ???

**TODO:** What about here:

    var x = 4.add;  #
    x[7];           # does this somehow know it belonged to '4' before


Creating Functions and Classes
----

Functions are a slightly differnt form of code block. Actually if a function takes no arguments then it is the same as the code blocks defined in the section on *values*. A function that take one argument is as follows:

    def AddOne = ![x]{
      x.Add[1];
    };

With two arguemnts:

    def AddTwo = ![x, y]{
      x.Add[y];
    };

With zero or more arguments:

    def AddAll = ![&args]{
      var result = 0;
      args.ForEach[![arg]{
        result.Add[arg];
      }];
      result;
    };

----------------------------------------------------------------------

Progress
====

The lexer, parser and evaluator basically work and there is a few predefined functions. The main problem is scope. We need to think about the cases (in *scope* above) and how they are to be solved. 

1. Think about scope issues.
1. Add a load of built-in functions (in a new file).
1. Create a built-in type for reading and writing files.
1. Allow comments in code (extend lexer).
1. Write Inc.evaluate[].

Low Priority
----

- need to deal with non integer numbers
- needs to deal with escaping '"' with '\'
- needs to deal with def `a.b = 4;`
- in special forms if the chain is the value of kind code then save the name in that code for better debugging.
- include 'this' in new environment of Code.call
- work out how to evaluate long chains

Very Low Priority
----

- implement data types and types checking
- create emacs mode