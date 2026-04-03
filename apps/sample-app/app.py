# Create a simple Python app with deliberate issues:
cat > app.py <<'EOF'
import flask
import requests

app = flask.Flask(__name__)

# DELIBERATE: hardcoded secret — Gitleaks will find this
DATABASE_PASSWORD = "SuperSecret123!"
API_KEY = "sk-1234567890abcdef"

@app.route('/')
def hello():
    return "Hello Security Lab!"

if __name__ == '__main__':
    app.run(debug=True)
