import os
import boto3
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configurações MinIO
s3_client = boto3.client(
    's3',
    endpoint_url=f"http://{os.getenv('MINIO_ENDPOINT', 'localhost:9000')}",
    aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'admin'),
    aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'password123'),
)

BUCKET_NAME = 'videos'

# Cria o bucket se não existir
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
        return jsonify({"error": "Nome vazio"}), 400

    filename = secure_filename(file.filename)
    
    try:
        # Upload direto para o MinIO
        s3_client.upload_fileobj(
            file,
            BUCKET_NAME,
            filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        return jsonify({"message": f"Vídeo {filename} armazenado no MinIO!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')