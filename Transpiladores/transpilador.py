import re

# Lexer
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

        return {"tipo": "if", "condicao": condicao, "bloco": bloco, "elifos": elifos, "else": else_bloco}

    def declaracao_while(self):
        self.eat("KEYWORD") 
        condicao = self.condicao()
        self.eat("DELIMITER")  
        bloco = self.bloco()
        return {"tipo": "while", "condicao": condicao, "bloco": bloco}

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
       
        esquerda = self.expressao()
        
       
        while self.current_token() and self.current_token()[0] == "OPERATOR" and self.current_token()[1] in ["<", ">", "==", "<=", ">=", "!="]:
            operador = self.current_token()[1]
            self.eat("OPERATOR")  
            direita = self.expressao()
            esquerda = {"tipo": "comparacao", "esquerda": esquerda, "operador": operador, "direita": direita}

        
        while self.current_token() and self.current_token()[0] == "KEYWORD" and self.current_token()[1] in ["and", "or"]:
            operador = self.current_token()[1]
            self.eat("KEYWORD") 
            direita = self.expressao()
            esquerda = {"tipo": "logico", "esquerda": esquerda, "operador": operador, "direita": direita}

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

class Programa:
    def __init__(self, declaracoes):
        self.declaracoes = declaracoes 

    def __str__(self):
        return "\n".join(str(declaracao) for declaracao in self.declaracoes)

class Funcao:
    def __init__(self, nome, parametros, corpo):
        self.nome = nome
        self.parametros = parametros
        self.corpo = corpo

    def __str__(self):
        return f"Função {self.nome}({', '.join(self.parametros)})\n{str(self.corpo)}"

class Return:
    def __init__(self, expressao):
        self.expressao = expressao

    def __str__(self):
        return f"Return {self.expressao}"

class Atribuicao:
    def __init__(self, identificador, expressao):
        self.identificador = identificador
        self.expressao = expressao

    def __str__(self):
        return f"{self.identificador} = {self.expressao}"

class ChamadaFuncao:
    def __init__(self, nome, parametros):
        self.nome = nome
        self.parametros = parametros

    def __str__(self):
        return f"{self.nome}({', '.join(self.parametros)})"

class Termo:
    def __init__(self, fatores, operador=None):
        self.fatores = fatores
        self.operador = operador

    def __str__(self):
        if self.operador:
            return f"({self.fatores[0]} {self.operador} {self.fatores[1]})"
        return str(self.fatores[0])

class Fator:
    def __init__(self, valor):
        self.valor = valor 

    def __le__(self, outro):
        if isinstance(outro, Fator):
            return self.valor <= outro.valor  
        return False  

    def __repr__(self):
        return str(self.valor)

    def __str__(self):
        return str(self.valor)

class FuncaoChamada:
    def __init__(self, nome, parametros):
        self.nome = nome
        self.parametros = parametros

    def __str__(self):
        return f"{self.nome}({', '.join(self.parametros)})"

class Bloco:
    def __init__(self, comandos):
        self.comandos = comandos

    def __str__(self):
        return "\n".join(str(comando) for comando in self.comandos)


class GeradorJavaScript:
    def __init__(self, programa):
        self.programa = programa

    def gerar_codigo(self):
        return "\n".join(self.gerar_declaracao(declaracao) for declaracao in self.programa.declaracoes)

    def gerar_declaracao(self, declaracao):
        if isinstance(declaracao, Funcao):
            return self.gerar_funcao(declaracao)
        elif isinstance(declaracao, Return):
            return f"return {self.gerar_expressao(declaracao.expressao)};"
        elif isinstance(declaracao, Atribuicao):
            return f"{declaracao.identificador} = {self.gerar_expressao(declaracao.expressao)};"
        elif isinstance(declaracao, ChamadaFuncao):
            return f"{declaracao.nome}({', '.join(declaracao.parametros)})"
        elif isinstance(declaracao, dict):
            if declaracao["tipo"] == "if":
                condicao = self.gerar_expressao(declaracao["condicao"])
                bloco = "\n    ".join(self.gerar_declaracao(c) for c in declaracao["bloco"].comandos)
                elifos = "\n    ".join(f"else if ({self.gerar_expressao(elif_item['condicao'])}) {{\n        " + "\n        ".join(self.gerar_declaracao(c) for c in elif_item['bloco'].comandos) + "\n    }}" for elif_item in declaracao["elifos"])
                else_bloco = f"else {{\n    " + "\n    ".join(self.gerar_declaracao(c) for c in declaracao["else"].comandos) + "\n}" if declaracao["else"] else ""
                return f"if ({condicao}) {{\n    {bloco}\n}} {elifos} {else_bloco}"
            elif declaracao["tipo"] == "while":
                condicao = self.gerar_expressao(declaracao["condicao"])
                bloco = "\n    ".join(self.gerar_declaracao(c) for c in declaracao["bloco"].comandos)
                return f"while ({condicao}) {{\n    {bloco}\n}}"
        else:
            return str(declaracao)


    def gerar_funcao(self, funcao):
        parametros = ", ".join(funcao.parametros)
        corpo = "\n    ".join(self.gerar_declaracao(comando) for comando in funcao.corpo.comandos) 
        return f"function {funcao.nome}({parametros}) {{\n    {corpo}\n}}"

    def gerar_expressao(self, expressao):
        if isinstance(expressao, Fator):
            return str(expressao)
        elif isinstance(expressao, Termo):
            if expressao.operador:
                return f"({self.gerar_expressao(expressao.fatores[0])} {expressao.operador} {self.gerar_expressao(expressao.fatores[1])})"
            else:
                return self.gerar_expressao(expressao.fatores[0])
        elif isinstance(expressao, FuncaoChamada):
            return f"{expressao.nome}({', '.join(expressao.parametros)})"
        else:
            raise ValueError(f"Expressão inválida: {expressao}")


    def gerar_termo(self, termo):
        if isinstance(termo.fatores, list):
            return f"({self.gerar_expressao(termo.fatores[0])} {termo.operador} {self.gerar_expressao(termo.fatores[1])})"
        return self.gerar_expressao(termo.fatores)

    def gerar_fator(self, fator):
        return str(fator.valor)

    def gerar_chamada_funcao(self, chamada):
        return f"{chamada.nome}({', '.join(chamada.parametros)})"
    
    def gerar_if(self, declaracao_if):
        condicao = self.gerar_expressao(declaracao_if["condicao"])
        bloco = "\n    ".join(self.gerar_declaracao(comando) for comando in declaracao_if["bloco"].comandos)
        resultado = f"if ({condicao}) {{\n    {bloco}\n}}"

        
        for elifo in declaracao_if["elifos"]:
            condicao_elif = self.gerar_expressao(elifo["condicao"])
            bloco_elif = "\n    ".join(self.gerar_declaracao(comando) for comando in elifo["bloco"].comandos)
            resultado += f"\nelse if ({condicao_elif}) {{\n    {bloco_elif}\n}}"

        
        if declaracao_if["else"]:
            else_bloco = "\n    ".join(self.gerar_declaracao(comando) for comando in declaracao_if["else"].comandos)
            resultado += f"\nelse {{\n    {else_bloco}\n}}"

        return resultado


# Escreva o codigo python aqui
codigo = """
if x <= y:
    x = x+5
elif x >= y:
    x = x-5
else:
    x = y
"""


lexer = Lexer(codigo)
tokens = lexer.tokenize()
parser = Parser(tokens) 
programa = parser.parse()


gerador = GeradorJavaScript(programa)
print(gerador.gerar_codigo())

