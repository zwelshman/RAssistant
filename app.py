import streamlit as st
import anthropic
import re

# Page config
st.set_page_config(
    page_title="R Code Wizard 🧙‍♂️",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stTextArea textarea {
        background-color: #2d3748;
        color: #e2e8f0;
        border-radius: 10px;
        border: 2px solid #4a5568;
        font-size: 16px;
    }
    .stButton button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 25px;
        padding: 15px 40px;
        font-size: 18px;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    .title-container {
        text-align: center;
        padding: 20px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 30px;
    }
    .title-text {
        font-size: 3.5em;
        font-weight: bold;
        background: linear-gradient(90deg, #ffd89b 0%, #19547b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .subtitle-text {
        color: white;
        font-size: 1.3em;
        margin-top: 10px;
    }
    .response-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 25px;
        margin-top: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="title-container">
        <h1 class="title-text">🧙‍♂️ R Code Wizard</h1>
        <p class="subtitle-text">Your magical assistant for R programming ✨</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🎯 Quick Tips")
    st.info("""
    **Get the best results:**
    - Be specific about your data structure
    - Mention packages you prefer
    - Share error messages if debugging
    - Specify output format needs
    """)
    
    st.markdown("## 📚 Example Questions")
    examples = [
        "How do I pivot data with dplyr?",
        "Create a ggplot2 scatter plot",
        "Read and clean CSV data",
        "Build a linear regression model"
    ]
    for example in examples:
        if st.button(example, key=example):
            st.session_state.example_question = example
    
    st.markdown("---")
    st.markdown("### ⚡ Powered by Claude Sonnet 4.5")

# Get API key from secrets
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("🔑 Please set up your ANTHROPIC_API_KEY in Streamlit secrets!")
    st.stop()

# Question input with columns for better layout
col1, col2 = st.columns([3, 1])

with col1:
    # Pre-fill with example if clicked
    default_value = st.session_state.get('example_question', '')
    r_question = st.text_area(
        "💭 What R challenge can I help you solve?",
        height=150,
        placeholder="e.g., How do I create a violin plot with ggplot2 showing multiple groups?",
        value=default_value
    )
    if default_value:
        st.session_state.example_question = ''  # Clear after use

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    submit_button = st.button("🚀 Get Solution", use_container_width=True)

def format_response(text):
    """Format the response to display R code with syntax highlighting."""
    parts = re.split(r'<r_code>|</r_code>', text)
    
    formatted_output = []
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Text outside r_code tags
            formatted_output.append(('text', part))
        else:  # Code inside r_code tags
            formatted_output.append(('code', part))
    
    return formatted_output

if submit_button and r_question:
    with st.spinner('🔮 Conjuring your R solution...'):
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

Use <scratchpad> tags if you need to think through complex multi-step problems before responding.

If the question lacks necessary details (e.g., data structure, specific requirements), ask for clarification first."""
            
            full_response = ""
            
            # Create a container for the response
            response_container = st.container()
            
            with response_container:
                st.markdown('<div class="response-container">', unsafe_allow_html=True)
                
                # Stream the response
                with client.messages.stream(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=20000,
                    temperature=0.1,
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
                
                # Format and display the final response
                formatted_parts = format_response(full_response)
                
                for part_type, content in formatted_parts:
                    if part_type == 'text':
                        st.markdown(content)
                    else:  # code
                        st.code(content, language='r')
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Add action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        label="📥 Download Code",
                        data=full_response,
                        file_name="r_solution.R",
                        mime="text/plain"
                    )
                with col2:
                    if st.button("🔄 Ask Follow-up"):
                        st.info("💡 Just type your follow-up question above!")
                with col3:
                    if st.button("⭐ New Question"):
                        st.rerun()
            
        except Exception as e:
            st.error(f"❌ Oops! Something went wrong: {str(e)}")
            st.info("💡 Try refreshing the page or checking your API key.")

elif submit_button and not r_question:
    st.warning("🤔 Please enter a question first!")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: white; padding: 20px;'>
        <p>Made with ❤️ using Streamlit and Claude AI | 
        <a href='https://www.anthropic.com' style='color: #ffd89b;'>Learn more about Claude</a></p>
    </div>
""", unsafe_allow_html=True)
