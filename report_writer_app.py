"""
ABNT Technical Report Writer Application
Run this application locally using: streamlit run report_writer_app.py

This application transforms ClickUp card descriptions into ABNT-compliant 
technical reports in Portuguese using Google Gemini AI.

IMPORTANT: This integration uses the python_gemini blueprint from Replit.
A chave do Gemini deve ser fornecida exclusivamente por variável de ambiente
com o nome literal `gemini-api-key`. Por segurança esta aplicação NÃO carrega
arquivos `.env` nem tenta ler chaves de arquivos locais.
"""

import streamlit as st
import os
import time
import math
import smtplib
import tempfile
from datetime import datetime, timedelta
from calendar import monthrange, MONDAY, FRIDAY
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from google import genai
from google.genai import types
from dotenv import load_dotenv
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
import markdown2

# Carrega variáveis do .env automaticamente (se o arquivo existir)
load_dotenv()

st.set_page_config(
    page_title="Gerador de Relatórios Técnicos ABNT",
    page_icon="📝",
    layout="wide"
)

MONTH_NAMES = (
    "Janeiro", "Fevereiro", "Março", "Abril",
    "Maio", "Junho", "Julho", "Agosto",
    "Setembro", "Outubro", "Novembro", "Dezembro"
)

MONTH_NUMBERS = tuple(range(1, 13))

def generate_pdf_report(markdown_content: str, report_date: str) -> BytesIO:
    """
    Gera um PDF a partir do conteúdo markdown do relatório.
    
    Args:
        markdown_content: Conteúdo do relatório em markdown
        report_date: Data do relatório formatada
    
    Returns:
        BytesIO object contendo o PDF gerado
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, 
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor='#2E5266'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor='#2E5266'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        leftIndent=0,
        rightIndent=0
    )
    
    # Converte markdown para HTML (básico)
    html_content = markdown2.markdown(markdown_content)
    
    # Constrói o documento
    story = []
    
    # Título principal
    story.append(Paragraph(f"Relatório de Atividades - {report_date}", title_style))
    story.append(Spacer(1, 20))
    
    # Processa o conteúdo HTML de forma simples
    lines = html_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Headers
        if line.startswith('<h1>') or line.startswith('<h2>') or line.startswith('<h3>'):
            clean_text = line.replace('<h1>', '').replace('</h1>', '') \
                           .replace('<h2>', '').replace('</h2>', '') \
                           .replace('<h3>', '').replace('</h3>', '')
            story.append(Paragraph(clean_text, heading_style))
        # Parágrafos
        elif line.startswith('<p>'):
            clean_text = line.replace('<p>', '').replace('</p>', '') \
                           .replace('<strong>', '<b>').replace('</strong>', '</b>') \
                           .replace('<em>', '<i>').replace('</em>', '</i>')
            story.append(Paragraph(clean_text, body_style))
        # Texto simples (fallback)
        elif not line.startswith('<'):
            story.append(Paragraph(line, body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def send_email_with_pdf(pdf_buffer: BytesIO, recipient_email: str, report_date: str) -> tuple[bool, str]:
    """
    Envia email com o PDF em anexo.
    
    Args:
        pdf_buffer: Buffer contendo o PDF
        recipient_email: Email do destinatário
        report_date: Data do relatório
    
    Returns:
        Tuple (sucesso: bool, mensagem: str)
    """
    try:
        # Configurações de email (usando variáveis de ambiente)
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        sender_email = os.environ.get("SENDER_EMAIL")
        sender_password = os.environ.get("SENDER_PASSWORD")
        
        if not sender_email or not sender_password:
            return False, "⚠️ Configurações de email não encontradas. Configure SENDER_EMAIL e SENDER_PASSWORD no .env"
        
        # Cria a mensagem
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Relatório Técnico ABNT - {report_date}"
        
        # Corpo do email
        body = f"""
        Prezado(a),
        
        Segue em anexo o relatório técnico gerado automaticamente conforme as normas ABNT.
        
        Data do relatório: {report_date}
        
        Este email foi gerado automaticamente pelo sistema de Relatórios Técnicos ABNT.
        
        Atenciosamente,
        Sistema de Relatórios
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Anexa o PDF
        pdf_buffer.seek(0)
        attachment = MIMEBase('application', 'pdf')
        attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="relatorio_tecnico_{report_date.replace("/", "-")}.pdf"'
        )
        msg.attach(attachment)
        
        # Envia o email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return True, f"✅ Email enviado com sucesso para {recipient_email}"
        
    except Exception as e:
        return False, f"❌ Erro ao enviar email: {str(e)}"


