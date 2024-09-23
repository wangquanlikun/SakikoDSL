class Symbol:
    def __init__(self, name, symbol_type, value=None):
        self.name = name  # 符号的名称
        self.symbol_type = symbol_type  # 符号的类型（如变量、函数等）
        self.value = value  # 符号的值或初始值（变量可以存储其值）

    def __str__(self):
        return f"Symbol(name={self.name}, type={self.symbol_type}, value={self.value})"

    def is_func(self):
        return self.symbol_type == 'f' # 变量 value储存函数实现所在的行数

    def is_goto_label(self):
        return self.symbol_type == 'l' # 变量 value储存goto的目标行数

    def is_var(self):
        return self.symbol_type == 'v' # 变量 value储存地址

    def is_const(self):
        return self.symbol_type == 'c' # 常量 value储存值

class SymbolTable:
    def __init__(self):
        self.symbols = {} # Map<str, Symbol>

    def add(self, symbol):
        self.symbols[symbol.name] = symbol

    def get(self, name):
        return self.symbols.get(name)

    def delete(self, name):
        del self.symbols[name]