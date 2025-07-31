import streamlit as st
import os
import tempfile
import uuid
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
import google.generativeai as genai
import base64
from datetime import datetime
import pickle
import json
import io

# Page configuration with custom theme
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9fa;
        margin: 1rem 0;
    }
    
    .success-message {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .question-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .answer-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .flashcard-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .stats-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 0.5rem;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Custom button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* File uploader styling */
    .stFileUploader > div > div {
        border: 2px dashed #667eea;
        border-radius: 10px;
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'rag_chain' not in st.session_state:
    st.session_state.rag_chain = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Ensure session state for navigation
if 'page' not in st.session_state:
    st.session_state['page'] = "🏠 Dashboard"

# Initialize AI models
@st.cache_resource
def initialize_ai_models():
    """Initialize AI models and vector store"""
    try:
        with st.spinner("Setting up AI models..."):
            # Initialize embeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # Initialize FAISS with cloud storage
            vector_store = FAISSWithCloudStorage(embeddings)
            
            # Try to load existing index from cloud
            existing_store = vector_store.load_from_cloud()
            if existing_store:
                vector_store.vectorstore = existing_store
            
            # Initialize LLM
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.0-pro",
                google_api_key=st.secrets.get("GOOGLE_API_KEY"),
                temperature=0.7,
                convert_system_message_to_human=True
            )
            
            # Create RAG chain
            if vector_store.vectorstore:
                rag_chain = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=vector_store.vectorstore.as_retriever(search_kwargs={"k": 5}),
                    return_source_documents=True
                )
            else:
                rag_chain = None
            
            st.success("✅ AI models initialized successfully!")
            return embeddings, vector_store, llm, rag_chain
            
    except Exception as e:
        st.error(f"❌ Failed to setup AI processing: {str(e)}")
        return None, None, None, None

# This will be called after all functions are defined

# Initialize Google Cloud Storage
def init_google_storage():
    """Initialize Google Cloud Storage client"""
    try:
        # For Streamlit Cloud, we'll use service account key from secrets
        if 'GOOGLE_CLOUD_CREDENTIALS' in st.secrets:
            import json
            credentials_info = json.loads(st.secrets['GOOGLE_CLOUD_CREDENTIALS'])
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            storage_client = storage.Client(credentials=credentials)
        else:
            # Fallback to default credentials (for local development)
            storage_client = storage.Client()
        
        bucket_name = st.secrets.get('GOOGLE_CLOUD_BUCKET', 'your-bucket-name')
        bucket = storage_client.bucket(bucket_name)
        return storage_client, bucket
    except Exception as e:
        st.error(f"Failed to initialize Google Cloud Storage: {str(e)}")
        return None, None

# FAISS Vector Store with Google Cloud Storage
class FAISSWithCloudStorage:
    def __init__(self, embeddings, bucket_name="your-bucket-name"):
        self.embeddings = embeddings
        self.bucket_name = bucket_name
        self.storage_client, self.bucket = init_google_storage()
        self.vectorstore = None
        self.index_name = "faiss_index"
        
    def load_from_cloud(self):
        """Load FAISS index from Google Cloud Storage"""
        try:
            if not self.bucket:
                return None
                
            # Download index files from cloud
            index_blob = self.bucket.blob(f"{self.index_name}.pkl")
            if index_blob.exists():
                index_data = index_blob.download_as_bytes()
                self.vectorstore = pickle.loads(index_data)
                st.success("✅ Loaded existing vector store from Google Cloud")
                return self.vectorstore
            else:
                st.info("No existing vector store found. Starting fresh.")
                return None
        except Exception as e:
            st.warning(f"Could not load from cloud: {str(e)}")
            return None
    
    def save_to_cloud(self):
        """Save FAISS index to Google Cloud Storage"""
        try:
            if not self.bucket or not self.vectorstore:
                return
                
            # Serialize and upload to cloud
            index_data = pickle.dumps(self.vectorstore)
            index_blob = self.bucket.blob(f"{self.index_name}.pkl")
            index_blob.upload_from_string(index_data)
            st.success("✅ Saved vector store to Google Cloud")
        except Exception as e:
            st.error(f"Failed to save to cloud: {str(e)}")
    
    def add_documents(self, documents):
        """Add documents to FAISS vector store"""
        try:
            if not self.vectorstore:
                # Create new FAISS index
                self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            else:
                # Add to existing index
                self.vectorstore.add_documents(documents)
            
            # Save to cloud after adding documents
            self.save_to_cloud()
            return self.vectorstore
        except Exception as e:
            st.error(f"Failed to add documents: {str(e)}")
            return None
    
    def similarity_search(self, query, k=5):
        """Search for similar documents"""
        if not self.vectorstore:
            return []
        try:
            return self.vectorstore.similarity_search(query, k=k)
        except Exception as e:
            st.error(f"Search failed: {str(e)}")
            return []

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None

