import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Buscador Licitaciones UGL", layout="wide")
st.title("🔎 Monitoreo de Licitaciones PAMI")
st.subheader("Neuromodulación y Alta Complejidad")

# --- Parámetros de búsqueda ---
palabras_clave = [
    'kit', 'neuro', 'neurocirugía', 'estimulador', 'batería',
    'electrodos', 'neuroestimulador', 'bomba', 'intratecal',
    'Prodigy','eterna','burst','incontinencia','espiculado','liberta',
    'DRG', 'proclaim','abbott','infinity','IOS','direccional','penta',
    'incontinencia','morfina','baclofeno','refill','espasticidad',
    'DBS','parkinson','oncologico','medular','recambio','sacro',
    'epidural','ganglio','corriente','cerebral','electrodo','profundo'
]

destinos = [
    "UGL II Corrientes", "UGL IX Rosario", "UGL XIII Chaco",
    "UGL XIV Entre Ríos", "UGL XV Santa Fé", "UGL XVIII Misiones",
    "UGL XXIII Formosa", "UGL XXXIV Concordia"
]

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # IMPORTANTE: En Streamlit Cloud, Chromium se instala en esta ruta
    options.binary_location = "/usr/bin/chromium"
    
    # Ya no necesitamos Service(ChromeDriverManager().install())
    # porque el driver viene en el paquete 'chromium-driver'
    return webdriver.Chrome(options=options)

# --- Interfaz de Streamlit ---
if st.button('🚀 Iniciar Búsqueda en PAMI'):
    todos_los_resultados = []
    progreso = st.progress(0)
    
    hoy_dia = (datetime.datetime.now()).day
    # Ajustado a 1 día para búsqueda estándar, puedes cambiarlo
    mañana_dia = (datetime.datetime.now() + datetime.timedelta(days=5)).day 

    driver = configurar_driver()
    
    try:
        for i, destino in enumerate(destinos):
            st.write(f"Buscando en: **{destino}**...")
            progreso.progress((i + 1) / len(destinos))
            
            driver.get("https://prestadores.pami.org.ar/result.php?c=7-5&par=2")
            wait = WebDriverWait(driver, 15)

            # Selección de UGL
            select_destino = Select(wait.until(EC.presence_of_element_located((By.ID, "destino_compra"))))
            select_destino.select_by_visible_text(destino)

            # Selección de fechas (Desde/Hasta)
            for campo_id in ['fecha_post', 'fecha_ant']:
                campo = driver.find_element(By.ID, campo_id)
                campo.click()
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'ui-datepicker-calendar')))
                # Intentamos buscar el día (esto puede fallar si el día no está en el mes actual)
                try:
                    dia = hoy_dia if campo_id == 'fecha_post' else mañana_dia
                    dia_element = driver.find_element(By.XPATH, f"//a[text()='{dia}']")
                    dia_element.click()
                except:
                    st.warning(f"No se pudo seleccionar el día {dia} en el calendario.")

            driver.find_element(By.ID, 'srchBtn').click()

            try:
                wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="resultados"]/table')))
                tabla = driver.find_element(By.XPATH, '//*[@id="resultados"]/table')
                filas = tabla.find_elements(By.TAG_NAME, 'tr')

                for fila in filas:
                    columnas = fila.find_elements(By.TAG_NAME, 'td')
                    if len(columnas) >= 5:
                        detalle_texto = columnas[4].text.lower().strip()
                        if any(palabra in detalle_texto for palabra in palabras_clave):
                            todos_los_resultados.append({
                                "Número": columnas[0].text.strip(),
                                "UGL": columnas[2].text.strip(),
                                "Destino": destino,
                                "Detalle": columnas[4].text.strip()
                            })
            except:
                continue

        driver.quit()

        # --- Mostrar Resultados ---
        if todos_los_resultados:
            st.success(f"¡Se encontraron {len(todos_los_resultados)} coincidencias!")
            df = pd.DataFrame(todos_los_resultados)
            st.table(df) # Muestra una tabla limpia
        else:
            st.info("No se encontraron licitaciones con esas palabras clave para las fechas seleccionadas.")

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
        if 'driver' in locals(): driver.quit()
