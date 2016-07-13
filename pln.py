# -*- coding: utf-8 -*-

# Cadete: Processamento de linguagem natural
#
# Author: Luís Augusto Weber Mercado <lawmercado@inf.ufrgs.br>
#

"""
Módulo de processamento de linguagem natural (PLN)

"""

from singleton import Singleton
from spacy.en import English

TIPO_SENTENCA_DECLARATIVA = 0
TIPO_SENTENCA_CONDICIONAL = 1

RELACOES_OBJETO = ("dobj", "iobj", "dative")
RELACOES_OBJETO_DIRETO = ("dobj",)
RELACOES_OBJETO_INDIRETO = ("iobj", "dative") 

class PLN(metaclass = Singleton):
    """
    Implementa os métodos utilizados para análise de sentenças
     
    """

    def __init__(self):
        self.api = English(entity = False, matcher = False) # Não usa-se todos os recursos
        self.analise = None

    def analisar(self, texto):
        """
        A partir de uma frase, dá início a pipeline de análise

        :param texto: Texto a ser analisado
        :type texto: string
        """

        assert isinstance(texto, str), "O argumento da função 'analisar' deve ser um texto!"

        # Faz a análise sintática da frase
        doc = self.api(texto)

        # Normaliza a análise sintática feita pela api
        sentencas = self.__normalizarAnaliseSintatica(doc)
        
        for sentenca in sentencas:
            sentenca.tipo = self.__obterTipoDaSentenca(sentenca)
            
            if sentenca.tipo == TIPO_SENTENCA_DECLARATIVA:
                svos = self.__extrairSVOs(sentenca)
                sentenca.svos = svos
            
        self.mostrarAnaliseSintatica(sentencas)

    def __normalizarAnaliseSintatica(self, doc):
        """
        Normaliza a análise feita pela api para objetos manejáveis pelos outros
        processos da aplicação

        :param doc: Análise provinda da API
        :type doc: object

        :return: Sentencas com suas devidas informações
        :rtype: list
        """

        sentencas = []
        
        for frase in doc.sents:
            tokens = []
            indice = 0
            
            for palavra in frase:
                # Para desconsiderar a pontuação:
                # if not palavra.is_punct:
                token = Token(palavra.lower_)
                token.indice = indice
                token.pos = palavra.pos_
                token.tag = palavra.tag_
                token.lemma = palavra.lemma_
                token.dependencia = self.__obterDependenciasDoToken(frase, palavra)
                
                tokens.append(token)
                
                indice += 1

            sentencas.append(Sentenca(tokens))

        return sentencas

    def __obterTipoDaSentenca(self, sentenca):
        """
        A partir do token, obtém a relação de dependência com o pai

        :param sentenca: Sentença a ser analisada
        :type sentenca: object
    
        :return: Tipo da sentença
        :rtype: integer
        """
        
        # Verifica se é uma sentença condicional, procurando por palavras chave da mesma
        if sentenca.tokens[0].pos == "ADP":
            if sentenca.tokens[0].texto == "if" or sentenca.tokens[1].texto == "case":
                return TIPO_SENTENCA_CONDICIONAL
        
        return TIPO_SENTENCA_DECLARATIVA

    def __obterDependenciasDoToken(self, sentenca, token):
        """
        A partir do token, obtém a relação de dependência com o pai

        :param sentenca: Sentença a ser analisada
        :type sentenca: object
        :param token: Token a ser analisado
        :type token: object

        :return: Tupla com a relação mais próxima ('<relação com o pai>', <indice do pai>)
        :rtype: tuple
        """

        dependencia = None
        tokens = list(sentenca)
        
        # Na spacy, a raiz tem seu pai (head) como ela mesma
        if token.head is not token:
            iPai = tokens.index(token.head)
            dependencia = (token.dep_, iPai)

        return dependencia

    def __extrairSVOs(self, sentenca):
        """
        Extrai as estruturas Sujeito Verbo Objeto da sentença
        
        :param sentenca: Sentença sendo analisada
        :type sentenca: Sentenca
        
        :return: Lista com os sujeitos da sentença
        :rtype: list
        """
        svos = []
            
        sujeitos = self.__extrairSujeitos(sentenca)
        
        for sujeito in sujeitos:
            svo = SVO(sujeito)
            svo.verbo = self.__obterVerboRelacionadoAoSujeito(sentenca, sujeito)
            svo.objetoDireto = self.__obterObjetosRelacionadosAoVerbo(sentenca, svo.verbo, RELACOES_OBJETO_DIRETO)
            svo.objetoIndireto = self.__obterObjetosRelacionadosAoVerbo(sentenca, svo.verbo, RELACOES_OBJETO_INDIRETO)
            
            svos.append(svo)
            
        return svos
    
    def __extrairSujeitos(self, sentenca):
        """
        Extrai os sujeitos de uma dada sentença
        
        :param sentenca: Sentença sendo analisada
        :type sentenca: Sentenca
        
        :return: Lista com os sujeitos da sentença
        :rtype: list
        """
        
        sujeitos = []
        
        nsubjs = [token for token in sentenca.tokens if token.dependencia is not None and token.dependencia[0].startswith("nsubj")]
            
        for token in nsubjs:
            descendentes = self.__obterDescendentes(sentenca, token)
            
            tokens = [token] + descendentes
            
            trecho = Trecho(tokens)
            trecho.ordenar()
            
            sujeitos.append(trecho)
            
        return sujeitos

    def __obterDescendentes(self, sentenca, raiz):
        """
        Obtém os descendentes de um Token na árvore sintática
        
        :param sentenca: Sentença sendo analisada
        :type sentenca: Sentenca
        :param raiz: Token a ter seus descendentes obtidos
        :type raiz: Token
        
        :return: Lista com os descendentes
        :rtype: list
        """
        descendentes = []
    
        for token in sentenca.tokens:
            if token.dependencia is not None:
                if token.dependencia[1] == raiz.indice:
                    descendentes.append(token)
                    descendentes = descendentes + self.__obterDescendentes(sentenca, token)
                    
        return descendentes

    def __obterVerboRelacionadoAoSujeito(self, sentenca, sujeito):
        """
        Procura o verbo mais próximo relacionado ao sujeito na árvore de sintaxe
        
        :param sentenca: Sentença sendo analisada
        :type sentenca: Sentenca
        :param sujeito: Sujeito a ser relacionado a um verbo
        :type sujeito: Trecho
        
        :return: Verbo relacionado ao sujeito
        :rtype: Trecho
        """
        
        tokenChave = None
        
        # Busca entre o token relacionado diretamente ao verbo
        for token in sujeito.tokens:
            if token.dependencia is not None:
                if token.dependencia[0].startswith("nsubj"):
                    tokenChave = token
                    break
        
        verbo = self.__buscarAscendenteComPOSEspecifico(sentenca, tokenChave, "VERB")
        
        if verbo is not None:
            trecho = [verbo]
            trecho = trecho + self.__obterComplementaresDoVerbo(sentenca, verbo)
            
            return Trecho(trecho)
        
        else:
            return None
    
    def __buscarAscendenteComPOSEspecifico(self, sentenca, folha, pos):
        """
        Navega 'subindo' na árvore de sintaxe da sentença, procurando pelo item
        com dada POS (Part-of-speech tag)
        
        :param sentenca: Sentença sendo analisada
        :type sentenca: Sentenca
        :param folha: Token a partir de onde deve-se "subir" na árvore
        :type folha: Token
        
        :return: Token relacionado a folha com a pos especificada, None se não houver nenhum
        :rtype: Token ou None
        """
        
        if folha.dependencia is not None:
            if sentenca.tokens[folha.dependencia[1]].pos == pos:
                return sentenca.tokens[folha.dependencia[1]]
            else:
                return self.__buscarAscendenteComPOSEspecifico(sentenca, sentenca.tokens[folha.dependencia[1]], pos)
        
        else:
            return None
    
    def __obterComplementaresDoVerbo(self, sentenca, raiz):
        """
        Obtém os complementos do verbo, desconsiderando objetos diretos e indiretos.
        
        :param sentenca: Sentença sendo analisada
        :type sentenca: Sentenca
        :param raiz: Token a ter seus descendentes obtidos
        :type raiz: Token
        
        :return: Lista com os complementares
        :rtype: list
        """
        
        complementares = []
    
        for i in range(raiz.indice, len(sentenca.tokens) - 1):
            token = sentenca.tokens[i]
            
            if token.dependencia is not None:
                if token.dependencia[1] == raiz.indice and (token.dependencia[0] not in RELACOES_OBJETO):
                    complementares.append(token)
                    complementares = complementares + self.__obterComplementaresDoVerbo(sentenca, token)
                    
        return complementares
    
    def __obterDescendentesDaDireita(self, sentenca, raiz):
        """
        Obtém os descendentes à direita de um Token na árvore sintática
        
        :param sentenca: Sentença sendo analisada
        :type sentenca: Sentenca
        :param raiz: Token a ter seus descendentes obtidos
        :type raiz: Token
        
        :return: Lista com os descendentes
        :rtype: list
        """
        descendentes = []
    
        for i in range(raiz.indice, len(sentenca.tokens)):
            token = sentenca.tokens[i]
            
            if token.dependencia is not None and token.pos != "PUNCT":
                if token.dependencia[1] == raiz.indice:
                    descendentes.append(token)
                    descendentes = descendentes + self.__obterDescendentes(sentenca, token)
                    
        return descendentes
    
    def __obterObjetosRelacionadosAoVerbo(self, sentenca, verbo, relacoes = RELACOES_OBJETO):
        """
        Procura o objeto (se houver) relacionado ao dado verbo
        
        :param sentenca: Sentença sendo analisada
        :type sentenca: Sentenca
        :param verbo: Verbo a ter um objeto relacionado
        :type verbo: Trecho
        :param relacoes: Relações de depêndencias a considerar como objeto
        :type relacoes: tuple
        
        :return: Objeto relacionado ao sujeito
        :rtype: Trecho
        """
        
        tokenChave = None
        
        # Busca entre o verbo principal na frase verbal
        for token in verbo.tokens:
                if token.pos == "VERB":
                    tokenChave = token
                    break
        
        descendentes = self.__obterDescendentesDaDireita(sentenca, tokenChave)
        
        objetos = [token for token in descendentes if token.dependencia is not None and (token.dependencia[0] in relacoes)]
                
        if len(objetos) > 0:
            complementares = []
            
            for objeto in objetos:
                complementares = complementares + self.__obterDescendentes(sentenca, objeto)
                
            objetos = objetos + complementares
        
            trecho = Trecho(objetos)
            trecho.ordenar()
            
            return trecho
        else:
            return None
    
    def mostrarAnaliseSintatica(self, sentencas):
        """
        Mostra a análise sintática de uma maneira estruturada

        :param sentencas: Sentenças analisadas
        :type sentencas: list
        """

        for sentenca in sentencas:
            print("Sentença: '" + str(sentenca) + "'")
            print("--Tipo: " + ("Declarativa" if sentenca.tipo == TIPO_SENTENCA_DECLARATIVA else "Condicional"))

            print("")

            for token in sentenca.tokens:
                print("--Token " + str(token.indice))
                print("----Texto: " + str(token.texto))
                print("----POS: " + str(token.pos))
                print("----Tag: " + str(token.tag))
                print("----Lemma: " + str(token.lemma))
                print("----Dependência: " + str(token.dependencia))
                print("")

            for contador, svo in enumerate(sentenca.svos):
                print("--SVO " + str(contador + 1))
                print("----Sujeito: " + str(svo.sujeito))
                print("----Verbo: " + str(svo.verbo))
                print("----Objeto direto: " + str(svo.objetoDireto))
                print("----Objeto indireto: " + str(svo.objetoIndireto))
                print("")