def create_chunks(text, chunk_size=1000, chunk_overlap=200):
    """Split text into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(text)
    return chunks

# This function is no longer needed as we use FAISSWithCloudStorage

def generate_flashcards(question, answer):
    """Generate flashcards from Q&A"""
    try:
        genai.configure(api_key=st.secrets.get("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Based on this question and answer, create 3-5 flashcards in this format:
        
        Question: [Clear, specific question]
        Answer: [Concise, accurate answer]
        
        Original Q&A:
        Q: {question}
        A: {answer}
        
        Generate flashcards that test understanding of the key concepts.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating flashcards: {e}")
        return None

# Sidebar configuration
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h2>🎓 AI Study Assistant</h2>
        <p>Your intelligent learning companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Key input
    if 'GOOGLE_API_KEY' not in st.secrets:
        api_key = st.text_input("🔑 Google API Key", type="password", help="Enter your Google API key for Gemini AI")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            st.secrets["GOOGLE_API_KEY"] = api_key
            st.success("✅ API Key configured!")
    
    # Navigation
    st.markdown("### 📚 Navigation")
    page = st.selectbox(
        "Choose a section:",
        ["🏠 Dashboard", "📄 Upload Documents", "❓ Ask Questions", "📋 Document Library", "📝 Flashcards"],
        key="page"
    )
    # DO NOT set st.session_state['page'] = page here!
    
    # Stats
    if st.session_state.documents:
        st.markdown("### 📊 Statistics")
        total_docs = len(st.session_state.documents)
        total_chunks = sum(doc.get('chunks', 0) for doc in st.session_state.documents)
        st.metric("Documents", total_docs)
        st.metric("Text Chunks", total_chunks)

# Main content based on navigation
page = st.session_state['page']
if page == "🏠 Dashboard":
    # Hero section
    st.markdown("""
    <div class="main-header">
        <h1>🎓 AI Study Assistant</h1>
        <p>Transform your learning with AI-powered document analysis and intelligent Q&A</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 Smart Document Processing</h3>
            <p>Upload PDF documents and let AI extract, analyze, and organize your content for easy learning.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>❓ Intelligent Q&A</h3>
            <p>Ask questions about your documents and get accurate, contextual answers powered by advanced AI.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📝 Flashcard Generation</h3>
            <p>Automatically create study flashcards from your Q&A sessions to reinforce learning.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Upload New Document", use_container_width=True):
            st.session_state['page'] = "📄 Upload Documents"
    
    with col2:
        if st.button("❓ Start Asking Questions", use_container_width=True):
            st.session_state['page'] = "❓ Ask Questions"

