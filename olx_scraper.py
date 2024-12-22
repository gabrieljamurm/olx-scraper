# Importação das bibliotecas necessárias
# --------------------------------------
from selenium import webdriver  # Para controle do navegador
from selenium.webdriver.common.by import By  # Para localizar elementos
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta  # Para trabalhar com datas e horários
import time  # Para gerenciar intervalos e cronômetro
from twilio.rest import Client  # Para enviar notificações via WhatsApp
import sys  # Para permitir saída controlada
import json  # Para manipular JSON extraído do HTML
from urllib.parse import urlparse  # Para validar URLs

# Suas credenciais do Twilio
TWILIO_SID = "ACee646467cc93eb3673277b60e09c5618"
TWILIO_AUTH_TOKEN = "86a405de411a2060d9a5f6c3cf54312f"
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
SEU_WHATSAPP = "whatsapp:+553194901800"

# Lista para armazenar os anúncios já notificados
anuncios_notificados = set()

# Função para validar URLs
# --------------------------------
def url_valida(url):
    try:
        resultado = urlparse(url)
        return all([resultado.scheme, resultado.netloc])
    except ValueError:
        return False

# Função 1: Buscar Anúncios na OLX usando Selenium
# --------------------------------
def buscar_anuncios():
    """
    Busca anúncios estruturados na página da OLX usando Selenium.
    Filtra os anúncios publicados nas últimas 2 horas e retorna uma lista de novos anúncios.
    """
    # URL base da OLX
    url_base = "https://www.olx.com.br/brasil?pe=5000&ps=500&q=tag+heuer+1500"
    anuncios_novos = []  # Lista para armazenar os novos anúncios
    limite_tempo = datetime.now() - timedelta(hours=2)  # Limite de tempo de 2 horas atrás

    # Configurações do Selenium
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Removido para permitir interação manual
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    for pagina in range(1, 5):  # Itera pelas 4 primeiras páginas
        try:
            url = f"{url_base}&o={pagina}"
            print(f"DEBUG: Acessando URL: {url}")
            driver.get(url)

            # Extrai JSON do script "__NEXT_DATA__"
            try:
                json_data = driver.find_element(By.ID, "__NEXT_DATA__").get_attribute("innerText")
                ads = json.loads(json_data)["props"]["pageProps"].get("ads", [])
            except Exception as e:
                print(f"DEBUG: Erro ao extrair JSON: {e}")
                ads = []

            print(f"DEBUG: {len(ads)} anúncios encontrados na página {pagina}.")

            for ad in ads:
                try:
                    titulo = ad.get("subject", "Sem título")
                    preco = ad.get("price", "Sem preço")
                    link = ad.get("url", "#")
                    data_publicacao = ad.get("date", 0)

                    # Converte data_publicacao para datetime
                    data_publicacao_dt = datetime.fromtimestamp(data_publicacao)

                    # Filtra anúncios publicados nas últimas 2 horas
                    if data_publicacao_dt >= limite_tempo and url_valida(link):
                        if link not in anuncios_notificados:
                            anuncios_novos.append((titulo, preco, link))  # Adiciona título, preço e link
                            anuncios_notificados.add(link)
                            print(f"DEBUG: Novo anúncio listado: {titulo}")
                except Exception as e:
                    print(f"DEBUG: Erro ao processar anúncio: {e}")

        except Exception as e:
            print(f"DEBUG: Erro ao acessar a página {pagina}: {e}")

    driver.quit()  # Fecha o navegador
    print(f"DEBUG: Total de anúncios novos encontrados: {len(anuncios_novos)}")
    return anuncios_novos

# Função 2: Enviar Notificações
# -----------------------------
def enviar_notificacao(anuncios):
    """
    Envia uma notificação via WhatsApp com os novos anúncios encontrados.
    Inclui o título, preço e link do anúncio.
    """
    if not anuncios:  # Verifica se há anúncios novos
        print("DEBUG: Nenhum novo anúncio para enviar notificações.")
        return  # Se não houver, não faz nada

    # Configura o cliente do Twilio
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    for titulo, preco, link in anuncios:
        try:
            print(f"DEBUG: Tentando enviar mensagem para o anúncio: {titulo}")
            # Envia a mensagem via Twilio
            message = client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                body=f"🚨 Novo anúncio encontrado:\n\nTítulo: {titulo}\nPreço: {preco}\nLink: {link}",
                to=SEU_WHATSAPP
            )
            print(f"DEBUG: Mensagem enviada com sucesso! SID: {message.sid}")
        except Exception as e:
            print(f"DEBUG: Erro ao enviar mensagem para {link}: {e}")

# Função 3: Tarefa Principal (Periodicamente Executada)
# -----------------------------------------------------
def tarefa_periodica():
    """
    Função principal que busca anúncios e envia notificações.
    """
    print("🔄 Verificando novos anúncios...")  # Log no terminal
    anuncios_novos = buscar_anuncios()  # Busca os anúncios
    enviar_notificacao(anuncios_novos)  # Envia notificações se houver novos anúncios

# Execução Controlada para Exibir Todos os Anúncios
# -------------------------------------------------
print("🚀 Monitoramento iniciado para execução controlada...")

tarefa_periodica()  # Executa a tarefa inicial

while True:
    time.sleep(60)  # Mantém o programa ativo aguardando novas execuções ou interações
    tarefa_periodica()
