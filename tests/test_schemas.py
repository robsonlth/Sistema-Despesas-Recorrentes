# Testes das regras de validação dos schemas.
import unittest
from decimal import Decimal

from pydantic import ValidationError

from backend import schemas


def dados_despesa():
    return {
        "fornecedor_id": 1,
        "departamento_id": 1,
        "natureza_financeira_id": 1,
        "rateio_id": 1,
        "descricao": "Aluguel",
        "data_inicio_vigencia": "2026-09-01",
    }


def dados_lancamento():
    return {
        "despesa_recorrente_id": 1,
        "valor_recebido": "100.25",
        "data_recebimento": "2026-09-20",
    }


class TestValidacoesSchemas(unittest.TestCase):
    def test_nomes_validos_e_limites(self):
        for schema in (
            schemas.FornecedorCreate, schemas.DepartamentoCreate,
            schemas.NaturezaFinanceiraCreate, schemas.RateioCreate
        ):
            for nome in ("A", "A" * 150, "  João da Silva  "):
                with self.subTest(schema=schema.__name__, nome=nome):
                    self.assertEqual(schema(nome=nome).nome, nome.strip())

    def test_nomes_invalidos(self):
        for schema in (
            schemas.FornecedorCreate, schemas.DepartamentoCreate,
            schemas.NaturezaFinanceiraCreate, schemas.RateioCreate
        ):
            for nome in ("", " \t\n ", "A" * 151, None, 123, True):
                with self.subTest(schema=schema.__name__, nome=nome):
                    with self.assertRaises(ValidationError):
                        schema(nome=nome)

    def test_cnpj_valido_e_normalizado(self):
        # O exemplo alfanumérico e seu DV vêm do manual da Receita Federal.
        casos = {
            "11.222.333/0001-81": "11222333000181",
            "04252011000110": "04252011000110",
            "00.000.000/0001-91": "00000000000191",
            "12.ABC.345/01DE-35": "12ABC34501DE35",
            "  12abc34501de35  ": "12ABC34501DE35",
        }
        for entrada, esperado in casos.items():
            with self.subTest(cnpj=entrada):
                resultado = schemas.FornecedorCreate(nome="Empresa", cnpj=entrada)
                self.assertEqual(resultado.cnpj, esperado)

    def test_cnpj_opcional(self):
        for cnpj in (None, "", "  "):
            with self.subTest(cnpj=cnpj):
                self.assertIsNone(schemas.FornecedorCreate(nome="Empresa", cnpj=cnpj).cnpj)
        self.assertIsNone(schemas.FornecedorCreate(nome="Empresa").cnpj)

    def test_cnpj_invalido(self):
        for cnpj in (
            "123", "11222333000180", "12ABC34501DE36", "00000000000000",
            "11111111111111", "1122233300018A", "11/222/333/0001/81",
            "11.222.333/0001-81!", "11222333 000181", "Á2ABC34501DE35",
            "１２２２３３３０００１８１", 11222333000181, True,
        ):
            with self.subTest(cnpj=cnpj):
                with self.assertRaises(ValidationError):
                    schemas.FornecedorCreate(nome="Empresa", cnpj=cnpj)

    def test_descricao(self):
        for descricao in ("A", "A" * 350, "  Energia elétrica  "):
            with self.subTest(descricao=descricao):
                resultado = schemas.DespesaRecorrenteCreate(**{**dados_despesa(), "descricao": descricao})
                self.assertEqual(resultado.descricao, descricao.strip())
        for descricao in ("", "  ", "A" * 351, None):
            with self.subTest(descricao=descricao):
                with self.assertRaises(ValidationError):
                    schemas.DespesaRecorrenteCreate(**{**dados_despesa(), "descricao": descricao})

    def test_vigencia(self):
        for fim in (None, "2026-09-01", "2026-12-31"):
            with self.subTest(fim=fim):
                schemas.DespesaRecorrenteCreate(**{**dados_despesa(), "data_fim_vigencia": fim})
        for fim in ("2026-08-31", "2026-02-30", "data inválida"):
            with self.subTest(fim=fim):
                with self.assertRaises(ValidationError):
                    schemas.DespesaRecorrenteCreate(**{**dados_despesa(), "data_fim_vigencia": fim})

    def test_valores_validos(self):
        for schema, campo, dados in (
            (schemas.DespesaRecorrenteCreate, "valor_estimado", dados_despesa()),
            (schemas.LancamentoDespesaCreate, "valor_recebido", dados_lancamento()),
        ):
            for valor in ("0", "0.01", "150.25", "99999999.99", "1.2300"):
                with self.subTest(schema=schema.__name__, valor=valor):
                    resultado = schema(**{**dados, campo: valor})
                    self.assertEqual(getattr(resultado, campo), Decimal(valor))
        self.assertIsNone(schemas.DespesaRecorrenteCreate(**dados_despesa()).valor_estimado)

    def test_valores_invalidos(self):
        for schema, campo, dados in (
            (schemas.DespesaRecorrenteCreate, "valor_estimado", dados_despesa()),
            (schemas.LancamentoDespesaCreate, "valor_recebido", dados_lancamento()),
        ):
            for valor in ("-0.01", "1.234", "100000000", "1e100", "NaN", "Infinity", "-Infinity", "texto", True):
                with self.subTest(schema=schema.__name__, valor=valor):
                    with self.assertRaises(ValidationError):
                        schema(**{**dados, campo: valor})
        with self.assertRaises(ValidationError):
            schemas.LancamentoDespesaCreate(**{**dados_lancamento(), "valor_recebido": None})

    def test_ids_dos_relacionamentos(self):
        for schema, dados, campos in (
            (schemas.DespesaRecorrenteCreate, dados_despesa(), ("fornecedor_id", "departamento_id", "natureza_financeira_id", "rateio_id")),
            (schemas.LancamentoDespesaCreate, dados_lancamento(), ("despesa_recorrente_id",)),
        ):
            for campo in campos:
                for valor in (0, -1, 2147483648, True, "1", 1.5):
                    with self.subTest(schema=schema.__name__, campo=campo, valor=valor):
                        with self.assertRaises(ValidationError):
                            schema(**{**dados, campo: valor})
                resultado = schema(**{**dados, campo: 2147483647})
                self.assertEqual(getattr(resultado, campo), 2147483647)

    def test_observacao(self):
        for entrada, esperado in ((None, None), ("  ", None), ("  Nota pendente  ", "Nota pendente"), ("A" * 320, "A" * 320)):
            with self.subTest(observacao=entrada):
                resultado = schemas.LancamentoDespesaCreate(**{**dados_lancamento(), "observacao": entrada})
                self.assertEqual(resultado.observacao, esperado)
        with self.assertRaises(ValidationError):
            schemas.LancamentoDespesaCreate(**{**dados_lancamento(), "observacao": "A" * 321})

    def test_campos_desconhecidos(self):
        for schema, dados in (
            (schemas.FornecedorCreate, {"nome": "Empresa"}),
            (schemas.DepartamentoCreate, {"nome": "Financeiro"}),
            (schemas.NaturezaFinanceiraCreate, {"nome": "Energia"}),
            (schemas.RateioCreate, {"nome": "Administrativo"}),
            (schemas.DespesaRecorrenteCreate, dados_despesa()),
            (schemas.LancamentoDespesaCreate, dados_lancamento()),
        ):
            with self.subTest(schema=schema.__name__):
                with self.assertRaises(ValidationError):
                    schema(**{**dados, "campo_digitado_errado": "teste"})
        with self.assertRaises(ValidationError):
            schemas.LancamentoDespesaCreate(**{**dados_lancamento(), "mes_referencia": "2020-01-01"})

    def test_resposta_permite_consultar_dados_antigos(self):
        # Confere a leitura de registros anteriores às regras de validação.
        resultado = schemas.FornecedorResponse(id=1, nome=" ", cnpj="123")
        self.assertEqual(resultado.cnpj, "123")
        resultado = schemas.DespesaRecorrenteResponse(**{
            **dados_despesa(), "id": 1, "valor_estimado": "-10", "data_fim_vigencia": "2020-01-01"
        })
        self.assertEqual(resultado.valor_estimado, Decimal("-10"))


if __name__ == "__main__":
    unittest.main()
