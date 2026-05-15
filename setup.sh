python -m venv .venv
OS=$(uname -s)
if [ "$OS" = "Linux" ] || [ "$OS" = "Darwin" ]; then
    source .venv/bin/activate
elif [ "$OS" = "Windows_NT" ]; then
    .venv\Scripts\activate
else
    echo "Unsupported OS: $OS"
    exit 1
fi
pip install -r requirements.txt
where ollama >null 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo "Ollama is not installed. Please install Ollama and try again."
    exit /b 1
)
ollama pull llama3.1
ollama pull nomic-embed-text