<p align="center">
  <img src="assets/logo.png" alt="Logo Caminho dos Direitos" width="320">
</p>

<h3 align="center">Levando os direitos sociais até quem mais precisa, com dados e com quem está em campo.</h3>

<p align="center">
  <b>Global Solution 2026.2 · FIAP</b> · Desafio <b>CitizenTech</b> · Tecnologia em Data Science, 2º ano
</p>

<p align="center">
  <a href="https://karen-akemi.github.io/Caminho_dos_direitos/"><b>📊 Abrir o dashboard</b></a> ·
  <a href="https://karen-akemi.github.io/Caminho_dos_direitos/indexsite.html"><b>🌐 Site do projeto</b></a> ·
  <a href="https://karen-akemi.github.io/Caminho_dos_direitos/site/entrar.html"><b>🔐 Demo por cargo</b></a> ·
  <a href="https://karen-akemi.github.io/Caminho_dos_direitos/indexsite.html#prototipo"><b>📱 Protótipo do app</b></a> ·
  <a href="#-demonstração"><b>🎥 Pitch</b></a> ·
  <a href="#-demonstração"><b>🖥️ Slides</b></a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-Colab-3776AB?logo=python&logoColor=white">
  <img alt="Power BI" src="https://img.shields.io/badge/Power%20BI-Dashboard-F2C811?logo=powerbi&logoColor=black">
  <img alt="Figma" src="https://img.shields.io/badge/Figma-Prot%C3%B3tipo-F24E1E?logo=figma&logoColor=white">
  <img alt="Recorte" src="https://img.shields.io/badge/Recorte-96%20distritos%20de%20S%C3%A3o%20Paulo-1F3FAE">
</p>

<p align="center">
  👥 <b>Equipe:</b> Angelo Rabello · Karen Akemi de Oliveira · Milena Barbosa
</p>

---

# Caminho dos Direitos

O **Caminho dos Direitos** aproxima pessoas em situação de vulnerabilidade dos benefícios sociais e dos documentos a que elas têm direito. Ele junta um **app para os agentes em campo**, um **painel para coordenadores e gestores** e um **modelo de priorização** que mostra onde agir primeiro nos 96 distritos do município de São Paulo.

## 📖 Sobre o Projeto

- **Problema:** muitas pessoas que teriam direito a benefícios sociais não os recebem. Falta documento, o cadastro (como o CadÚnico) está desatualizado ou elas não sabem que têm o direito.
- **Motivação:** os agentes de saúde e os assistentes sociais são quem chega até essas pessoas. Mas eles não têm uma ferramenta simples para identificar as pendências, orientar e encaminhar cada caso aos serviços (CRAS, cartório, Poupatempo, UBS). A ideia é ser um diferencial em relação ao e-SUS para quem trabalha em campo.
- **Objetivo principal:** responder **quem está sem documento ou sem direito, onde, e o que fazer primeiro**. Para isso, o projeto cruza o que o app registra com os dados públicos do território.
- **Público-alvo:**
  - agentes de saúde e assistentes sociais em campo, que usam o app;
  - coordenadores e gestores públicos, que usam o painel;
  - famílias em situação de vulnerabilidade, que são atendidas por eles.

## ⚙️ Funcionalidades

**📱 App do agente** (protótipo de ideação no Figma)
- **Plano de Direitos:** a partir de um formulário, o app lista os **possíveis benefícios** da pessoa ou da família entre 7 programas: Documentação básica, CadÚnico, Bolsa Família, BPC, Tarifa Social de Energia, Pé-de-Meia e Farmácia Popular.
- **Pendências e encaminhamento:** o agente marca a situação de cada benefício (*já recebe*, *bloqueado*, *precisa atualizar*, *falta documento*, *ainda não pediu*). Depois encaminha a pessoa ao serviço certo, com a lista de documentos para levar.
- **Renda sem constrangimento:** uma calculadora (pessoas na casa + renda de cada uma) chega à renda por pessoa. O app guarda só a faixa, nunca o valor.
- **Anotação por voz com IA:** a IA transcreve o que o agente fala e remove o dado clínico. Depois organiza a visita e sugere marcações, que o agente confirma.
- **Lembretes por WhatsApp**, em texto e em **áudio**, como recurso de acessibilidade.
- **Acesso simples, sem gov.br:**
  - o agente pede acesso com CPF e a unidade (UBS/CRAS);
  - o coordenador aprova o pedido;
  - a entrada é por PIN de 6 dígitos ou por código no WhatsApp.
