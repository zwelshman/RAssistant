import streamlit as st
import anthropic
import re

# Page config
st.set_page_config(
    page_title="R Code Wizard",
    page_icon="🧙‍♂️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Clean, modern CSS
st.markdown("""
    <style>
    /* Main background */
    .main {
        background: #f8f9fa;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom header */
    .custom-header {
        text-align: center;
        padding: 2rem 0 3rem 0;
    }
    
    .custom-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
    }
    
    .custom-header p {
        font-size: 1.1rem;
        color: #666;
        font-weight: 400;
    }
    
    /* Text area styling */
    .stTextArea textarea {
        background-color: white;
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        font-size: 16px;
        padding: 16px;
        transition: all 0.3s ease;
        color: #000000 !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Button styling */
    .stButton button {
        background: #667eea;
        color: white;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-size: 16px;
        font-weight: 600;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background: #5568d3;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Response container */
    .response-box {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* Code blocks */
    .stMarkdown code {
        background: #1e1e1e;
        color: #d4d4d4;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-size: 14px;
    }
    
    pre {
        background: #1e1e1e !important;
        border-radius: 8px;
        padding: 1.5rem;
        border: 1px solid #333;
    }
    
    pre code {
        background: transparent !important;
        color: #d4d4d4 !important;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.6;
    }
    
    /* Example chips */
    .example-chip {
        display: inline-block;
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        font-size: 14px;
        color: #666;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .example-chip:hover {
        border-color: #667eea;
        color: #667eea;
        background: #f0f2ff;
    }
    
    /* Info box */
    .info-box {
        background: #f0f2ff;
        border-left: 4px solid #667eea;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        font-size: 14px;
        color: #444;
    }
    
    /* Download button */
    .stDownloadButton button {
        background: white;
        color: #667eea;
        border: 2px solid #667eea;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    
    .stDownloadButton button:hover {
        background: #f0f2ff;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        font-weight: 600;
    }
    
    /* Examples and tips sections */
    .main h3 {
        color: #333;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 0.75rem;
    }
    
    .main ul {
        color: #666;
        font-size: 14px;
        line-height: 1.6;
    }
    
    /* Clean spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="custom-header">
        <h1>🧙‍♂️ R Code Wizard</h1>
        <p>Your AI assistant for R programming</p>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_question' not in st.session_state:
    st.session_state.current_question = ''

# Get API key
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("🔑 Please configure your ANTHROPIC_API_KEY in Streamlit secrets")
    st.stop()

# Example questions (always visible)
st.markdown("### 💡 Example Questions")
examples = [
    "How do I create a violin plot with ggplot2?",
    "Read and clean CSV data with dplyr",
    "Build a linear regression model",
    "Pivot data from wide to long format",
    "Create a correlation heatmap",
    "Handle missing values in a dataset"
]

cols = st.columns(2)
for idx, example in enumerate(examples):
    with cols[idx % 2]:
        st.markdown(f"- {example}")

# Main question input
r_question = st.text_area(
    "What would you like help with?",
    height=120,
    placeholder="Example: How do I create a bar chart showing patient outcomes by treatment group?",
    value=st.session_state.current_question,
    key="question_input",
    label_visibility="visible"
)

# Submit button
submit_button = st.button("✨ Generate Solution", type="primary", use_container_width=True)

def remove_scratchpad(text):
    """Remove scratchpad tags and their content from the response."""
    cleaned_text = re.sub(r'<scratchpad>.*?</scratchpad>', '', text, flags=re.DOTALL)
    return cleaned_text.strip()

# Process request
if submit_button:
    if not r_question:
        st.warning("👆 Please enter your question above")
    else:
        with st.spinner('🔮 Generating your solution...'):
            try:
                client = anthropic.Anthropic(api_key=api_key)
                
                prompt = f"""You are an expert R programmer and data scientist. 

Here is the R question or problem you need to solve:

<r_question>
{r_question}
</r_question>

Provide your response in two parts:

1. **R Code**: Well-commented, production-ready R code following best practices
2. **Summary**: Brief explanation of the approach, key functions used, and any important considerations

Provide one code example that is specific to health care, do not include a lot of methods or examples.

Use <scratchpad> tags if you need to think through complex multi-step problems before responding. 

If the question lacks necessary details (e.g., data structure, specific requirements), ask for clarification first.

If a user asks a question that is nothing to do with data analysis or R you must generate a very short response."""
                
                # Stream response in a container
                st.markdown('<div class="response-box">', unsafe_allow_html=True)
                response_placeholder = st.empty()
                full_response = ""
                
                with client.messages.stream(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=20000,
                    temperature=1,
                    messages=[{
                        "role": "user",
                        "content": [{
                            "type": "text",
                            "text": prompt
                        }]
                    }]
                ) as stream:
                    for text in stream.text_stream:
                        full_response += text
                        # Remove scratchpad in real-time
                        cleaned = remove_scratchpad(full_response)
                        response_placeholder.markdown(cleaned)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Get final cleaned response for download
                cleaned_response = remove_scratchpad(full_response)
                
                # Action buttons
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.download_button(
                        label="📥 Download Code",
                        data=cleaned_response,
                        file_name="r_solution.R",
                        mime="text/plain",
                        use_container_width=True
                    )
                
                with col2:
                    if st.button("🔄 Ask Another Question", use_container_width=True):
                        st.session_state.current_question = ''
                        st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Please check your API key and try again")

# Tips section (always visible)
st.markdown("### 📌 Tips for Better Results")
st.markdown("""
- Be specific about your data structure and variables
- Mention any packages you prefer (tidyverse, data.table, etc.)
- Share error messages if you're debugging
- Specify your desired output format
""")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #999; font-size: 14px; padding: 1rem;'>
        Powered by Claude Sonnet 4.5 | Built with Streamlit
    </div>
""", unsafe_allow_html=True)
