import typing
from calciumlang.expression.assignable import (
    Assignable,
    Variable,
    Attribute,
    Subscript,
)
from calciumlang.expression.call import Call, KeywordArgument
from calciumlang.expression.operator import UnaryOperator, BinaryOperator
from calciumlang.command.assign import Assign
from calciumlang.command.class_stmt import Class
from calciumlang.command.command import Command
from calciumlang.command.expr_stmt import ExprStmt
from calciumlang.command.function import Return
from calciumlang.command.ifs import Ifs, If, Elif, Else
from calciumlang.command.import_stmt import Import
from calciumlang.command.loop import For, While, Break, Continue
from calciumlang.command.pass_stmt import Comment, Pass, End
from calciumlang.element import Element
from calciumlang.index import Index
from calciumlang.keyword import Keyword


class Parser:
    def __init__(self):
        pass

    def read(self, line: list[Element]) -> Command:
        kwd: Keyword = line[Index.KEYWORD]  # type: ignore
        parser_func = _table[kwd]
        cmd = parser_func(self, line)
        return cmd

    def read_args(self, args_list: list[Element]) -> list[typing.Any]:
        args = []
        for elem in args_list:
            arg = self.read_expr(elem)
            args.append(arg)
        return args

    def read_expr(self, obj: Element) -> typing.Any:
        if isinstance(obj, dict):
            parsed_dict = {}
            for key, value in obj.items():
                # key must be str type
                parsed_dict[key] = self.read_expr(value)
            return parsed_dict
        if not isinstance(obj, list):
            return obj
        # when obj is list, it should have at least one element
        if isinstance(obj[0], list):
            # a list literal
            parsed_list = []
            for elem in obj[0]:
                parsed_list.append(self.read_expr(elem))
            return parsed_list
        # calcium's expression with keyword in the first element of a list
        kwd = obj[Index.EXPRESSION_KEYWORD]
        if kwd in (Keyword.VARIABLE, Keyword.ATTRIBUTE, Keyword.SUBSCRIPT):
            return self.read_assignable(obj)
        if kwd == Keyword.CALL:
            callee = self.read_assignable(obj[Index.CALL_CALLEE])
            args = self.read_args(obj[Index.CALL_ARGS])
            return Call(callee, args)  # type: ignore
        if kwd in (Keyword.TUPLE, Keyword.COMMA):
            return tuple(
                self.read_expr(elem) for elem in obj[Index.EXPRESSION_KEYWORD :]
            )
        if kwd == Keyword.KWARG:
            return KeywordArgument(
                obj[Index.KWARG_NAME], self.read_expr(obj[Index.KWARG_VALUE])
            )
        if kwd in (Keyword.NOT, Keyword.NEGATIVE):
            operand = self.read_expr(obj[Index.UNARY_OPERAND])
            return UnaryOperator(kwd, operand)
        # should be a binary operator
        left = self.read_expr(obj[Index.LEFT_OPERAND])
        right = self.read_expr(obj[Index.RIGHT_OPERAND])
        return BinaryOperator(kwd, left, right)

    def read_assignable(self, listobj: list[Element]) -> Assignable:
        kwd = listobj[Index.EXPRESSION_KEYWORD]
        if kwd == Keyword.VARIABLE:
            name: str = listobj[Index.VAR_NAME]  # type: ignore
            return Variable(name)
        if kwd == Keyword.ATTRIBUTE:
            obj = self.read_expr(listobj[Index.ATTR_OBJECT])
            properties = []
            # attributes can chain property names
            for i in range(Index.ATTR_NAME, len(listobj)):
                properties.append(listobj[i])
            return Attribute(obj, properties)
        if kwd == Keyword.SUBSCRIPT:
            obj = self.read_assignable(listobj[Index.SUBSCRIPT_OBJECT])  # type: ignore
            if len(listobj) == Index.SUBSCRIPT_INDEX + 1:
                index = self.read_expr(listobj[Index.SUBSCRIPT_INDEX])
                return Subscript(obj, index)
            if len(listobj) == Index.SUBSCRIPT_SLICE_STOP + 1:
                start = self.read_expr(listobj[Index.SUBSCRIPT_SLICE_START])
                stop = self.read_expr(listobj[Index.SUBSCRIPT_SLICE_STOP])
                return Subscript(obj, None, start, stop)
        raise ValueError("Invalid keyword for expression")


