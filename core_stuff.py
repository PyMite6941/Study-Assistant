# Modules to run the necessary programs
import os
import platform
import subprocess
import time
import datetime
import tomllib
# Module to be able to test users properly
import re
# Module to create and store flashcard data
import json
from dateutil import parser as dateparser
# Modules for processing data
from PIL import Image
import pypdf
import pytesseract
# Modules for making everything work
import chromadb
from chromadb.config import Settings
import ollama
import requests
import socket
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

GROQ_MODEL_MAP = {
    "llama3.1":  "llama-3.1-8b-instant",
    "llama3.2":  "llama-3.1-8b-instant",
    "mistral":   "llama-3.1-8b-instant",
    "phi3:mini": "llama-3.1-8b-instant",
}
OPENAI_MODEL_MAP = {
    "llama3.1":  "gpt-4o-mini",
    "llama3.2":  "gpt-4o-mini",
    "mistral":   "gpt-4o-mini",
    "phi3:mini": "gpt-4o-mini",
}
ANTHROPIC_MODEL_MAP = {
    "llama3.1":  "claude-3-5-haiku-20241022",
    "llama3.2":  "claude-3-5-haiku-20241022",
    "mistral":   "claude-3-5-haiku-20241022",
    "phi3:mini": "claude-3-5-haiku-20241022",
}
GEMINI_MODEL_MAP = {
    "llama3.1":  "gemini-2.0-flash",
    "llama3.2":  "gemini-2.0-flash",
    "mistral":   "gemini-2.0-flash",
    "phi3:mini": "gemini-2.0-flash",
}

XP_LEVELS = [
    (0,    1, "Novice"),
    (100,  2, "Apprentice"),
    (250,  3, "Scholar"),
    (500,  4, "Expert"),
    (1000, 5, "Master"),
    (2000, 6, "Legend"),
]

