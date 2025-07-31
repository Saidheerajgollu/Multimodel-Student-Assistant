import streamlit as st
import os
import tempfile
import uuid
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.llms import GoogleGenerativeAI
from langchain.chains import RetrievalQA
import google.generativeai as genai

# Page configuration
st.set_page_config(
    page_title="Multimodal Study Assistant",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = None
if 'rag_chain' not in st.session_state:
    st.session_state.rag_chain = None

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
        llm = GoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            max_output_tokens=2048
        )
        
        # Create RAG chain
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 5})
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

# Main app
st.title("📚 Multimodal Study Assistant")
st.markdown("Upload documents and ask questions using AI!")

# Sidebar for API key (for local testing)
if 'GOOGLE_API_KEY' not in st.secrets:
    api_key = st.sidebar.text_input("Google API Key", type="password", help="Enter your Google API key for Gemini AI")
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.secrets["GOOGLE_API_KEY"] = api_key

# Main content
tab1, tab2, tab3 = st.tabs(["📄 Upload Documents", "❓ Ask Questions", "📋 Document List"])

with tab1:
    st.header("Upload Documents")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file", 
        type=['pdf'],
        help="Upload a PDF document to analyze"
    )
    
    if uploaded_file is not None:
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                try:
                    # Extract text from PDF
                    text = extract_text_from_pdf(uploaded_file)
                    
                    if text:
                        # Create chunks
                        chunks = create_chunks(text)
                        st.success(f"✅ Extracted {len(chunks)} text chunks from document")
                        
                        # Setup RAG chain
                        vector_store, rag_chain = setup_rag_chain(chunks)
                        
                        if vector_store and rag_chain:
                            st.session_state.vector_store = vector_store
                            st.session_state.rag_chain = rag_chain
                            
                            # Store document info
                            doc_info = {
                                "name": uploaded_file.name,
                                "chunks": len(chunks),
                                "id": str(uuid.uuid4())
                            }
                            st.session_state.documents.append(doc_info)
                            
                            st.success(f"✅ Document '{uploaded_file.name}' processed successfully!")
                            st.info(f"Document ID: {doc_info['id']}")
                        else:
                            st.error("Failed to setup RAG chain")
                    else:
                        st.error("Failed to extract text from PDF")
                        
                except Exception as e:
                    st.error(f"Error processing document: {e}")

with tab2:
    st.header("Ask Questions")
    
    if st.session_state.rag_chain:
        question = st.text_area("Enter your question:", height=100)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Ask Question") and question:
                with st.spinner("Generating answer..."):
                    try:
                        answer = st.session_state.rag_chain.run(question)
                        st.subheader("Answer:")
                        st.write(answer)
                        
                        # Store Q&A for flashcards
                        st.session_state.last_qa = {"question": question, "answer": answer}
                        
                    except Exception as e:
                        st.error(f"Error generating answer: {e}")
        
        with col2:
            if 'last_qa' in st.session_state:
                if st.button("Generate Flashcards"):
                    with st.spinner("Generating flashcards..."):
                        flashcards = generate_flashcards(
                            st.session_state.last_qa["question"],
                            st.session_state.last_qa["answer"]
                        )
                        if flashcards:
                            st.subheader("📝 Flashcards:")
                            st.text_area("Flashcards", flashcards, height=200)
    else:
        st.warning("Please upload a document first to ask questions.")

with tab3:
    st.header("Document List")
    
    if st.session_state.documents:
        st.write("Uploaded documents:")
        for doc in st.session_state.documents:
            st.write(f"📄 {doc['name']} (ID: {doc['id']}) - {doc['chunks']} chunks")
    else:
        st.info("No documents uploaded yet.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, LangChain, and Google AI")

# Instructions for deployment
if st.sidebar.checkbox("Show Deployment Instructions"):
    st.sidebar.markdown("""
    ### 🚀 Deploy to Streamlit Cloud:
    
    1. Push this code to GitHub
    2. Go to [share.streamlit.io](https://share.streamlit.io)
    3. Connect your GitHub repository
    4. Set main file path to: `streamlit_app.py`
    5. Add your `GOOGLE_API_KEY` in the secrets
    6. Deploy!
    
    Your app will be live at: `https://your-app-name.streamlit.app`
    """) 