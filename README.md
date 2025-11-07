# Gerador de Relatórios Técnicos ABNT

## Visão Geral
Aplicação web Streamlit que transforma descrições de atividades do ClickUp em relatórios técnicos profissionais seguindo as normas ABNT, utilizando Google Gemini AI.

## Data de Criação
07 de novembro de 2025

## Funcionalidades Principais

### 1. Interface Streamlit
- Interface limpa e moderna em português
- Layout responsivo com sidebar para configurações
- Área de texto grande para colar descrições 

### 2. Seleção de Data
- Seletores de mês e ano na barra lateral
- Cálculo automático do último dia útil (segunda a sexta) do mês selecionado
- Exibição da data formatada em DD/MM/YYYY

### 3. Geração de Relatórios com Gemini AI
- Integração com Google Gemini API (modelo gemini-2.5-flash)
- Prompt do sistema em português seguindo normas ABNT NBR 10719/2015
- Estrutura obrigatória dos relatórios:
  - Nome da Atividade
  - Descrição da atividade
  - Descrição do desenvolvimento de forma cronológica
  - Descrição dos testes executados
  - Descrição dos procedimentos com "erros" e "acertos"
  - Justificativa
  - Evidências
  - Ferramentas utilizadas
- Estilo formal, impessoal, com voz passiva ou 3ª pessoa
- Mínimo de bullet points para evitar aparência de texto gerado por LLM

### 4. Resiliência da API
- Lógica de retry com exponential backoff (até 5 tentativas)
- Tratamento robusto de erros

### 5. Funcionalidades Simuladas
- Export para PDF (simulado - requer implementação real com fpdf2 ou reportlab)
- Envio por email (simulado - requer implementação real com smtplib)
- Mensagens claras sobre a natureza simulada dessas funções

## Arquitetura Técnica

### Arquivo Principal
- `report_writer_app.py` - Arquivo único contendo toda a aplicação

### Constantes do Sistema
- `MONTH_NAMES` - Tupla com nomes dos meses em português
- `MONTH_NUMBERS` - Tupla com números dos meses (1-12)
- Uso de tuplas no nível do módulo para evitar problemas de virtualização do Streamlit

### Funções Principais
1. `get_last_business_day(year, month)` - Calcula o último dia útil do mês
2. `call_gemini_with_retry(client, prompt, system_instruction, max_retries)` - Chama API Gemini com retry
3. `generate_report(clickup_description, report_date)` - Gera relatório completo
4. `main()` - Função principal da interface Streamlit

## Configuração

### Variáveis de Ambiente Necessárias
- `gemini-api-key` - Chave de API do Google Gemini (obtida em https://aistudio.google.com/app/apikey)

Observação: a aplicação foi modificada para ler exclusivamente a variável de ambiente com o nome literal `gemini-api-key` e NÃO carrega arquivos `.env` locais.

### Execução Local
```bash
streamlit run report_writer_app.py --server.port 5000
```

### Workflow Configurado
- Nome: `streamlit_app`
- Comando: `streamlit run report_writer_app.py --server.port 5000`
- Porta: 5000 (webview)

## Dependências
- `streamlit` - Framework web
- `google-genai` - Cliente da API Gemini
- Bibliotecas Python padrão: `os`, `time`, `math`, `datetime`, `calendar`

## Correções Importantes

### Problema de Virtualização do Seletor de Mês (RESOLVIDO)
**Problema:** O seletor de mês do Streamlit não exibia todos os 12 meses (Novembro e Dezembro estavam faltando) devido a problema de virtualização quando listas eram recriadas a cada rerun.

**Solução:** Substituição de listas dinâmicas por tuplas constantes no nível do módulo:
- Criação de `MONTH_NAMES` e `MONTH_NUMBERS` como tuplas imutáveis
- Uso direto dessas tuplas no `st.selectbox` com `format_func`
- Prevenção de recriação de listas em cada rerun

## Normas ABNT Implementadas
- NBR 10719:2015 (relatórios técnicos)
- NBR 6023:2018 (referências bibliográficas)
- NBR 6024:2012 (numeração progressiva)
- NBR 6027:2012 (sumário)
- NBR 6028:2021 (resumo)
- NBR 10520:2002 (citações)
- NBR 14724:2011 (estrutura de trabalhos acadêmicos)

## Segurança
- Chave API gerenciada via variáveis de ambiente (Replit Secrets)
- Sem exposição de credenciais no código
- Integração segura com blueprint python_gemini do Replit

## Melhorias Futuras Sugeridas
1. Implementar geração real de PDF usando fpdf2 ou ReportLab
2. Adicionar envio real de email via SMTP
3. Implementar logging e persistência de relatórios gerados
4. Adicionar histórico de relatórios
5. Permitir customização de templates de relatório
6. Processamento em lote de múltiplos cards 

## Status do Projeto
✅ **Completo e funcional** - Pronto para uso após configuração da GEMINI_API_KEY

## Testes Realizados
- ✅ Interface carrega corretamente
- ✅ Seletor de mês mostra todos os 12 meses
- ✅ Seletor de ano funciona corretamente
- ✅ Cálculo de último dia útil preciso
- ✅ Campos de entrada funcionais
- ✅ Integração com Gemini API configurada (requer chave API para teste completo)
