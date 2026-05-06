# Module to run the necessary programs
import subprocess
# Module to be able to test users properly
import re
# Modules for making everything work
import chromadb
from chromadb.config import Settings
import ollama
import uuid


class OllamaEmbedding:
    def __init__(self,model_name='nomic-embed-text'):
        self.model_name = model_name

    def __call__(self,input:chromadb.Documents) -> chromadb.Embeddings:
        embeddings = []
        for text in input:
            response = ollama.embeddings(model=self.model_name,prompt=text)
            embeddings.append(response['embedding'])
        return embeddings

class StudyAssistant:
    def __init__(self,chroma_path="./local_db"):
        self.asking_model = 'llama3.1'
        self.processing_model = 'nomic-embed-text'
        self.chroma_client = chromadb.PersistentClient(name="study_stuff",settings=Settings(persist_directory=chroma_path,anonymized_telemetry=False,allow_reset=True))
        ollamaEmbedding = OllamaEmbedding(model_name=self.processing_model)
        self.collection = self.chroma_client.get_or_create_collection(embedding_function=ollamaEmbedding)

    def add_data(self,data):
        self.collection.add(ids=[str(uuid.uuid4())],documents=[data])
        return True

    def search_data(self,query):
        results = self.collection.query(query_texts=[query],n_results=5)
        context = " ".join(results['documents'][0])
        prompt = f"You are an AI assistant that will never hallucinate answers. Use the context to answer the question being asked.\nContext: {context}\nQuestion: {query}"
        response = ollama.chat(model=self.asking_model,messages=[{'role':'user','content':prompt}])
        return response['message']['content']

    def quiz_stuff(self,topic):
        results = self.collection.query(query_texts=[topic],n_results=1)
        if not results['documents'][0]:
            return "No relevant content about this topic was found"
        relevant_context = results['documents'][0][0]
        prompt = f"You are an AI assistant that will never hallucinate answers. Use the context to answer the question being asked.\nContext: {relevant_context}\nCreate a multiple choice question using A-D and at the very end write 'ANSWER: X' where X is the right letter in the multiple choice that you create."
        response = ollama.chat(model=self.asking_model,messages=[{'role':'user','prompt':prompt}])
        match = re.search(r"ANSWER:\s([A-D])",response['message']['content'],re.IGNORECASE)
        if not match:
            return
        correct_answer = match.group(1).upper()
        question_text = re.sub(r"ANSWER:\s([A-D])", "", response, flags=re.IGNORECASE).strip()
        return {
            'question': question_text,
            'answer': correct_answer
        }

    def install_stuff(self):
        try:
            subprocess.run(['ollama','pull','llama3.1'])
            subprocess.run(['ollama','pull','nomic-embed-text'])
        except:
            subprocess.run(['irm','https://ollama.com/install.ps1','|','iex'])
        return True