- **Visão do coordenador:** aprovar ou recusar acessos, ver os casos da unidade e transferir casos entre agentes.

**📊 Painel do monitoramento** (Power BI e versão HTML)
- **Indicadores e mapa:**
  - indicadores do app;
  - **mapa de prioridade** dos 96 distritos;
  - tabela **Onde agir primeiro**.
- **Direitos e encaminhamentos:**
  - situação dos direitos por programa;
  - documentos que faltam;
  - resultado dos encaminhamentos.
- **Campanhas recomendadas** para os distritos urgentes e de prioridade alta, e **alertas cruzados** entre o território e o que o app registrou.
- **Filtros** por subprefeitura, distrito, unidade e programa. No Power BI, cada gestor vê só a sua subprefeitura.
- Na versão HTML, a segurança por linha é simulada pela URL: `dashboard/?sub=M'Boi Mirim&travar=1` ou `dashboard/?uni=410&travar=1` travam o filtro (é o que a demo por cargo usa).

**🧠 Modelo de priorização** (Python)
- **Direito provável sem benefício:** compara cada distrito com os de perfil social parecido. Assim estima quantas pessoas têm direito provável a **BPC idoso** ou **Bolsa Família** e não recebem.
- **Índice e campanhas:** calcula um **índice de prioridade (0 a 100)** e sugere campanhas.
- **Resultado do modelo:**
  - os **10 distritos urgentes** concentram **55%** dessas pessoas (cerca de 54.947);
  - os mais prioritários são Jardim Ângela, Tremembé e Grajaú.

## 🛠️ Tecnologias Utilizadas

- **Front-end:**
  - **Figma**, para o protótipo do app;
  - **HTML, CSS e JavaScript**, para o painel interativo e o site do projeto, publicados no **GitHub Pages**.
- **Back-end:**
  - **Python** no **Google Colab**;
  - **FastAPI** com **Cloudflare Tunnel**, para o servidor do WhatsApp;
  - **WhatsApp Cloud API** (Meta).
- **Banco de dados:**
  - **Oracle SQL Developer Data Modeler**, para o modelo conceitual, o lógico e o dimensional (Snowflake + Galaxy), com scripts SQL;
  - os dados tratados ficam em CSV.
- **Outras ferramentas:**
  - **Power BI**;
  - **IA:** Whisper para a transcrição, Claude (Anthropic) para a explicação com RAG e para organizar a anotação, edge-tts e gTTS para as vozes;
  - **bibliotecas de dados:** pandas, NumPy, scikit-learn, SciPy, statsmodels, GeoPandas e PySAL.

## 🚀 Demonstração

