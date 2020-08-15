import lark
import ast
from collections import namedtuple

with open('grammar.lark', 'r') as file:
    parser = lark.Lark(file.read())

with open('example.candy', 'r') as file:
    tree = parser.parse(file.read())

print(tree.pretty())

VALUE_SB = 'value'
VAR_PREFIX = '$'

def get_var(name):
    return VAR_PREFIX + name

def sb_operation(a, operator, b): return f'scoreboard players operation {get_var(a)} {VALUE_SB} {operator} {get_var(b)} {VALUE_SB}'
def sb_set(name, value): return f'scoreboard players set {get_var(name)} {VALUE_SB} {value}'
def sb_reset(name): return f'scoreboard players reset {get_var(name)} {VALUE_SB}'

def parse_function(tree):
    assert tree.data == 'function'
    tree = tree.children

    name = tree[0].value
    args = [token.value for token in tree[1].children]
    body = tree[2].children
    print(f'func {name!r}, {args}')

    data = {name: []}

    for stmt in body:
        stmt_type = stmt.data

        if stmt_type == 'raw_command':
            data[name].append(stmt.children[0].value)
        elif stmt_type == 'assignment':
            var = stmt.children[0].value
            expr = stmt.children[1]
            
            # god this is jank
            value = parse_expr(expr, var_name=var)

            print(var, '=', value)
            if isinstance(value, list):
                data[name].extend(value)
                data[name].extend([
                    sb_operation(var, '=', '__tmp_expr_final'),
                    sb_reset('__tmp_expr_final')
                ])
            else:
                data[name].append(sb_set(var, value))
                
            # data[name].append(f'scoreboard ')
    print('\n'.join(data[name]))
    return data

_OPERATORS = {
    'add': '+',
    'sub': '-',
    'mul': '*',
    'div': '/',
    'mod': '%'
}

def parse_expr(tree, **kwargs):
    expr_type = tree.data

    if expr_type == 'number':
        return int(tree.children[0].value)
    elif expr_type in {'add', 'sub', 'mul', 'div'}:
        if not any(tree.find_data('var')):
            a = parse_expr(tree.children[0])
            b = parse_expr(tree.children[1])
            if expr_type == 'div':  
                return a // b
            return eval(f'a {_OPERATORS[expr_type]} b')
        else:
            var_name = kwargs.get('var_name')
            if not var_name or var_name not in {i.children[0].value for i in tree.find_data('var')}:
                var_name = None
            test = MutExprParser(protected_var=var_name).run(tree)
            return test

class MutExprParser:
    def __init__(self, protected_var=None):
        self.protected_var = protected_var
        self.current_var = 0
        self.commands = []
        self.var_prefix = '__tmp_literal_'

    def get_next_var(self):
        self.current_var += 1
        return self.var_prefix + str(self.current_var - 1)

    def sb_operation(self, *args):
        self.commands.append(sb_operation(*args))

    def parse(self, tree):
        type_ = tree.data
        if type_ == 'number':
            var = self.get_next_var()
            self.commands.append(sb_set(var, tree.children[0].value))
            return var
        elif type_ == 'var':
            var = tree.children[0].value
            if var == self.protected_var:
                new_var = self.get_next_var()
                self.sb_operation(new_var, '=', var)
                var = new_var
            return var
        elif type_ in {'add', 'sub', 'mul', 'div'}:
            a = self.parse(tree.children[0])
            b = self.parse(tree.children[1])
            op = _OPERATORS[type_]
            var = self.get_next_var()
            self.sb_operation(var, '=', a)
            self.sb_operation(var, op + '=', b)
            return var

    def run(self, tree):
        last = self.parse(tree)
        self.sb_operation('__tmp_expr_final', '=', last)
        for i in range(self.current_var):
            self.commands.append(sb_reset(self.var_prefix + str(i)))
        return self.commands

for function in tree.children:
    parse_function(function)