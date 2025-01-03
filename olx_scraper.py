# Importação das bibliotecas necessárias
# --------------------------------------
from selenium import webdriver  # Para controle do navegador
from selenium.webdriver.common.by import By  # Para localizar elementos
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta  # Para trabalhar com datas e horários
import time  # Para gerenciar intervalos e cronômetro
import requests  # Para enviar notificações via Telegram
import sys  # Para permitir saída controlada
import json  # Para manipular JSON extraído do HTML
from urllib.parse import urlparse  # Para validar URLs
import traceback  # Para capturar e exibir erros no terminal
import chromedriver_autoinstaller

# Credenciais do Telegram
TELEGRAM_TOKEN = "7600843587:AAED5vim3LYA09022gpS6cmXrxFIiccGa-Y"
TELEGRAM_CHAT_ID = "1543695433"

# Lista para armazenar os anúncios já notificados
anuncios_notificados = set()

driver = None  # Driver do navegador inicializado globalmente

# Função para inicializar o driver
# --------------------------------
def inicializar_driver():
    global driver
    if driver is None:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Removido para permitir interação manual
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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
    # URLs base da OLX
    urls_base = [
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?pe=1500&ps=200&q=seiko",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?q=tag%20heuer%202000",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?pe=5000&ps=800&q=tag%20heuer",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?pe=5000&ps=1000&q=omega",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?q=spinnaker",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?pe=5000&ps=1000&q=breitling",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?pe=1000&ps=200&q=victorinox",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?pe=3500&ps=1000&q=omega+mission",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?pe=3500&ps=1000&q=tag+heuer+1500",
        "https://www.olx.com.br/bijouteria-relogios-e-acessorios?pe=4000&ps=1000&q=hamilton",
    ]
    anuncios_novos = []  # Lista para armazenar os novos anúncios
    limite_tempo = datetime.now() - timedelta(hours=2)  # Limite de tempo de 2 horas atrás

    inicializar_driver()  # Garante que o driver está inicializado

    for url_base in urls_base:
        iteracoes = 12 if "heuer" in url_base.lower() else 4
        for pagina in range(1, iteracoes + 1):
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

                if not ads:
                    print(f"DEBUG: Nenhum anúncio encontrado na página {pagina}, interrompendo iteração.")
                    break

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
                                anuncios_novos.append((titulo, preco, link, data_publicacao_dt.strftime('%d/%m/%Y %H:%M:%S')))
                                anuncios_notificados.add(link)
                                print(f"DEBUG: Novo anúncio listado: {titulo}")
                    except Exception as e:
                        print(f"DEBUG: Erro ao processar anúncio: {e}")

            except Exception as e:
                print(f"DEBUG: Erro ao acessar a página {pagina}: {e}")

    print(f"DEBUG: Total de anúncios novos encontrados: {len(anuncios_novos)}")
    return anuncios_novos

# Função 2: Enviar Notificações
# -----------------------------
def enviar_notificacao(anuncios):
    """
    Envia uma notificação via Telegram com os novos anúncios encontrados.
    Inclui o título, preço, data/hora e link do anúncio.
    """
    if not anuncios:  # Verifica se há anúncios novos
        print("DEBUG: Nenhum novo anúncio para enviar notificações.")
        return  # Se não houver, não faz nada

    mensagens = []
    mensagem_atual = "🚨 Novos anúncios encontrados:\n"

    for titulo, preco, link, data_hora in anuncios:
        anuncio_texto = f"\nTítulo: {titulo}\nPreço: {preco}\nData/Hora: {data_hora}\nLink: {link}\n"
        if len(mensagem_atual) + len(anuncio_texto) > 4000:  # Limite do Telegram para mensagens
            mensagens.append(mensagem_atual)
            mensagem_atual = "🚨 Novos anúncios encontrados:\n"
        mensagem_atual += anuncio_texto

    if mensagem_atual:
        mensagens.append(mensagem_atual)

    for msg in mensagens:
        try:
            print(f"DEBUG: Enviando mensagem consolidada.")
            # Envia a mensagem via Telegram
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
            )
            if response.status_code == 200:
                print(f"DEBUG: Mensagem enviada com sucesso!")
            else:
                print(f"DEBUG: Erro ao enviar mensagem: {response.text}")
            time.sleep(5)  # Aguarda 5 segundos entre os envios
        except Exception as e:
            print(f"DEBUG: Erro ao enviar mensagem consolidada: {e}")

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
print("🚀 Monitoramento iniciado para execução contínua...")

while True:
    try:
        print("🔄 Verificando novos anúncios...")
        tarefa_periodica()  # Executa a tarefa principal
    except KeyboardInterrupt:
        print("⏹ Execução interrompida manualmente. Encerrando o programa...")
        if driver:
            driver.quit()
        break
    except Exception as e:
        print(f"⚠️ Ocorreu um erro: {e}")
        traceback.print_exc()
    finally:
        # Aguarda 5 minutos antes de rodar novamente
        print("⏳ Aguardando 5 minutos para a próxima verificação...")
        time.sleep(300)

# Finaliza o driver ao encerrar o programa
if driver:
    driver.quit()
