from flask import Flask

app = Flask(__name__)

@app.route("/hello")
def hello_world():
    return "<h1>YO</h1>"












if __name__ == '__main__':
    app.run(debug=True)