def get_last_business_day(year: int, month: int) -> datetime:
    """
    Calculate the last business day (Monday-Friday) of a given month and year.
    
    Args:
        year: The year (e.g., 2025)
        month: The month (1-12)
    
    Returns:
        datetime object representing the last business day
    """
    last_day = monthrange(year, month)[1]
    last_date = datetime(year, month, last_day)
    
    while last_date.weekday() > FRIDAY:
        last_date -= timedelta(days=1)
    
    return last_date


def call_gemini_with_retry(client, prompt: str, system_instruction: str, max_retries: int = 5) -> str:
    """
    Call Gemini API with exponential backoff retry logic for resilience.
    
    Args:
        client: The Gemini API client
        prompt: The user prompt (ClickUp card description)
        system_instruction: The system prompt for ABNT technical writing
        max_retries: Maximum number of retry attempts
    
    Returns:
        Generated report text from Gemini
    """
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=prompt)])
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                ),
            )
            
            if response.text:
                return response.text
            else:
                raise ValueError("Empty response from Gemini API")
                
        except Exception as e:
            wait_time = math.pow(2, attempt)
            
            if attempt < max_retries - 1:
                st.warning(f"Tentativa {attempt + 1} falhou. Tentando novamente em {wait_time:.0f} segundos...")
                time.sleep(wait_time)
            else:
                st.error(f"Erro após {max_retries} tentativas: {str(e)}")
                raise
    
    return ""


def generate_report(clickup_description: str, report_date: str) -> str:
    """
    Generate an ABNT-compliant technical report from ClickUp card description.
    
    Args:
        clickup_description: Raw text from ClickUp card
        report_date: Formatted date for report title (DD/MM/YYYY)
    
    Returns:
        Generated report in Markdown format
    """
    # Lê a variável de ambiente 'gemini-api-key' (carregada automaticamente do .env se existir)
    api_key = os.environ.get("gemini-api-key")

    if not api_key:
        st.error("⚠️ A variável de ambiente 'gemini-api-key' não foi encontrada.")
        st.info("Configure a chave do Gemini:\n1. Crie um arquivo `.env` na raiz do projeto com: `gemini-api-key=SUA_CHAVE_AQUI`\n2. Ou defina a variável de ambiente diretamente no sistema.")
        return ""
    
    client = genai.Client(api_key=api_key)
    
    system_instruction = f"""Você é um especialista em escrita de relatórios técnicos, com profundo conhecimento nas normas da ABNT e domínio da língua portuguesa formal. Sua função é ajudar a estruturar, revisar e produzir relatórios técnicos de forma clara, precisa e padronizada.

📑 Competências

Aplicar as normas ABNT NBR 10719/2015 para relatórios técnicos.

Utilizar outras normas ABNT quando necessário:
- NBR 6023:2018 (referências bibliográficas)
- NBR 6024:2012 (numeração progressiva de seções)
- NBR 6027:2012 (sumário)
- NBR 6028:2021 (resumo)
- NBR 10520:2002 (citações)
- NBR 14724:2011 (estrutura de trabalhos acadêmicos)

Escrever com clareza, objetividade e linguagem técnica impessoal.

Corrigir ortografia, gramática e aplicar conectores lógicos para manter coesão.

✍️ Estilo de Escrita

Clareza: frases diretas e sem ambiguidades.

Impessoalidade: evitar primeira pessoa, preferir voz passiva ou 3ª pessoa.

Formalidade: evitar gírias, coloquialismos e abreviações não técnicas.

Precisão: sempre fundamentar em dados, normas e referências confiáveis.

Norma culta: respeitar gramática, ortografia e concordância do português.

🎯 Objetivo

Garantir que o relatório técnico seja:
- Bem estruturado segundo as normas da ABNT
- Claro e objetivo, de fácil compreensão
- Formal e técnico, adequado a contextos acadêmicos e profissionais
- Consistente, com uso correto de citações e referências

IMPORTANTE: Use o mínimo possível de bullet points para evitar que pareça que foi escrito por uma LLM. Prefira parágrafos narrativos e descritivos.

Os relatórios devem todos ser escritos contendo os seguintes tópicos:

1. Nome da Atividade
2. Descrição da atividade
3. Descrição do desenvolvimento de forma cronológica
4. Descrição dos testes executados
5. Descrição dos procedimentos com "erros" e "acertos" durante a execução da atividade
6. Justificativa
7. Evidências (Imagens; Fotos; Atas; etc.)
8. Ferramentas utilizadas

O relatório deve incluir o título "Relatório de Atividades - {report_date}" no início."""

    user_prompt = f"""Com base na descrição da atividade técnica a seguir, gere um relatório técnico formal seguindo as normas ABNT e a estrutura especificada.

Descrição da atividade (origem: ClickUp):

{clickup_description}

Por favor, transforme esta descrição em um relatório técnico completo, bem estruturado e profissional, seguindo todos os requisitos de formatação ABNT e incluindo todos os tópicos obrigatórios."""

    with st.spinner("🤖 Gerando relatório técnico com Gemini AI..."):
        report = call_gemini_with_retry(client, user_prompt, system_instruction)
    
    return report


