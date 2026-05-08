# Modules to run the necessary programs
import platform
import subprocess
# Module to be able to test users properly
import re
# Module to create and store flashcard data
import json
# Modules for making everything work
import chromadb
from chromadb.config import Settings
import ollama
import uuid

class OllamaEmbedding(chromadb.EmbeddingFunction):
    def __init__(self,model_name='nomic-embed-text'):
        self.model_name = model_name

    def __call__(self,input:chromadb.Documents) -> chromadb.Embeddings:
        try:
            embeddings = []
            for text in input:
                response = ollama.embeddings(model=self.model_name,prompt=text)
                embeddings.append(response['embedding'])
            return embeddings
        except Exception as e:
            print("Ollama isn't running, beginning task ...")
            try:
                os_type = platform.system()
                if os_type == "Windows":
                    subprocess.Popen(["ollama", "serve"],creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    with open(os_type.devnull, 'wb') as devnull:
                        subprocess.Popen(["ollama", "serve"],stdout=devnull,stderr=devnull)
            except Exception as e:
                print("Ollama isn't installed, go to https://ollama.com/ for downloading the app.")

class StudyAssistant:
    def __init__(self,chroma_path:str="./local_db"):
        self.asking_model = 'llama3.1'
        self.processing_model = 'nomic-embed-text'
        self.chroma_client = chromadb.PersistentClient(settings=Settings(persist_directory=chroma_path,anonymized_telemetry=False,allow_reset=True))
        ollamaEmbedding = OllamaEmbedding(model_name=self.processing_model)
        self.collection = self.chroma_client.get_or_create_collection(name="study_stuff",embedding_function=ollamaEmbedding)

    def add_data(self,data):
        self.collection.add(ids=[str(uuid.uuid4())],documents=[data])
        return True

    def search_data(self,query:str,result_num:int=5):
        results = self.collection.query(query_texts=[query],n_results=result_num)
        context = " ".join(results['documents'][0])
        prompt = f"You are an AI assistant that will never hallucinate answers. Use the context to answer the question being asked.\nContext: {context}\nQuestion: {query}"
        response = ollama.chat(model=self.asking_model,messages=[{'role':'user','content':prompt}])
        return response['message']['content']

    def quiz_stuff(self,topic:str):
        results = self.collection.query(query_texts=[topic],n_results=1)
        if not results.get('documents') or len(results['documents']) == 0 or not results['documents'][0]:
            return "No relevant content about this topic was found"
        relevant_context = results['documents'][0][0]
        prompt = f"You are an AI assistant that will never hallucinate answers. Use the context to answer the question being asked.\nContext: {relevant_context}\nCreate a multiple choice question using A-D and at the very end write 'ANSWER: X' where X is the right letter in the multiple choice that you create."
        response = ollama.chat(model=self.asking_model,messages=[{'role':'user','content':prompt}])
        match = re.search(r"ANSWER:\s([A-D])",response['message']['content'],re.IGNORECASE)
        if not match:
            return
        correct_answer = match.group(1).upper()
        question_text = re.sub(r"ANSWER:\s([A-D])", "", response['message']['content'], flags=re.IGNORECASE).strip()
        return {
            'question': question_text,
            'answer': correct_answer
        }

    def create_flashcards(self,topic:str,card_number:int=15):
        results = self.collection.query(query_texts=[topic],n_results=card_number)
        if not results.get('documents') or len(results['documents']) == 0 or not results['documents'][0]:
            return "No relevant content about this topic was found"
        
    def designate_function(self,raw_input:str):
        input = raw_input.lower().strip()
        commands = {
            r"(generate|make|create|compile)\s+flashcards": "flashcards",
            r"(generate|make|create|compile)\s+quiz": "quiz",
            r"quiz\s+me": "quiz",
        }
        for pattern,intent in commands.items():
            if re.search(pattern,input):
                topic = re.sub(pattern,"",input).strip()
                if intent == "flashcards":
                    return "flashcards", self.create_flashcards(topic)
                elif intent == "quiz":
                    return "quiz", self.quiz_stuff(topic)
            else:
                return "chat", self.search_data(input)

    def install_stuff(self):
        try:
            subprocess.run(['ollama','pull','llama3.1'])
            subprocess.run(['ollama','pull','nomic-embed-text'])
        except:
            subprocess.run(['irm','https://ollama.com/install.ps1','|','iex'])
        return True