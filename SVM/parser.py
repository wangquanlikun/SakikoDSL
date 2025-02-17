import pyparsing as pp

class Parser:
    # 定义语法
    _integer_constant = pp.Regex("[-+]?[0-9]+").set_parse_action(lambda tokens: int(tokens[0]))  # 2
    _real_constant = pp.Regex("[-+]?[0-9]*\\.?[0-9]+([eE][-+]?[0-9]+)?").set_parse_action(lambda tokens: float(tokens[0]))  # 2.0
    _string_constant = pp.quoted_string('"')  # "a"

    _note = pp.Group(pp.Regex("//.*").suppress())  # // 注释内容

    _variable = pp.Word("_" + pp.alphas, pp.alphanums + "_")  # a _a
    _variable_decl = pp.Group((pp.Keyword("string") ^ pp.Keyword("int") ^ pp.Keyword("float") ^ pp.Keyword("var")) + pp.delimited_list(_variable))  # int a, b, c

    _string = pp.Group(pp.delimited_list(_string_constant ^ _variable, "+"))  # "a" + "b" + str

    _input_statement = pp.Group(pp.Keyword("input") + _variable)  # input a
    _print_statement = pp.Group(pp.Keyword("print") + pp.delimited_list(_variable ^ _string_constant))  # print a, "b"

    _timeout_set = pp.Group(pp.Keyword("Timeout") + _integer_constant)  # Timeout 1000
    _exit_statement = pp.Group(pp.Keyword("Exit") + _integer_constant)  # Exit 0

    _function = pp.Group(_variable + "(" + pp.Optional(pp.delimited_list(_variable ^ _integer_constant ^ _real_constant)) + ")")
    _function_call = pp.Group(pp.Keyword("call") + _variable + "(" + pp.Optional(pp.delimited_list(_variable ^ _integer_constant ^ _real_constant)) + ")")  # call func(a, 2, 3.0)
    _function_start = pp.Group(pp.Keyword("def") + _function + ":")  # def func(a, 2, 3.0):
    _function_end = pp.Group(pp.Keyword("endFunc") + pp.Optional(_integer_constant ^ _real_constant ^ _string_constant ^ _variable))  # endFunc 0

    _expression = pp.Forward()  # 表达式
    _factor = _integer_constant ^ _real_constant ^ _variable ^ _string_constant ^ pp.Group("(" + _expression + ")")
    _term = pp.Forward()
    _expression <<= _term + pp.ZeroOrMore(pp.oneOf("+ -") + _term)
    _term <<= _factor + pp.ZeroOrMore(pp.oneOf("* /") + _factor)

    _variable_assignment = pp.Group(_variable + "=" + pp.Group(_expression))  # a = 2

    _condition = pp.Group(_variable + pp.oneOf("< > <= >= == !=") + (_integer_constant ^ _real_constant ^ _variable ^ _string_constant))  # a >= 2
    _if_start = pp.Group(pp.Keyword("if") + _condition + ":")  # if a >= 2:
    _if_end = pp.Group(pp.Keyword("endIf"))  # endIf
    _if_str_match = pp.Group(pp.Keyword("ifLike") + "(" + _variable + "," + _string_constant + ")" + ":")  # ifLike(a, "b"): # 模糊匹配

    _switch_start = pp.Group(pp.Keyword("switch") + _variable + ":")  # switch a:
    _switch_case = pp.Group(pp.Keyword("case") + (_integer_constant ^ _string_constant ^ _real_constant) + ":")  # case 1:
    _switch_default = pp.Group(pp.Keyword("default") + ":")  # default:
    _switch_end = pp.Group(pp.Keyword("endSwitch"))  # endSwitch

    _goto_statement = pp.Group(pp.Keyword("goto") + _variable)  # goto a
    _goto_to_place_statement = pp.Group(pp.Keyword("To") + _variable + ":")  # To a:

    _input_with_timeout_call = pp.Group(pp.Keyword("input") + _variable + _timeout_set + _function)  # input a Timeout 1000 timeout()

    _blank_line = pp.LineEnd()  # 空行
    _blank_char = pp.White()  # 空白字符

    _login = pp.Group(pp.Keyword("__login__") + "(" + ")") # __login__()

    _find_db_data = pp.Group(pp.Keyword("findData") + "(" + _variable + "," + _string_constant + ")") # findData(a, "b")
    # a 记录返回数据，b 代表查询内容
    _save_db_data = pp.Group(pp.Keyword("saveData") + "(" + _variable + "," + _string_constant + ")") # saveData(a, "b")
    _update_balance = pp.Group(pp.Keyword("updateBalance") + "(" + _variable + ")") # updateBalance(a)

    _grammar_line = _login ^ _find_db_data ^ _save_db_data ^ _update_balance ^ _goto_statement ^ _goto_to_place_statement ^ _variable_decl ^ _variable_assignment ^ _input_statement ^ _print_statement ^ _timeout_set ^ _exit_statement ^ _function_start ^ _function_end ^ _if_start ^ _if_str_match ^ _if_end ^ _switch_start ^ _switch_case ^ _switch_default ^ _switch_end ^ _input_with_timeout_call ^ _note ^ _function_call

    def parse_code(self, code):
        result = self._grammar_line.parseString(code)[0]
        return result

    def try_parse_variable_assignment(self, code):
        try:
            return self._variable_assignment.parseString(code)[0]
        except pp.ParseException:
            return None

    def is_variable(self, code):
        return self._variable.matches(code)

    def parse_expression(self, code):
        return self._expression.parseString(code)

# 解释器模块 测试桩
if __name__ == "__main__":
    parser = Parser()
    while True:
        test_code = input("请输入代码：")
        if test_code != "exit":
            try:
                test_result = parser.parse_code(test_code)
                print(test_result)
            except pp.ParseException as e:
                print("解析失败：", e)
        else:
            break

    # 用于单独测试，手动模拟输入的原始代码，输出解析后的结果