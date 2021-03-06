from AST import *
from sexpdata import *
from Types import *


def checkExpectedTypesOfValue(value, types):
    for type in types:
        if _isConsistentTypeOfValue(value, type):
            return
    raise ValueError(' or '.join(map(str, types)) + ' was expected.')


def _isConsistentTypeOfValue(value, type):
    if isinstance(type, DynamicType):
        return True
    if isinstance(type, FunctionType):
        if not isinstance(value, FunctionExpression):
            return False
        return _areConsistentTypes(value.functionType, type)
    return isinstance(value, type)


def _areConsistentTypes(type1, type2):
    if isinstance(type1, DynamicType) or isinstance(type2, DynamicType):
        return True
    if isinstance(type1, FunctionType) and isinstance(type2, FunctionType):
        return _areConsistenFunctionTypes(type1, type2)
    if isinstance(type1, FunctionType) or isinstance(type2, FunctionType):
        return False
    return type1 == type2


def _areConsistenFunctionTypes(functionType1, functionType2):
    parameterLength1 = len(functionType1.parameterTypes)
    parameterLength2 = len(functionType2.parameterTypes)
    if parameterLength1 != parameterLength2 or not _areConsistentTypes(functionType1.returnType,
                                                                       functionType2.returnType):
        return False
    for i in range(parameterLength1):
        if not _areConsistentTypes(functionType1.parameterTypes[i], functionType2.parameterTypes[i]):
            return False
    return True


def _checkExpectedTypes(type, types):
    for t in types:
        if _areConsistentTypes(type, t):
            return
    raise ValueError(' or '.join(map(str, types)) + ' was expected.')


def typeCheck(ast):
    return ast.accept(TypeChecker())


