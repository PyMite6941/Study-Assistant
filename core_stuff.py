# Modules to run the necessary programs
import os
import platform
import subprocess
import time
# Module to be able to test users properly
import re
# Module to create and store flashcard data
import json
# Modules for processing data
from PIL import pillow
import pypdf
import pytesseract
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
            self.start_ollama()
            time.sleep(5)
            embeddings = []
            for text in input:
                response = ollama.embeddings(model=self.model_name, prompt=text)
                embeddings.append(response['embedding'])
            return embeddings
            
    def start_ollama(self):
        os_type = platform.system()
        try:
            if os_type == "Windows":
                subprocess.Popen(["ollama", "serve"],creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            elif os_type == "Darwin":
                subprocess.Popen(["open", "-a", "Ollama"])
            else:
                subprocess.Popen(["ollama", "serve"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            return "Ollama isn't installed. Download it at https://ollama.com/"

class StudyAssistant:
    def __init__(self,chroma_path:str="./chroma"):
        self.asking_model = 'llama3.1'
        self.processing_model = 'nomic-embed-text'
        self.chroma_client = chromadb.PersistentClient(settings=Settings(persist_directory=chroma_path,anonymized_telemetry=False,allow_reset=True))
        ollamaEmbedding = OllamaEmbedding(model_name=self.processing_model)
        self.collection = self.chroma_client.get_or_create_collection(name="study_stuff",embedding_function=ollamaEmbedding)

    def add_data(self,data):
        for file in data:
            root,extension = os.path.splitext(file)
            if extension == ".md":
                with open(file, "r") as f:
                    content = f.read()
            elif extension == ".pdf":
                with open(file, "rb") as f:
                    content = pypdf.PdfReader(f).pages[0].extract_text()
            elif extension in [".png",".jpg",".jpeg"]:
                img = pillow.Image.open(file)
                content = pytesseract.image_to_string(img)
            else:
                continue
            self.collection.add(ids=[str(uuid.uuid4())],documents=[content])
        return True

    def search_data(self,query:str,result_num:int=5):
        if self.collection.count() == 0:
            return "No notes have been added yet. Use 'Add Content' to upload your notes first."
        results = self.collection.query(query_texts=[query],n_results=result_num)
        context = " ".join(results['documents'][0])
        prompt = f"You are a study assistant. Answer ONLY using the context provided — do not use any outside knowledge. If the context does not contain enough information to answer, say so explicitly. At the end of your answer, quote the exact passage(s) from the context that support your answer under a 'Sources:' heading.\nContext: {context}\nQuestion: {query}"
        response = ollama.chat(model=self.asking_model,messages=[{'role':'user','content':prompt}])
        return response['message']['content']

    def quiz_stuff(self,topic:str):
        results = self.collection.query(query_texts=[topic],n_results=1)
        if not results.get('documents') or len(results['documents']) == 0 or not results['documents'][0]:
            return "No relevant content about this topic was found"
        relevant_context = results['documents'][0][0]
        prompt = f"You are an AI assistant that will never hallucinate answers. Use the context to answer the question being asked.\nContext: {relevant_context}\nCreate a multiple choice question using A-D and at the very end write 'ANSWER: X' where X is the right letter in the multiple choice that you create. Make sure to mention what source you got the information from in the question so that the user can find it in their notes. The question should be about {topic}."
        response = ollama.chat(model=self.asking_model,messages=[{'role':'user','content':prompt}])
        match = re.search(r"ANSWER:\s([A-D])",response['message']['content'],re.IGNORECASE)
        if not match:
            return "The model did not produce a valid question. Try again."
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
        context = " ".join(results['documents'][0])
        prompt = (
            f"You are a study assistant. Using ONLY the context below, generate up to {card_number} flashcards as Q&A pairs. "
            f"Format each one exactly as: 'Q: <question> | A: <answer>' on its own line. Do not use outside knowledge.\n\n"
            f"Context: {context}\nTopic: {topic}"
        )
        response = ollama.chat(model=self.asking_model,messages=[{'role':'user','content':prompt}])
        cards = []
        for line in response['message']['content'].split('\n'):
            if '|' in line and line.strip().startswith('Q:'):
                parts = line.split('|',1)
                if len(parts) == 2:
                    q = parts[0].replace('Q:','').strip()
                    a = parts[1].replace('A:','').strip()
                    cards.append({'Question': q, 'Answer': a})
        return cards if cards else "Could not generate flashcards from the available content."
        
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
                    return "flashcards",self.create_flashcards(topic)
                elif intent == "quiz":
                    return "quiz",self.quiz_stuff(topic)
        return "chat",self.search_data(input)

    def install_stuff(self):
        try:
            subprocess.run(['ollama','pull','llama3.1'])
            subprocess.run(['ollama','pull','nomic-embed-text'])
        except:
            subprocess.run(['irm','https://ollama.com/install.ps1','|','iex'])
        return True