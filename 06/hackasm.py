from lark import Lark, Transformer
import argparse, sys, logging, copy

JMPTAB = {
  "GT": "001",
  "EQ": "010",
  "GE": "011",
  "LT": "100",
  "NE": "101",
  "LE": "110",
  "MP": "111"
}

DESTTAB = {
  "A": 0,
  "D": 1,
  "M": 2
}

COMPTAB = {
  "0": "0101010",
  "1": "0111111",
  "-1": "0111010",
  "D": "0001100",
  "A": "0110000",
  "M": "1110000",
  "!D": "0001101",
  "!A": "0110001",
  "!M": "1110001",
  "-D": "0001111",
  "-A": "0110011",
  "-M": "1110011",
  "D+1": "0011111",
  "A+1": "0110111",
  "M+1": "1110111",
  "D-1": "0001110",
  "A-1": "0110010",
  "M-1": "1110010",
  "D+A": "0000010",
  "A+D": "0000010",
  "D+M": "1000010",
  "M+D": "1000010",
  "D-A": "0010011",
  "A-D": "0000111",
  "D-M": "1010011",
  "M-D": "1000111",
  "D&A": "0000000",
  "A&D": "0000000",
  "D&M": "1000000",
  "M&D": "1000000",
  "D|A": "0010101",
  "A|D": "0010101",
  "D|M": "1010101",
  "M|D": "1010101"
}

grammar = """
program: [_NEWLINE*] ((instruction | label | _COMMENT) (_NEWLINE)+)+

?instruction: (a_instruction | c_instruction) [_COMMENT]
a_instruction: "@" (SYMBOL | INT)
c_instruction: [dest "="] comp [";" jump]

// destination spec
dest: A | M | D | A M | A D | M D | A M D

// compute spec
comp: CONST | REGISTER | (NOT REGISTER) | (NEG REGISTER) | (REGISTER INCR) | (REGISTER DECR)
  | (D BINOP A) | (D BINOP M) | (A BINOP D) | (M BINOP D)

CONST: "0" | "1" | "-1"

NOT: "!"
NEG: "-"
INCR: "+1"
DECR: "-1"

// jump spec
jump: "J" (GT | LT | GE | LE | EQ | NE | MP)

GT: "GT"
LT: "LT"
GE: "GE"
LE: "LE"
EQ: "EQ"
NE: "NE"
MP: "MP"

A: "A"
D: "D"
M: "M"

BINOP: "+" | "-" | "&" | "|"
REGISTER: A | D | M

SYMBOL: /[a-zA-Z$_:\.][a-zA-Z0-9$_:\.]*/ 
label: "(" SYMBOL ")"

_COMMENT: /\/\/.*/

%import common.INT -> INT
%import common.NEWLINE -> _NEWLINE
"""

class T(Transformer):

  def __init__(self):
    self.var_loc = 16
    self.vartab = {}
    self.labtab = {}

  def program(self, x):
    return "\n".join(x) + "\n"

  def a_instruction(self, x):
    u = x[0]
    if u.type == "INT":
      val = int(u)
      if val >= 2**15:
        logging.error("Integer value {} out of range on line {}".format(val, u.line))
        sys.exit(-1)
      return "{0:016b}".format(val)
  
  def c_instruction(self, x):
    jmp = "000"
    dest = ["0", "0", "0"]
    comp = None
    for c in x:
      if c.data == "dest":
        for d in c.children:
          dest[DESTTAB[d]] = "1"
      elif c.data == "jump":
        jmp = JMPTAB[c.children[0]]
      else:
        s = ""
        for v in c.children:
          s += v
        comp = COMPTAB[s]
    return "111" + comp + "".join(dest) + jmp;
        


ap = argparse.ArgumentParser(prog="hackasm", description='An assembler targeting the HACK architecture')
ap.add_argument("infile", help="input file")
ap.add_argument("-o", dest="outfile", default="out.hack", help="output file")
ap.add_argument("-v", dest="verbose", action="store_true", help="verbose output")
ap.add_argument("--version", action="version", version="%(prog)s 1.0")
args = ap.parse_args()

logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.DEBUG if args.verbose else logging.WARNING)

parser = Lark(grammar, start="program")

with open(args.infile, "r") as f:
  logging.debug("Trimming inline whitespace from input")
  raw = f.read()
  trim = raw.replace(" ", "").replace("\t", "")
  logging.debug("Parsing")
  tree = parser.parse(trim)

logging.debug("Parse tree:\n" + tree.pretty())

logging.debug("Computing label positions")
# first pass removes labels and keeps track of their locations
var_loc = 16
symtab = {}
instructions = []
for c in tree.children:
  if c.data == "label":
    symbol = c.children[0]
    if symbol in symtab:
      logging.error("Symbol {} defined multiple times on line {}".format(symbol, symbol.line))
      sys.exit(-1)
    symtab[symbol] = len(instructions)
  else:
    instructions.append(c)


# add default symbols if not overwritten by a label
symtab.setdefault("SP", 0)
symtab.setdefault("LCL", 1)
symtab.setdefault("ARG", 2)
symtab.setdefault("THIS", 3)
symtab.setdefault("THAT", 4)
symtab.setdefault("SCREEN", 0x4000)
symtab.setdefault("KBD", 0x6000)
for i in range(16):
  symtab.setdefault("R{}".format(i), i)

logging.debug("Resolving symbol references")
# second pass removes variable occurrences in a-instructions
instructions2 = []
for c in instructions:
  if c.data == "a_instruction" and c.children[0].type == "SYMBOL":
    symbol = copy.copy(c.children[0])
    if symbol not in symtab:
      if var_loc == 0x4000:
        logging.warning("Too many variables, will overflow into screen buffer")
      elif var_loc == 0:
        logging.warning("Too many variables, will overflow and wrap around")
      symtab[symbol] = var_loc
      var_loc = (var_loc + 1) % 0x8000
    loc = symtab[symbol]
    c.children[0].type = "INT"
    c.children[0] = c.children[0].update(value="{}".format(loc))
  instructions2.append(c)

tree.children = instructions2

logging.debug("Parse tree:\n" + tree.pretty())

logging.debug("Translating to machine code")
result = T().transform(tree)

with open(args.outfile, "w") as f:
  f.write(result)
