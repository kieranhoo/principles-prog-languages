from Visitor import Visitor
from AST import *
from StaticError import *
from Utils import *
from abc import ABC


class Symbol(ABC):
    def __init__(self, name, typ, kind = Function(), param = None, inherit = None, pinherit = None, isGlobal = True):
        self.name = name
        self.typ = typ
        self.param = param
        self.kind = kind
        self.pinherit = pinherit
        self.inherit = inherit
        self.isGlobal = isGlobal

    def return_type(self):
        return self.typ

class Util:
    @staticmethod
    def get_dimensions(sym):
        if type(sym) is ArrayLit and isinstance(sym.explist, list):
            if len(sym.explist) != 0:
                return [len(sym.explist)] + Util.get_dimensions(sym.explist[0])
            else: return [len(sym.explist)]
        else:
            return []
    
    @staticmethod
    def flatten(lst, param = []):
        if type(lst) is ArrayLit and isinstance(lst.explist, list):
            for i in lst.explist:
                param = Util.flatten(i, param)
        elif type(lst) is ArrayLit and type(lst.explist) is not list:
            param = param + [lst.explist]
        else : param = param + [lst]
        return param
    
    @staticmethod
    def findSymbol(lst, name, typ):
        for sym in lst:
            for mem in sym:
                if type(mem) is typ and mem.name == name:
                    return mem
        return None
    
    @staticmethod
    def set_symbol(lst, name, kind, typeset):
        for sym in lst:
            for mem in sym:
                if type(mem) is kind and mem.name == name:
                    if kind is FuncDecl:
                        mem.return_type = typeset
                    elif kind is VarDecl:
                        mem.typ = typeset
    @staticmethod
    def getInheritParam(lst, parent):
        if parent is None:
            return []
        psymbol = Util.findSymbol(lst, parent, FuncDecl)
        if psymbol is not None:
            lstparams = []
            for param in psymbol.params:
                if param.inherit is True:
                    lstparams.append(param)
            return lstparams
        return []
    
    @staticmethod
    def addSpecialFunctions(param):
        param[0] += [FuncDecl("readInteger", IntegerType(), [], None, BlockStmt([]))]
        param[0] += [FuncDecl("printInteger", VoidType(), [ParamDecl("a", IntegerType())], None, BlockStmt([]))]
        param[0] += [FuncDecl("readFloat", FloatType(), [], None, BlockStmt([]))]
        param[0] += [FuncDecl("printFloat", VoidType(), [ParamDecl("a", FloatType())], None, BlockStmt([]))]
        param[0] += [FuncDecl("readBoolean", BooleanType(), [], None, BlockStmt([]))]
        param[0] += [FuncDecl("printBoolean", VoidType(), [ParamDecl("a", BooleanType())], None, BlockStmt([]))]
        param[0] += [FuncDecl("readString", StringType(), [], None, BlockStmt([]))]
        param[0] += [FuncDecl("printString", VoidType(), [ParamDecl("a", StringType())], None, BlockStmt([]))]
        param[0] += [FuncDecl("preventDefault", VoidType(), [], None, BlockStmt([]))]
        return param
    
class Loop(ABC):
    pass
class IfStmt(ABC):
    pass

# {{{1},{2}},{{1},{2}},{{1},{2}},{{1},{2}}}

