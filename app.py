from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    # Aqui você poderia buscar os vídeos do banco de dados para o histórico
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)