# Regras reutilizadas pelos schemas, sem consultar o banco de dados.
import re


def validar_nome_cadastro(nome: str) -> str:
    nome_limpo = nome.strip()

    if len(nome_limpo) > 150 or len(nome_limpo) == 0:
        raise ValueError("O nome deve ter entre 1 e 150 caracteres.")

    return nome_limpo


def calcular_digito_cnpj(base: str, pesos: list[int]) -> str:
    soma = 0

    # A Receita usa o código ASCII menos 48 para converter números e letras.
    # Multiplica cada caractere convertido pelo peso correspondente.
    for caractere, peso in zip(base, pesos):
        soma += (ord(caractere) - 48) * peso

    resto = soma % 11

    if resto < 2:
        return "0"

    return str(11 - resto)


def validar_cnpj(cnpj: str | None) -> str | None:
    # CNPJ vazio é tratado como não informado.
    if cnpj is None or len(cnpj.strip()) == 0:
        return None

    cnpj_limpo = cnpj.strip()

    # Evita aceitar letras acentuadas e algarismos de outros alfabetos.
    if not cnpj_limpo.isascii():
        raise ValueError("O CNPJ deve usar apenas letras de A a Z e números de 0 a 9.")

    cnpj_limpo = cnpj_limpo.upper()

    # Confere o formato do CNPJ, com ou sem máscara.
    sem_mascara = re.fullmatch(r"[A-Z0-9]{12}[0-9]{2}", cnpj_limpo)
    com_mascara = re.fullmatch(
        r"[A-Z0-9]{2}\.[A-Z0-9]{3}\.[A-Z0-9]{3}/[A-Z0-9]{4}-[0-9]{2}",
        cnpj_limpo
    )

    if sem_mascara is None and com_mascara is None:
        raise ValueError("Informe um CNPJ com 14 posições e os dois últimos dígitos numéricos.")

    cnpj_limpo = cnpj_limpo.replace(".", "").replace("/", "").replace("-", "")

    if cnpj_limpo == cnpj_limpo[0] * 14:
        raise ValueError("O CNPJ informado é inválido.")

    # A mesma conta atende aos CNPJs numéricos e alfanuméricos.
    # Referência: manual de cálculo do DV publicado pela Receita Federal.
    # https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/documentos-tecnicos/cnpj/manual-dv-cnpj.pdf
    primeiro_digito = calcular_digito_cnpj(
        cnpj_limpo[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    )
    segundo_digito = calcular_digito_cnpj(
        cnpj_limpo[:12] + primeiro_digito, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    )

    if cnpj_limpo[-2:] != primeiro_digito + segundo_digito:
        raise ValueError("Os dígitos verificadores do CNPJ são inválidos.")

    # Salva sempre sem máscara e com letras maiúsculas para comparar duplicados.
    return cnpj_limpo
