import time
from time import sleep
import asyncio

from SakikoDSL.SVM import parser
from SakikoDSL.SVM import memory
from SakikoDSL.SVM import symbol
from SakikoDSL.SVM import database as db
from SakikoDSL.UI import uinteraction as ui

class VirtualMachine:
    input_cache = ""
    output_cache = ""
    call_and_ret = []  # 函数调用栈
    switched_var_value = None  # switch-case 语句中的变量值
    is_in_switch = False  # 是否已经进入了 switch-case 语句
    return_code = -1  # 主函数/脚本退出代码

    parser = parser.Parser()

    websocket = None
    def set_websocket(self, _websocket):
        self.websocket = _websocket

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
            if isinstance(token, (int, float)):  # 处理数字常量
                value = token
            elif token.startswith('"') and token.endswith('"'):  # 处理字符串常量
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

    def get_condition_value(self, condition):
        value_left = self.memory.heap.load(self.symbol_table.get(condition[0]).value)
        _right = condition[2]
        if self.parser.is_variable(_right):
            value_right = self.memory.heap.load(self.symbol_table.get(_right).value)
        elif isinstance(_right, int):
            value_right = _right
            try:
                value_left = int(value_left)
            except ValueError:
                return False
        elif isinstance(_right, float):
            value_right = _right
            try:
                value_left = float(value_left)
            except ValueError:
                return False
        elif _right.startswith('"') and _right.endswith('"'):
            value_right = _right[1:-1]
        else:
            raise ValueError(f"Invalid token: {_right}")

        try:
            if condition[1] == '<':
                return value_left < value_right
            elif condition[1] == '>':
                return value_left > value_right
            elif condition[1] == '<=':
                return value_left <= value_right
            elif condition[1] == '>=':
                return value_left >= value_right
            elif condition[1] == '==':
                return value_left == value_right
            elif condition[1] == '!=':
                return value_left != value_right
            else:
                return False
        except TypeError:
            return False

    def run(self, code):
        code_lines = code.split("\n")  # 按行分割代码
        self.memory.code = memory.CodeSegment(code_lines)

        system_database = db.Database()

        while self.websocket is None:
            print("Waiting for connection...")
            sleep(1)

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
                continue # 跳过注释造成的空行

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
                if_condition = result[1]
                if self.get_condition_value(if_condition):
                    i += 1
                else:
                    end_if_match = 1
                    while i < len(code_lines):
                        i += 1
                        if code_lines[i].strip() == "endIf":
                            end_if_match -= 1
                        elif code_lines[i].strip().startswith("ifLike"):
                            end_if_match += 1
                        elif code_lines[i].strip().startswith("if"):
                            end_if_match += 1

                        if end_if_match == 0:
                            i += 1
                            break
            elif result[0] == 'ifLike':  # 模糊匹配
                var_name = result[2]
                str_to_match = result[4][1:-1]
                var_value = self.memory.heap.load(self.symbol_table.get(var_name).value)
                if var_value.find(str_to_match) != -1: # var_value 包含 str_to_match
                    i += 1
                else:
                    end_if_match = 1
                    while i < len(code_lines):
                        i += 1
                        if code_lines[i].strip() == "endIf":
                            end_if_match -= 1
                        elif code_lines[i].strip().startswith("if"):
                            end_if_match += 1
                        elif code_lines[i].strip().startswith("ifLike"):
                            end_if_match += 1

                        if end_if_match == 0:
                            i += 1
                            break
            elif result[0] == 'switch':  # switch-case
                switch_var_name = result[1]
                try:
                    self.switched_var_value = self.memory.heap.load(self.symbol_table.get(switch_var_name).value)
                except AttributeError:
                    self.throw_error(f"Variable {switch_var_name} not declared")
                    break
                i += 1
            elif result[0] == 'case':  # case
                if self.switched_var_value is None:
                    self.throw_error("Switch variable not initialized")
                    break

                if self.is_in_switch:
                    while i < len(code_lines):
                        i += 1
                        if code_lines[i].strip() == "endSwitch":
                            break
                    continue

                this_case = result[1]
                if isinstance(this_case, (int, float)):
                    case_value = this_case
                else:
                    case_value = this_case[1:-1]

                if type(self.switched_var_value) != type(case_value):
                    self.throw_error(f"Type mismatch between {type(self.switched_var_value)} and {type(case_value)}")
                    break

                if self.switched_var_value == case_value:
                    self.is_in_switch = True
                    i += 1
                else:
                    while i < len(code_lines):
                        i += 1
                        temp_line = code_lines[i]
                        if not temp_line.strip():
                            i += 1
                            continue
                        temp_result = self.parser.parse_code(temp_line.lstrip())
                        if len(temp_result) != 0 and (temp_result[0] == 'case' or temp_result[0] == 'default'):
                            break
            elif result[0] == 'default':  # default
                if self.switched_var_value is None:
                    self.throw_error("Switch variable not initialized")
                    break

                if self.is_in_switch:
                    while i < len(code_lines):
                        i += 1
                        if code_lines[i].strip() == "endSwitch":
                            break
                else:
                    self.is_in_switch = True
                    i += 1
            elif result[0] == 'endSwitch':  # endSwitch
                self.switched_var_value = None
                self.is_in_switch = False
                i += 1
            elif result[0] == 'To':  # 跳转地点
                goto_label = result[1]
                new_symbol = symbol.Symbol(goto_label, 'l', i)
                self.symbol_table.add(new_symbol)
                i += 1
            elif result[0] == 'goto':  # 跳转
                goto_label = result[1]
                i = self.symbol_table.get(goto_label).value + 1
            elif result[0] == 'findData':  # 查询数据库
                store_var_name = result[2]
                query_content = result[4][1:-1]
                var_addr = self.symbol_table.get(store_var_name).value
                username = self.memory.heap.load(self.symbol_table.get("__username__").value)
                if query_content == "gameBalance":
                    user_balance = system_database.get_balance(username)
                    self.memory.heap.store(var_addr, user_balance)
                elif query_content == "shopOrder":
                    shop_order = system_database.get_order_info(username)
                    self.memory.heap.store(var_addr, shop_order)
                elif query_content == "shopLogistics":
                    shop_logistics = system_database.get_logistics_info(username)
                    self.memory.heap.store(var_addr, shop_logistics)
                elif query_content == "gameAccount":
                    game_account = system_database.get_game_info(username)
                    self.memory.heap.store(var_addr, game_account)
                elif query_content == "fesInfo":
                    fes_info = db.Database.get_game_fes_info()
                    self.memory.heap.store(var_addr, fes_info)
                i += 1
            elif result[0] == 'saveData':  # 保存数据到数据库
                save_var_name = result[2]
                save_content = result[4][1:-1]
                var_val = self.memory.heap.load(self.symbol_table.get(save_var_name).value)
                username = self.memory.heap.load(self.symbol_table.get("__username__").value)
                if save_content == "balance":
                    system_database.update_balance(username, var_val)
                i += 1
            elif result[0] == 'updateBalance':  # 更新余额
                balance_var_name = result[2]
                balance_var_addr = self.symbol_table.get(balance_var_name).value
                balance = self.memory.heap.load(balance_var_addr)
                username = self.memory.heap.load(self.symbol_table.get("__username__").value)
                system_database.update_balance(username, balance)
                i += 1
            elif result[0] == '__login__':  # 登录
                while True:
                    if self.input_cache:
                        result = self.input_cache.split(':')  # 按照 : 分割用户名和密码
                        login_try = result[0]
                        username = result[1]
                        password = result[2]
                        self.input_cache = ""
                        self.print_debug(f"Login try: {login_try}, username: {username}, password: {password}")

                        is_login = False

                        if login_try == "login":
                            if system_database.password_match(username, password):
                                is_login = True
                                asyncio.run(ui.UserInteraction.print('LOGIN_OK', self.websocket))
                            else:
                                asyncio.run(ui.UserInteraction.print('LOGIN_ERROR', self.websocket))
                        elif login_try == "register":
                            if system_database.user_exist(username):
                                asyncio.run(ui.UserInteraction.print('REGISTER_ERROR', self.websocket))
                            else:
                                system_database.add_user(username, password)
                                asyncio.run(ui.UserInteraction.print('REGISTER_OK', self.websocket))

                        sleep(1)

                        if is_login:
                            new_addr = self.set_new_var_addr()
                            new_symbol = symbol.Symbol("__username__", 'v', new_addr)
                            self.symbol_table.add(new_symbol)
                            self.memory.heap.store(new_addr, username)

                            i += 1
                            break
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
                asyncio.run(ui.UserInteraction.print(self.output_cache, self.websocket))
                sleep(0.5) # 等待输出
                self.output_cache = ""

        system_database.close()
        return self.return_code

    def out_input(self, _input):
        self.input_cache = _input

# 虚拟机测试桩 -- 表达式求值
if __name__ == "__main__":
    vm = VirtualMachine()
    parser = parser.Parser()
    testsource = input()
    try:
        text_expr = parser.parse_expression(testsource)
    except Exception as e:
        print("Parse error:", e)
        exit(1)
    print("Expression:", text_expr)
    p_result = vm.get_expression_value(text_expr)
    print("Result:", p_result)