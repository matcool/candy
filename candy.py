from lark import Lark
import sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    text = f.read()
with open('grammar.lark', 'r') as f:
    grammar = f.read()

parser = Lark(grammar)
parsed = parser.parse(text)