class Trecho:
    """
    Representa sequencia de tokens
    
    """
    
    def __init__(self, tokens):
        self.tokens = tokens
        
    def __str__(self):
        texto = ""
        
        for token in self.tokens:
            texto = (texto[:-1] if token.pos == "PUNCT" else texto) + token.texto + " ";
        
        # Para remover o espaço desnecessário do texto
        texto = texto[:-1]
        
        return texto
    
    def ordenar(self):
        self.tokens = sorted(self.tokens, key = lambda x: x.indice)
        
class Sentenca(Trecho):
    """
    Representa uma sentença e sua análise

    """
    
    def __init__(self, tokens):
        # Inicializa a classe pai
        super().__init__(tokens)
        
        self.tipo = None
        self.svos = []
        self.svcs = []
        
class Token:
    """
    Representa um token (item de uma sentença) e sua análise

    """

    def __init__(self, texto):
        self.texto = texto
        self.indice = None
        self.pos = None
        self.tag = None
        self.lemma = None
        self.dependencia = None
        
    def __str__(self):
        return self.texto
    
class SVO:
    """
    Representa uma análise do tipo Sujeito Verbo Objeto

    """

    def __init__(self, sujeito, verbo = None, objetoDireto = None, objetoIndireto = None):
        self.sujeito = sujeito
        self.verbo = verbo
        self.objetoDireto = objetoDireto
        self.objetoIndireto = objetoIndireto
        
    def __str__(self):
        texto = "Sujeito: " + str(self.sujeito) + "\n"
        texto += "Verbo: " + str(self.verbo) + "\n"
        texto += "Objeto (direto): " + str(self.objetoDireto) + "\n"
        texto += "Objeto (indireto): " + str(self.objetoIndireto) + "\n"
        
        return texto
