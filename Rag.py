import sys
print("PYTHON UTILISÉ :", sys.executable)

import os
import shutil
import streamlit as st
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

import json

# Prompt
PROMPT_TEMPLATE = """
    Vous etes un assistant util. Utilise le contexte fournit pour répondre à la requete. Si vous ne savez
    pas la réponse, indiquez que vous ne savez pas. Soyez concis et factuel.

    Query : {user_query}

    Context : {document_context}

    Answer : 
"""

# téléchargement des fichiers
pdf_stotage_path = "Fichiers/pdf/"

# models d'embedding
embedding_model = OllamaEmbeddings(model="nomic-embed-text")

# moddel de communication
llm = OllamaLLM(model= "deepseek-r1:8b", temperature= 0.9)

# enrégistrement du fichier téléverser
#def save_upload_file (upload_file) :
#    file_path = pdf_stotage_path + upload_file.name

def save_upload_file (chemin, upload_file) :
    file_path = chemin + upload_file.name

    with open(file_path, "wb") as f :
        f.write(upload_file.getbuffer())

    return file_path

# Chargement du fichier
def load_pdf (file_path) :
    loader = PDFPlumberLoader(file_path)
    return loader.load()

# Découpage du fichier en morceau ou chunks avec 1000 Mots et 200 mots pour le chevauchement
def chunk_document(document) :
    spliter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 200)
    return spliter.split_documents(document)

# génération de la réponse
def generate_answer(query, docs) :
    context = "\n\n".join([doc.page_content for doc in docs])
    promp = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    reponse_chain = promp | llm
    return reponse_chain.invoke({"user_query" : query, "document_context" : context})

# Liste des chats
def chats_list (files_path) : 
    if not os.path.exists(files_path):
        return []
    
    all_list_chats = [
        f for f in os.listdir(files_path) 
        if f.endswith(".pdf")
                ]
    
    Chats = [f.replace(".pdf", "") for f in all_list_chats]
    #return Chats
    return all_list_chats



if "json_path" not in st.session_state :
    st.session_state.json_path = "chats.json"

#JSON_PATH = st.session_state.history

if "chats" not in st.session_state:
    st.session_state.chats = []
    #if os.path.exists(st.session_state.json_path):
    #    with open(st.session_state.json_path, "r", encoding="utf-8") as f:
    #        st.session_state.chats = json.load(f)
    #else:
    #    st.session_state.chats = []



if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "vectorstores" not in st.session_state:
    st.session_state.vectorstores = {}

if "old_file" not in st.session_state:
    st.session_state.old_file = None

#chat_names = list(st.session_state.chats.keys())
#chat_names = chats_list(pdf_stotage_path)

# Initialiser la liste des chats
if "chat_names" not in st.session_state:
    st.session_state.chat_names = None

# Initialiser le chat sélectionné
if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None

if "user_trouve" not in st.session_state:
    st.session_state.user_trouve = None

if "files" not in st.session_state :
    st.session_state.files = None

def create_user(username, password):
    user_dir = os.path.join("chatlogs", username)
    os.makedirs(user_dir, exist_ok=True)
    
    with open(os.path.join(user_dir, "infos_user.json"), "w") as f:
        json.dump({"username" : username,"password": password, "Admin" : "False"}, f)

    files = os.path.join(user_dir, pdf_stotage_path)
    os.makedirs(files, exist_ok= True)
    

def check_users(username, password):
    path = os.path.join("chatlogs", username, "infos_user.json")
    if os.path.exists(path):
        with open(path) as f:
            stored = json.load(f)
            return stored.get("password") == password
    return False

def save_chats():
    with open(st.session_state.json_path, "w", encoding="utf-8") as f:
        json.dump(st.session_state.chats, f, indent=4, ensure_ascii=False)


#Interface utilisateur pour entrer le nom
if st.session_state.user_trouve is None:

    st.title(" Connexion / Inscription")
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])

    with tab1:
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if check_users(username, password):
                st.session_state.user_trouve = username
                #path = os.path.join("chatlogs", username, "history.json")

                user_dir = os.path.join("chatlogs", username)

                st.session_state.files = os.path.join(user_dir, pdf_stotage_path)

                st.rerun()

            else:
                st.error(" Nom d'utilisateur ou mot de passe incorrect. ")

    with tab2:
        new_user = st.text_input("Choisir un nom d'utilisateur")
        new_pass = st.text_input("Choisir un mot de passe", type="password")
        if st.button("Créer mon compte") :
            user_path = os.path.join("chatlogs", new_user)
            if os.path.exists(user_path) :
                st.warning("Ce nom d'utilisateur existe déjà.")
            else:
                create_user(new_user, new_pass)
                st.success("Compte créé avec succès. Vous pouvez maintenant vous connecter.")        

