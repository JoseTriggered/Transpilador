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
            ("OPERATOR", r'[+\-/*=<>!]+'),  # Incluído suporte para ==, !=, etc.
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
        self.eat("KEYWORD")  # "def"
        nome_funcao = self.current_token()[1]
        self.eat("IDENTIFIER")  # Nome da função
        self.eat("DELIMITER")  # "("
        parametros = self.parametros()
        self.eat("DELIMITER")  # ")"
        self.eat("DELIMITER")  # ":"
        corpo = self.bloco()
        return Funcao(nome_funcao, parametros, corpo)
    
    def declaracao_return(self):
        self.eat("KEYWORD")  # "return"
        expressao = self.expressao()  # Pega a expressão após 'return'
        return Return(expressao)

    def parametros(self):
        parametros = []
        while self.current_token() and self.current_token()[0] != "DELIMITER" and self.current_token()[1] != ")":
            if self.current_token()[0] == "IDENTIFIER":  # Identificador de parâmetro
                parametros.append(self.current_token()[1])
                self.eat("IDENTIFIER")
            elif self.current_token()[0] == "NUMBER":  # Caso em que há um número como parâmetro
                parametros.append(self.current_token()[1])
                self.eat("NUMBER")
            
            if self.current_token() and self.current_token()[1] == ",":  # Se houver vírgula, consome e continua
                self.eat("DELIMITER")
        
        return parametros

    def declaracao_if(self):
        self.eat("KEYWORD")  # "if"
        condicao = self.condicao()
        self.eat("DELIMITER")  # ":"
        bloco = self.bloco()

        elifos = []
        while self.current_token() and self.current_token()[0] == "KEYWORD" and self.current_token()[1] == "elif":
            self.eat("KEYWORD")  # "elif"
            condicao_elif = self.condicao()
            self.eat("DELIMITER")  # ":"
            bloco_elif = self.bloco()
            elifos.append({"condicao": condicao_elif, "bloco": bloco_elif})

        else_bloco = None
        if self.current_token() and self.current_token()[0] == "KEYWORD" and self.current_token()[1] == "else":
            self.eat("KEYWORD")  # "else"
            self.eat("DELIMITER")  # ":"
            else_bloco = self.bloco()

        return {"tipo": "if", "condicao": condicao, "bloco": bloco, "elifos": elifos, "else": else_bloco}

    def declaracao_while(self):
        self.eat("KEYWORD")  # "while"
        condicao = self.condicao()
        self.eat("DELIMITER")  # ":"
        bloco = self.bloco()
        return {"tipo": "while", "condicao": condicao, "bloco": bloco}

    def atribuicao(self):
        identificador = self.current_token()[1]  # Pega o identificador
        self.eat("IDENTIFIER")  # Identificador
        if self.current_token() and self.current_token()[0] == "DELIMITER" and self.current_token()[1] == "(":
            self.eat("DELIMITER")  # "("
            parametros = self.parametros()  # Chamada de função com parâmetros
            self.eat("DELIMITER")  # ")"
            return ChamadaFuncao(identificador, parametros)
        self.eat("OPERATOR")  # "="
        expressao = self.expressao()
        return Atribuicao(identificador, expressao)

    def condicao(self):
        esquerda = self.expressao()
        operador = self.current_token()
        if operador and operador[0] == "OPERATOR" and operador[1] in ["==", "!=", "<", ">", "<=", ">="]:
            self.eat("OPERATOR")  # Come o operador de comparação
            direita = self.expressao()
            return {"esquerda": esquerda, "operador": operador[1], "direita": direita}
        return esquerda

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
            return Fator(int(token[1]))  # Retorna número
        elif token and token[0] == "IDENTIFIER":
            self.eat("IDENTIFIER")
            if self.current_token() and self.current_token()[0] == "DELIMITER" and self.current_token()[1] == "(":
                self.eat("DELIMITER")  # Consumir '('
                parametros = self.parametros()
                self.eat("DELIMITER")  # Consumir ')'
                return FuncaoChamada(token[1], parametros)  # Criar a chamada de função
            return Fator(token[1])  # Retorna identificador
        elif token and token[0] == "DELIMITER" and token[1] == "(":
            self.eat("DELIMITER")  # "("
            expressao = self.expressao()
            self.eat("DELIMITER")  # ")"
            return expressao
        else:
            raise ValueError(f"Fator inválido: {token}")

class Programa:
    def __init__(self, declaracoes):
        self.declaracoes = declaracoes  # Lista de declarações

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
        else:
            return str(declaracao)

    def gerar_funcao(self, funcao):
        parametros = ", ".join(funcao.parametros)
        corpo = "\n    ".join(self.gerar_declaracao(comando) for comando in funcao.corpo.comandos)  # Acessando os comandos do bloco
        return f"function {funcao.nome}({parametros}) {{\n    {corpo}\n}}"

    def gerar_expressao(self, expressao):
        if isinstance(expressao, Fator):
            return str(expressao.valor)
        elif isinstance(expressao, Termo):
            return f"({self.gerar_expressao(expressao.fatores[0])} {expressao.operador} {self.gerar_expressao(expressao.fatores[1])})"
        elif isinstance(expressao, ChamadaFuncao):
            return f"{expressao.nome}({', '.join(expressao.parametros)})"
        else:
            return str(expressao)

# Exemplo de uso
codigo = """
if x == y and y == x: y + 10
"""

# Passo 1: Tokenizar o código
lexer = Lexer(codigo)
tokens = lexer.tokenize()
print("Tokens:", tokens)

# Passo 2: Analisar sintaticamente os tokens
parser = Parser(tokens)
ast = parser.parse()
print("Árvore Sintática:", ast)