class StudyAssistant:
    __version__ = 'v1.1'
    def __init__(self,chroma_path:str="./chroma"):
        self.processing_model = 'nomic-embed-text'
        self.xp = 0
        self.chroma_client = chromadb.PersistentClient(settings=Settings(persist_directory=chroma_path,anonymized_telemetry=False,allow_reset=True))
        self._init_provider()
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        self.collection = self.chroma_client.get_or_create_collection(name="study_stuff",embedding_function=DefaultEmbeddingFunction())

    def check_chat_ready(self) -> tuple:
        if self._provider != "ollama":
            return True, ""
        try:
            result = ollama.list()
            names = [m.model for m in result.models]
            if not any(self.asking_model in n for n in names):
                return False, f"Ollama model '{self.asking_model}' is not pulled. Run: ollama pull {self.asking_model}"
            return True, ""
        except Exception:
            return False, "Ollama is not running and no API key is set. Start Ollama or add an API key in Settings."

    def _has_internet(self):
        """Check if any cloud API endpoint is reachable via TCP."""
        for host in ("api.groq.com", "api.openai.com", "api.anthropic.com"):
            try:
                s = socket.create_connection((host, 443), timeout=2)
                s.close()
                return True
            except Exception:
                continue
        return False

    def _resolve_model(self, name, key, base):
        """Fetch the provider's model list and return usable chat model ids."""
        try:
            if name == "anthropic":
                return []
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            r = requests.get(f"{base}/models", headers=headers, timeout=8)
            if not r.ok:
                return []
            data = r.json()
            model_ids = [m.get("id","") for m in data.get("data", [])]
            skip = ("embed", "moderat", "whisper", "tts", "dall", "vision", "guard", "tool-use", "batch")
            candidates = [m for m in model_ids if not any(s in m.lower() for s in skip)]
            return candidates
        except Exception:
            return []

    def _test_provider(self, name, key, base, model):
        """Send a minimal chat request. Returns True if the API responds correctly."""
        try:
            if name == "anthropic":
                headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
                r = requests.post("https://api.anthropic.com/v1/messages",
                             json={"model": model, "max_tokens": 16, "messages": [{"role":"user","content":"hi"}]},
                             headers=headers, timeout=10)
            else:
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                r = requests.post(f"{base}/chat/completions",
                             json={"model": model, "max_tokens": 16, "messages": [{"role":"user","content":"hi"}]},
                             headers=headers, timeout=10)
            return r.ok
        except Exception:
            return False

    def _init_provider(self):
        config = self.load_config()
        keys = config.get("api_keys",{})
        models = config.get("models",{})
        base_model = models.get("chat_model","llama3.1")
        configured_provider = models.get("provider","ollama")

        CLOUD_PROVIDERS = [
            ("groq",      keys.get("groq",""),      "https://api.groq.com/openai/v1",  GROQ_MODEL_MAP),
            ("openai",    keys.get("openai",""),     "https://api.openai.com/v1",        OPENAI_MODEL_MAP),
            ("anthropic", keys.get("anthropic",""),  "https://api.anthropic.com/v1",     ANTHROPIC_MODEL_MAP),
            ("gemini",    keys.get("gemini",""),     "https://generativelanguage.googleapis.com/v1beta/openai", GEMINI_MODEL_MAP),
        ]

        self._provider = "ollama"
        self._api_key = ""
        self._api_base = ""
        self.asking_model = base_model

        if not self._has_internet():
            return

        ordered = sorted(CLOUD_PROVIDERS, key=lambda p: 0 if p[0] == configured_provider else 1)
        for name, key, base, model_map in ordered:
            if not key:
                continue
            map_model = model_map.get(base_model, base_model)
            live_models = self._resolve_model(name, key, base)
            seen = set()
            candidates = []
            for m in [map_model] + live_models:
                if m and m not in seen:
                    candidates.append(m)
                    seen.add(m)
            for model in candidates:
                if self._test_provider(name, key, base, model):
                    self._provider = name
                    self._api_key = key
                    self._api_base = base
                    self.asking_model = model
                    return

    def _llm_chat(self,messages:list,stream:bool=False):
        if self._provider == "ollama":
            if stream:
                s = ollama.chat(model=self.asking_model,messages=messages,stream=True)
                return (chunk.message.content or '' for chunk in s)
            resp = ollama.chat(model=self.asking_model,messages=messages)
            return resp.message.content

        if self._provider == "anthropic":
            headers = {
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {"model":self.asking_model,"max_tokens":2048,"messages":messages}
            if stream:
                payload["stream"] = True
                def _anthropic_gen():
                    r = requests.post("https://api.anthropic.com/v1/messages",
                                 json=payload,headers=headers,stream=True,timeout=60)
                    r.raise_for_status()
                    for raw in r.iter_lines():
                        line = (raw.decode("utf-8") if isinstance(raw,bytes) else raw).strip()
                        if line.startswith("data: "):
                            try:
                                evt = json.loads(line[6:])
                                if evt.get("type") == "content_block_delta":
                                    yield evt["delta"].get("text","")
                            except Exception:
                                pass
                return _anthropic_gen()
            r = requests.post("https://api.anthropic.com/v1/messages",
                         json=payload,headers=headers,timeout=60)
            r.raise_for_status()
            body = r.json()
            if "error" in body:
                raise RuntimeError(f"Anthropic error: {body['error'].get('message', body['error'])}")
            return body["content"][0]["text"]

        headers = {"Authorization":f"Bearer {self._api_key}","Content-Type":"application/json"}
        payload = {"model":self.asking_model,"messages":messages,"max_tokens":2048}
        if stream:
            payload["stream"] = True
            def _gen():
                r = requests.post(f"{self._api_base}/chat/completions",
                             json=payload,headers=headers,stream=True,timeout=60)
                r.raise_for_status()
                for raw in r.iter_lines():
                    line = (raw.decode("utf-8") if isinstance(raw,bytes) else raw).strip()
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            chunk = json.loads(line[6:])
                            content = chunk["choices"][0]["delta"].get("content") or ""
                            if content:
                                yield content
                        except Exception:
                            pass
            return _gen()
        r = requests.post(f"{self._api_base}/chat/completions",
                     json=payload,headers=headers,timeout=60)
        if not r.ok:
            try:
                err = r.json().get("error",{})
                msg = err.get("message", r.text)
            except Exception:
                msg = r.text
            raise RuntimeError(f"API {r.status_code}: {msg}")
        body = r.json()
        if "error" in body:
            raise RuntimeError(f"API error: {body['error'].get('message', body['error'])}")
        return body["choices"][0]["message"]["content"]

    def add_data(self,data):
        results = []
        for file in data:
            if not os.path.exists(file):
                results.append((file, False, f"File not found: {file}"))
                continue
            _,extension = os.path.splitext(file)
            extension = extension.lower()
            try:
                if extension == ".md":
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()
                elif extension == ".pdf":
                    with open(file, "rb") as f:
                        content = " ".join(p.extract_text() for p in pypdf.PdfReader(f).pages if p.extract_text())
                elif extension in [".png",".jpg",".jpeg"]:
                    img = Image.open(file)
                    content = pytesseract.image_to_string(img)
                elif extension in [".txt",".rst",".tex"]:
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()
                else:
                    results.append((file, False, f"Unsupported file type: {extension}"))
                    continue
                source_name = os.path.basename(file)
                chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 20]
                if not chunks:
                    chunks = [content]
                ids = [str(uuid.uuid4()) for _ in chunks]
                self.collection.add(ids=ids,documents=chunks,metadatas=[{"source": source_name}] * len(chunks))
                results.append((file, True, f"Added {len(chunks)} chunk(s)"))
            except Exception as e:
                results.append((file, False, str(e)))
        return results

    def add_text(self,text:str,source_name:str="manual input"):
        if not text or not text.strip():
            return 0
        chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 20]
        if not chunks:
            chunks = [text.strip()]
        ids = [str(uuid.uuid4()) for _ in chunks]
        self.collection.add(ids=ids,documents=chunks,metadatas=[{"source": source_name}] * len(chunks))
        return len(chunks)

    def _retrieve(self,query:str,result_num:int=5):
        result_num = min(result_num, max(1, self.collection.count()))
        results = self.collection.query(query_texts=[query],n_results=result_num)
        context = " ".join(results['documents'][0])
        sources = list({m.get('source','Unknown') for m in results['metadatas'][0]})
        return context, sources

    def _search_prompt(self,context:str,query:str):
        context = context[:6000] if len(context) > 6000 else context
        return (
            f"You are a study assistant. Answer using ONLY the context below. "
            f"If the context lacks enough info, say: 'I could not find this in your notes.'\n\n"
            f"Context: {context}\n\nQuestion: {query}"
        )

    def search_data(self,query:str,result_num:int=5):
        if self.collection.count() == 0:
            return "No notes have been added yet. Use 'Add Content' to upload your notes first.", []
        context, sources = self._retrieve(query,result_num)
        return self._llm_chat([{'role':'user','content':self._search_prompt(context,query)}]), sources

    def search_data_stream(self,query:str,result_num:int=5):
        if self.collection.count() == 0:
            return (c for c in ["No notes have been added yet. Use 'Add Content' to upload your notes first."]), []
        context, sources = self._retrieve(query,result_num)
        return self._llm_chat([{'role':'user','content':self._search_prompt(context,query)}],stream=True), sources

    def quiz_stuff(self,topic:str,previous_questions:list=None,comments:str=None):
        results = self.collection.query(query_texts=[topic],n_results=min(3, max(1, self.collection.count())))
        if not results.get('documents') or len(results['documents']) == 0 or not results['documents'][0]:
            return "No relevant content about this topic was found"
        relevant_context = " ".join(results['documents'][0])
        prev_q_text = f"Do not repeat any of these previous questions: {previous_questions}." if previous_questions else ""
        comments_text = f"Additional guidance: {comments}" if comments else ""
        prompt = f"You are an AI assistant that will never hallucinate answers. Use the context to answer the question being asked.\nContext: {relevant_context}\nCreate a multiple choice question using A-D and at the very end write 'ANSWER: X' where X is the right letter in the multiple choice that you create. The question should be about {topic}. {prev_q_text} {comments_text} If you cannot create a new question, say so explicitly and do not write 'ANSWER: X'."
        response = self._llm_chat([{'role':'user','content':prompt}])
        match = re.search(r"ANSWER:\s([A-D])",response,re.IGNORECASE)
        if not match:
            return "The model did not produce a valid question. Try again."
        correct_answer = match.group(1).upper()
        question_text = re.sub(r"ANSWER:\s([A-D])", "", response, flags=re.IGNORECASE).strip()
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
        results = self.collection.query(query_texts=[topic],n_results=min(card_number, max(1, self.collection.count())))
        if not results.get('documents') or len(results['documents']) == 0 or not results['documents'][0]:
            return "No relevant content about this topic was found"
        context = " ".join(results['documents'][0])
        prompt = (
            f"You are a study assistant. Using ONLY the context below, generate up to {card_number} flashcards as Q&A pairs. "
            f"Format each one exactly as: 'Q: <question> | A: <answer>' on its own line. Do not use outside knowledge.\n\n"
            f"Context: {context}\nTopic: {topic}"
        )
        response = self._llm_chat([{'role':'user','content':prompt}])
        cards = []
        for line in response.split('\n'):
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

    def _clean_topic(self,raw:str) -> str:
        raw = re.sub(r'^(on|about|for|the|a|an|regarding|related to)\s+','',raw.strip(),flags=re.IGNORECASE)
        raw = re.sub(r'\s+(please|now|for me|thanks)$', '', raw.strip(), flags=re.IGNORECASE)
        return raw.strip()

    def _extract_study_plan_params(self,query:str):
        days = 7
        topic = query
        m = re.search(r'in\s+(\d+)\s+(day|week)s?',query,re.IGNORECASE)
        if m:
            n = int(m.group(1))
            days = n * 7 if 'week' in m.group(2).lower() else n
            topic = (query[:m.start()] + query[m.end():]).strip()
        else:
            m = re.search(r'\b(by|before|until|on)\s+(.+?)$',query,re.IGNORECASE)
            if m:
                try:
                    target = dateparser.parse(m.group(2),default=datetime.datetime.today()).date()
                    days = max(1,(target - datetime.date.today()).days)
                    topic = query[:m.start()].strip()
                except Exception:
                    pass
        topic = re.sub(r'(create|make|generate|build|a\s+)?study\s+plan\s*(for|about|on|regarding)?','',topic,flags=re.IGNORECASE)
        return self._clean_topic(topic) or query, days

    def create_study_plan(self,topic:str,days:int=7):
        n = min(5,self.collection.count())
        context = ""
        if n > 0:
            results = self.collection.query(query_texts=[topic],n_results=n)
            context = " ".join(results['documents'][0])
        prompt = (
            f"Create a {days}-day study plan for '{topic}' using the context below. "
            f"Return ONLY a valid JSON array. Each item must have: {{\"day\": N, \"focus\": \"short focus area\", \"tasks\": [\"task1\", \"task2\"]}}. "
            f"No text outside the JSON array.\n\nContext: {context if context else 'No notes available — use general knowledge.'}"
        )
        raw = self._llm_chat([{'role':'user','content':prompt}])
        try:
            plan = json.loads(raw)
        except Exception:
            match = re.search(r'\[.*\]',raw,re.DOTALL)
            plan = json.loads(match.group()) if match else None
        if not plan:
            return None
        return {"topic": topic, "days": days, "created": str(datetime.date.today()), "plan": plan}

    def save_study_plan(self,plan:dict):
        plans = self.load_study_plans()
        plans.append(plan)
        os.makedirs("saved_data",exist_ok=True)
        with open("saved_data/study_plans.json","w") as f:
            json.dump(plans,f)

    def load_study_plans(self):
        if not os.path.exists("saved_data/study_plans.json"):
            return []
        with open("saved_data/study_plans.json","r") as f:
            content = f.read()
            return json.loads(content) if content.strip() else []

    def create_concept_map(self,topic:str):
        n = min(5,self.collection.count())
        if n == 0:
            return None
        results = self.collection.query(query_texts=[topic],n_results=n)
        context = " ".join(results['documents'][0])
        prompt = (
            f"Extract key concepts and relationships about '{topic}' from the context below. "
            f"Return ONLY a valid JSON array of triples: [[\"concept1\", \"relationship\", \"concept2\"], ...]. "
            f"Maximum 12 triples. Keep concept names short (1-4 words). "
            f"No text outside the JSON array.\n\nContext: {context}"
        )
        raw = self._llm_chat([{'role':'user','content':prompt}])
        try:
            return json.loads(raw)
        except Exception:
            match = re.search(r'\[.*\]',raw,re.DOTALL)
            try:
                return json.loads(match.group()) if match else None
            except Exception:
                return None

    def save_concept_map(self,concept_map:dict):
        maps = self.load_concept_maps()
        maps.append(concept_map)
        os.makedirs("saved_data",exist_ok=True)
        with open("saved_data/concept_maps.json","w") as f:
            json.dump(maps,f)

    def load_concept_maps(self):
        if not os.path.exists("saved_data/concept_maps.json"):
            return []
        with open("saved_data/concept_maps.json","r") as f:
            content = f.read()
            return json.loads(content) if content.strip() else []

    def search_videos(self,query:str):
        import urllib.parse
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        return [{"title": f"YouTube: {query}", "url": search_url}]

    def designate_function(self,raw_input:str,stream:bool=True):
        query = raw_input.lower().strip()
        commands = {
            r"(generate|make|create|compile)\s+flashcards": "flashcards",
            r"(generate|make|create|compile)\s+quiz": "quiz",
            r"quiz\s+me": "quiz",
            r"(create|make|generate|build)?\s*(a\s+)?study\s+plan": "study_plan",
            r"(create|make|generate|show|draw|build)?\s*(a\s+)?concept\s+(map|graph|diagram)": "concept_map",
            r"(find|search\s(a\s+)?video)": "video",
        }
        for pattern,intent in commands.items():
            if re.search(pattern,query):
                if intent == "flashcards":
                    topic = self._clean_topic(re.sub(pattern,"",query).strip())
                    return "flashcards", self.create_flashcards(topic), []
                elif intent == "quiz":
                    topic = self._clean_topic(re.sub(pattern,"",query).strip())
                    return "quiz", self.quiz_stuff(topic), []
                elif intent == "study_plan":
                    topic, days = self._extract_study_plan_params(query)
                    return "study_plan", self.create_study_plan(topic,days), []
                elif intent == "concept_map":
                    topic = self._clean_topic(re.sub(pattern,"",query).strip())
                    return "concept_map", self.create_concept_map(topic), []
                elif intent == "video":
                    topic = self._clean_topic(re.sub(pattern,"",query).strip())
                    return "video", self.search_videos(topic), []
        if stream:
            gen, sources = self.search_data_stream(query)
            return "chat_stream", gen, sources
        response, sources = self.search_data(query)
        return "chat", response, sources

    def _config_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)),"config.toml")

    def _default_config(self):
        return {
            "api_keys": {"groq":"","openai":"","gemini":"","anthropic":""},
            "models": {"provider":"ollama","chat_model":"llama3.1","embedding_model":"nomic-embed-text"},
            "paths": {"chroma_path":"./chroma","saved_data_path":"./saved_data"},
        }

    def _write_toml(self,config:dict) -> str:
        lines = []
        for section,values in config.items():
            lines.append(f"[{section}]")
            for key,value in values.items():
                lines.append(f'{key} = "{value}"')
            lines.append("")
        return "\n".join(lines)

    def load_config(self) -> dict:
        path = self._config_path()
        if not os.path.exists(path):
            return self._default_config()
        with open(path,"rb") as f:
            return tomllib.load(f)

    def save_config(self,config:dict):
        with open(self._config_path(),"w",encoding="utf-8") as f:
            f.write(self._write_toml(config))
        self._init_provider()

    def load_stats(self):
        if not os.path.exists("saved_data/stats.json"):
            return {"total_questions": 0, "correct": 0, "by_topic": {}}
        with open("saved_data/stats.json","r") as f:
            return json.load(f)

    def save_stats(self,topic:str,correct:bool):
        stats = self.load_stats()
        stats["total_questions"] += 1
        if correct:
            stats["correct"] += 1
        t = stats["by_topic"].setdefault(topic,{"correct": 0, "total": 0})
        t["total"] += 1
        if correct:
            t["correct"] += 1
        os.makedirs("saved_data",exist_ok=True)
        with open("saved_data/stats.json","w") as f:
            json.dump(stats,f)

    def get_streak(self) -> dict:
        if not os.path.exists("saved_data/streak.json"):
            return {"streak": 0, "last_date": ""}
        with open("saved_data/streak.json") as f:
            return json.load(f)

    def update_streak(self) -> dict:
        data = self.get_streak()
        today = str(datetime.date.today())
        yesterday = str(datetime.date.today() - datetime.timedelta(days=1))
        if data["last_date"] == today:
            return data
        elif data["last_date"] == yesterday:
            data["streak"] += 1
        else:
            data["streak"] = 1
        data["last_date"] = today
        os.makedirs("saved_data", exist_ok=True)
        with open("saved_data/streak.json", "w") as f:
            json.dump(data, f)
        return data

    def get_xp_data(self) -> dict:
        return {'xp':self.xp}

    def calculate_xp(self,xp:int,answer_streak:int,incorrect_streak) -> int:
        if answer_streak > 0:
            xp *= answer_streak
        else:
            xp = xp - 6 * incorrect_streak
        self.xp += xp
        return xp

    def get_level_info(self) -> dict:
        xp = self.xp
        level, title = XP_LEVELS[0][1], XP_LEVELS[0][2]
        for threshold, lvl, name in XP_LEVELS:
            if xp >= threshold:
                level, title = lvl, name
        if level < len(XP_LEVELS):
            next_thresh = XP_LEVELS[level][0]
            prev_thresh = XP_LEVELS[level - 1][0]
            span = max(1, next_thresh - prev_thresh)
            progress = min(1.0, (xp - prev_thresh) / span)
            xp_to_next = max(0, next_thresh - xp)
        else:
            progress, xp_to_next = 1.0, 0
        return {"xp": xp, "level": level, "title": title, "progress": progress, "xp_to_next": xp_to_next}

    def calculate_levels(self) -> float:
        self.levels = self.xp / 100
        return self.levels

    def load_levels(self) -> float:
        try:
            with open("saved_data/levels.txt") as file:
                data = file.readlines()
                self.levels = data
                return data
        except FileNotFoundError:
            return 0

    def save_levels(self):
        try:
            with open("saved_data/levels.txt") as file:
                data = file.readlines()
            new_levels = data + self.calculate_levels()
            with open("saved_data/levels.txt") as file:
                self.levels = new_levels
                file.write(new_levels)
        except FileNotFoundError:
            with open("saved_data/levels.txt") as file:
                file.write(0)

    def install_stuff(self):
        subprocess.run(['bash','setup.sh'])
        return True

    def _check_for_updates(self):
        """Returns dict: {up_to_date, current, latest, error}."""
        current = self.__version__
        try:
            r = requests.get(
                "https://raw.githubusercontent.com/pymite6941/study-assistant/main/core_stuff.py",
                timeout=8
            )
            if not r.ok:
                return {"up_to_date": None, "current": current, "latest": None, "error": f"HTTP {r.status_code}"}
            m = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", r.text)
            if not m:
                return {"up_to_date": None, "current": current, "latest": None, "error": "Version not found in remote file"}
            latest = m.group(1)
            return {"up_to_date": current == latest, "current": current, "latest": latest, "error": None}
        except Exception as e:
            return {"up_to_date": None, "current": current, "latest": None, "error": str(e)}

    def update_program(self):
        info = self._check_for_updates()
        if info["error"]:
            return f"Could not check for updates: {info['error']}"
        if info["up_to_date"]:
            return f"Already on the latest version ({info['current']})."
        try:
            subprocess.run(['git', 'pull'], check=True)
            return f"Updated from {info['current']} to {info['latest']}. Restart to apply."
        except Exception as e:
            return f"Update failed: {e}"