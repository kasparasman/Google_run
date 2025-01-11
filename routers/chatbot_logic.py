# --------------------------------------------------
# chatbotlogic.py
# --------------------------------------------------
import os
import uuid
import asyncio
import logging
from typing import Dict, Any
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Import our utility for cleaning environment variables
from .env_utils import load_and_clean_env_var

logger.info("Loading environment variables")
load_dotenv()

# Log environment setup
logger.debug("Setting up environment variables")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "default"

# Clean + load the OpenAI key
OPENAI_API_KEY = load_and_clean_env_var("OPENAI_API_KEY")

logger.info("Initializing OpenAI embeddings")
try:
    emb_start = time.time()
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    logger.debug("OpenAI embeddings initialized successfully")
    emb_end = time.time()
    logger.debug(f"[TIMING] Embeddings init took {emb_end - emb_start:.4f} seconds")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI embeddings: {e}", exc_info=True)
    raise

logger.info("Initializing Chroma vectorstore")
try:
    vcr_start = time.time()
    vectorstore = Chroma(
        persist_directory='../vectorstore',
        embedding_function=embeddings
    )
    logger.debug("Chroma vectorstore initialized successfully")
    vcr_end = time.time()
    logger.debug(f"[TIMING] vectorstore init took {vcr_end - vcr_start:.4f} seconds")
except Exception as e:
    logger.error(f"Failed to initialize Chroma vectorstore: {e}", exc_info=True)
    raise

logger.info("Setting up LLM and retriever")
try:
    # Use the cleaned key implicitly via environment if needed,
    # or pass it explicitly to ChatOpenAI if it has openai_api_key param:
    llm = ChatOpenAI(
        model_name="gpt-4",
        temperature=0,
        openai_api_key=OPENAI_API_KEY  # if needed
    )
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    logger.debug("LLM and retriever setup complete")
except Exception as e:
    logger.error(f"Failed to setup LLM or retriever: {e}", exc_info=True)
    raise

# Contextualize question
logger.info("Setting up question contextualization")
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question which might reference context in the chat history, "
    "formulate a standalone question which can be understood without the chat history. "
    "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

logger.debug("Creating history aware retriever")
history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

# QA chain
logger.info("Setting up QA chain")
system_prompt = (
    "You are an assistant for question-answering tasks about ZinZino health supplements. "
    "Use the following pieces of retrieved context to answer the question. If you don't know the answer, say you don't know. "
    "Use three sentences maximum and keep the answer concise.\n\n{context}"
)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# Statefully manage chat history
logger.info("Initializing chat history store")
store: Dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    logger.debug(f"Getting session history for session_id: {session_id}")
    if session_id not in store:
        logger.debug(f"Creating new chat history for session_id: {session_id}")
        store[session_id] = ChatMessageHistory()
    return store[session_id]

logger.info("Creating conversational RAG chain")
try:
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )
    logger.debug("Conversational RAG chain created successfully")
except Exception as e:
    logger.error(f"Failed to create conversational RAG chain: {e}", exc_info=True)
    raise

logger.info("Chatbot logic initialization complete")
