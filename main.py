from flask import Flask, request, jsonify, send_file
import pandas as pd
import os
import time 
# importacion de clase 
from logic.valid_cronos.VlCronos import VlKronos

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return jsonify({"mensaje": "¡Hola, mundo!"})

def procesar_archivo(file):
    """
    Procesa un archivo y lo convierte en un DataFrame según reglas específicas.
    :param file: Archivo cargado.
    :return: Tupla con (clave, DataFrame).
    """
    filename = file.filename

    if filename == "Solicitudes_vac.xls":
        df = pd.read_excel(file, skiprows=6, engine="xlrd" )  # Saltar las primeras 6 filas
    elif filename == "Solicitudes _lic.xls":
        df = pd.read_excel(file, skiprows=6, engine="xlrd" )  # Saltar las primeras 6 filas
    elif filename == "lista_incapacidades.xlsx":
        df = pd.read_excel(file, skiprows=1, engine="openpyxl" )  # Saltar la primera fila
    elif filename == "Headcount.xlsx":
        df = pd.read_excel(file, engine="openpyxl")  # No se saltan filas
    else:
        raise ValueError(f"Nombre de archivo no reconocido: {filename}")

    return filename, df

@app.route('/validaciones-kronos', methods=['POST'])
def procesar_documentos():
    time_start = time.time()
    """
    Endpoint para procesar archivos y guardarlos en un diccionario.
    """
    if 'files' not in request.files:
        return jsonify({"error": "No se encontraron archivos en la solicitud"}), 400

    files = request.files.getlist('files')
    dataframes = {
        "Solicitudes_vac.xls":0,
        "Solicitudes _lic.xls":0,
        "lista_incapacidades.xlsx":0,
        "Headcount.xlsx":0
    }

    for file in files:
        try:
            clave, df = procesar_archivo(file)
            dataframes[clave] = df
        except Exception as e:
            return jsonify({"error": f"Error al procesar el archivo {file.filename}: {str(e)}"}), 400

    # Aquí puedes usar el diccionario `dataframes` para procesar los DataFrames
    validate = VlKronos(dataframes["Solicitudes_vac.xls"], 
                        dataframes["Solicitudes _lic.xls"],
                        dataframes["lista_incapacidades.xlsx"],
                        dataframes["Headcount.xlsx"])
    
    # proceso de validacion 
    result = validate.validation()

    time_end = time.time()


    execution_time = time_end - time_start  # Calcular el tiempo de ejecución
    print(result.info())

    # Guardar el DataFrame en un archivo CSV
    output_file = 'CO_Novedades.csv'
    result.to_csv(output_file, index=False, sep=';')

    # Guarda el DataFrame resultante en un archivo CSV
    result.to_csv('CO_Novedades.csv', index=False, sep=';')
    return jsonify({
        "mensaje": "Archivos procesados correctamente",
        "dataframes": list(dataframes.keys()),
        "tiempo_ejecucion": f"{execution_time:.4f} segundos", # Tiempo de ejecución con 4 decimales
        "Novedades_file":f"http://127.0.0.1:5000/descargar/{output_file}"
    })

@app.route('/descargar/<filename>', methods=['GET'])
def descargar_archivo(filename):
    """
    Endpoint para descargar el archivo generado.
    """
    file_path = os.path.join(os.getcwd(), filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "Archivo no encontrado"}), 404

    return send_file(file_path, mimetype='text/csv', as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True)