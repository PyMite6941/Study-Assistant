# Module to run the necessary programs
import subprocess
# Modules for making everything work
import chromadb
import ollama
import uuid

class StudyAssistant:
    def __init__(self,chroma_path="./local_db",table_notes='study-stuff'):
        self.table_notes = table_notes
        self.asking_model = 'llama3.1'
        self.processing_model = 'nomic-embed-text'
        self.chroma_client = chromadb.Client(path=chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(name=self.table_notes)

    def add_data(self,data):
        self.collection.add(id=[uuid.uuid4],documents=[data])
        return True

    def search_data(self,query):
        results = self.collection.query(query_texts=[query],n_results=5)
        context = " ".join(results['documents'][0])
        prompt = f"You are an AI assistant that will never hallucinate answers. Use the context to answer the question being asked.\nContext: {context}\nQuestion: {query}"
        response = ollama.chat(model=self.asking_model,messages=prompt)
        return response['message']['content']

    def install_stuff(self):
        try:
            subprocess.run(['ollama','pull','llama3.1'])
            subprocess.run(['ollama','pull','nomic-embed-text'])
        except:
            subprocess.run(['irm','https://ollama.com/install.ps1','|','iex'])
        return True