"""Implementação dos algoritmos de criação de IDs para entidades principais.

Este módulo implementa os algoritmos complexos de criação de IDs para:
- Alunos (STD_): baseado em iniciais + CEP + celular + curso
- Funcionários (EMP_): baseado em iniciais + CEP + telefone + cargo
- Parceiros (PTN_): baseado em iniciais + CNPJ + categoria

Todos os IDs têm exatamente 15 caracteres seguindo padrões específicos.
"""

import re

from src.models.partner import PartnerCategory


class IDGenerators:
    """Classe para geração de IDs únicos das entidades principais."""

    # Preposições e artigos a serem ignorados na extração de iniciais
    PREPOSITIONS = {"da", "de", "do", "dos", "das", "e", "&", "and"}

    # Mapeamento de cargos para códigos
    CARGO_CODES = {
        "ADM. PEDAGÓGICO": "AP",
        "CDA": "CDA",
        "PROFESSORA": "PR",
        "PROFESSOR": "PR",
        "CONSULTOR COMERCIAL": "CC",
        "ADM. FINANCEIRO": "AF",
        "COORD. PEDAGÓGICA": "CP",
    }

    # Mapeamento de cursos para códigos
    CURSO_CODES = {
        "KIDS 1": "K1",
        "KIDS 2": "K2",
        "KIDS 3": "K3",
        "SEEDS 1": "S1",
        "SEEDS 2": "S2",
        "SEEDS 3": "S3",
        "TEENS 1": "T1",
        "TEENS 2": "T2",
        "TEENS 3": "T3",
        "TWEENS 1": "TW1",
        "TWEENS 2": "TW2",
        "TWEENS 3": "TW3",
        "KEEP_TALKING 1": "KT1",
        "KEEP_TALKING 2": "KT2",
        "KEEP_TALKING 3": "KT3",
        "ADVANCED 1": "A1",
        "ADVANCED 2": "A2",
        "KINDER": "KD",
    }

    # Mapeamento de categorias de parceiros para códigos
    CATEGORY_CODES = {
        PartnerCategory.ALIMENTACAO: "ALM",
        PartnerCategory.EDUCACAO: "EDU",
        PartnerCategory.SAUDE_BEM_ESTAR: "SAU",
        PartnerCategory.ENTRETENIMENTO: "ENT",
        PartnerCategory.TECNOLOGIA: "TEC",
        PartnerCategory.MODA: "MOD",
        PartnerCategory.ESPORTE: "ESP",
        PartnerCategory.OUTROS: "OUT",
        PartnerCategory.AUTOMOTIVO: "AUT",
        PartnerCategory.VAREJO: "VAR",
        PartnerCategory.SERVICOS: "SRV",
        PartnerCategory.PAPELARIA: "PAP",
        PartnerCategory.TURISMO_VIAGEM: "TVG",
    }

    # Mapeamento de tipos de benefícios para códigos
    TIPO_BENEFICIO_CODES = {
        "DESCONTO": "DC",
        "FRETE GRÁTIS": "FG",
        "FRETE GRATIS": "FG",
        "CASHBACK": "CB",
        "PRODUTO GRÁTIS": "PG",
        "PRODUTO GRATIS": "PG",
        "SERVIÇO GRATUITO": "SG",
        "SERVICO GRATUITO": "SG",
        "PONTOS": "PT",
        "MILHAS": "PT",
        "PONTOS/MILHAS": "PT",
        "ACESSO EXCLUSIVO": "AE",
        "UPGRADE": "UP",
        "COMBO": "CP",
        "PACOTE": "CP",
        "COMBO/PACOTE": "CP",
    }

    @classmethod
    def extract_initials(cls, nome: str, max_iniciais: int = 4) -> str:
        """Extrai as iniciais de um nome, ignorando preposições.

        Args:
            nome: Nome completo
            max_iniciais: Número máximo de iniciais a extrair

        Returns:
            String com as iniciais em maiúsculo
        """
        if not nome:
            return ""

        # Remover acentos e caracteres especiais, mas manter hífens e apóstrofos
        nome_limpo = re.sub(r"[^a-zA-ZÀ-ÿ\s'-]", "", nome)

        # Normalizar acentos (conversão básica)
        acentos = {
            "à": "a",
            "á": "a",
            "â": "a",
            "ã": "a",
            "ä": "a",
            "è": "e",
            "é": "e",
            "ê": "e",
            "ë": "e",
            "ì": "i",
            "í": "i",
            "î": "i",
            "ï": "i",
            "ò": "o",
            "ó": "o",
            "ô": "o",
            "õ": "o",
            "ö": "o",
            "ù": "u",
            "ú": "u",
            "û": "u",
            "ü": "u",
            "ç": "c",
            "ñ": "n",
        }

        for acento, letra in acentos.items():
            nome_limpo = nome_limpo.replace(acento, letra)
            nome_limpo = nome_limpo.replace(acento.upper(), letra.upper())

        # Remove apóstrofos para evitar que nomes como "L'Oréal" sejam divididos
        nome_limpo = re.sub(r"['’]", "", nome_limpo)

        # Dividir em palavras por espaços ou hífens
        palavras = re.split(r"[\s\-]", nome_limpo.strip())

        # Se houver apenas uma palavra, retorna a primeira letra
        if len(palavras) == 1:
            return palavras[0][0].upper()

        iniciais = []
        for palavra in palavras:
            palavra_lower = palavra.lower()
            if palavra_lower not in cls.PREPOSITIONS and palavra:
                iniciais.append(palavra[0].upper())

        return "".join(iniciais)

    @classmethod
    def extract_cep_digits(cls, cep: str) -> str:
        """Extrai os últimos 3 dígitos do CEP.

        Args:
            cep: CEP no formato XXXXX-XXX

        Returns:
            Últimos 3 dígitos do CEP
        """
        if not cep:
            return ""

        # Remover hífen e manter apenas dígitos
        digitos = re.sub(r"[^0-9]", "", cep)

        if len(digitos) >= 3:
            return digitos[-3:]

        return digitos.ljust(3, "0")  # Preencher com zeros se necessário

    @classmethod
    def extract_phone_digits(cls, telefone: str) -> str:
        """Extrai os últimos 3 dígitos do telefone.

        Args:
            telefone: Número de telefone

        Returns:
            Últimos 3 dígitos do telefone
        """
        if not telefone:
            return ""

        # Remover caracteres não numéricos
        digitos = re.sub(r"[^0-9]", "", telefone)

        if len(digitos) >= 3:
            return digitos[-3:]

        return digitos.ljust(3, "0")  # Preencher com zeros se necessário

    @classmethod
    def extract_cnpj_digits(cls, cnpj: str, quantidade: int) -> str:
        """Extrai os últimos N dígitos da base de 8 dígitos do CNPJ.

        Args:
            cnpj: CNPJ (pode estar formatado ou não)
            quantidade: Quantidade de dígitos a extrair

        Returns:
            Últimos N dígitos da base do CNPJ
        """
        if not cnpj:
            return "0" * quantidade

        # Remover caracteres não numéricos para obter o CNPJ limpo
        digitos_limpos = re.sub(r"[^0-9]", "", cnpj)

        # A lógica de ID considera apenas a base do CNPJ (primeiros 8 dígitos)
        base_cnpj = digitos_limpos[:8]

        # Pega os dígitos necessários do final do CNPJ base
        digitos = base_cnpj[-quantidade:]

        # Preenche com zeros à esquerda se a quantidade for menor que o esperado
        return digitos.zfill(quantidade)

    @classmethod
    def interleave_initials_digits(
        cls, iniciais: list[str], digitos: str, tamanho_secao: int
    ) -> str:
        """Intercala iniciais com dígitos para formar a seção central do ID.

        Args:
            iniciais: Lista de iniciais
            digitos: String de dígitos para intercalar
            tamanho_secao: Tamanho da seção central

        Returns:
            Seção central intercalada
        """
        resultado = []
        idx_inicial = 0
        idx_digito = 0

        while len(resultado) < tamanho_secao:
            # Adiciona uma inicial se ainda houver iniciais
            if idx_inicial < len(iniciais):
                resultado.append(iniciais[idx_inicial])
                idx_inicial += 1

            # Se o resultado ainda não atingiu o tamanho, adiciona um dígito
            if len(resultado) < tamanho_secao and idx_digito < len(digitos):
                resultado.append(digitos[idx_digito])
                idx_digito += 1
            # Se acabaram os dígitos mas não as iniciais, continue com as iniciais
            elif len(resultado) < tamanho_secao and idx_inicial < len(iniciais):
                continue
            # Se acabaram ambos, preencha com o que for necessário (ou nada, se a lógica for outra)
            elif len(resultado) < tamanho_secao:
                # Se acabaram os dígitos, mas o tamanho da seção ainda não foi atingido,
                # preenche com as iniciais restantes (se houver)
                if idx_inicial < len(iniciais):
                    resultado.append(iniciais[idx_inicial])
                    idx_inicial += 1
                else:
                    # Se não há mais iniciais nem dígitos, preenche com '0'
                    resultado.append("0")

        return "".join(resultado[:tamanho_secao])

    @classmethod
    def extract_partner_initials(cls, nome: str) -> str:
        """Extrai iniciais do nome do parceiro ignorando preposições.

        Método específico para benefícios que retorna string ao invés de lista.

        Args:
            nome: Nome completo do parceiro

        Returns:
            String com iniciais em maiúsculo
        """
        preposicoes = {"da", "de", "do", "dos", "das", "e", "&", "em", "na", "no"}
        palavras = nome.split()
        iniciais = ""

        for palavra in palavras:
            palavra_limpa = palavra.lower().strip("()[]{}.,;:")
            if palavra_limpa not in preposicoes and palavra_limpa:
                iniciais += palavra[0].upper()

        return iniciais

    @classmethod
    def extract_partner_initials_from_id(cls, partner_id: str) -> str:
        """Extrai iniciais do ID do parceiro.

        Exemplo: 'PTN_A2B9C547_DC' -> 'ABC'

        Args:
            partner_id: ID do parceiro no formato PTN_XXXXXXX_XXX

        Returns:
            String com iniciais extraídas do ID
        """
        parts = partner_id.split("_")
        if len(parts) != 3:
            raise ValueError(f"ID do parceiro inválido: {partner_id}")
        return "".join(ch for ch in parts[1] if ch.isalpha())

    @classmethod
    def generate_student_id(
        cls,
        nome: str,
        curso: str = "",
        cep: str = "",
        celular: str = "",
        email: str = "",
    ) -> str:
        """Gera ID para aluno seguindo o padrão STD_XXXXXXXX_XX.

        Args:
            nome: Nome completo do aluno
            curso: Curso do aluno
            cep: CEP do aluno
            celular: Celular do aluno
            email: Email do aluno

        Returns:
            ID do aluno no formato STD_XXXXXXXX_XX
        """
        # 1. Extrair iniciais
        iniciais = cls.extract_initials(nome)

        # 2. Obter código do curso
        # logger.debug(f"Curso recebido: {curso}")
        # logger.debug(f"Curso em maiúsculas: {curso.upper()}")
        # logger.debug(f"CURSO_CODES: {CURSO_CODES}")
        codigo_curso = cls.CURSO_CODES.get(curso.upper(), "XX")

        # 3. Calcular tamanho da seção central
        tamanho_secao = 15 - 4 - len(codigo_curso) - 1  # STD_ + _ + codigo

        # 4. Obter dígitos de preenchimento
        digitos_cep = cls.extract_cep_digits(cep)
        digitos_celular = cls.extract_phone_digits(celular)

        # Extrair dígitos do email se necessário
        digitos_email = re.sub(r"[^0-9]", "", email) if email else ""

        # Combinar todos os dígitos
        todos_digitos = digitos_cep + digitos_celular + digitos_email

        # 5. Intercalar iniciais com dígitos
        secao_central = cls.interleave_initials_digits(
            iniciais, todos_digitos, tamanho_secao
        )

        # 6. Construir ID final
        return f"STD_{secao_central}_{codigo_curso}"

    @classmethod
    def generate_employee_id(
        cls, nome: str, cpf: str, cargo: str, cep: str = "", telefone: str = ""
    ) -> str:
        """Gera ID para funcionário seguindo o padrão EMP_XXXXXXXX_XX.
        Args:
            nome: Nome completo do funcionário
            cpf: CPF do funcionário (deve conter 11 dígitos)
            cargo: Cargo do funcionário
            cep: CEP do funcionário
            telefone: Telefone do funcionário
        Returns:
            ID do funcionário no formato EMP_XXXXXXXX_XX
        """
        # 0. Validar CPF
        cpf_limpo = re.sub(r"[^0-9]", "", cpf)
        if len(cpf_limpo) != 11:
            raise ValueError("O CPF deve conter exatamente 11 dígitos.")

        # 1. Extrair iniciais
        iniciais = cls.extract_initials(nome)
        # 2. Obter código do cargo
        codigo_cargo = cls.CARGO_CODES.get(cargo.upper(), "XX")
        # 3. Calcular tamanho da seção central
        tamanho_secao = 15 - 4 - len(codigo_cargo) - 1  # EMP_ + _ + codigo
        # 4. Obter dígitos de preenchimento
        digitos_cep = cls.extract_cep_digits(cep)
        digitos_telefone = cls.extract_phone_digits(telefone)
        # Combinar dígitos
        todos_digitos = digitos_cep + digitos_telefone + cpf_limpo
        # 5. Intercalar iniciais com dígitos
        secao_central = cls.interleave_initials_digits(
            iniciais, todos_digitos, tamanho_secao
        )
        # 6. Construir ID final
        return f"EMP_{secao_central}_{codigo_cargo}"

    @classmethod
    def generate_partner_id(
        cls, trade_name: str, cnpj: str, category: PartnerCategory
    ) -> str:
        """Gera ID para parceiro seguindo o padrão PTN_XXXXXXX_XXX.

        Args:
            trade_name: Nome comercial do parceiro
            cnpj: CNPJ do parceiro
            category: Categoria do parceiro

        Returns:
            ID do parceiro no formato PTN_XXXXXXX_XXX
        """
        # 0. Validar CNPJ
        cnpj_limpo = re.sub(r"[^0-9]", "", cnpj)
        if len(cnpj_limpo) != 14:
            raise ValueError("O CNPJ deve conter exatamente 14 dígitos.")

        # 1. Extrair iniciais
        iniciais = cls.extract_initials(trade_name)

        # 2. Obter código da categoria
        codigo_categoria = cls.CATEGORY_CODES.get(category, "OUT")

        # 3. Definir tamanho da seção central
        tamanho_secao = 7

        # 4. Calcular quantos dígitos do CNPJ são necessários
        # Garante que não seja negativo se as iniciais forem muito longas
        digitos_necessarios = max(0, tamanho_secao - len(iniciais))

        # 5. Extrair dígitos do CNPJ
        digitos_cnpj = cls.extract_cnpj_digits(cnpj, digitos_necessarios)

        # 6. Intercalar iniciais com dígitos do CNPJ
        secao_central = cls.interleave_initials_digits(
            iniciais, digitos_cnpj, tamanho_secao
        )

        # 7. Construir ID final
        return f"PTN_{secao_central}_{codigo_categoria}"

    @classmethod
    def generate_benefit_id_old(
        cls, nome_parceiro: str, contador: int, tipo_beneficio: str
    ) -> str:
        """Gera ID único para benefício seguindo padrão simplificado.

        Formato: BNF_[INICIAIS]_[CONTADOR]_[TIPO]

        Args:
            nome_parceiro: Nome completo do parceiro
            contador: Número sequencial do benefício (0, 1, 2...)
            tipo_beneficio: Tipo do benefício (DESCONTO, CASHBACK, etc.)

        Returns:
            ID único do benefício no formato BNF_[INICIAIS]_[CONTADOR]_[TIPO]

        Examples:
            >>> cls.gerar_id_beneficio("Autoescola Escórcio", 0, "DESCONTO")
            'BNF_AE_00_DC'
            >>> cls.gerar_id_beneficio("Colégio Adventista", 1, "FRETE GRÁTIS")
            'BNF_CA_01_FG'
        """
        # Extrair iniciais do parceiro
        iniciais = "".join(cls.extract_initials(nome_parceiro))

        # Formatar contador com 2 dígitos
        contador_formatado = f"{contador:02d}"

        # Obter código do tipo de benefício
        codigo_tipo = cls.TIPO_BENEFICIO_CODES.get(tipo_beneficio.upper(), "DC")

        # Montar ID final
        id_beneficio = f"BNF_{iniciais}_{contador_formatado}_{codigo_tipo}"

        return id_beneficio

    @classmethod
    def generate_benefit_id(
        cls, iniciais_parceiro: str, tipo_beneficio: str = "DESCONTO"
    ) -> str:
        """Gera ID único para benefício baseado em timestamp + hash.

        Formato: BNF_[INICIAIS]_[ID5]_[TIPO]

        Vantagens:
        - Não depende de contagem sequencial
        - Único por natureza (baseado em timestamp)
        - Não precisa consultar benefícios existentes
        - Resistente a exclusões e concorrência
        - Mantém ordem cronológica aproximada

        Args:
            iniciais_parceiro: Iniciais do parceiro (ex: "TL", "AE")
            tipo_beneficio: Tipo do benefício (DESCONTO, CASHBACK, etc.)

        Returns:
            ID único do benefício no formato BNF_[INICIAIS]_[ID5]_[TIPO]

        Examples:
            >>> cls.gerar_id_beneficio_timestamp("TL", "DESCONTO")
            'BNF_TL_1A2B3_DC'
            >>> cls.gerar_id_beneficio_timestamp("AE", "CASHBACK")
            'BNF_AE_0Z9Q1_CB'
        """
        import hashlib
        import time

        # Obter timestamp atual em milissegundos
        timestamp_ms = int(time.time() * 1000)

        # Converter para base36 para compactar (usa 0-9 e A-Z)
        def to_base36(num):
            alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if num == 0:
                return "0"
            result = ""
            while num > 0:
                result = alphabet[num % 36] + result
                num //= 36
            return result

        # Gerar hash curto para garantir unicidade adicional
        hash_input = f"{iniciais_parceiro}_{timestamp_ms}_{tipo_beneficio}"
        hash_short = hashlib.md5(hash_input.encode()).hexdigest()[:2].upper()

        # Timestamp em base36 (mais compacto)
        # Para atender ao formato solicitado de 5 caracteres no código central,
        # utilizamos 3 caracteres do timestamp em base36 + 2 caracteres do hash.
        timestamp_b36 = to_base36(timestamp_ms)[-3:]  # Últimos 3 caracteres

        # Combinar timestamp + hash para garantir unicidade
        identificador = f"{timestamp_b36}{hash_short}"

        # Obter código do tipo de benefício
        codigo_tipo = cls.TIPO_BENEFICIO_CODES.get(tipo_beneficio.upper(), "DC")

        # Montar ID final
        id_beneficio = f"BNF_{iniciais_parceiro}_{identificador}_{codigo_tipo}"

        return id_beneficio

    @classmethod
    def validate_id_format(cls, id_str: str, tipo: str) -> bool:
        """Valida se um ID está no formato correto.

        Args:
            id_str: ID a ser validado
            tipo: Tipo do ID ('student', 'employee', 'partner', 'benefit')

        Returns:
            True se o formato estiver correto
        """
        if not id_str or len(id_str) < 10:
            return False

        if tipo == "student":
            return (
                bool(re.match(r"^STD_[A-Z0-9]{8}_[A-Z0-9]{2}$", id_str))
                and len(id_str) == 15
            )
        elif tipo == "employee":
            return (
                bool(re.match(r"^EMP_[A-Z0-9]{7,8}_[A-Z]{2,3}$", id_str))
                and len(id_str) == 15
            )
        elif tipo == "partner":
            return (
                bool(re.match(r"^PTN_[A-Z0-9]{7}_[A-Z]{3}$", id_str))
                and len(id_str) == 15
            )
        elif tipo == "benefit":
            # Suporte a ambos os formatos:
            # Formato antigo (sequencial): BNF_[INICIAIS]_[00-99]_[TIPO]
            # Formato novo (timestamp): BNF_[INICIAIS]_[ID5]_[TIPO]
            formato_antigo = bool(re.match(r"^BNF_[A-Z]+_\d{2}_[A-Z]{2}$", id_str))
            formato_novo = bool(re.match(r"^BNF_[A-Z]+_[A-Z0-9]{5}_[A-Z]{2}$", id_str))
            return formato_antigo or formato_novo

        return False


# Instância global para uso direto
id_generators = IDGenerators()
