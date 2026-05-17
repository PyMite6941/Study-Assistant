touch config.toml
cat << 'EOF' > config.toml
[api_keys]
groq = ""
openai = ""
gemini = ""
anthropic = ""

[models]
provider = "ollama"
chat_model = "llama3.1"
embedding_model = "nomic-embed-text"

[paths]
chroma_path = "./chroma"
saved_data_path = "./saved_data"
EOF
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
ollama pull nomic-embed-text
echo "Do you want to set up Ollama as your default provider? (y/n)"
read answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    ollama pull llama3.1
fi
exit /b 0