else :
    user = st.session_state.user_trouve

    st.session_state.chat_names = chats_list(st.session_state.files)


    selected = st.sidebar.selectbox(
        "📂 Chats",
        options=st.session_state.chat_names if st.session_state.chat_names else ["Aucun chat"],
        index=(
            st.session_state.chat_names.index(st.session_state.selected_chat)
            if st.session_state.selected_chat in st.session_state.chat_names
            else 0
        )
    )


    #print(f"INDEX : {st.session_state.chat_names.index(st.session_state.selected_chat)}")

    if selected != "Aucun chat":
        #st.session_state.current_chat = selected
        st.session_state.selected_chat = selected

        #file_path = pdf_stotage_path + f"{chat_name}.pdf"
        file_path =  os.path.join(st.session_state.files, st.session_state.selected_chat)
        #st.write(file_path)

        print("File path:", file_path)
        print("Exists:", os.path.exists(file_path))
        print("Size:", os.path.getsize(file_path) if os.path.exists(file_path) else "N/A")

        #with open(file_path, "wb") as f :
        #    f.write(file_path)

        # traitement RAG
        raw_docs = load_pdf(file_path)
        chunks = chunk_document(raw_docs)

        vector_db = InMemoryVectorStore(embedding_model)
        vector_db.add_documents(chunks)

        # stockage
        #"file_path": file_path,
        #st.session_state.chats[chat_name] = {
        #    "chat_name" : chat_name,
        #    "messages": []
        #}

        st.session_state.vectorstores[st.session_state.selected_chat] = vector_db
        #st.session_state.json_path = f"{st.session_state.selected_chat}.json"
        st.session_state.json_path = f"{file_path}.json"

        if os.path.exists(st.session_state.json_path):
            with open(st.session_state.json_path, "r", encoding="utf-8") as f:
                st.session_state.chats = json.load(f)

        #save_chats()

        st.session_state.current_chat = st.session_state.selected_chat
        #st.rerun()


    uploaded_file = st.sidebar.file_uploader("➕ Nouveau PDF", type="pdf", accept_multiple_files=False)

    if uploaded_file != st.session_state.old_file:
        # Sélection automatique
        st.session_state.selected_chat = uploaded_file.name
        #file_path = save_upload_file(uploaded_file)
        file_path = save_upload_file(st.session_state.files, uploaded_file)
        print("ok")
        #st.rerun()
        st.session_state.chat_names = chats_list(st.session_state.files)

        st.session_state.chats = []

        file_path =  os.path.join(st.session_state.files, st.session_state.selected_chat)
        
        st.session_state.json_path = f"{file_path}.json" 

        st.session_state.current_chat = st.session_state.selected_chat

        st.session_state.old_file = uploaded_file

        #save_chats()
        #st.rerun()

    #st.session_state.chat_names = chats_list(file_path)

    current_chat = st.session_state.current_chat
    chat_data = {}
    if current_chat:
        #chat_data = st.session_state.chats[current_chat]
        file_path =  os.path.join(st.session_state.files, st.session_state.selected_chat)
        st.session_state.json_path =f"{file_path}.json"
        #chat_data = st.session_state.chats

        st.subheader(f"📄 {current_chat}")
        if os.path.exists(st.session_state.json_path):
            with open(st.session_state.json_path, "r", encoding="utf-8") as f:
                st.session_state.chats = json.load(f)

        save_chats()
        #st.rerun(scope="fragment")


    #for msg in chat_data[current_chat]["messages"]:
    for msg in st.session_state.chats:
        if msg.get("role") is not None :
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        else :
            continue


    query = st.chat_input("Posez votre question")

    if query:
        st.session_state.chats.append({"role": "user", "content": query})

        with st.chat_message("user"):
            st.write(query)

        # vector store spécifique au chat
        vector_db = st.session_state.vectorstores[current_chat]

        related_docs = vector_db.similarity_search(query)

        with st.spinner("Analyse du document ..........") :
            # Traitement de la réponse
            answer = generate_answer(query, related_docs)

        st.session_state.chats.append({"role": "assistant", "content": answer})

        with st.chat_message("assistant"):
            st.write(answer)

        save_chats()