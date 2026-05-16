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
from PIL import Image
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
            return self._embed(input)
        except Exception:
            self.start_ollama()
            return self._embed(input)

    def _embed(self,input:chromadb.Documents) -> chromadb.Embeddings:
        response = ollama.embed(model=self.model_name,input=list(input))
        return response['embeddings']

    def start_ollama(self):
        try:
            ollama.list()
            return
        except Exception:
            pass
        os_type = platform.system()
        try:
            if os_type == "Windows":
                subprocess.Popen(["ollama", "serve"],creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            elif os_type == "Darwin":
                subprocess.Popen(["open", "-a", "Ollama"])
            else:
                subprocess.Popen(["ollama", "serve"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            raise RuntimeError("Ollama isn't installed. Download it at https://ollama.com/")
        for _ in range(15):
            try:
                ollama.list()
                return
            except Exception:
                time.sleep(1)
        raise RuntimeError("Ollama failed to start within 15 seconds.")

class StudyAssistant:
    def __init__(self,chroma_path:str="./chroma"):
        self.asking_model = 'llama3.1'
        self.processing_model = 'nomic-embed-text'
        self.chroma_client = chromadb.PersistentClient(settings=Settings(persist_directory=chroma_path,anonymized_telemetry=False,allow_reset=True))
        ollamaEmbedding = OllamaEmbedding(model_name=self.processing_model)
        self.collection = self.chroma_client.get_or_create_collection(name="study_stuff",embedding_function=ollamaEmbedding)

    def add_data(self,data):
        for file in data:
            _,extension = os.path.splitext(file)
            extension = extension.lower()
            if extension == ".md":
                with open(file, "r") as f:
                    content = f.read()
            elif extension == ".pdf":
                with open(file, "rb") as f:
                    content = " ".join(p.extract_text() for p in pypdf.PdfReader(f).pages if p.extract_text())
            elif extension in [".png",".jpg",".jpeg"]:
                img = Image.open(file)
                content = pytesseract.image_to_string(img)
            else:
                continue
            source_name = os.path.basename(file)
            chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 20]
            if not chunks:
                chunks = [content]
            ids = [str(uuid.uuid4()) for _ in chunks]
            self.collection.add(ids=ids,documents=chunks,metadatas=[{"source": source_name}] * len(chunks))
        return True

    def _retrieve(self,query:str,result_num:int=5):
        results = self.collection.query(query_texts=[query],n_results=result_num)
        context = " ".join(results['documents'][0])
        sources = list({m.get('source','Unknown') for m in results['metadatas'][0]})
        return context, sources

    def _search_prompt(self,context:str,query:str):
        return (
            f"You are a study assistant. You MUST answer using ONLY the context provided below. "
            f"Do not use any knowledge from your training data. "
            f"If the context does not contain enough information to answer the question, say exactly: 'I could not find this in your notes.' and nothing else. "
            f"Do not make up, infer, or expand beyond what is explicitly stated in the context.\n\n"
            f"Context: {context}\n\nQuestion: {query}"
        )

    def search_data(self,query:str,result_num:int=5):
        if self.collection.count() == 0:
            return "No notes have been added yet. Use 'Add Content' to upload your notes first.", []
        context, sources = self._retrieve(query,result_num)
        response = ollama.chat(model=self.asking_model,messages=[{'role':'user','content':self._search_prompt(context,query)}])
        return response['message']['content'], sources

    def search_data_stream(self,query:str,result_num:int=5):
        if self.collection.count() == 0:
            return (c for c in ["No notes have been added yet. Use 'Add Content' to upload your notes first."]), []
        context, sources = self._retrieve(query,result_num)
        stream = ollama.chat(model=self.asking_model,messages=[{'role':'user','content':self._search_prompt(context,query)}],stream=True)
        return (chunk['message']['content'] or '' for chunk in stream), sources

    def quiz_stuff(self,topic:str,previous_questions:list=None,comments:str=None):
        results = self.collection.query(query_texts=[topic],n_results=3)
        if not results.get('documents') or len(results['documents']) == 0 or not results['documents'][0]:
            return "No relevant content about this topic was found"
        relevant_context = " ".join(results['documents'][0])
        prev_q_text = f"Do not repeat any of these previous questions: {previous_questions}." if previous_questions else ""
        comments_text = f"Additional guidance: {comments}" if comments else ""
        prompt = f"You are an AI assistant that will never hallucinate answers. Use the context to answer the question being asked.\nContext: {relevant_context}\nCreate a multiple choice question using A-D and at the very end write 'ANSWER: X' where X is the right letter in the multiple choice that you create. The question should be about {topic}. {prev_q_text} {comments_text} If you cannot create a new question, say so explicitly and do not write 'ANSWER: X'."
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

    def save_quizzes(self,data:dict):
        if not data:
            return "No data to process"
        quizzes = self.load_quizzes()
        existing = {q.get('question') for q in quizzes}
        if data.get('question') not in existing:
            quizzes.append(data)
        os.makedirs("saved_data",exist_ok=True)
        with open("saved_data/quizzes.json",'w') as file:
            json.dump(quizzes,file)
        return "Saved quizzes successfully"
    
    def load_quizzes(self):
        if not os.path.exists("saved_data/quizzes.json"):
            return []
        with open("saved_data/quizzes.json",'r') as file:
            content = file.read()
            return json.loads(content) if content.strip() else []

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
        
    def save_flashcards(self,data:list):
        if not data:
            return "No data to process"
        flashcards = self.load_flashcards()
        existing = {f.get('Question') for f in flashcards}
        for card in data:
            if card.get('Question') not in existing:
                flashcards.append(card)
                existing.add(card.get('Question'))
        os.makedirs("saved_data",exist_ok=True)
        with open("saved_data/flashcards.json",'w') as file:
            json.dump(flashcards,file)
        return "Saved flashcards successfully"
    
    def load_flashcards(self):
        if not os.path.exists("saved_data/flashcards.json"):
            return []
        with open("saved_data/flashcards.json",'r') as file:
            content = file.read()
            return json.loads(content) if content.strip() else []

    def designate_function(self,raw_input:str,stream:bool=True):
        query = raw_input.lower().strip()
        commands = {
            r"(generate|make|create|compile)\s+flashcards": "flashcards",
            r"(generate|make|create|compile)\s+quiz": "quiz",
            r"quiz\s+me": "quiz",
        }
        for pattern,intent in commands.items():
            if re.search(pattern,query):
                topic = re.sub(pattern,"",query).strip()
                if intent == "flashcards":
                    return "flashcards", self.create_flashcards(topic), []
                elif intent == "quiz":
                    return "quiz", self.quiz_stuff(topic), []
        if stream:
            gen, sources = self.search_data_stream(query)
            return "chat_stream", gen, sources
        response, sources = self.search_data(query)
        return "chat", response, sources

    def install_stuff(self):
        try:
            subprocess.run(['ollama','pull','llama3.1'])
            subprocess.run(['ollama','pull','nomic-embed-text'])
        except:
            subprocess.run(['irm','https://ollama.com/install.ps1','|','iex'])
        return True