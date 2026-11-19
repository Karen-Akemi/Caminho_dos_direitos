# 📊 Pesquisa de Campo Primária — Caminho dos Direitos

Este diretório contém os dados tratados (camadas **Prata** e **Ouro**; nos nomes dos arquivos, `silver_` e `gold_`), o pipeline de higienização e os principais *insights* extraídos da pesquisa primária realizada pelo grupo para fundamentar a solução **Caminho dos Direitos** (Global Solution FIAP 2026.2 — CitizenTech).

---

## 🔗 Links dos Instrumentos de Coleta (Google Forms)

A escuta ativa foi dividida em duas frentes complementares para capturar as duas pontas do ecossistema (o cidadão em busca do direito e o profissional da linha de frente):

* **Formulário 1 — Experiência dos Cidadãos (Moradores de São Paulo):** https://docs.google.com/forms/d/e/1FAIpQLSdtQHJIurISK_tursUmGYUhlFhmI-WG_FN4gbNM_2NHsJU-8w/viewform?usp=sharing
* **Formulário 2 — Profissionais da Linha de Frente (UBS / Assistência Social):** https://docs.google.com/forms/d/e/1FAIpQLSehmwNxE7cwcq04-ZV8DZPZDECy-SDVx1zVyVdnIY6R7vyUeQ/viewform?usp=sharing
* **Aplicação Web e Protótipo:** [Caminho dos Direitos — GitHub Pages](https://karen-akemi.github.io/Caminho_dos_direitos/indexsite.html)

---

## 🗂️ Estrutura dos Arquivos no Repositório

Os dados brutos (camada Bronze) passaram por um pipeline em Python (`Pandas`) aplicando padronização `snake_case`, reconciliação territorial com a malha oficial de distritos da Prefeitura de São Paulo e **pseudonimização via hash criptográfico (`SHA-256`)** para proteção da privacidade dos respondentes (LGPD *by design*):

| Arquivo | Camada | Descrição Técnica |
| :--- | :---: | :--- |
| `silver_pesquisa_cidadaos_tratada.csv` | **Prata** | Base higienizada de moradores ($n=19$), com bairros padronizados para Distritos/Subprefeituras oficiais e *flags* binárias de risco de bloqueio e fricção documental. |
| `silver_pesquisa_agentes_tratada.csv` | **Prata** | Base higienizada de profissionais de saúde e assistência ($n=2$, Subprefeitura M'Boi Mirim), mapeando fluxos de encaminhamento e gargalos operacionais. |
| `gold_pesquisa_canais_informacao.csv` | **Ouro** | Tabela dimensional explodida (1:N) contabilizando a frequência individual de cada canal de informação utilizado pelos moradores. |
| `gold_pesquisa_gargalos_documentais.csv` | **Ouro** | Tabela analítica explodida (1:N) isolando os documentos e benefícios específicos que travaram a jornada dos respondentes. |

---

## 💡 Principais Insights Extraídos dos Dados

### 1. O Gargalo Silencioso da Manutenção Cadastral (62,5% em Risco de Bloqueio)
* **O Dado:** Na amostra geral ($n=19$), **47,4%** não possuem CadÚnico, **26,3%** possuem cadastro desatualizado há mais de 2 anos, **15,8%** estão com o cadastro atualizado e **10,5%** sequer sabem o que é o CadÚnico.
* **Análise de Negócio:** Ao isolar apenas os moradores que já estão inseridos no CadÚnico ($n=8$), **62,5% (5 em cada 8) estão com o cadastro vencido há mais de 2 anos** — exatamente na janela crítica de bloqueio e cancelamento de benefícios como Bolsa Família e Tarifa Social.
* **Decisão de Produto:** Justifica os **alertas preventivos via WhatsApp (em texto e áudio)** e a checagem de status cadastral logo na visita do Agente Comunitário.

### 2. O Paradoxo da Fricção Burocrática (62,5% vs. 18,2%)
* **O Dado:** Cruzando o vínculo cadastral com o relato de dificuldades práticas, **62,5%** das pessoas que já têm CadÚnico relataram travas com documentos ou benefícios (contra apenas **18,2%** de quem está fora do cadastro).
* **Principais Travas Mapeadas:** Entre os casos com dificuldade reportada, os maiores ofensores foram **Inclusão/Atualização do CadÚnico (57,1%)**, **Título de Eleitor (28,6%)**, **Bolsa Família (28,6%)**, **Comprovante de Residência (14,3%)** e **Tarifa Social de Energia (14,3%)**.
* **Análise de Negócio:** Quem está fora do sistema muitas vezes não relata trava documental porque ainda não conhece os benefícios a que tem direito (**68,4%** da amostra afirma conhecer apenas "alguns" ou "nenhum" benefício). Quando o cidadão tenta acessar ou manter o direito, quase 2 em cada 3 esbarram na burocracia.

### 3. A "Cegueira" Pós-Encaminhamento na Linha de Frente (100% sem Rastreabilidade)
* **O Dado:** **100%** dos profissionais entrevistados na Subprefeitura M'Boi Mirim apontaram **"Filas e demora"** como a maior barreira enfrentada pela população e relataram que só ficam sabendo se o cidadão conseguiu resolver a pendência **"Raramente" (50%) ou "Às vezes" (50%)**.
* **Análise de Negócio:** Hoje, o encaminhamento entre UBS, CRAS, Cartório e Poupatempo é feito entregando um papel com endereço, sem retorno sistêmico.
* **Decisão de Produto:** Valida o núcleo do **App do Agente e Painel do Coordenador**, permitindo registrar o caso na visita e acompanhar o funil completo (*Identificado $\rightarrow$ Encaminhado $\rightarrow$ Agendado $\rightarrow$ Concluído*).

### 4. Hiperconcentração Territorial e Validação da Rede de Apoio
* **O Dado:** **84,2%** das respostas dos moradores concentraram-se na Zona Sul de São Paulo (**47,4%** na Subprefeitura M'Boi Mirim — distrito Jardim Ângela — e **36,8%** na Subprefeitura Campo Limpo — Paraisópolis, Capão Redondo e Campo Limpo).
* **Canais de Confiança:** Embora **94,7%** utilizem a internet para buscar informações, as redes comunitárias aparecem logo em seguida: **Família ou Vizinhos (31,6%)** e **Agentes de Saúde (26,3%)** superam a busca direta no CRAS (**10,5%**).
* **Decisão de Produto:** Confirma que a entrada do serviço público precisa acontecer através de quem já tem a confiança do território (o Agente de Saúde na porta de casa e o WhatsApp de familiares de confiança).

---

## ⚖️ Análise de Viés Amostral e Governança (Data Ethics)

Durante a análise exploratória, identificamos que **73,7%** dos respondentes do formulário de moradores possuem entre 18 e 29 anos e **94,7%** possuem conta `gov.br` ativa. 

* **Diagnóstico de Viés de Seleção:** Como o formulário de moradores foi distribuído digitalmente, ele capturou majoritariamente a camada jovem e alfabetizada digitalmente das famílias periféricas, sub-representando idosos e pessoas em exclusão digital severa.
* **Mitigação Metodológica:** O cruzamento com o formulário dos **Agentes Comunitários de Saúde (UBS)** corrige esse ponto cego institucional: na ponta presencial, os agentes confirmam atender **frequentemente** moradores sem Certidão de Nascimento, sem CPF/RG e sem Comprovante de Residência. Por isso, o **Caminho dos Direitos** foi desenhado como uma ferramenta mediada pelo agente (acesso por CPF + PIN, sem exigir `gov.br` do morador).

---

## 💬 A Voz do Território (Relatos Reais da Pesquisa)

Quando questionados sobre *"O que mais ajudaria você a resolver documentos e benefícios?"*, os próprios moradores descreveram a proposta de valor da plataforma:

> *"Um passo a passo objetivo sobre os documentos exigidos e suporte para dúvidas."* — **Morador(a) do Jardim Guarujá (Distrito Jardim Ângela), 18–29 anos**

> *"Acho que seria legal um sistema que com os meus dados apresentasse todos os benefícios que tenho direito e como consigo ter acesso a eles."* — **Morador(a) do Jardim Ângela, 18–29 anos**

> *"Talvez uma forma, app ou sistema, não sei, que explicasse onde e como conseguir esses benefícios."* — **Morador(a) da Vila Franca (Paraisópolis), 18–29 anos**

[← Voltar para o README principal](../README.md)
