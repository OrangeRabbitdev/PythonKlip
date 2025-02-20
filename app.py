from flask import Flask, jsonify, request, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import img2pdf


app = Flask(__name__)

# Función para capturar dashboards y generar el PDF
def capture_dashboards():
    # Configuración de Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ejecutar en modo headless (sin interfaz gráfica)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")  # Tamaño inicial de la ventana

    # Configuración automática de chromedriver
    service = ChromeService(ChromeDriverManager().install())

    # Inicializar el navegador
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Lista de URLs de los dashboards
    urls = [
        "https://app.klipfolio.com/published/61daedb930b345b49d75f5f6e1fe7ac6/principal-data",
        "https://app.klipfolio.com/published/429a3c2e6f292b4c504d6a7527b3189f/geo",
        "https://app.klipfolio.com/published/d7a139b1e038b1be8befb9233f04a504/tech",
        "https://app.klipfolio.com/published/104859d210f21508786a8cb4bf8b41c3/views",
        "https://app.klipfolio.com/published/083b5e4529574c3bcf3d0faabaffc8d0/analtica"
    ]

    # Capturar pantallas de cada dashboard
    screenshots = []
    for i, url in enumerate(urls):
        print(f"Capturando {url}...")
        driver.get(url)

        # Esperar a que el dashboard esté completamente cargado
        try:
            # Ejemplo: Esperar a que un elemento específico del dashboard esté visible
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "selector_del_elemento_clave"))
            )
            print("Dashboard cargado completamente.")
        except Exception as e:
            print(f"Error al esperar la carga del dashboard: {e}")

        # Obtener la altura total del contenido de la página
        total_height = driver.execute_script("return document.body.scrollHeight")

        # Ajustar el tamaño de la ventana para que coincida con la altura total
        driver.set_window_size(1920, total_height + 100)

        # Capturar la pantalla completa
        screenshot_path = f"screenshot_{i}.png"
        driver.save_screenshot(screenshot_path)
        screenshots.append(screenshot_path)
        print(f"Captura guardada como {screenshot_path}")

    # Cerrar el navegador
    driver.quit()
    print("Capturas de pantalla completadas.")

    # Combinar las imágenes en un PDF
    output_pdf = "dashboards_unificados.pdf"
    print(f"Combinando capturas en {output_pdf}...")
    with open(output_pdf, "wb") as f:
        f.write(img2pdf.convert([open(img, "rb") for img in screenshots]))

    # Limpiar las imágenes capturadas
    for img in screenshots:
        os.remove(img)
    print(f"PDF generado exitosamente: {output_pdf}")

    return output_pdf

# Ruta para ejecutar el script desde el botón HTML
@app.route('/ejecutar-script', methods=['POST'])
def ejecutar_script():
    try:
        # Ejecutar la función para capturar dashboards
        pdf_path = capture_dashboards()
        # Devolver el archivo PDF para descargar
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Ruta para servir el archivo HTML
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ejecutar Script</title>
        <style>
            #mensaje {
                margin-top: 20px;
                font-weight: bold;
            }
            .hidden {
                display: none;
            }
        </style>
    </head>
    <body>
        <h1>Generar PDF de Dashboards</h1>
        <button id="ejecutarBtn">Ejecutar Script</button>
        <p id="mensaje" class="hidden"></p>

        <script>
            document.getElementById('ejecutarBtn').addEventListener('click', function() {
                const mensaje = document.getElementById('mensaje');
                mensaje.innerText = 'Cargando...';
                mensaje.classList.remove('hidden');

                fetch('/ejecutar-script', { method: 'POST' })
                    .then(response => {
                        if (response.ok) {
                            return response.blob();
                        } else {
                            throw new Error('Error al generar el PDF');
                        }
                    })
                    .then(blob => {
                        // Crear un enlace temporal para descargar el PDF
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'dashboards_unificados.pdf';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);

                        mensaje.innerText = 'PDF generado y descargado exitosamente.';
                    })
                    .catch(error => {
                        mensaje.innerText = 'Error: ' + error.message;
                    });
            });
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 8080))  # Usa el puerto de Render.com o 5000 por defecto
    app.run(host="0.0.0.0", port=port)