| | Link |
|---|---|
| 📊 **Painel do monitoramento** (interativo, sem baixar nada) | [Abrir no navegador](https://karen-akemi.github.io/Caminho_dos_direitos/) · [arquivo do Power BI](dashboard/Caminho-dos-direitos.pbix) |
| 🌐 **Site do projeto** | [Abrir o site](https://karen-akemi.github.io/Caminho_dos_direitos/indexsite.html) |
| 🔐 **Demo por cargo** (login simulado: secretaria, subprefeitura, coordenação e agente) | [Entrar na demo](https://karen-akemi.github.io/Caminho_dos_direitos/site/entrar.html) |
| 📱 **Protótipo do app** | [Ver as telas no site](https://karen-akemi.github.io/Caminho_dos_direitos/indexsite.html#prototipo) |
| 🎬 **Vídeos das funções de IA** | [Ver abaixo](#-vídeos-de-demonstração) |
| 🎥 **Pitch** e 🖥️ **Slides** | 🚧 Em finalização |

## 🐍 Função dos notebooks

Os notebooks rodam no **Google Colab** com **Ambiente de execução → Executar tudo**. Eles estão divididos em duas trilhas.

| Trilha | Notebook | Principais funcionalidades |
|---|---|---|
| Dashboard · 1 | [`Tratamento_GS_v6`](notebooks/Tratamento_GS_v6.ipynb) | Padroniza os 96 distritos, junta e confere as bases públicas |
| Dashboard · 2 | [`Modelo_GS_v4`](notebooks/Modelo_GS_v4.ipynb) | Estima quem tem direito e não recebe, prioriza os distritos e sugere campanhas |
| Dashboard · 3 | [`Simulacao_App_v2`](notebooks/Simulacao_App_v2.ipynb) | Simula o que os agentes registrariam no app, calibrado nos dados reais e no modelo |
| App | [`caminho_dos_direitos_colab_v4`](notebooks/caminho_dos_direitos_colab_v4.ipynb) | Demonstra o app com a persona Dona Cida. Mostra o Plano de Direitos, os testes, a explicação com IA (RAG), a calculadora de renda, a anotação por voz e o lembrete |
| App | [`anotacao_por_voz`](notebooks/anotacao_por_voz.ipynb) | Transcreve a fala, remove o dado clínico, resume a visita e sugere marcações que o agente confirma |
| App | [`servidor_whatsapp_colab`](notebooks/servidor_whatsapp_colab.ipynb) | Envia o lembrete por WhatsApp de verdade, em texto e em mensagem de voz |

Na trilha do dashboard, o 2 só funciona depois do 1, e o 3 depois do 2. A trilha do app é independente. O guia seção por seção está em [`notebooks/README.md`](notebooks/README.md).

### 🎬 Vídeos de demonstração

Clique na imagem para assistir.

<table>
<tr>
<td align="center" width="50%" valign="top">
<a href="https://karen-akemi.github.io/Caminho_dos_direitos/assets/videos/anotacao_app.mp4"><img src="assets/videos/anotacao_app.jpg" alt="Vídeo: anotação por voz com IA" width="220"></a><br>
<b>🎙️ Anotação por voz com IA</b> <sub>(29 s)</sub>
</td>
<td align="center" width="50%" valign="top">
<a href="https://karen-akemi.github.io/Caminho_dos_direitos/assets/videos/lembrete_whatsapp.mp4"><img src="assets/videos/lembrete_whatsapp.jpg" alt="Vídeo: lembrete por WhatsApp" width="220"></a><br>
<b>💬 Lembrete por WhatsApp</b> <sub>(36 s)</sub>
</td>
</tr>
<tr>
<td valign="top">

Tela do app no caso da **Dona Cida**, gerada pelo notebook [`anotacao_por_voz`](notebooks/anotacao_por_voz.ipynb). O agente grava a anotação da visita e o app:

- mostra a transcrição, com o trecho de saúde já removido pela IA;
- sugere as marcações (dificuldade de se locomover, precisa de atendimento médico, precisa de acompanhante, melhor horário: à tarde), que o agente pode tirar ou adicionar;
- propõe próximos passos, como remarcar o Poupatempo para a tarde e confirmar com o filho;
- ao salvar, guarda só as marcações em `fato_necessidade_caso.csv`, apaga o áudio e descarta o texto.

</td>
<td valign="top">

O lembrete chegando a um celular de verdade, pela Cloud API da Meta, enviado pelo notebook [`servidor_whatsapp_colab`](notebooks/servidor_whatsapp_colab.ipynb):

- mensagem em texto para a **Dona Cida**: atendimento no Poupatempo M'Boi Mirim em 18/11, às 9h, levando certidão de nascimento, RG e comprovante de residência, como na tela de encaminhamento do protótipo;
- a opção de responder PARAR para não receber mais;
- em seguida, a **mensagem de voz** com o mesmo lembrete, como recurso de acessibilidade.

</td>
</tr>
</table>

## 📁 Estrutura do Projeto

```
├── README.md
├── index.html                     # abre o painel no GitHub Pages
├── indexsite.html                 # site de apresentação do projeto
├── site/
│   ├── entrar.html                # login simulado: escolha do cargo
│   ├── plataforma.html            # plataforma por cargo (secretaria, subprefeitura, coordenação, agente)
│   ├── plataforma.js · site.js · site.css
│   ├── dados_site.js              # dados do site, gerados a partir de dados/
│   └── gerar_dados_site.py        # gera o dados_site.js (python site/gerar_dados_site.py .)
├── assets/
│   ├── logo.png
│   ├── telas/                     # telas do protótipo do app
│   └── videos/                    # vídeos de demonstração (anotação por voz e WhatsApp)
├── dashboard/
│   ├── index.html                 # painel interativo (HTML)
│   └── Caminho-dos-direitos.pbix  # arquivo do Power BI
├── notebooks/
│   ├── Tratamento_GS_v6.ipynb
│   ├── Modelo_GS_v4.ipynb
│   ├── Simulacao_App_v2.ipynb
│   ├── caminho_dos_direitos_colab_v4.ipynb
│   ├── anotacao_por_voz.ipynb
│   ├── servidor_whatsapp_colab.ipynb
│   ├── simulador/                 # motor de regras do Plano de Direitos (regras, testes e RAG)
│   ├── ia/                        # anotação por voz, voz e WhatsApp
│   └── README.md                  # guia dos notebooks
├── dados/
│   ├── saida/                     # território tratado
│   ├── saida_modelo/              # indicadores, lacunas e recomendações do modelo
│   └── saida_app/                 # dados do app (SIMULADO)
├── modelagem/                     # modelos conceitual, lógico e dimensional e dicionário de dados
├── documentacao/
│   └── Notebooks_e_bases_de_dados.pdf   # guia dos notebooks e das bases de dados
└── apresentacao/                  # 🚧 pitch e slides (em finalização)
```

## 👥 Equipe e Colaboradores

| Integrante | Links |
|---|---|
| Angelo Rabello | [GitHub](https://github.com/AngeloRBLL0) |
| Karen Akemi de Oliveira | [GitHub](https://github.com/Karen-Akemi) |
| Milena Barbosa | [GitHub](https://github.com/MiihDev) |

## 📚 Referências

O projeto usa 14 bases públicas, recortadas nos 96 distritos da cidade de São Paulo:

- **GeoSampa (Prefeitura de São Paulo):** limites dos distritos e setores de risco geológico (R1 a R4);
- **IBGE, Censo 2022:** população total, população por faixa etária (via TabNet SMS-SP) e crianças de até 5 anos sem registro (SIDRA);
- **SMADS:** famílias no CadÚnico (jan/2026) e localização dos CRAS (Geoportal SMADS);
- **Portal de Dados Abertos da Prefeitura de São Paulo:**
  - famílias no CadÚnico (jan/2026);
  - famílias com Bolsa Família (2025);
  - beneficiários do BPC (jul/2025);
- **CNES (Ministério da Saúde):** UBS;
- **ANEEL:** beneficiários da Tarifa Social (testada e descartada);
- **Levantamento do grupo (2026):** cartórios de registro civil e postos do Poupatempo;
- **Documentação da WhatsApp Cloud API (Meta):** base do servidor de lembretes.

Os detalhes de cada base, de como foram juntadas e das limitações estão em [`documentacao/Notebooks_e_bases_de_dados.pdf`](documentacao/Notebooks_e_bases_de_dados.pdf).

## 📄 Licença

Projeto acadêmico, desenvolvido para a Global Solution 2026.2 da FIAP. O repositório ainda não tem uma licença definida. Sem ela, todos os direitos ficam com os autores.
