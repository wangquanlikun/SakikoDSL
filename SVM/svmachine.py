import time
from time import sleep

from SakikoDSL.SVM import parser
from SakikoDSL.SVM import memory
from SakikoDSL.SVM import symbol
from SakikoDSL.UI import uinteraction as ui

class VirtualMachine:
    input_cache = ""
    output_cache = ""
    call_and_ret = []  # 函数调用栈
    return_code = -1  # 主函数/脚本退出代码

    parser = parser.Parser()

    debug_mode = True
    def print_debug(self, _string):
        if self.debug_mode:
            print(_string)

    def __init__(self):
        self.memory = memory.Memory()
        self.symbol_table = symbol.SymbolTable()

    def throw_error(self, error):
        print(f"Error: {error}")
        self.return_code = -1

    def set_new_var_addr(self):
        new_addr = self.memory.heap.get_new_addr()
        self.memory.heap.store(new_addr, None)
        return new_addr

    def get_expression_value(self, expr):
        result = None  # 存储最终结果
        current_operator = None  # 当前的运算符

        for token in expr:
            if token.startswith('"') and token.endswith('"'):  # 处理字符串常量
                value = token[1:-1]  # 去掉首尾的引号
            elif self.parser.is_variable(token):  # 处理变量
                var_value = self.memory.heap.load(self.symbol_table.get(token).value)
                if isinstance(var_value, (int, float)):
                    value = var_value
                elif isinstance(var_value, str):
                    value = var_value
                else:
                    raise TypeError(f"Unsupported variable type: {type(var_value)}")
            elif token == '+' or token == '-':  # 处理运算符
                current_operator = token
                continue
            else:
                raise ValueError(f"Invalid token: {token}")

            # 将当前的值和 result 结合
            if result is None:
                result = value
            else:
                if isinstance(result, str) and isinstance(value, str) and current_operator == '+':
                    result += value  # 字符串拼接
                elif isinstance(result, (int, float)) and isinstance(value, (int, float)):
                    if current_operator == '+':
                        result += value  # 数字加法
                    elif current_operator == '-':
                        result -= value  # 数字减法
                else:
                    raise TypeError(f"Unsupported operation between {type(result)} and {type(value)}")

        return result

    def run(self, code):
        code_lines = code.split("\n")  # 按行分割代码
        self.memory.code = memory.CodeSegment(code_lines)

        i = 0
        while i < len(code_lines):
            line = code_lines[i]
            if not line.strip():
                i += 1
                continue # 跳过空行
            result = self.parser.parse_code(line.lstrip())  # 逐行解析代码
            self.print_debug(result)

            if len(result) == 0:
                i += 1
                continue

            # 实际根据代码内容，判断执行下一条或跳转到指定行
            if result[0] == 'string' or result[0] == 'int' or result[0] == 'float' or result[0] == 'var':  # 变量声明
                new_addr = self.set_new_var_addr()
                new_symbol = symbol.Symbol(result[1], 'v', new_addr)
                self.symbol_table.add(new_symbol)
                i += 1
            elif result[0] == 'def':  # 函数定义
                if result[1][0] == 'main':
                    i += 1  # 执行主函数
                else:
                    # 保存符号表
                    new_symbol = symbol.Symbol(result[1][0], 'f', i)
                    self.symbol_table.add(new_symbol)
                    # 跳转到函数结束：在函数被调用时再实现
                    while i < len(code_lines):
                        i += 1
                        if code_lines[i].strip() == "endFunc":
                            i += 1
                            break
            elif result[0] == 'Exit':  # 退出
                self.return_code = int(result[1])
                self.call_and_ret.clear()
                break
            elif result[0] == 'endFunc': # 函数结束
                func_ret = -1
                if len(result) == 2:
                    func_ret = result[1]

                if len(self.call_and_ret):
                    i = self.call_and_ret.pop()
                else:
                    self.return_code = int(func_ret)
                    break
                i += 1
            elif result[0] == 'print':  # 打印
                nums_to_print = len(result) - 1
                for j in range(1, nums_to_print + 1):
                    if result[j][0] == '"':
                        self.output_cache += result[j][1:-1]
                    else:
                        var_addr = self.symbol_table.get(result[j]).value
                        self.output_cache += str(self.memory.heap.load(var_addr))
                    if j < nums_to_print:
                        self.output_cache += " "
                i += 1
            elif result[0] == 'input':  # 输入
                var_name = result[1]
                var_addr = self.symbol_table.get(var_name).value
                if len(result) == 2:  # 无超时处理的输入
                    while True:
                        if self.input_cache:
                            self.memory.heap.store(var_addr, self.input_cache)
                            self.input_cache = ""
                            break
                else:  # 有超时处理的输入
                    timeout_time = int(result[2][1])  # 超时时间
                    pre_time = time.time()
                    while True:
                        if self.input_cache:
                            self.memory.heap.store(var_addr, self.input_cache)
                            self.input_cache = ""
                            break
                        if time.time() - pre_time > timeout_time:
                            func_call_name = result[3][0]
                            self.call_and_ret.append(i)  # 记录返回地址，保存当前状态，跳转到指定函数
                            i = self.symbol_table.get(func_call_name).value
                            break
                i += 1
            elif result[0] == 'Timeout': # 超时
                timeout_time = int(result[1])
                sleep(timeout_time)
                i += 1
            elif result[0] == 'call':  # 函数调用
                func_name = result[1]
                self.call_and_ret.append(i)
                i = self.symbol_table.get(func_name).value + 1
            elif result[0] == 'if':  # 条件判断
                i += 1
                pass
            elif result[0] == 'switch':  # switch-case
                i += 1
                pass
            else:
                if self.parser.try_parse_variable_assignment(line.lstrip()) is not None:
                    var_name = result[0]
                    try:
                        var_addr = self.symbol_table.get(var_name).value
                    except AttributeError:
                        self.throw_error(f"Variable {var_name} not declared")
                        break
                    expr = result[2]
                    self.memory.heap.store(var_addr, self.get_expression_value(expr))
                i += 1

            if self.output_cache: # 不为空则输出
                ui.UserInteraction.print(self.output_cache)
                self.output_cache = ""

        print(f"脚本执行结束，退出代码为 {self.return_code}")