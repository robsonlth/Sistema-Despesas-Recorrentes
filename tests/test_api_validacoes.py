# Testes das rotas com SQLite em memória. O PostgreSQL não é acessado.
import asyncio
import importlib
import json
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


class TestValidacoesAPI(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://", poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )

        @event.listens_for(cls.engine, "connect")
        def ativar_chaves_estrangeiras(conexao, registro):
            conexao.execute("PRAGMA foreign_keys=ON")

        # Usa o banco de teste na criação das tabelas durante a importação da API.
        with patch("sqlalchemy.create_engine", return_value=cls.engine):
            cls.api = importlib.import_module("backend.main")

        cls.sessoes = sessionmaker(bind=cls.engine)

        def banco_de_teste():
            with cls.sessoes() as db:
                yield db

        cls.overrides_anteriores = cls.api.app.dependency_overrides.copy()
        cls.api.app.dependency_overrides[cls.api.get_db] = banco_de_teste

    @classmethod
    def tearDownClass(cls):
        cls.api.app.dependency_overrides = cls.overrides_anteriores
        cls.engine.dispose()

    async def asyncSetUp(self):
        # Cada teste começa com tabelas vazias no banco temporário.
        self.api.Base.metadata.drop_all(self.engine)
        self.api.Base.metadata.create_all(self.engine)

    async def requisitar(self, metodo, caminho, dados=None, status_esperado=200):
        # Envia uma requisição à aplicação e captura a resposta pela interface ASGI.
        # Na requisição HTTP, a rota e os parâmetros da URL ficam separados.
        rota, _, parametros = caminho.partition("?")
        corpo = json.dumps(dados).encode() if dados is not None else b""
        mensagens = []
        recebido = False

        async def receber():
            nonlocal recebido
            if not recebido:
                recebido = True
                return {"type": "http.request", "body": corpo, "more_body": False}
            await asyncio.Event().wait()

        async def enviar(mensagem):
            mensagens.append(mensagem)

        escopo = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": metodo, "scheme": "http", "path": rota,
            "raw_path": rota.encode(), "root_path": "", "query_string": parametros.encode(),
            "headers": [(b"content-type", b"application/json")],
            "client": ("127.0.0.1", 12345), "server": ("teste", 80),
        }
        await self.api.app(escopo, receber, enviar)
        status = next(item["status"] for item in mensagens if item["type"] == "http.response.start")
        conteudo = b"".join(item.get("body", b"") for item in mensagens if item["type"] == "http.response.body")
        resposta = json.loads(conteudo)
        self.assertEqual(status, status_esperado, (metodo, caminho, resposta))
        return resposta

    async def preparar_despesa(self):
        dados = {"descricao": "Aluguel", "data_inicio_vigencia": "2026-09-01"}
        for rota, campo in (
            ("/fornecedores", "fornecedor_id"), ("/departamentos", "departamento_id"),
            ("/naturezas-financeiras", "natureza_financeira_id"), ("/rateios", "rateio_id"),
        ):
            cadastro = await self.requisitar("POST", rota, {"nome": "Cadastro"})
            dados[campo] = cadastro["id"]
        despesa = await self.requisitar("POST", "/despesas-recorrentes", dados)
        return dados, despesa

    async def test_nomes_no_cadastro_e_na_atualizacao(self):
        for rota in ("/fornecedores", "/departamentos", "/naturezas-financeiras", "/rateios"):
            with self.subTest(rota=rota):
                criado = await self.requisitar("POST", rota, {"nome": "  João da Silva  "})
                self.assertEqual(criado["nome"], "João da Silva")
                caminho = f"{rota}/{criado['id']}"
                for nome in ("", " \t ", "A" * 151):
                    await self.requisitar("POST", rota, {"nome": nome}, 422)
                    await self.requisitar("PUT", caminho, {"nome": nome}, 422)
                self.assertEqual(await self.requisitar("GET", caminho), criado)
                atualizado = await self.requisitar("PUT", caminho, {"nome": "  Nome atualizado  "})
                self.assertEqual(atualizado["nome"], "Nome atualizado")

    async def test_cnpj_duplicado_e_atualizacao_do_proprio_cadastro(self):
        primeiro = await self.requisitar("POST", "/fornecedores", {"nome": "Primeiro", "cnpj": "11.222.333/0001-81"})
        self.assertEqual(primeiro["cnpj"], "11222333000181")
        duplicado = await self.requisitar("POST", "/fornecedores", {"nome": "Outro", "cnpj": "11222333000181"}, 409)
        self.assertEqual(duplicado["detail"], "Já existe um fornecedor com esse CNPJ.")
        caminho = f"/fornecedores/{primeiro['id']}"
        await self.requisitar("PUT", caminho, {"nome": "Mesmo fornecedor", "cnpj": "11.222.333/0001-81"})
        segundo = await self.requisitar("POST", "/fornecedores", {"nome": "Segundo", "cnpj": "04252011000110"})
        segundo_caminho = f"/fornecedores/{segundo['id']}"
        await self.requisitar("PUT", segundo_caminho, {"nome": "Não deve mudar", "cnpj": "11222333000181"}, 409)
        self.assertEqual(await self.requisitar("GET", segundo_caminho), segundo)
        await self.requisitar("DELETE", caminho)
        await self.requisitar("POST", "/fornecedores", {"nome": "Outro", "cnpj": "11222333000181"}, 409)

    async def test_cnpj_opcional_alfanumerico_e_invalido(self):
        for cnpj in (None, "", " "):
            criado = await self.requisitar("POST", "/fornecedores", {"nome": "Sem CNPJ", "cnpj": cnpj})
            self.assertIsNone(criado["cnpj"])
        criado = await self.requisitar("POST", "/fornecedores", {"nome": "Alfanumérico", "cnpj": "12.abc.345/01de-35"})
        self.assertEqual(criado["cnpj"], "12ABC34501DE35")
        await self.requisitar("POST", "/fornecedores", {"nome": "Duplicado", "cnpj": "12ABC34501DE35"}, 409)
        for cnpj in ("123", "11222333000180", "00000000000000", "12ABC34501DE36"):
            await self.requisitar("POST", "/fornecedores", {"nome": "Inválido", "cnpj": cnpj}, 422)
            await self.requisitar("PUT", f"/fornecedores/{criado['id']}", {"nome": "Inválido", "cnpj": cnpj}, 422)
        sem_cnpj = await self.requisitar("PUT", f"/fornecedores/{criado['id']}", {"nome": "Sem CNPJ", "cnpj": None})
        self.assertIsNone(sem_cnpj["cnpj"])

    async def test_cnpj_antigo_com_letras_minusculas_nao_pode_ser_duplicado(self):
        with self.sessoes() as db:
            db.add(self.api.models.Fornecedor(nome="Cadastro antigo", cnpj="12abc34501de35"))
            db.commit()
        await self.requisitar("POST", "/fornecedores", {"nome": "Duplicado", "cnpj": "12ABC34501DE35"}, 409)

    async def test_colisao_no_commit_faz_rollback(self):
        existente = await self.requisitar("POST", "/fornecedores", {"nome": "Existente", "cnpj": "11222333000181"})
        segundo = await self.requisitar("POST", "/fornecedores", {"nome": "Segundo"})
        validar_original = self.api.validar_cnpj_unico

        for metodo, caminho in (("POST", "/fornecedores"), ("PUT", f"/fornecedores/{segundo['id']}")):
            chamadas = 0

            def simular_concorrencia(*args, **kwargs):
                nonlocal chamadas
                chamadas += 1
                # Simula a primeira consulta sem encontrar o CNPJ concorrente.
                if chamadas > 1:
                    return validar_original(*args, **kwargs)

            with patch.object(self.api, "validar_cnpj_unico", side_effect=simular_concorrencia):
                with patch.object(Session, "rollback", autospec=True, side_effect=Session.rollback) as rollback:
                    await self.requisitar(metodo, caminho, {"nome": "Conflito", "cnpj": "11222333000181"}, 409)
                    self.assertEqual(rollback.call_count, 1)
            self.assertEqual(chamadas, 2)
        self.assertEqual(await self.requisitar("GET", f"/fornecedores/{existente['id']}"), existente)
        self.assertEqual(await self.requisitar("GET", f"/fornecedores/{segundo['id']}"), segundo)
        self.assertEqual(len(await self.requisitar("GET", "/fornecedores")), 2)

    async def test_outro_erro_de_integridade_nao_vira_cnpj_duplicado(self):
        erro = IntegrityError("comando de teste", {}, Exception("outro erro de integridade"))
        with patch.object(Session, "commit", side_effect=erro):
            with self.assertRaises(IntegrityError) as resultado:
                await self.requisitar("POST", "/fornecedores", {"nome": "Empresa"})
        self.assertIs(resultado.exception, erro)
        self.assertEqual(await self.requisitar("GET", "/fornecedores"), [])

    async def test_despesa_rejeita_dados_invalidos_sem_alterar_registro(self):
        dados, despesa = await self.preparar_despesa()
        caminho = f"/despesas-recorrentes/{despesa['id']}"
        casos = (
            {"descricao": " "}, {"descricao": "A" * 351},
            {"data_fim_vigencia": "2026-08-31"}, {"valor_estimado": "-1"},
            {"valor_estimado": "1.234"}, {"valor_estimado": "100000000"},
            {"valor_estimado": "NaN"}, {"fornecedor_id": 0},
            {"fornecedor_id": True}, {"fornecedor_id": 2147483648},
        )
        for alteracao in casos:
            with self.subTest(alteracao=alteracao):
                await self.requisitar("POST", "/despesas-recorrentes", {**dados, **alteracao}, 422)
                await self.requisitar("PUT", caminho, {**dados, **alteracao}, 422)
        self.assertEqual(await self.requisitar("GET", caminho), despesa)
        atualizado = await self.requisitar("PUT", caminho, {**dados, "valor_estimado": "0", "data_fim_vigencia": "2026-09-01"})
        self.assertEqual(atualizado["data_fim_vigencia"], "2026-09-01")

    async def test_lancamento_rejeita_dados_invalidos_e_atualiza_mes(self):
        _, despesa = await self.preparar_despesa()
        dados = {"despesa_recorrente_id": despesa["id"], "valor_recebido": "100.25", "data_recebimento": "2026-09-20"}
        criado = await self.requisitar("POST", "/lancamentos-despesa", dados)
        caminho = f"/lancamentos-despesa/{criado['id']}"
        self.assertEqual(criado["mes_referencia"], "2026-09-01")
        for alteracao in (
            {"valor_recebido": "-1"}, {"valor_recebido": "1.234"},
            {"valor_recebido": "100000000"}, {"valor_recebido": "Infinity"},
            {"observacao": "A" * 321}, {"data_recebimento": "2026-02-30"},
            {"despesa_recorrente_id": 0}, {"mes_referencia": "2020-01-01"},
        ):
            with self.subTest(alteracao=alteracao):
                await self.requisitar("POST", "/lancamentos-despesa", {**dados, **alteracao}, 422)
                await self.requisitar("PUT", caminho, {**dados, **alteracao}, 422)
        self.assertEqual(await self.requisitar("GET", caminho), criado)
        atualizado = await self.requisitar("PUT", caminho, {**dados, "valor_recebido": "0", "data_recebimento": "2026-10-15", "observacao": "  "})
        self.assertEqual(atualizado["mes_referencia"], "2026-10-01")
        self.assertIsNone(atualizado["observacao"])

    async def test_filtros_de_lancamentos_isolados_e_combinados(self):
        dados, despesa = await self.preparar_despesa()
        outra_despesa = await self.requisitar(
            "POST", "/despesas-recorrentes", {**dados, "descricao": "Energia"}
        )
        ids = []
        # Varia cada filtro para detectar registros que não deveriam ser retornados.
        for despesa_id, recebimento, ativo, pendente in (
            (despesa["id"], "2026-09-01", True, True),
            (despesa["id"], "2026-09-30", True, False),
            (despesa["id"], "2026-09-15", False, True),
            (despesa["id"], "2026-10-01", False, False),
            (outra_despesa["id"], "2026-09-20", True, True),
            (despesa["id"], "2025-09-20", True, True),
        ):
            criado = await self.requisitar("POST", "/lancamentos-despesa", {
                "despesa_recorrente_id": despesa_id,
                "data_recebimento": recebimento,
                "valor_recebido": "100.00",
                "ativo": ativo,
                "nota_pendente": pendente,
            })
            ids.append(criado["id"])

        filtro_despesa = f"despesa_recorrente_id={despesa['id']}"
        casos = (
            ("", ids),
            ("ativo=true", [ids[0], ids[1], ids[4], ids[5]]),
            ("ativo=false", [ids[2], ids[3]]),
            ("nota_pendente=true", [ids[0], ids[2], ids[4], ids[5]]),
            ("nota_pendente=false", [ids[1], ids[3]]),
            ("ativo=true&nota_pendente=true", [ids[0], ids[4], ids[5]]),
            ("ativo=false&nota_pendente=false", [ids[3]]),
            ("mes_referencia=2026-09-01", [ids[0], ids[1], ids[2], ids[4]]),
            ("mes_referencia=2026-09-30", [ids[0], ids[1], ids[2], ids[4]]),
            ("mes_referencia=2026-10-01", [ids[3]]),
            ("mes_referencia=2025-09-01", [ids[5]]),
            (filtro_despesa, [ids[0], ids[1], ids[2], ids[3], ids[5]]),
            (f"despesa_recorrente_id={outra_despesa['id']}", [ids[4]]),
            (f"mes_referencia=2026-09-01&{filtro_despesa}", [ids[0], ids[1], ids[2]]),
            (f"ativo=true&nota_pendente=true&mes_referencia=2026-09-15&{filtro_despesa}", [ids[0]]),
            (f"ativo=false&nota_pendente=false&mes_referencia=2026-10-01&{filtro_despesa}", [ids[3]]),
            ("mes_referencia=2027-01-01", []),
            ("despesa_recorrente_id=2147483647", []),
            ("ativo=true&mes_referencia=2026-10-01", []),
        )
        for parametros, esperados in casos:
            with self.subTest(parametros=parametros):
                caminho = "/lancamentos-despesa"
                if parametros:
                    caminho += f"?{parametros}"
                resposta = await self.requisitar("GET", caminho)
                self.assertCountEqual([item["id"] for item in resposta], esperados)

    async def test_lancamentos_rejeita_filtros_invalidos(self):
        for parametros in (
            "ativo=invalido", "nota_pendente=invalido",
            "mes_referencia=2026-02-30", "mes_referencia=2026-13-01",
            "mes_referencia=texto", "mes_referencia=",
            "despesa_recorrente_id=0", "despesa_recorrente_id=-1",
            "despesa_recorrente_id=2147483648", "despesa_recorrente_id=abc",
            "despesa_recorrente_id=1.5", "despesa_recorrente_id=",
        ):
            with self.subTest(parametros=parametros):
                await self.requisitar("GET", f"/lancamentos-despesa?{parametros}", status_esperado=422)

    async def test_resumo_mensal_soma_por_despesa_e_filtra_lancamentos(self):
        dados, despesa = await self.preparar_despesa()
        outras = []
        for descricao in ("Energia", "Valor zero", "Somente inativos", "Sem lançamentos no mês"):
            outras.append(await self.requisitar(
                "POST", "/despesas-recorrentes", {**dados, "descricao": descricao}
            ))

        # Insere fora da ordem dos IDs e repete valores para conferir soma e ordenação.
        for despesa_id, valor, recebimento, ativo, pendente in (
            (outras[0]["id"], "80.01", "2026-10-15", True, False),
            (despesa["id"], "200.10", "2026-10-01", True, False),
            (despesa["id"], "150.25", "2026-10-31", True, True),
            (despesa["id"], "150.25", "2026-10-20", True, False),
            (despesa["id"], "700.00", "2026-10-15", False, False),
            (despesa["id"], "900.00", "2026-09-30", True, False),
            (despesa["id"], "800.00", "2025-10-15", True, False),
            (outras[1]["id"], "0.00", "2026-10-15", True, False),
            (outras[2]["id"], "600.00", "2026-10-15", False, False),
            (outras[3]["id"], "400.00", "2026-09-15", True, False),
        ):
            await self.requisitar("POST", "/lancamentos-despesa", {
                "despesa_recorrente_id": despesa_id,
                "valor_recebido": valor,
                "data_recebimento": recebimento,
                "ativo": ativo,
                "nota_pendente": pendente,
            })

        caminho = "/lancamentos-despesa/resumo-mensal"
        for dia in ("01", "15", "31"):
            with self.subTest(dia=dia):
                resposta = await self.requisitar("GET", f"{caminho}?mes_referencia=2026-10-{dia}")
                self.assertEqual(resposta, [
                    {"despesa_recorrente_id": despesa["id"], "descricao": "Aluguel",
                     "total_recebido": "500.60", "quantidade_lancamentos": 3},
                    {"despesa_recorrente_id": outras[0]["id"], "descricao": "Energia",
                     "total_recebido": "80.01", "quantidade_lancamentos": 1},
                    {"despesa_recorrente_id": outras[1]["id"], "descricao": "Valor zero",
                     "total_recebido": "0.00", "quantidade_lancamentos": 1},
                    {"despesa_recorrente_id": outras[2]["id"], "descricao": "Somente inativos",
                     "total_recebido": "0.00", "quantidade_lancamentos": 0},
                    {"despesa_recorrente_id": outras[3]["id"], "descricao": "Sem lançamentos no mês",
                     "total_recebido": "0.00", "quantidade_lancamentos": 0},
                ])

        sem_despesas = await self.requisitar("GET", f"{caminho}?mes_referencia=2024-01-01")
        self.assertEqual(sem_despesas, [])

    async def test_resumo_mensal_permite_total_maior_que_limite_individual(self):
        _, despesa = await self.preparar_despesa()
        for _ in range(2):
            await self.requisitar("POST", "/lancamentos-despesa", {
                "despesa_recorrente_id": despesa["id"],
                "valor_recebido": "99999999.99",
                "data_recebimento": "2026-10-15",
            })
        resposta = await self.requisitar(
            "GET", "/lancamentos-despesa/resumo-mensal?mes_referencia=2026-10-01"
        )
        self.assertEqual(resposta, [
            {"despesa_recorrente_id": despesa["id"], "descricao": "Aluguel",
             "total_recebido": "199999999.98", "quantidade_lancamentos": 2}
        ])

    async def test_resumo_mensal_acompanha_inativacao(self):
        _, despesa = await self.preparar_despesa()
        lancamentos = []
        for valor in ("100.00", "50.00"):
            lancamentos.append(await self.requisitar("POST", "/lancamentos-despesa", {
                "despesa_recorrente_id": despesa["id"],
                "valor_recebido": valor,
                "data_recebimento": "2026-10-15",
            }))

        caminho = "/lancamentos-despesa/resumo-mensal?mes_referencia=2026-10-01"
        self.assertEqual(await self.requisitar("GET", caminho), [
            {"despesa_recorrente_id": despesa["id"], "descricao": "Aluguel",
             "total_recebido": "150.00", "quantidade_lancamentos": 2}
        ])
        await self.requisitar("DELETE", f"/lancamentos-despesa/{lancamentos[1]['id']}")
        self.assertEqual(await self.requisitar("GET", caminho), [
            {"despesa_recorrente_id": despesa["id"], "descricao": "Aluguel",
             "total_recebido": "100.00", "quantidade_lancamentos": 1}
        ])
        await self.requisitar("DELETE", f"/lancamentos-despesa/{lancamentos[0]['id']}")
        self.assertEqual(await self.requisitar("GET", caminho), [
            {"despesa_recorrente_id": despesa["id"], "descricao": "Aluguel",
             "total_recebido": "0.00", "quantidade_lancamentos": 0}
        ])

    async def test_resumo_mensal_considera_vigencia_e_situacao_das_previstas(self):
        caminho = "/lancamentos-despesa/resumo-mensal?mes_referencia=2026-10-15"
        self.assertEqual(await self.requisitar("GET", caminho), [])
        dados, despesa = await self.preparar_despesa()
        esperadas = [despesa["id"]]
        for descricao, inicio, fim, ativo, prevista in (
            ("Termina no primeiro dia", "2026-01-01", "2026-10-01", True, True),
            ("Começa no último dia", "2026-10-31", None, True, True),
            ("Vigora no meio do mês", "2026-10-10", "2026-10-20", True, True),
            ("Terminou antes", "2026-01-01", "2026-09-30", True, False),
            ("Começa depois", "2026-11-01", None, True, False),
            ("Inativa sem lançamentos", "2026-01-01", None, False, False),
        ):
            criada = await self.requisitar("POST", "/despesas-recorrentes", {
                **dados, "descricao": descricao, "data_inicio_vigencia": inicio,
                "data_fim_vigencia": fim, "ativo": ativo,
            })
            if prevista:
                esperadas.append(criada["id"])

        resposta = await self.requisitar("GET", caminho)
        self.assertEqual([item["despesa_recorrente_id"] for item in resposta], esperadas)
        for item in resposta:
            self.assertEqual(item["total_recebido"], "0.00")
            self.assertEqual(item["quantidade_lancamentos"], 0)

    async def test_resumo_mensal_preserva_lancamentos_fora_da_previsao(self):
        dados, despesa = await self.preparar_despesa()
        despesas = [despesa]
        for descricao, inicio, fim in (
            ("Vigência futura", "2026-11-01", None),
            ("Vigência encerrada", "2026-01-01", "2026-09-30"),
        ):
            despesas.append(await self.requisitar("POST", "/despesas-recorrentes", {
                **dados, "descricao": descricao, "data_inicio_vigencia": inicio,
                "data_fim_vigencia": fim,
            }))

        for item in despesas:
            await self.requisitar("POST", "/lancamentos-despesa", {
                "despesa_recorrente_id": item["id"],
                "valor_recebido": "25.50", "data_recebimento": "2026-10-15",
            })
        # Inativar a despesa depois do lançamento não deve esconder seu valor.
        await self.requisitar("DELETE", f"/despesas-recorrentes/{despesa['id']}")
        resposta = await self.requisitar(
            "GET", "/lancamentos-despesa/resumo-mensal?mes_referencia=2026-10-01"
        )
        self.assertEqual(
            [item["despesa_recorrente_id"] for item in resposta],
            [item["id"] for item in despesas]
        )
        for item in resposta:
            self.assertEqual(item["total_recebido"], "25.50")
            self.assertEqual(item["quantidade_lancamentos"], 1)

    async def test_resumo_mensal_respeita_fim_de_fevereiro_e_dezembro(self):
        dados, despesa = await self.preparar_despesa()
        await self.requisitar("DELETE", f"/despesas-recorrentes/{despesa['id']}")
        for mes, ultimo_dia, dia_seguinte in (
            ("2024-02-01", "2024-02-29", "2024-03-01"),
            ("2025-02-01", "2025-02-28", "2025-03-01"),
            ("2026-12-01", "2026-12-31", "2027-01-01"),
        ):
            with self.subTest(mes=mes):
                prevista = await self.requisitar("POST", "/despesas-recorrentes", {
                    **dados, "data_inicio_vigencia": ultimo_dia,
                    "data_fim_vigencia": ultimo_dia,
                })
                await self.requisitar("POST", "/despesas-recorrentes", {
                    **dados, "data_inicio_vigencia": dia_seguinte,
                    "data_fim_vigencia": dia_seguinte,
                })
                resposta = await self.requisitar(
                    "GET", f"/lancamentos-despesa/resumo-mensal?mes_referencia={mes}"
                )
                self.assertEqual(resposta, [
                    {"despesa_recorrente_id": prevista["id"], "descricao": "Aluguel",
                     "total_recebido": "0.00", "quantidade_lancamentos": 0}
                ])

    async def test_resumo_mensal_exige_mes_valido(self):
        caminho = "/lancamentos-despesa/resumo-mensal"
        await self.requisitar("GET", caminho, status_esperado=422)
        for mes in ("", "texto", "2026-02-30", "2026-13-01", "2026-10-32"):
            with self.subTest(mes=mes):
                await self.requisitar(
                    "GET", f"{caminho}?mes_referencia={mes}", status_esperado=422
                )

    async def test_relacionamentos_inexistentes(self):
        dados, despesa = await self.preparar_despesa()
        for campo in ("fornecedor_id", "departamento_id", "natureza_financeira_id", "rateio_id"):
            invalido = {**dados, campo: 999999}
            await self.requisitar("POST", "/despesas-recorrentes", invalido, 404)
            await self.requisitar("PUT", f"/despesas-recorrentes/{despesa['id']}", invalido, 404)
        lancamento = {"despesa_recorrente_id": despesa["id"], "valor_recebido": "10", "data_recebimento": "2026-09-20"}
        criado = await self.requisitar("POST", "/lancamentos-despesa", lancamento)
        invalido = {**lancamento, "despesa_recorrente_id": 999999}
        await self.requisitar("POST", "/lancamentos-despesa", invalido, 404)
        await self.requisitar("PUT", f"/lancamentos-despesa/{criado['id']}", invalido, 404)

    async def test_ids_invalidos_nas_urls(self):
        dados, despesa = await self.preparar_despesa()
        recursos = [
            (rota, {"nome": "Cadastro"})
            for rota in ("/fornecedores", "/departamentos", "/naturezas-financeiras", "/rateios")
        ] + [
            ("/despesas-recorrentes", dados),
            ("/lancamentos-despesa", {"despesa_recorrente_id": despesa["id"], "valor_recebido": "10", "data_recebimento": "2026-09-20"}),
        ]
        for rota, corpo in recursos:
            for metodo in ("GET", "PUT", "DELETE"):
                for identificador in ("0", "-1", "2147483648", "abc"):
                    with self.subTest(rota=rota, metodo=metodo, id=identificador):
                        await self.requisitar(metodo, f"{rota}/{identificador}", corpo if metodo == "PUT" else None, 422)
                await self.requisitar(metodo, f"{rota}/999999", corpo if metodo == "PUT" else None, 404)

    async def test_leitura_e_inativacao_de_cadastro_antigo(self):
        with self.sessoes() as db:
            antigo = self.api.models.Fornecedor(nome=" ", cnpj="123")
            db.add(antigo)
            db.commit()
            identificador = antigo.id
        caminho = f"/fornecedores/{identificador}"
        lido = await self.requisitar("GET", caminho)
        self.assertEqual(lido["cnpj"], "123")
        inativo = await self.requisitar("DELETE", caminho)
        self.assertFalse(inativo["ativo"])
        self.assertEqual(await self.requisitar("DELETE", caminho), inativo)
        self.assertIn(inativo, await self.requisitar("GET", "/fornecedores"))


if __name__ == "__main__":
    unittest.main()
