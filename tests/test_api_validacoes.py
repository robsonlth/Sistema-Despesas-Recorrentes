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
            "method": metodo, "scheme": "http", "path": caminho,
            "raw_path": caminho.encode(), "root_path": "", "query_string": b"",
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
