from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import requests
import uvicorn

app = FastAPI()

# Simple HTML page
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Reflexive Vault</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        input, button { padding: 10px; margin: 5px; }
        input { width: 70%; }
        button { background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .result { background: #f0f0f0; padding: 15px; margin-top: 20px; border-radius: 10px; }
        .error { background: #ffe0e0; color: red; }
    </style>
</head>
<body>
    <h1>Reflexive Vault AI Agent</h1>
    <p>Ask anything to the AI agent</p>
    
    <form method="post">
        <input type="text" name="question" placeholder="Type your question here..." required>
        <button type="submit">Ask Agent</button>
    </form>
    
    {% if answer %}
    <div class="result">
        <strong>Answer:</strong> {{ answer }}
    </div>
    {% endif %}
    
    {% if error %}
    <div class="result error">
        <strong>Error:</strong> {{ error }}
    </div>
    {% endif %}
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE.replace("{% if answer %}", "<!--").replace("{{ answer }}", "").replace("{% endif %}", "-->").replace("{% if error %}", "<!--").replace("{{ error }}", "").replace("{% endif %}", "-->")

@app.post("/", response_class=HTMLResponse)
async def ask(question: str = Form(...)):
    try:
        # Call ClawRouter
        response = requests.post(
            "http://127.0.0.1:8402/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "blockrun/free",
                "messages": [{"role": "user", "content": question}],
                "max_tokens": 300
            },
            timeout=30
        )
        
        if response.status_code == 200:
            answer = response.json()["choices"][0]["message"]["content"]
            html = HTML_PAGE.replace("{% if answer %}", "").replace("{{ answer }}", answer).replace("{% endif %}", "").replace("{% if error %}", "<!--").replace("{{ error }}", "").replace("{% endif %}", "-->")
            return html
        else:
            error = f"API Error: Status {response.status_code}"
            html = HTML_PAGE.replace("{% if answer %}", "<!--").replace("{{ answer }}", "").replace("{% endif %}", "-->").replace("{% if error %}", "").replace("{{ error }}", error).replace("{% endif %}", "")
            return html
            
    except requests.exceptions.ConnectionError:
        error = "Cannot connect to ClawRouter. Make sure it's running in another terminal."
        html = HTML_PAGE.replace("{% if answer %}", "<!--").replace("{{ answer }}", "").replace("{% endif %}", "-->").replace("{% if error %}", "").replace("{{ error }}", error).replace("{% endif %}", "")
        return html
    except Exception as e:
        error = f"Error: {str(e)}"
        html = HTML_PAGE.replace("{% if answer %}", "<!--").replace("{{ answer }}", "").replace("{% endif %}", "-->").replace("{% if error %}", "").replace("{{ error }}", error).replace("{% endif %}", "")
        return html

if __name__ == "__main__":
    print("=" * 50)
    print("Reflexive Vault Web Interface")
    print("=" * 50)
    print("Open http://localhost:8000 in your browser")
    print("=" * 50)
    uvicorn.run(app, host="127.0.0.1", port=8000)