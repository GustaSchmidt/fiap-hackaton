import os
import boto3
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configurações do MinIO via variáveis de ambiente (definidas no docker-compose)
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'admin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'password123')
BUCKET_NAME = 'videos'

# Inicializa o cliente S3 compatível com MinIO
s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1' # Valor padrão necessário para o boto3
)

# Garante que o bucket existe ao iniciar
try:
    s3_client.head_bucket(Bucket=BUCKET_NAME)
except:
    s3_client.create_bucket(Bucket=BUCKET_NAME)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nome do arquivo vazio"}), 400

    filename = secure_filename(file.filename)
    
    try:
        # Upload direto para o MinIO sem salvar localmente
        s3_client.upload_fileobj(
            file,
            BUCKET_NAME,
            filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        return jsonify({"message": f"Vídeo {filename} armazenado com sucesso no MinIO!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list-videos', methods=['GET'])
def list_videos():
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                files.append({
                    "name": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].strftime('%d/%m/%Y %H:%M')
                })
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)