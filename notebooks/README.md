# 🐍 Notebooks

São 6 notebooks em duas trilhas independentes. Todos rodam no **Google Colab** com **Ambiente de execução → Executar tudo**.

| Trilha | Ordem | Notebook | Para quê |
|---|---|---|---|
| Dashboard | 1 | [`Tratamento_GS_v6`](Tratamento_GS_v6.ipynb) | Junta e confere as bases públicas dos 96 distritos |
| Dashboard | 2 | [`Modelo_GS_v4`](Modelo_GS_v4.ipynb) | Estima quem tem direito e não recebe, prioriza distritos e sugere campanhas |
| Dashboard | 3 | [`Simulacao_App_v2`](Simulacao_App_v2.ipynb) | Simula o que os agentes registrariam no app, calibrado nos dados reais e no modelo |
| App | 4 | [`caminho_dos_direitos_colab_v4`](caminho_dos_direitos_colab_v4.ipynb) | Demonstra o app com a persona Dona Cida |
| App | 5 | [`anotacao_por_voz`](anotacao_por_voz.ipynb) | Anotação por voz com IA, sozinha, para mostrar no pitch |
| App | 6 | [`servidor_whatsapp_colab`](servidor_whatsapp_colab.ipynb) | Liga o app ao WhatsApp de verdade (Cloud API da Meta) |

Na trilha do dashboard, o 2 só funciona depois do 1, e o 3 depois do 2. A trilha do app não depende dela. O guia completo da trilha do dashboard (bases, saídas, Power BI e problemas comuns) está em [`documentacao/Notebooks_e_bases_de_dados.pdf`](../documentacao/Notebooks_e_bases_de_dados.pdf). Para a trilha do app, vale este guia, que está mais atualizado que o PDF.

---

## 4. caminho_dos_direitos_colab_v4

Demonstra o app funcionando com a persona **Dona Cida**, a mesma das telas do protótipo. Lê os arquivos do app na pasta do Drive indicada em `PROJETO` (seção 2).

| Seção | O que faz |
|---|---|
| 1. Conectar o Google Drive | Monta o Drive |
| 2. Achar os arquivos do projeto | Confere os arquivos obrigatórios e carrega os módulos |
| 3. Motor de regras | Gera o Plano de Direitos da Dona Cida |
| 4. Testes | Roda os 30 casos rotulados à mão e salva `resultado_testes.csv` |
| 5. IA generativa (RAG) | Explica o plano em linguagem simples, citando as fontes. Sem chave, usa o modo offline |
| 6. Dúvida do agente | Responde uma pergunta livre com base nas fontes |
| 7. LLM de verdade (opcional) | Carrega a `ANTHROPIC_API_KEY` dos Secrets; depois rode as seções 5 e 6 de novo |
| 8. Testar um caso seu | Calculadora de renda: pessoas na casa + renda de cada uma → faixa. O app guarda só a faixa, nunca o valor |
| 9. Do plano ao que o agente registra | Mostra cada sugestão no formato de `fato_item_plano`. É só demonstração: o painel usa os dados do notebook 3 |
| 10. Anotação por voz com IA | Digitada, pelo microfone ou por áudio do celular. Filtra dado clínico, organiza um resumo da visita, sugere 5 marcações e refaz o plano com elas |
| 11. Lembrete por WhatsApp | Lembrete em texto com o botão "Ouvir em áudio" e mensagem de voz. Sem `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID`, roda em modo demonstração e nada é enviado |
| 11b. Comparar as vozes | A mesma mensagem em gTTS e nas vozes `feminina`, `feminina2` e `masculina` (padrão: `feminina`) |
| 12. WhatsApp de verdade | Aponta para o notebook 6 |

**Arquivos de apoio no Drive:** `simulador.py`, `avaliar.py`, `regras.csv`, `casos_teste.json`, `explicador.py` e `base_conhecimento.csv` são obrigatórios. `anotacoes.py` (seção 10), `whatsapp.py` (seção 11) e `voz.py` (seção 11b) são opcionais. Podem ficar todos na mesma pasta ou separados em `simulador/` e `ia/`.

---

## 5. anotacao_por_voz

Versão independente e mais completa da anotação por voz. O código está todo dentro do notebook.

1. **Grava e transcreve** a fala no próprio Colab (Whisper local) e apaga o áudio.
2. **Remove os dados clínicos** (pressão, peso, altura, glicemia, nome de doença ou remédio) e avisa: *registre no e-SUS*.
3. **Organiza** o texto filtrado em um resumo da visita (situação, prioridade, próximos passos e pendências) e em **10 marcações**: dificuldade de se locomover, dificuldade de ir ao posto, pessoa com deficiência, precisa de atendimento médico, uso contínuo de remédio ou fralda, precisa de acompanhante, melhor horário, problema com benefício, problema com documentos e urgência social.
4. **Guarda só as marcações que o agente confirmar** (`fato_necessidade_caso`): nem o texto, nem o áudio, nem o dado clínico.

| Teste | O que mostra |
|---|---|
| Teste 1 | Anotação digitada da Dona Cida, com dado clínico que o filtro remove |
| Teste 2 | Outros exemplos, inclusive fala solta e sem pontuação |
| Teste 3 | Anotação falada pelo microfone (clique em *Permitir* e depois em **Parar e organizar**) |
| Teste 4 | Áudio gravado no celular, enviado como arquivo |

Sem `ANTHROPIC_API_KEY` funciona só com regras. Com a chave, o Claude recebe apenas o texto já filtrado. Na primeira vez, o modelo de transcrição é baixado, o que leva alguns minutos.

---

## 6. servidor_whatsapp_colab

Liga o app ao WhatsApp de verdade, seguindo o manual da Cloud API da Meta. Sobe o servidor (`servidor_whatsapp.py`) no Colab e cria um endereço público HTTPS com o Cloudflare Tunnel.

**Fluxo do lembrete:** o agente salva o encaminhamento → a pessoa recebe o **texto** (mensagem-modelo) com o botão **Ouvir em áudio** → toca no botão (ou manda OUVIR) → recebe a **mensagem de voz**.

| Seção | O que faz |
|---|---|
| 1. Drive e instalação | Acha `servidor_whatsapp.py` e `voz.py` no Drive e instala as bibliotecas |
| 2. Segredos | `WA_VERIFY_TOKEN`, `WA_APP_SECRET`, `WA_ACCESS_TOKEN` e `WA_PHONE_ID` nos Secrets. Sem os dois últimos, roda em modo demonstração |
| 3. Teste sem a Meta | Simula o que a Meta manda: verificação, POST sem assinatura (401), lembrete, toque no botão, mensagem repetida, PARAR e foto |
| 4. Servidor e endereço público | Sobe o servidor e mostra a URL do webhook para colar no painel da Meta |
| 5. Mensagem-modelo | Texto do modelo `lembrete_encaminhamento`, para cadastrar uma vez na Meta |
| 6. Mandar o lembrete | Envia para um celular cadastrado no painel. Enquanto o modelo não é aprovado, usa a janela de 24 h (plano B) |
| 7. Acompanhar | Envios e status de entrega |
| 8. Desligar | Para o servidor e o túnel |

**Segurança e LGPD:** valida a assinatura `X-Hub-Signature-256`, não duplica mensagens, respeita PARAR / VOLTAR, mascara o telefone no log, guarda o telefone como hash, apaga conversas em 30 dias e limita os envios por pessoa.

[← Voltar para o README principal](../README.md)
