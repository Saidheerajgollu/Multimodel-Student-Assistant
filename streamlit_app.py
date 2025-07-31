import streamlit as st
import os
import tempfile
import uuid
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
import google.generativeai as genai
import base64
from datetime import datetime

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

def setup_rag_chain(chunks):
    """Setup RAG chain with embeddings and vector store"""
    try:
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Create vector store
        vector_store = Chroma.from_texts(
            texts=chunks,
            embedding=embeddings,
            persist_directory="./chroma_db"
        )
        
        # Setup LLM
        genai.configure(api_key=st.secrets.get("GOOGLE_API_KEY"))
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.1,
            max_output_tokens=2048
        )
        
        # Create RAG chain
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )
        
        return vector_store, rag_chain
    except Exception as e:
        st.error(f"Error setting up RAG chain: {e}")
        return None, None

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
        ["🏠 Dashboard", "📄 Upload Documents", "❓ Ask Questions", "📋 Document Library", "📝 Flashcards"]
    )
    
    # Stats
    if st.session_state.documents:
        st.markdown("### 📊 Statistics")
        total_docs = len(st.session_state.documents)
        total_chunks = sum(doc.get('chunks', 0) for doc in st.session_state.documents)
        st.metric("Documents", total_docs)
        st.metric("Text Chunks", total_chunks)

# Main content based on navigation
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
            st.switch_page("📄 Upload Documents")
    
    with col2:
        if st.button("❓ Start Asking Questions", use_container_width=True):
            st.switch_page("❓ Ask Questions")

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
                        
                        # Setup RAG chain
                        status_text.text("🤖 Setting up AI models...")
                        progress_bar.progress(60)
                        
                        vector_store, rag_chain = setup_rag_chain(chunks)
                        
                        if vector_store and rag_chain:
                            st.session_state.vector_store = vector_store
                            st.session_state.rag_chain = rag_chain
                            
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
                        result = st.session_state.rag_chain({"query": question})
                        answer = result["result"]
                        
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
            st.switch_page("📄 Upload Documents")

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
                        st.switch_page("❓ Ask Questions")
                
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

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>Built with ❤️ using Streamlit, LangChain, and Google AI</p>
    <p>🎓 Your intelligent study companion</p>
</div>
""", unsafe_allow_html=True) 