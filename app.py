from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from fastapi import FastAPI
from pathlib import Path
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
import os

# Load .env variables (make sure your .env file is in the same directory)
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
# 2. Build the Conversational Retrieval Chain with Memory
# =============================================================================

def build_conversational_chain(vectorstore: FAISS, openai_api_key: str):
    """
    Build the conversational retrieval chain using ChatOpenAI and conversation memory.
    This chain uses a custom prompt (with the "refine" chain type) to improve answer accuracy.
    """
    # Initialize the chat-based language model (chatbot approach)
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini", openai_api_key=openai_api_key)

    # Create a retriever from the vector store
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    
    # Create conversation memory to store chat history
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # Build the conversational retrieval chain using the "refine" chain type for iterative refinement.
    conv_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        chain_type="stuff",
    )
    
    return conv_chain, memory

# =============================================================================
# 3. Serve the Chatbot API using FastAPI
# =============================================================================

# Configuration: Ensure your .env contains the OPENAI_API_KEY variable.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SOURCE_MD_DIR = "source_data"  # Folder containing your .md and .pdf files

# Build vector store and conversational chain
try:
    vectorstore = build_vectorstore(SOURCE_MD_DIR, OPENAI_API_KEY)
    conv_chain, memory = build_conversational_chain(vectorstore, OPENAI_API_KEY)
except Exception as e:
    print(f"Error during initialization: {e}")
    exit(1)

# Initialize the FastAPI application.
app = FastAPI(title="Promtior Chatbot API")

# Allow CORS for frontend (http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Only allow requests from Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Define the input model for API requests.
class Query(BaseModel):
    question: str

@app.post("/query", summary="Get answer from the chatbot", response_description="Answer generated by the chatbot")
async def get_answer(query: Query):
    """
    Endpoint to handle user queries. It logs the retrieved document chunks and then generates
    an answer using the conversational retrieval chain, preserving conversation history.
    """
    try:
        
        # Generate an answer using the conversational chain (conversation history maintained automatically)
        result = conv_chain({"question": query.question})
        return {"answer": result["answer"]}
    except Exception as e:
        return {"error": str(e)}

# Run the API server locally.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