class StaticChecker(Visitor):
    def __init__(self, ast):
        self.ast = ast

    def check(self):
        return self.visit(self.ast, [])

    def visitIntegerType(self, ast, param): 
        return IntegerType()
    
    def visitFloatType(self, ast, param): 
        return FloatType()

    def visitBooleanType(self, ast, param):
        return BooleanType()
    
    def visitStringType(self, ast, param):
        return StringType()
    
    def visitArrayType(self, ast, param): 
        return ArrayType(ast.dimensions, ast.typ)
    
    def visitAutoType(self, ast, param):
        return AutoType()
    
    def visitVoidType(self, ast, param):
        return VoidType()

    def visitBinExpr(self, ast, param):
        e1t = self.visit(ast.left, param)
        e2t = self.visit(ast.right, param)

        # raise TypeMismatchInExpression(e1t)
        if type(e1t) is AutoType:
            for sym in param:
                for mem in sym:
                    if type(mem) is FuncDecl and mem.name == ast.left.name:
                        if type(mem.return_type) is AutoType and type(e2t) is not AutoType:
                            mem.return_type = self.visit(e2t, param)
                            e1t = self.visit(e2t, param)
                            break
                        else:
                            raise TypeMismatchInExpression(ast)
                    elif type(mem) is ParamDecl and mem.name == ast.left.name:
                        if type(mem.typ) is AutoType and type(e2t) is not AutoType:
                            mem.typ = self.visit(e2t, param)
                            e1t = self.visit(e2t, param)
                            break
                        else:
                            raise TypeMismatchInExpression(ast)


        if type(e2t) is AutoType:
            for sym in param:
                for mem in sym:
                    if type(mem) is FuncDecl and mem.name == ast.right.name:
                        if type(mem.return_type) is AutoType and type(e1t) is not AutoType:
                            mem.return_type = self.visit(e1t, param)
                            e2t = self.visit(e1t, param)
                            break
                        else:
                            raise TypeMismatchInExpression(ast)
                    elif type(mem) is ParamDecl and mem.name == ast.right.name:
                        if type(mem.typ) is AutoType and type(e1t) is not AutoType:
                            mem.typ = self.visit(e1t, param)
                            e2t = self.visit(e1t, param)
                            break
                        else:
                            raise TypeMismatchInExpression(ast)
                        
        if type(e1t) is AutoType:
            raise Invalid(Variable(), ast.left.name)
        if type(e2t) is AutoType:
            raise Invalid(Variable(), ast.right.name)

        if ast.op in ['+', '-', '*', '/']:
            # FIXME: auto type conversion checking
            if type(e1t) is not FloatType and type(e1t) is not IntegerType:
                raise TypeMismatchInExpression(ast)
            if type(e2t) is not FloatType and type(e2t) is not IntegerType:
                raise TypeMismatchInExpression(ast)
            if type(e1t) is FloatType or type(e2t) is FloatType:
                return FloatType()
            return IntegerType()
                
        if ast.op in ['%']:
            if type(e1t) is not IntegerType or type(e2t) is not IntegerType:
                raise TypeMismatchInExpression(ast)
            return IntegerType()
        
        if ast.op in ['::']:
            # raise TypeMismatchInExpression(ast)
            if type(e1t) is StringType and type(e2t) is StringType:
                return StringType()
            raise TypeMismatchInExpression(ast)
        
        if ast.op in ['&&', '||']:
            # raise TypeMismatchInExpression(e1t)
            if type(e1t) is BooleanType and type(e2t) is BooleanType:
                return BooleanType()
            raise TypeMismatchInExpression(ast)
        
        if ast.op in ['==', '!=']:
            if type(e1t) is not type(e2t):
                raise TypeMismatchInExpression(ast)
            if type(e1t) is IntegerType and type(e2t) is IntegerType:
                return BooleanType()
            if type(e1t) is BooleanType and type(e2t) is BooleanType:
                return BooleanType()
            raise TypeMismatchInExpression(ast)
        
        if ast.op in ['<', '>', '<=', '>=']:
            if type(e1t) is not FloatType and type(e1t) is not IntegerType:
                raise TypeMismatchInExpression(ast)
            if type(e2t) is not FloatType and type(e2t) is not IntegerType:
                raise TypeMismatchInExpression(ast)
            return BooleanType()
        
        # return self.visit(e1t, param)
    
    def visitUnExpr(self, ast, param):
        et = self.visit(ast.val, param)
        if type(et) is AutoType:
            raise Invalid(Variable(), ast.val.name)
        # FIXME: miss Index operator [,]
        if ast.op in ['!']:
            if type(et) is not BooleanType:
                raise TypeMismatchInExpression(ast)
            return BooleanType()
        if ast.op in ['-']:
            if type(et) is not IntegerType and type(et) is not FloatType:
                raise TypeMismatchInExpression(ast)
            return IntegerType() if type(et) is IntegerType else FloatType()

    def visitId(self, ast, param):
        for sym in param:
            # raise TypeMismatchInExpression(param)
            for mem in sym:
                if type(mem) is Symbol:
                    continue
                if (type(mem) is VarDecl or type(mem) is ParamDecl) and mem.name == ast.name:
                    return mem.typ
        raise Undeclared(Identifier(), ast.name)
    
    def visitArrayCell(self, ast, param):
        for sym in param:
            for mem in sym:
                if type(mem) is Symbol:
                    continue
                if mem.name == ast.name and (type(mem) is VarDecl or type(mem) is ParamDecl):
                    if type(mem.typ) is not ArrayType :
                        raise TypeMismatchInExpression(ast)
                    # FIXME: bug here ?
                    if len(mem.typ.dimensions) == len(ast.cell):
                        for cell in ast.cell:
                            if type(self.visit(cell, param)) is not IntegerType:
                                raise TypeMismatchInExpression(ast)
                        return mem.typ.typ
                    else:
                        raise TypeMismatchInExpression(ast)
        raise Undeclared(Variable(), ast.name)
        # raise TypeMismatchInExpression(ast)
        
    def visitIntegerLit(self, ast, param):
        return IntegerType()
    
    def visitFloatLit(self, ast, param):
        return FloatType()
    
    def visitStringLit(self, ast, param):
        return StringType()
    
    def visitBooleanLit(self, ast, param):
        return BooleanType()
    
    def visitArrayLit(self, ast, param):
        # raise IllegalArrayLiteral(ast)
        # FIXME: continue
        def get_num(lst):
            count = 1
            for i in lst:
                count = count * i
            return count
        
        def check_type(lst):
            typ = self.visit(lst[0], param)
            for i in lst:
                _typ = self.visit(i, param)
                if type(typ) is not type(_typ):
                    return False, None
            return True, typ
            
        if len(ast.explist) != 0:
            __dimension = Util.get_dimensions(ast)
            __check, __typ = check_type(Util.flatten(ast))
            check = (get_num(__dimension) == len(Util.flatten(ast))) and __check
            # check = check_type(Symbol.flatten(ast))
            if check is False:
                raise IllegalArrayLiteral(ast)
            return ArrayType(__dimension, self.visit(__typ, param))
        else: return ArrayType([], AutoType())

    def visitFuncCall(self, ast, param):

        def check_name(astc, lst):
            # find environment program
            for sym in lst:
                for mem in sym:
                    if type(mem) is Symbol:
                        continue
                    if mem.name == astc.name and type(mem) is FuncDecl:
                        return True, mem
            return False, None

        ok, func = check_name(ast, param)
        if ok is False:
            raise Undeclared(Function(), ast.name)

        # create env param
        param_func = [[]] + param
        for paramdecl in func.params:
            # get all env parameters
            param_func = self.visit(paramdecl, param_func)
        # func(a : int, b : float) -> what means ? func(1,2,3)
        ## FIXME: khi lấy prototype không quăng lỗi mà chỉ lấy tên + danh sách đối số
        # if len(ast.args) != len(param_func[0]):
        if len(ast.args) != len(func.params):
            raise TypeMismatchInExpression(ast)
        for i in range(0, len(ast.args)):
            # raise TypeMismatchInExpression(func)
            # raise TypeMismatchInExpression(param_func[0][i].typ)
            if type(param_func[0][i].typ) is AutoType:
                for sym in param:
                    for mem in sym:
                        if type(mem) is FuncDecl and mem.name == ast.name:
                            mem.params[i].typ = self.visit(ast.args[i], param)
                            param_func[0][i].typ = self.visit(ast.args[i], param)
            elif type(param_func[0][i].typ) is not AutoType:
                typ_ast = self.visit(ast.args[i], param)
                if type(param_func[0][i].typ) is not type(typ_ast):
                    # raise TypeMismatchInStatement(param_func[0][i].typ)
                    # raise TypeMismatchInStatement(typ_ast)
                    # is not so sánh về bộ nhớ, != so sánh về giá trị
                    # raise TypeMismatchInExpression(param_func[0][i].typ)
                    if type(param_func[0][i].typ) is not FloatType:
                        raise TypeMismatchInExpression(ast)
                    if type(typ_ast) is not IntegerType:
                        raise TypeMismatchInExpression(ast)

        return func.return_type
        
    def visitAssignStmt(self, ast, param): 
        rhs_t = self.visit(ast.rhs, param)
        lhs_t = self.visit(ast.lhs, param)
        # raise TypeMismatchInStatement(True)

        '''
            a = 1 + 2;
        '''
        # FIXME: rhs is VoidType, funcall
        if type(rhs_t) is VoidType:
            raise TypeMismatchInStatement(ast)
        # variable declarations
        if type(rhs_t) is AutoType and type(ast.rhs) is not FuncCall:
            raise Invalid(Variable(), ast.rhs.name)
        
        # raise TypeMismatchInExpression(rhs_t)
        if type(rhs_t) is AutoType:
            for sym in param:
                for mem in sym:
                    # FIXME: type(mem) is VarDecl and ?
                    if type(mem) is Symbol:
                        continue
                    elif type(mem) is FuncDecl and mem.name == ast.rhs.name:
                        if type(mem.return_type) is AutoType and type(lhs_t) is AutoType:
                            raise Invalid(Function(), mem.name)
                        if type(mem.return_type) is AutoType and type(lhs_t) is not AutoType:
                            mem.return_type = self.visit(lhs_t, param)
                            rhs_t = self.visit(lhs_t, param)
                            break
        
        if type(lhs_t) is not type(rhs_t) and type(lhs_t) is not AutoType:
            # raise TypeMismatchInStatement(rhs_t)
            if type(lhs_t) is not FloatType:
                raise TypeMismatchInStatement(ast)
            if type(rhs_t) is not IntegerType:
                raise TypeMismatchInStatement(ast)
                

        for sym in param:
            for mem in sym:
                if type(mem) is Symbol:
                    continue
                elif mem.name == ast.lhs.name and type(mem.typ) is AutoType:
                    mem.typ = self.visit(rhs_t, param)
                    # raise TypeMismatchInExpression(mem)
                    break
        return param

    def visitBlockStmt(self, ast, param):
        # env = [[]]
        func = param[0][0]
        if type(func) is Symbol and func.inherit is not None:
            # raise InvalidStatementInFunction(member)
            pfunc = Util.findSymbol(param, func.inherit, FuncDecl)
            # pinherit = Util.getInheritParam(param, func.inherit)
            if len(ast.body) != 0 and type(ast.body[0]) is CallStmt:
                if ast.body[0].name == "super":
                    if pfunc is not None :
                        if len(ast.body[0].args) > len(pfunc.params):
                            raise TypeMismatchInExpression(ast.body[0].args[0])
                        elif len(ast.body[0].args) < len(pfunc.params):
                            raise TypeMismatchInExpression("")
                        else:
                            for i in range(len(pfunc.params)):
                                if type(pfunc.params[i].typ) is AutoType:
                                    continue
                                bodytype = self.visit(ast.body[0].args[i], param)
                                if type(pfunc.params[i].typ) is not type(bodytype):
                                    if type(pfunc.params[i].typ) is not FloatType:
                                        raise TypeMismatchInExpression(type(ast.body[0].args[i]))
                                    if type(ast.body[0].args[i]) is not IntegerType:
                                        raise TypeMismatchInExpression(ast.body[0].args[i])
                elif len(pfunc.params) != 0 and ast.body[0].name != "preventDefault":
                    raise InvalidStatementInFunction(func.name)
            elif pfunc is not None and len(pfunc.params) != 0:
                raise InvalidStatementInFunction(func.name)
        for mem in ast.body:
            self.visit(mem, param)
        return param

    def visitIfStmt(self, ast, param):
        condition = self.visit(ast.cond, param)
        if type(condition) is not BooleanType:
            raise TypeMismatchInStatement(ast)
        t_env = [[Symbol(None, None, IfStmt())]] + param
        t_env = self.visit(ast.tstmt, t_env)
        if ast.fstmt is not None:
            f_env = [[Symbol(None, None, IfStmt())]] + param
            f_env = self.visit(ast.fstmt, f_env)
        return param
        
    def visitForStmt(self, ast, param):
        self.visit(ast.init, param)
        init = self.visit(ast.init.lhs, param)
        if type(init) is not IntegerType:
            raise TypeMismatchInStatement(ast)
        typ = self.visit(ast.cond, param)
        if type(typ) is not BooleanType:
            raise TypeMismatchInStatement(ast)
        self.visit(ast.upd, param)

        env = [[Symbol(None, None, Loop())]] + param
        env = self.visit(ast.stmt, env)
        return param

    def visitWhileStmt(self, ast, param): 
        cond = self.visit(ast.cond, param)
        if type(cond) is not BooleanType:
            raise TypeMismatchInStatement(ast)
        env = [[Symbol(None, None, Loop())]] + param
        self.visit(ast.stmt, env)
        return param
        
    def visitDoWhileStmt(self, ast, param):
        cond = self.visit(ast.cond, param)
        if type(cond) is not BooleanType:
            raise TypeMismatchInVarDecl(ast)
        env = [[Symbol(None, None, Loop())]] + param
        self.visit(ast.stmt, env)
        return param

    def visitBreakStmt(self, ast, param):
        # raise MustInLoop(ast)
        for sym in param:
            for mem in sym:
                if type(mem) is Symbol and type(mem.kind) is Loop:
                    return BreakStmt()
        raise MustInLoop(ast)

    def visitContinueStmt(self, ast, param): 
        for sym in param:
            for mem in sym:
                if type(mem) is Symbol and type(mem.kind) is Loop:
                    return ContinueStmt()
        raise MustInLoop(ast)
    
    def visitReturnStmt(self, ast, param):
        if param[0][0].isGlobal is True:
            # raise TypeMismatchInStatement(param)
            type_ret = self.visit(ast.expr, param) if ast.expr is not None else None
            # raise TypeMismatchInStatement(type_ret)
            if type(param[0][0].kind) is Function:
                param[0][0].isGlobal = False
            for sym in param:
                for mem in sym:
                    if type(mem) is Symbol and type(mem.kind) is Function:
                        if type(mem.typ) is type(type_ret):
                            return mem.typ
                        if type(mem.typ) is AutoType:
                            if type_ret is None:
                                Util.set_symbol(param, mem.name, FuncDecl, VoidType())
                                mem.typ = VoidType()
                            else:
                                Util.set_symbol(
                                    param, mem.name, FuncDecl, self.visit(type_ret, param))
                                mem.typ = self.visit(type_ret, param)
                        # raise TypeMismatchInStatement(type_ret)
                        if type(mem.typ) is VoidType and type_ret is None:
                            return VoidType()
                        if type(mem.typ) is not type(type_ret):
                            # raise TypeMismatchInStatement(mem.typ)
                            if type(mem.typ) is not FloatType:
                                raise TypeMismatchInStatement(ast)
                            if type(type_ret) is not IntegerType:
                                raise TypeMismatchInStatement(ast)
                            return mem.typ
                        else:
                            return mem.typ
            raise TypeMismatchInStatement(ast)
    
    def visitCallStmt(self, ast, param):
        def check_name(astc, lst):
            # find environment program 
            for sym in lst:
                for mem in sym:
                    if type(mem) is Symbol:
                        continue
                    if mem.name == astc.name and type(mem) is FuncDecl:
                        if mem.return_type is AutoType:
                            mem.return_type = VoidType()
                        return True, mem
            return False, None
        
        if ast.name not in ["super", "preventDefault"]:
            ok, func = check_name(ast, param)
            if ok is False:
                raise Undeclared(Function(), ast.name)

            # create env param
            param_func = [[]] + param
            for paramdecl in func.params:
                # get all env parameters
                param_func = self.visit(paramdecl, param_func)
            # func(a : int, b : float) -> what means ? func(1,2,3)
            if len(ast.args) != len(param_func[0]):
                raise TypeMismatchInStatement(ast)
            for i in range(0, len(ast.args)):
                if type(param_func[0][i].typ) is not AutoType:
                    typ_ast = self.visit(ast.args[i], param)
                    if type(param_func[0][i].typ) is not type(typ_ast):
                        if type(param_func[0][i].typ) is not FloatType:
                            raise TypeMismatchInStatement(ast)
                        if type(typ_ast) is not IntegerType:
                            raise TypeMismatchInStatement(ast)
        # elif ast.name == "super":
        #     #FIXME: here
        #     inherit = param[0][0].inherit
        #     func = Util.findSymbol(param, inherit, FuncDecl)
        #     in_param = []
        #     for p in func.params:
        #         if p.inherit is True:
        #             in_param = in_param + [p]
        return param
        

    def visitVarDecl(self, ast, param):
        if len(param) > 1:
            for p in param[0]:
                # if type(p) is VarDecl or type(p) is ParamDecl:
                if p.name == ast.name:
                    raise Redeclared(Variable(), ast.name)

            if type(ast.typ) is AutoType and ast.init is None:
                raise Invalid(Variable(), ast.name)

            if ast.init is not None:
                expr_type = self.visit(ast.init, param)
                # raise TypeMismatchInExpression(expr_type)
                if type(expr_type) is not type(ast.typ) and type(expr_type) is not AutoType:
                    if type(ast.typ) is AutoType and type(expr_type) is not VoidType:
                        ast.typ = self.visit(expr_type, param)
                    # int = int
                    # int = float -> error
                    # float = int -> ok
                    elif type(ast.typ) is not FloatType or type(expr_type) is not IntegerType:
                        raise TypeMismatchInVarDecl(ast)

                if type(expr_type) is ArrayType and type(ast.typ) is ArrayType:
                    # raise TypeMismatchInVarDecl(expr_type)
                    if len(expr_type.dimensions) == len(ast.typ.dimensions):
                        for i in range(0, len(expr_type.dimensions)):
                            if expr_type.dimensions[i] != ast.typ.dimensions[i]:
                                raise TypeMismatchInVarDecl(ast)
                    if type(ast.typ.typ) is AutoType:
                        ast.typ.typ = self.visit(expr_type.typ, param)
                    if type(expr_type.typ) is not type(ast.typ.typ):
                        if type(ast.typ.typ) is not FloatType:
                            raise TypeMismatchInVarDecl(ast)
                        if type(expr_type.typ) is not IntegerType:
                            raise TypeMismatchInVarDecl(ast)
                # raise TypeMismatchInVarDecl(expr_type)
                if type(expr_type) is AutoType and type(ast.init) is FuncCall and type(ast.typ) is AutoType:
                    raise Invalid(Function(), ast.init.name)
                elif type(expr_type) is AutoType and type(ast.init) is FuncCall:
                    for sym in param:
                        for mem in sym:
                            if mem.name == ast.init.name and type(mem) is FuncDecl:
                                mem.return_type = self.visit(ast.typ, param)
                                break

            param[0] += [ast]
        # return [Variable(), ast.name, ast.typ]
        return param
        

    def visitParamDecl(self, ast, param):
        # # FIXME: done
        for par in param[0]:
            if type(par) is ParamDecl and par.name == ast.name:
                raise Redeclared(Parameter(), ast.name)
        param[0] += [ast]
        return param
    
    def visitFuncDecl(self, ast, param):

        if len(param) == 1:
            param[0] += [ast]

        '''
            if length(param) == 1 : get environment for program
            if length(param) > 1: acess body of function
        '''
        if len(param) > 1: # param = [[],[ast]]

            for mem in param[0]:
                if mem.name == ast.name:
                    raise Redeclared(Function(), ast.name)

            if ast.name in ["super",]:
                raise Redeclared(Function(), ast.name)
            
            param[0] += [ast]

            pinherit = None
            # raise TypeMismatchInExpression(len([]) == 0)
            if ast.inherit is not None:
                if len(ast.body.body) != 0 and ast.body.body[0].name != "preventDefault":
                    params = Util.getInheritParam(param, ast.inherit)
                    # TODO: resume here
                    for astparam in ast.params:
                        for parentparam in params:
                            if astparam.name == parentparam.name:
                                raise Invalid(Parameter(), astparam.name)
                    pinherit = params

                pfunc = Util.findSymbol(param, ast.inherit, FuncDecl)
                if pfunc is None:
                    raise Undeclared(Function(), ast.inherit)
                # for p in pfunc.params:
                #     if p.inherit is True:
                #         for pthis in ast.params:
                #             if p.name == pthis.name:
                #                 raise Invalid(Parameter(), pthis.name)
                    
            env = [[Symbol(ast.name, ast.return_type, Function(), ast.params, ast.inherit)]] + param
            if pinherit is not None:
                env[0] = env[0] + pinherit
            for paramdecl in ast.params:
                # get parameters
                env = self.visit(paramdecl, env)
            # visit the body {BlockStmt}
            env = self.visit(ast.body, env)
        # return [Function() , ast.name , ast.return_type]
        return param


    def visitProgram(self, ast, param):
        param = [[]]
        for decl in ast.decls:
            # get and funcdecl
            param = self.visit(decl, param)
        
        body = [[]] + param
        body = Util.addSpecialFunctions(body)
        for env in ast.decls:
            # acess all function and variable decl
            body = self.visit(env, body)
    
        def isMain(decl):
            if decl.name == "main" and type(decl.return_type) is VoidType and len(decl.params) == 0:
                return "main"
            return ""
        if Utils().lookup("main", ast.decls, isMain) is None:
            raise NoEntryPoint()
        return []