_table: dict[Keyword, typing.Callable[[Parser, list[Element]], Command]] = {}


def _assign(parser: Parser, line: list[Element]) -> Assign:
    left = parser.read_assignable(line[Index.ASSIGN_LEFT])  # type: ignore
    right = parser.read_expr(line[Index.ASSIGN_RIGHT])
    return Assign(left, right)


def _make_compound_assign(
    parser: Parser, line: list[Element], keyword: Keyword
) -> Assign:
    lhs = parser.read_assignable(line[Index.ASSIGN_LEFT])  # type: ignore
    rhs = parser.read_expr(line[Index.ASSIGN_RIGHT])
    binop = BinaryOperator(keyword.value, lhs, rhs)
    return Assign(lhs, binop)


def _compound_add(parser: Parser, line: list[Element]) -> Assign:
    return _make_compound_assign(parser, line, Keyword.ADD)


def _compound_subtract(parser: Parser, line: list[Element]) -> Assign:
    return _make_compound_assign(parser, line, Keyword.SUBTRACT)


def _compound_multiply(parser: Parser, line: list[Element]) -> Assign:
    return _make_compound_assign(parser, line, Keyword.MULTIPLY)


def _ifs(parser: Parser, line: list[Element]) -> Command:
    return Ifs()


def _if(parser: Parser, line: list[Element]) -> Command:
    condition = parser.read_expr(line[Index.CONDITION])
    return If(condition)


def _elif(parser: Parser, line: list[Element]) -> Command:
    condition = parser.read_expr(line[Index.CONDITION])
    return Elif(condition)


def _else(parser: Parser, line: list[Element]) -> Command:
    return Else()


def _for(parser: Parser, line: list[Element]) -> Command:
    variables = parser.read_assignable(line[Index.FOR_VARIABLES])  # type: ignore
    iterable = parser.read_expr(line[Index.FOR_ITERABLE])
    return For(variables, iterable)


def _while(parser: Parser, line: list[Element]) -> Command:
    condition = parser.read_expr(line[Index.CONDITION])
    return While(condition)


def _break(parser: Parser, line: list[Element]) -> Command:
    return Break()


def _continue(parser: Parser, line: list[Element]) -> Command:
    return Continue()


def _return(parser: Parser, line: list[Element]) -> Command:
    if len(line) < Index.RETURN_VALUE + 1:
        # return without value
        return Return(None)
    expr = parser.read_expr(line[Index.RETURN_VALUE])
    return Return(expr)


def _class(parser: Parser, line: list[Element]) -> Command:
    name: str = line[Index.CLASS_NAME]  # type: ignore
    superclass = parser.read_expr(line[Index.CLASS_SUPERCLASS])
    return Class(name, superclass)


def _import(parser: Parser, line: list[Element]) -> Command:
    path: str = line[Index.IMPORT_PATH]  # type: ignore
    return Import(path)


def _expr_stmt(parser: Parser, line: list[Element]) -> Command:
    expr = parser.read_expr(line[Index.EXPR_STMT])
    return ExprStmt(expr)


def _comment(parser: Parser, line: list[Element]) -> Command:
    return Comment()


def _pass(parser: Parser, line: list[Element]) -> Command:
    return Pass()


def _end(parser: Parser, line: list[Element]) -> Command:
    return End()


_table[Keyword.ASSIGN] = _assign
_table[Keyword.COMPOUND_ADD] = _compound_add
_table[Keyword.COMPOUND_SUBTRACT] = _compound_subtract
_table[Keyword.COMPOUND_MULTIPLY] = _compound_multiply
_table[Keyword.IFS] = _ifs
_table[Keyword.IF] = _if
_table[Keyword.ELIF] = _elif
_table[Keyword.ELSE] = _else
_table[Keyword.FOR] = _for
_table[Keyword.WHILE] = _while
_table[Keyword.BREAK] = _break
_table[Keyword.CONTINUE] = _continue
_table[Keyword.RETURN] = _return
_table[Keyword.CLASS] = _class
_table[Keyword.IMPORT] = _import
_table[Keyword.EXPR_STMT] = _expr_stmt
_table[Keyword.COMMENT] = _comment
_table[Keyword.PASS] = _pass
_table[Keyword.END] = _end