# -*- coding: utf-8 -*-

from pln import PLN

# Carrega o módulo de processamento de linguagem natural
print("Carregando módulo de PLN...")
pln = PLN()
print("Módulo carregado.")

c = "s"

while c == "s":
    print("")

    # Input
    descricao = input("Informe a especificação: ")

    # PLN
    pln.analisar(descricao)

    c = input("Analisar outra especificação?")
