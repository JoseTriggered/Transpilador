import re


class Lexer:
    def __init__(self, source_code):
        self.tokens = []
        self.current_position = 0
        self.source_code = source_code
        self.token_regex = [
            ("KEYWORD", r'\b(if|else|elif|while|def|return|and|or)\b'),
            ("IDENTIFIER", r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
            ("NUMBER", r'\b\d+\b'),
            ("OPERATOR", r'[+\-/*=<>!]+'),  
            ("DELIMITER", r'[():,;]'),
            ("WHITESPACE", r'\s+'),
        ]

    def tokenize(self):
        while self.current_position < len(self.source_code):
            match_found = False
            for token_type, regex in self.token_regex:
                regex_compiled = re.compile(regex)
                match = regex_compiled.match(self.source_code, self.current_position)
                if match:
                    if token_type != "WHITESPACE":  # Ignorar espaços em branco
                        self.tokens.append((token_type, match.group(0)))
                    self.current_position = match.end()
                    match_found = True
                    break
            if not match_found:
                raise ValueError(f"Token inválido na posição {self.current_position}")
        return self.tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_position = 0

    def parse(self):
        return self.programa()

    def current_token(self):
        return self.tokens[self.current_position] if self.current_position < len(self.tokens) else None

    def eat(self, token_type):
        if self.current_token() and self.current_token()[0] == token_type:
            self.current_position += 1
        else:
            raise ValueError(f"Esperado token {token_type}, mas encontrado {self.current_token()}")

    def programa(self):
        declaracoes = []
        while self.current_position < len(self.tokens):
            declaracoes.append(self.declaracao())
        return Programa(declaracoes)

    def declaracao(self):
        token = self.current_token()
        if token and token[0] == "KEYWORD" and token[1] == "if":
            return self.declaracao_if()
        elif token and token[0] == "KEYWORD" and token[1] == "while":
            return self.declaracao_while()
        elif token and token[0] == "KEYWORD" and token[1] == "def":
            return self.declaracao_funcao()
        elif token and token[0] == "IDENTIFIER":
            return self.atribuicao()
        elif token and token[0] == "KEYWORD" and token[1] == "return":
            return self.declaracao_return()
        else:
            raise ValueError(f"Declaração inválida: {token}")

    def declaracao_funcao(self):
        self.eat("KEYWORD")  
        nome_funcao = self.current_token()[1]
        self.eat("IDENTIFIER")  
        self.eat("DELIMITER")  
        parametros = self.parametros()
        self.eat("DELIMITER")  
        self.eat("DELIMITER")  
        corpo = self.bloco()
        return Funcao(nome_funcao, parametros, corpo)
    
    def declaracao_return(self):
        self.eat("KEYWORD") 
        expressao = self.expressao()  
        return Return(expressao)

    def parametros(self):
        parametros = []
        while self.current_token() and self.current_token()[0] != "DELIMITER" and self.current_token()[1] != ")":
            if self.current_token()[0] == "IDENTIFIER":  
                parametros.append(self.current_token()[1])
                self.eat("IDENTIFIER")
            elif self.current_token()[0] == "NUMBER":  
                parametros.append(self.current_token()[1])
                self.eat("NUMBER")
            
            if self.current_token() and self.current_token()[1] == ",":  
                self.eat("DELIMITER")
        
        return parametros

    def declaracao_if(self):
        self.eat("KEYWORD")  
        condicao = self.condicao()
        self.eat("DELIMITER") 
        bloco = self.bloco()

       
        elifos = []
        while self.current_token() and self.current_token()[0] == "KEYWORD" and self.current_token()[1] == "elif":
            self.eat("KEYWORD") 
            condicao_elif = self.condicao()
            self.eat("DELIMITER")  
            bloco_elif = self.bloco()
            elifos.append({"condicao": condicao_elif, "bloco": bloco_elif})

        
        else_bloco = None
        if self.current_token() and self.current_token()[0] == "KEYWORD" and self.current_token()[1] == "else":
            self.eat("KEYWORD")  
            self.eat("DELIMITER") 
            else_bloco = self.bloco()

       
        return IfElse(condicao, bloco, elifos, else_bloco)


    def declaracao_while(self):
        self.eat("KEYWORD")  
        condicao = self.condicao()
        self.eat("DELIMITER")
        bloco = self.bloco()
        
       
        return While(condicao, bloco)


    def atribuicao(self):
        identificador = self.current_token()[1] 
        self.eat("IDENTIFIER") 
        if self.current_token() and self.current_token()[0] == "DELIMITER" and self.current_token()[1] == "(":
           
            self.eat("DELIMITER")  
            parametros = self.parametros()  
            self.eat("DELIMITER")  
            return ChamadaFuncao(identificador, parametros)
        self.eat("OPERATOR")  
        expressao = self.expressao()
        return Atribuicao(identificador, expressao)

    def condicao(self):
        expressao_esquerda = self.expressao()

        while self.current_token() and (
            (self.current_token()[0] == "OPERATOR" and self.current_token()[1] in ["<", ">", "==", "<=", ">=", "!="]) or
            (self.current_token()[0] == "KEYWORD" and self.current_token()[1] in ["and", "or"])
        ):
            operador = self.current_token()[1]
            if self.current_token()[0] == "OPERATOR":
                self.eat("OPERATOR")  
            elif self.current_token()[0] == "KEYWORD":
                self.eat("KEYWORD")  

            expressao_direita = self.expressao()
            expressao_esquerda = Termo([expressao_esquerda, expressao_direita], operador)

        return expressao_esquerda



    def bloco(self):
        comandos = []
        while self.current_token() and self.current_token()[0] != "KEYWORD":
            comandos.append(self.declaracao())
        return Bloco(comandos)

    def expressao(self):
        termo = self.termo()
        while self.current_token() and self.current_token()[0] == "OPERATOR" and self.current_token()[1] in "+-":
            operador = self.current_token()[1]
            self.eat("OPERATOR")
            termo2 = self.termo()
            termo = Termo([termo, termo2], operador)
        return termo

    def termo(self):
        fator = self.fator()
        while self.current_token() and self.current_token()[0] == "OPERATOR" and self.current_token()[1] in "*/":
            operador = self.current_token()[1]
            self.eat("OPERATOR")
            fator2 = self.fator()
            fator = Termo([fator, fator2], operador)
        return fator

    def fator(self):
        token = self.current_token()
        if token and token[0] == "NUMBER":
            self.eat("NUMBER")
            return Fator(int(token[1]))  
        elif token and token[0] == "IDENTIFIER":
            self.eat("IDENTIFIER")
            
            if self.current_token() and self.current_token()[0] == "DELIMITER" and self.current_token()[1] == "(":
                self.eat("DELIMITER")  
                parametros = self.parametros()
                self.eat("DELIMITER")  
                return FuncaoChamada(token[1], parametros) 
            return Fator(token[1]) 
        elif token and token[0] == "DELIMITER" and token[1] == "(":
            self.eat("DELIMITER") 
            expressao = self.expressao()
            self.eat("DELIMITER")  
            return expressao
        else:
            raise ValueError(f"Fator inválido: {token}")


class IfElse:
    def __init__(self, condicao, bloco_if, elifos=None, bloco_else=None):
        self.condicao = condicao
        self.bloco_if = bloco_if
        self.else_if = elifos if elifos else []
        self.bloco_else = bloco_else

    def __repr__(self):
        return (f"IfElse(condicao={self.condicao}, bloco_if={self.bloco_if}, "
                f"elifs={self.elifs}, bloco_else={self.bloco_else})")
    
class While:
    def __init__(self, condicao, bloco):
        self.condicao = condicao
        self.bloco = bloco

    def __repr__(self):
        return f"While(condicao={self.condicao}, bloco={self.bloco})"

class Programa:
    def __init__(self, declaracoes):
        self.declaracoes = declaracoes

class Declaracao:
    pass

class Atribuicao(Declaracao):
    def __init__(self, identificador, expressao):
        self.identificador = identificador
        self.expressao = expressao

class Condicao:
    def __init__(self, expressao):
        self.expressao = expressao

class Bloco:
    def __init__(self, comandos):
        self.comandos = comandos 
class Expressao:
    pass

class Termo(Expressao):
    def __init__(self, fatores, operador=None):
        self.fatores = fatores 
        self.operador = operador  

class Fator(Expressao):
    def __init__(self, valor):
        self.valor = valor

class Funcao(Declaracao):
    def __init__(self, nome, parametros, corpo):
        self.nome = nome
        self.parametros = parametros
        self.corpo = corpo

class Return(Declaracao):
    def __init__(self, expressao):
        self.expressao = expressao

class FuncaoChamada(Expressao):
    def __init__(self, nome, parametros):
        self.nome = nome
        self.parametros = parametros

class ChamadaFuncao(Declaracao):
    def __init__(self, nome_funcao, parametros):
        self.nome_funcao = nome_funcao
        self.parametros = parametros

class GeradorCodigo:
    def __init__(self, programa):
        self.programa = programa

    def gerar_codigo_js(self):
        return "\n".join([self.gerar_declaracao(declaracao) for declaracao in self.programa.declaracoes])

    def gerar_declaracao(self, declaracao):
        # Tratando dicionários
        if isinstance(declaracao, str):
            return declaracao
        if isinstance(declaracao, dict):
            return self.gerar_dicionario(declaracao)
        
        if isinstance(declaracao, Funcao):
            return self.gerar_funcao(declaracao)
        elif isinstance(declaracao, Atribuicao):
            return self.gerar_atribuicao(declaracao)
        elif isinstance(declaracao, Return):
            return self.gerar_return(declaracao)
        elif isinstance(declaracao, ChamadaFuncao):
            return self.gerar_chamada_funcao(declaracao)
        elif isinstance(declaracao, Bloco): 
            return self.gerar_bloco(declaracao)
        elif isinstance(declaracao, Termo):
            return self.gerar_termo(declaracao)
        elif hasattr(declaracao, 'condicao') and hasattr(declaracao, 'bloco_if'): 
            return self.gerar_if_else(declaracao)
        elif hasattr(declaracao, 'condicao') and hasattr(declaracao, 'bloco'): 
            return self.gerar_while(declaracao)
        else:
            raise ValueError(f"Tipo de declaração desconhecido: {type(declaracao)}")

    def gerar_termo(self, termo):
        fatores_codigo = [self.gerar_fator(fator) for fator in termo.fatores]
        if termo.operador:
            return f"({fatores_codigo[0]} {termo.operador} {fatores_codigo[1]})" 

    def gerar_fator(self, fator):
        if isinstance(fator, Fator):
            if isinstance(fator.valor, int):
                return str(fator.valor)
            else: 
                return fator.valor
        elif isinstance(fator, FuncaoChamada):
            parametros = ", ".join(fator.parametros)
            return f"{fator.nome}({parametros})"
        elif isinstance(fator, Termo):
            return self.gerar_termo(fator)
        else:
            raise ValueError(f"Tipo de fator desconhecido: {type(fator)}")

    def gerar_bloco(self, bloco):
        return "{\n" + "\n".join([self.gerar_declaracao(comando) for comando in bloco.comandos]) + "\n}"

    def gerar_dicionario(self, dicionario):
        return "{ " + ", ".join([f"{k}: {v}" for k, v in dicionario.items()]) + " }"

    def gerar_funcao(self, funcao):
        parametros = ", ".join(funcao.parametros)
        corpo = self.gerar_bloco(funcao.corpo)
        return f"function {funcao.nome}({parametros}) {corpo}"

    def gerar_atribuicao(self, atribuicao):
        return f"{atribuicao.identificador} = {self.gerar_declaracao(atribuicao.expressao)};"

    def gerar_return(self, retorno):
        return f"return {self.gerar_declaracao(retorno.expressao)};"

    def gerar_chamada_funcao(self, chamada):
        parametros = ", ".join([self.gerar_declaracao(param) for param in chamada.parametros])
        return f"{chamada.nome_funcao}({parametros});"

    def gerar_if_else(self, if_else):
        condicao = self.gerar_declaracao(if_else.condicao)
        bloco_if = self.gerar_bloco(if_else.bloco_if)
        else_if = ""
        if if_else.else_if:
            else_if = f" else if ({self.gerar_declaracao(if_else.else_if.condicao)}) {self.gerar_bloco(if_else.else_if.bloco_if)}"
        
        bloco_else = f" else {self.gerar_bloco(if_else.bloco_else)}" if if_else.bloco_else else ""
        return f"if ({condicao}) {bloco_if}{else_if}{bloco_else}"

    def gerar_while(self, while_stmt):
        condicao = self.gerar_declaracao(while_stmt.condicao)
        bloco_while = self.gerar_bloco(while_stmt.bloco)
        return f"while ({condicao}) {bloco_while}"


#Basta escrever o codigo aqui
source_code = """
def funcao(x, y):
    if x >= y and y >= 10:
        return y + 10

while y == 10:


funcao(10, numero)
"""


lexer = Lexer(source_code)
tokens = lexer.tokenize()
print("Tokens:", tokens)


print("\n--------------------\n")
parser = Parser(tokens)
ast = parser.parse()

gerador = GeradorCodigo(ast)
codigo_js = gerador.gerar_codigo_js()
print(codigo_js)

