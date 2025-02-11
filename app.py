from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA  # Use RetrievalQA instead of ConversationalRetrievalChain
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from langserve import add_routes
import os

# Load .env variables (ensure your .env file is in the same directory)
load_dotenv()

# =============================================================================
# 1. Data Storage & Vectorization (Markdown + PDF)
# =============================================================================

def build_vectorstore(source_dir: str, openai_api_key: str) -> FAISS:
    """
    Load and split all Markdown and PDF files in the specified directory,
    then build a FAISS vector store from the chunks.
    """
    source_path = Path(source_dir)
    if not source_path.exists() or not source_path.is_dir():
        raise FileNotFoundError(f"Directory '{source_dir}' not found or is not a directory!")

    all_documents = []

    # Load Markdown documents
    for md_file in source_path.glob("*.md"):
        loader = TextLoader(str(md_file), encoding="utf-8")
        documents = loader.load()
        all_documents.extend(documents)

    # Load PDF documents
    for pdf_file in source_path.glob("*.pdf"):
        loader = PyPDFLoader(str(pdf_file))
        documents = loader.load()
        all_documents.extend(documents)

    if not all_documents:
        raise ValueError("No Markdown or PDF files found or all files are empty. Please check the directory content.")

    # Split documents using a Recursive Character Text Splitter
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
    docs = text_splitter.split_documents(all_documents)

    if not docs:
        raise ValueError("No document chunks were created! Check the content and structure of your files.")

    # Initialize OpenAI embeddings (using a specified embedding model)
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key, model="text-embedding-3-large")
    vectorstore = FAISS.from_documents(docs, embeddings)

    return vectorstore

# =============================================================================
# 2. Build the Retrieval Chain Without Memory
# =============================================================================

def build_retrieval_chain(vectorstore: FAISS, openai_api_key: str):
    """
    Build a retrieval QA chain (without conversation memory) using ChatOpenAI.
    """
    # Initialize the chat-based language model (chatbot approach)
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini", openai_api_key=openai_api_key)

    # Create a retriever from the vector store
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    
    # Build the retrieval QA chain using the "stuff" chain type
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
    )
    
    return qa_chain

# =============================================================================
# 3. Prepare the Chain and Serve Using LangServe
# =============================================================================

# Configuration: Ensure your .env contains the OPENAI_API_KEY variable.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SOURCE_MD_DIR = "source_data"  # Folder containing your .md and .pdf files

try:
    vectorstore = build_vectorstore(SOURCE_MD_DIR, OPENAI_API_KEY)
    qa_chain = build_retrieval_chain(vectorstore, OPENAI_API_KEY)
except Exception as e:
    print(f"Error during initialization: {e}")
    exit(1)

# Create a FastAPI app and add LangServe routes for your chain.
app = FastAPI(title="Promtior Chatbot API")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)

add_routes(app, qa_chain, path="/query")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)