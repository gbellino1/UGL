import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
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

destinos = ["UGL IX Rosario", "UGL II Corrientes"]

config_ugls = {
    "UGL II Corrientes": {"cod": "2", "ext": "docx"},
    "UGL IX Rosario": {"cod": "9", "ext": "pdf"},
    "UGL XIII Chaco": {"cod": "13", "ext": "docx"}, 
    "UGL XIV Entre Ríos": {"cod": "14", "ext": "doc"},
    "UGL XV Santa Fé": {"cod": "15", "ext": "doc"},
    "UGL XVIII Misiones": {"cod": "18", "ext": "pdf"},
    "UGL XXIII Formosa": {"cod": "23", "ext": "pdf"},
    "UGL XXXIV Concordia": {"cod": "34", "ext": "docx"} 
}

def configurar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/usr/bin/chromium"
    return webdriver.Chrome(options=options)

# --- Interfaz de Streamlit ---
if st.button('🚀 Iniciar Búsqueda en PAMI'):
    todos_los_resultados = []
    progreso = st.progress(0)
    
    hoy = datetime.datetime.now()
    hoy_dia = hoy.day
    mañana_dia = (hoy + datetime.timedelta(days=5)).day 

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

            # Selección de fechas
            for campo_id in ['fecha_post', 'fecha_ant']:
                campo = driver.find_element(By.ID, campo_id)
                campo.click()
                wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'ui-datepicker-calendar')))
                try:
                    dia = hoy_dia if campo_id == 'fecha_post' else mañana_dia
                    dia_element = driver.find_element(By.XPATH, f"//a[text()='{dia}']")
                    dia_element.click()
                except:
                    st.warning(f"No se pudo seleccionar el día {dia} en {destino}.")

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
                            nro_completo = columnas[0].text.strip()
                            nro_solo = nro_completo.split('/')[0]
                            
                            conf = config_ugls.get(destino, {"cod": "9", "ext": "pdf"})
                            cod_ugl = conf["cod"]
                            ext = conf["ext"]
                            
                            base_url = "https://institucional.pami.org.ar/compras/archivos"
                            link_v1 = f"{base_url}/CAB_{nro_solo}_2026_{cod_ugl}_1.{ext}"
                            link_v2 = f"{base_url}/CAB_{nro_solo}_2026_{cod_ugl}_2.{ext}"
                            
                            todos_los_resultados.append({
                                "Número": nro_completo,
                                "UGL": columnas[2].text.strip(),
                                "Detalle": columnas[4].text.strip(),
                                "Fecha": columnas[5].text.strip(),
                                "Link Principal": link_v1,
                                "Link Alternativo": link_v2
                            })
            except Exception as e:
                continue

        driver.quit()

        # --- Mostrar Resultados ---
        if todos_los_resultados:
            st.success(f"¡Se encontraron {len(todos_los_resultados)} coincidencias!")
            df = pd.DataFrame(todos_los_resultados)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No se encontraron licitaciones con esas palabras clave.")

    except Exception as e:
        st.error(f"Ocurrió un error general: {e}")
        if 'driver' in locals(): driver.quit()
