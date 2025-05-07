from flask import Flask
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

import os
import datetime
import io
import contextlib

app = Flask(__name__)

@app.route('/')
def ejecutar_busqueda():
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        try:
            buscar_ugl()
        except Exception as e:
            print(f"⚠️ Error durante ejecución: {e}")
    return f"<h3>Resultado de la ejecución:</h3><pre>{salida.getvalue()}</pre>"


def buscar_ugl():
    # Instala automáticamente el chromedriver correcto si no está
    chromedriver_autoinstaller.install()

    opciones = webdriver.ChromeOptions()
    opciones.add_argument('--headless')
    opciones.add_argument('--no-sandbox')
    opciones.add_argument('--disable-dev-shm-usage')
    opciones.add_argument('--disable-gpu')
    opciones.add_argument('--window-size=1920,1080')

    palabras_clave = ['kit', 'neuro', 'neurocirugía', 'estimulador', 'batería',
                      'electrodos', 'neuroestimulador', 'bomba', 'intratecal']

    destinos = [
        "UGL II Corrientes", "UGL VII La Plata", "UGL IX Rosario", "UGL XIII Chaco",
        "UGL XIV Entre Ríos", "UGL XV Santa Fé", "UGL XVIII Misiones", "UGL XXIII Formosa",
        "UGL XXXIV Concordia", "Policlínico PAMI 1", "Policlínico PAMI 2"
    ]

    fecha_busqueda = datetime.datetime.now().day
    resultados = []

    for destino in destinos:
        print(f"\n🔍 Buscando en: {destino}")

        driver = webdriver.Chrome(options=opciones)
        wait = WebDriverWait(driver, 10)

        try:
            driver.get("https://prestadores.pami.org.ar/result.php?c=7-5&par=2")

            select_destino = Select(wait.until(EC.presence_of_element_located((By.ID, "destino_compra"))))
            select_destino.select_by_visible_text(destino)

            campo_desde = driver.find_element(By.ID, 'fecha_post')
            campo_desde.click()
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'ui-datepicker-calendar')))
            dia_element = driver.find_element(By.XPATH, f"//a[text()='{fecha_busqueda}']")
            dia_element.click()

            campo_hasta = driver.find_element(By.ID, 'fecha_ant')
            campo_hasta.click()
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'ui-datepicker-calendar')))
            dia_element_hasta = driver.find_element(By.XPATH, f"//a[text()='{fecha_busqueda}']")
            dia_element_hasta.click()

            driver.find_element(By.ID, 'srchBtn').click()

            try:
                wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="resultados"]/table')))
                tabla = driver.find_element(By.XPATH, '//*[@id="resultados"]/table')
                filas = tabla.find_elements(By.TAG_NAME, 'tr')

                for fila in filas:
                    columnas = fila.find_elements(By.TAG_NAME, 'td')
                    if len(columnas) >= 5:
                        detalle = columnas[4].text.lower().strip()
                        if any(palabra in detalle for palabra in palabras_clave):
                            numero = columnas[0].text.strip()
                            ugl = columnas[2].text.strip()
                            resultados.append((numero, ugl, destino))
            except:
                print("⚠️ No se encontraron resultados.")

        except Exception as e:
            print(f"❌ Error en destino {destino}: {e}")

        driver.quit()

    if resultados:
        for numero, ugl, destino in resultados:
            print(f"✅ Destino: {destino} | Número: {numero} | UGL: {ugl}")
    else:
        print("⚠️ No se encontraron coincidencias en ningún destino.")

    print("\n✔ Búsqueda completada.")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