elif page == "📄 Upload Documents":
    st.markdown("""
    <div class="main-header">
        <h1>📄 Upload Documents</h1>
        <p>Upload your PDF documents to start learning with AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload area
    st.markdown("""
    <div class="upload-area">
        <h3>📁 Drop your PDF files here</h3>
        <p>Supported format: PDF</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file", 
        type=['pdf'],
        help="Upload a PDF document to analyze",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        # File info
        file_size = len(uploaded_file.getvalue()) / 1024  # KB
        st.info(f"📄 **File:** {uploaded_file.name} | 📏 **Size:** {file_size:.1f} KB")
        
        if st.button("🚀 Process Document", use_container_width=True):
            with st.spinner("🔄 Processing your document..."):
                try:
                    # Extract text from PDF
                    text = extract_text_from_pdf(uploaded_file)
                    
                    if text:
                        # Create chunks
                        chunks = create_chunks(text)
                        
                        # Progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("📝 Extracting text chunks...")
                        progress_bar.progress(30)
                        
                        # Setup RAG chain with FAISS
                        status_text.text("🤖 Setting up AI models...")
                        progress_bar.progress(60)
                        
                        # Create documents for vector store
                        from langchain.schema import Document
                        documents = [Document(page_content=chunk, metadata={"source": uploaded_file.name}) for chunk in chunks]
                        
                        # Add to FAISS vector store
                        if st.session_state.vector_store:
                            st.session_state.vector_store.add_documents(documents)
                            
                            # Update RAG chain with new vector store
                            if st.session_state.vector_store.vectorstore:
                                st.session_state.rag_chain = RetrievalQA.from_chain_type(
                                    llm=st.session_state.llm,
                                    chain_type="stuff",
                                    retriever=st.session_state.vector_store.vectorstore.as_retriever(search_kwargs={"k": 5}),
                                    return_source_documents=True
                                )
                            
                            # Store document info
                            doc_info = {
                                "name": uploaded_file.name,
                                "chunks": len(chunks),
                                "id": str(uuid.uuid4()),
                                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "size": f"{file_size:.1f} KB"
                            }
                            st.session_state.documents.append(doc_info)
                            
                            progress_bar.progress(100)
                            status_text.text("✅ Processing complete!")
                            
                            st.markdown(f"""
                            <div class="success-message">
                                <h3>✅ Document processed successfully!</h3>
                                <p><strong>Document:</strong> {uploaded_file.name}</p>
                                <p><strong>Chunks extracted:</strong> {len(chunks)}</p>
                                <p><strong>Document ID:</strong> {doc_info['id']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("❌ Failed to setup AI processing")
                    else:
                        st.error("❌ Failed to extract text from PDF")
                        
                except Exception as e:
                    st.error(f"❌ Error processing document: {e}")

elif page == "❓ Ask Questions":
    st.markdown("""
    <div class="main-header">
        <h1>❓ Ask Questions</h1>
        <p>Get intelligent answers about your documents</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.rag_chain:
        # Question input
        st.markdown("""
        <div class="question-box">
            <h3>💭 What would you like to know?</h3>
        </div>
        """, unsafe_allow_html=True)
        
        question = st.text_area("Enter your question:", height=100, placeholder="Ask anything about your uploaded documents...")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🤖 Ask AI", use_container_width=True) and question:
                with st.spinner("🧠 Thinking..."):
                    try:
                        # Get answer with source documents
                        result = st.session_state.rag_chain({"query": question})
                        answer = result["result"]
                        source_docs = result.get("source_documents", [])
                        
                        # Store in chat history
                        st.session_state.chat_history.append({
                            "question": question,
                            "answer": answer,
                            "timestamp": datetime.now().strftime("%H:%M")
                        })
                        
                        st.markdown(f"""
                        <div class="answer-box">
                            <h4>🤖 AI Answer:</h4>
                            <p>{answer}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show source documents if available
                        if source_docs:
                            with st.expander("📚 View Sources"):
                                for i, doc in enumerate(source_docs[:3]):  # Show top 3 sources
                                    st.markdown(f"**Source {i+1}:** {doc.page_content[:200]}...")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating answer: {e}")
        
        with col2:
            if st.session_state.chat_history:
                if st.button("📝 Generate Flashcards", use_container_width=True):
                    with st.spinner("📝 Creating flashcards..."):
                        last_qa = st.session_state.chat_history[-1]
                        flashcards = generate_flashcards(
                            last_qa["question"],
                            last_qa["answer"]
                        )
                        if flashcards:
                            st.markdown(f"""
                            <div class="flashcard-box">
                                <h4>📝 Study Flashcards:</h4>
                                <pre>{flashcards}</pre>
                            </div>
                            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Please upload a document first to ask questions.")
        if st.button("📄 Upload Document"):
            st.session_state['page'] = "📄 Upload Documents"

elif page == "📋 Document Library":
    st.markdown("""
    <div class="main-header">
        <h1>📋 Document Library</h1>
        <p>Manage your uploaded documents</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.documents:
        # Document cards
        for i, doc in enumerate(st.session_state.documents):
            with st.expander(f"📄 {doc['name']}", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Chunks", doc['chunks'])
                
                with col2:
                    st.metric("Size", doc['size'])
                
                with col3:
                    st.metric("Uploaded", doc['upload_time'])
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"❓ Ask about this document", key=f"ask_{i}"):
                        st.session_state['page'] = "❓ Ask Questions"
                
                with col2:
                    if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                        st.session_state.documents.pop(i)
                        st.rerun()
    else:
        st.info("📚 No documents uploaded yet. Upload your first document to get started!")

elif page == "📝 Flashcards":
    st.markdown("""
    <div class="main-header">
        <h1>📝 Flashcards</h1>
        <p>Review your generated study materials</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.chat_history:
        for i, chat in enumerate(st.session_state.chat_history):
            with st.expander(f"💬 Q&A Session {i+1} - {chat['timestamp']}", expanded=True):
                st.markdown(f"""
                <div class="question-box">
                    <h4>❓ Question:</h4>
                    <p>{chat['question']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="answer-box">
                    <h4>🤖 Answer:</h4>
                    <p>{chat['answer']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("📝 No Q&A sessions yet. Ask some questions to generate flashcards!")

# Initialize AI models after all functions are defined
embeddings, vector_store, llm, rag_chain = initialize_ai_models()
if embeddings and vector_store and llm:
    st.session_state.embeddings = embeddings
    st.session_state.vector_store = vector_store
    st.session_state.llm = llm
    st.session_state.rag_chain = rag_chain

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Built with ❤️ using Streamlit, LangChain, and Google AI</p>
    <p>🎓 Your intelligent study companion</p>
</div>
""", unsafe_allow_html=True) 