class TypeChecker:
    def __init__(self):
        self.env = Environment()

    def visitBoolLiteral(self, boolLiteral):
        checkExpectedTypesOfValue(boolLiteral.value, [bool])
        return TypeCheckerResult(bool, boolLiteral)

    def visitIntLiteral(self, intLiteral):
        checkExpectedTypesOfValue(intLiteral.value, [int])
        return TypeCheckerResult(int, intLiteral)

    def visitFloatLiteral(self, floatLiteral):
        checkExpectedTypesOfValue(floatLiteral.value, [int, float])
        return TypeCheckerResult(float, floatLiteral)

    def visitStringLiteral(self, stringLiteral):
        checkExpectedTypesOfValue(stringLiteral.value, [str])
        return TypeCheckerResult(str, stringLiteral)

    def visitDynamicLiteral(self, dynamicLiteral):
        checkExpectedTypesOfValue(dynamicLiteral.value, [bool, int, float, str])
        return TypeCheckerResult(DynamicType(), dynamicLiteral)

    def visitUnaryExpression(self, unaryExpression):
        if unaryExpression.command == "not":
            expressionTypeCheckerResult = unaryExpression.expression.accept(self)
            unaryExpression.expression = expressionTypeCheckerResult.astNode
            expressionType = expressionTypeCheckerResult.type
            if isinstance(expressionType, DynamicType):
                unaryExpression.expression = CheckDynamicTypeExpression([bool], unaryExpression.expression)
            else:
                _checkExpectedTypes(expressionType, [bool])
            return TypeCheckerResult(bool, unaryExpression)
        raise ValueError(
            "UnaryExpression with command " + unaryExpression.command + " not yet implemented at typeChecker level.")

    def visitBinaryExpression(self, binaryExpression):
        firstExpressionTypeCheckerResult = binaryExpression.firstExpression.accept(self)
        binaryExpression.firstExpression = firstExpressionTypeCheckerResult.astNode
        firstExpressionType = firstExpressionTypeCheckerResult.type
        secondExpressionTypeCheckerResult = binaryExpression.secondExpression.accept(self)
        binaryExpression.secondExpression = secondExpressionTypeCheckerResult.astNode
        secondExpressionType = secondExpressionTypeCheckerResult.type
        if binaryExpression.command == "and" or binaryExpression.command == "or":
            if isinstance(firstExpressionType, DynamicType):
                binaryExpression.firstExpression = CheckDynamicTypeExpression([bool], binaryExpression.firstExpression)
            else:
                _checkExpectedTypes(firstExpressionType, [bool])
            if isinstance(secondExpressionType, DynamicType):
                binaryExpression.secondExpression = CheckDynamicTypeExpression([bool],
                                                                               binaryExpression.secondExpression)
            else:
                _checkExpectedTypes(secondExpressionType, [bool])
            return TypeCheckerResult(bool, binaryExpression)
        elif binaryExpression.command == "+" or binaryExpression.command == "-" or binaryExpression.command == "*" or binaryExpression.command == "/":
            if isinstance(firstExpressionType, DynamicType):
                binaryExpression.firstExpression = CheckDynamicTypeExpression([int, float],
                                                                              binaryExpression.firstExpression)
            else:
                _checkExpectedTypes(firstExpressionType, [int, float])
            if isinstance(secondExpressionType, DynamicType):
                binaryExpression.secondExpression = CheckDynamicTypeExpression([int, float],
                                                                               binaryExpression.secondExpression)
            else:
                _checkExpectedTypes(secondExpressionType, [int, float])

            type = int if firstExpressionType == int and secondExpressionType == int else float
            return TypeCheckerResult(type, binaryExpression)
        raise ValueError("BinaryExpression with command " + binaryExpression.command + " not yet implemented.")

    def visitIfExpression(self, ifExpression):
        conditionExpressionTypeCheckerResult = ifExpression.conditionExpression.accept(self)
        ifExpression.conditionExpression = conditionExpressionTypeCheckerResult.astNode
        conditionExpressionType = conditionExpressionTypeCheckerResult.type
        if isinstance(conditionExpressionType, DynamicType):
            ifExpression.conditionExpression = CheckDynamicTypeExpression([bool], ifExpression.conditionExpression)
        else:
            _checkExpectedTypes(conditionExpressionType, [bool])
        thenExpressionTypeCheckerResult = ifExpression.thenExpression.accept(self)
        ifExpression.thenExpression = thenExpressionTypeCheckerResult.astNode
        thenExpressionType = thenExpressionTypeCheckerResult.type
        elseExpressionTypeCheckerResult = ifExpression.elseExpression.accept(self)
        ifExpression.elseExpression = elseExpressionTypeCheckerResult.astNode
        elseExpressionType = elseExpressionTypeCheckerResult.type
        if isinstance(thenExpressionType, DynamicType) or isinstance(elseExpressionType, DynamicType):
            return TypeCheckerResult(DynamicType(), ifExpression)
        _checkExpectedTypes(thenExpressionType, [elseExpressionType])
        return TypeCheckerResult(thenExpressionType, ifExpression)

    def visitLetExpression(self, letExpression):
        oldEnv = self.env
        self.env = self.env.clone()
        valueExpressionTypeCheckerResult = letExpression.valueExpression.accept(self)
        letExpression.valueExpression = valueExpressionTypeCheckerResult.astNode
        valueExpressionType = valueExpressionTypeCheckerResult.type
        self.env.put(letExpression.symbol.value(), valueExpressionType)
        thenExpressionTypeCheckerResult = letExpression.thenExpression.accept(self)
        letExpression.thenExpression = thenExpressionTypeCheckerResult.astNode
        thenExpressionType = thenExpressionTypeCheckerResult.type
        self.env = oldEnv
        return TypeCheckerResult(thenExpressionType, letExpression)

    def visitGetExpression(self, getExpression):
        return TypeCheckerResult(self.env.get(getExpression.symbol.value()), getExpression)

    def visitFunctionExpression(self, functionExpression):
        functionType = functionExpression.functionType
        parametersLength = len(functionType.parameterTypes)
        oldEnv = self.env
        self.env = Environment()
        for i in range(parametersLength):
            symbol = functionExpression.parameterSymbols[i]
            if not isinstance(symbol, Symbol):
                raise ValueError('Each function parameter must be a symbol.')
            self.env.put(functionExpression.parameterSymbols[i].value(), functionType.parameterTypes[i])
        bodyExpressionTypeCheckerResult = functionExpression.bodyExpression.accept(self)
        functionExpression.bodyExpression = bodyExpressionTypeCheckerResult.astNode
        bodyExpressionType = bodyExpressionTypeCheckerResult.type
        _checkExpectedTypes(bodyExpressionType, [functionType.returnType])
        if not isinstance(functionType.returnType, DynamicType) and isinstance(bodyExpressionType, DynamicType):
            functionExpression.bodyExpression = CheckDynamicTypeExpression([functionType.returnType],
                                                                           functionExpression.bodyExpression)
        self.env = oldEnv
        return TypeCheckerResult(functionType, functionExpression)

    def visitApplyExpression(self, applyExpression):
        functionExpressionTypeCheckerResult = applyExpression.functionExpression.accept(self)
        applyExpression.functionExpression = functionExpressionTypeCheckerResult.astNode
        functionType = functionExpressionTypeCheckerResult.type
        argumentTypes = []
        for i in range(len(applyExpression.argumentExpressions)):
            argumentTypeCheckerResult = applyExpression.argumentExpressions[i].accept(self)
            applyExpression.argumentExpressions[i] = argumentTypeCheckerResult.astNode
            argumentType = argumentTypeCheckerResult.type
            argumentTypes.append(argumentType)
        argumentsLength = len(argumentTypes)
        if len(functionType.parameterTypes) != argumentsLength:
            raise ValueError('Function length of parameters and arguments in apply do not match.')
        for i in range(argumentsLength):
            parameterType = functionType.parameterTypes[i]
            argumentType = argumentTypes[i]
            _checkExpectedTypes(argumentType, [parameterType])
        if (isinstance(functionType.returnType, DynamicType)):
            return TypeCheckerResult(functionType.returnType, applyExpression)
        return TypeCheckerResult(functionType.returnType,
                                 CheckDynamicTypeExpression([functionType.returnType], applyExpression))


class TypeCheckerResult:
    def __init__(self, type, astNode):
        self.type = type
        self.astNode = astNode