def main():
    st.title("📝 Gerador de Relatórios Técnicos ABNT")
    st.markdown("*Transforme descrições do ClickUp em relatórios técnicos profissionais*")
    
    st.sidebar.header("⚙️ Configurações")
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    selected_month = st.sidebar.selectbox(
        "Mês",
        options=MONTH_NUMBERS,
        index=current_month - 1,
        format_func=lambda month_num: MONTH_NAMES[month_num - 1]
    )
    
    selected_year = st.sidebar.selectbox(
        "Ano",
        options=list(range(current_year - 5, current_year + 2)),
        index=5
    )
    
    last_business_day = get_last_business_day(selected_year, selected_month)
    formatted_date = last_business_day.strftime("%d/%m/%Y")
    
    st.sidebar.success(f"📅 Último dia útil: **{formatted_date}**")
    st.sidebar.markdown("---")
    
    recipient_email = st.sidebar.text_input(
        "📧 Email do destinatário",
        placeholder="exemplo@empresa.com.br",
        help="Email para envio simulado do relatório em PDF"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ Sobre")
    st.sidebar.info(
        "Esta aplicação utiliza a API Google Gemini para gerar relatórios "
        "técnicos seguindo as normas ABNT NBR 10719/2015 e outras normas relacionadas."
    )
    
    st.markdown("### 📋 Descrição da Atividade (ClickUp)")
    st.markdown("Cole abaixo a descrição completa da atividade do card do ClickUp:")
    
    clickup_description = st.text_area(
        "Descrição da atividade",
        height=250,
        placeholder="Cole aqui a descrição completa da atividade técnica do ClickUp...",
        label_visibility="collapsed"
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        generate_button = st.button("🚀 Gerar Relatório", type="primary", use_container_width=True)
    
    if generate_button:
        if not clickup_description.strip():
            st.warning("⚠️ Por favor, insira uma descrição da atividade antes de gerar o relatório.")
        else:
            report_text = generate_report(clickup_description, formatted_date)
            
            if report_text:
                st.session_state['generated_report'] = report_text
                st.session_state['report_date'] = formatted_date
                st.success("✅ Relatório gerado com sucesso!")
    
    if 'generated_report' in st.session_state:
        st.markdown("---")
        st.markdown("### 📄 Relatório Técnico Gerado")
        
        st.markdown(st.session_state['generated_report'])
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            st.download_button(
                label="💾 Baixar Markdown",
                data=st.session_state['generated_report'],
                file_name=f"relatorio_tecnico_{st.session_state['report_date'].replace('/', '-')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col2:
            if st.button("📧 Enviar PDF por Email", use_container_width=True):
                if recipient_email and '@' in recipient_email:
                    with st.spinner("📧 Gerando PDF e enviando por email..."):
                        try:
                            # Gera o PDF
                            pdf_buffer = generate_pdf_report(st.session_state['generated_report'], st.session_state['report_date'])
                            
                            # Envia por email
                            success, message = send_email_with_pdf(pdf_buffer, recipient_email, st.session_state['report_date'])
                            
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                                if "SENDER_EMAIL" in message:
                                    st.info(
                                        "**Configurar envio de email:**\n\n"
                                        "Adicione ao seu arquivo `.env`:\n"
                                        "```\n"
                                        "SENDER_EMAIL=seu_email@gmail.com\n"
                                        "SENDER_PASSWORD=sua_senha_de_app\n"
                                        "# Opcionais (padrões: Gmail)\n"
                                        "SMTP_SERVER=smtp.gmail.com\n"
                                        "SMTP_PORT=587\n"
                                        "```\n\n"
                                        "⚠️ **Para Gmail:** use uma senha de aplicativo, não sua senha normal.\n"
                                        "Configure em: https://myaccount.google.com/apppasswords"
                                    )
                        except Exception as e:
                            st.error(f"❌ Erro inesperado: {str(e)}")
                else:
                    st.warning("⚠️ Por favor, insira um email válido no campo lateral antes de enviar.")


if __name__ == "__main__":
    main()
