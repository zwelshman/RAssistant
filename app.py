import streamlit as st
import anthropic
import re

st.title("R Programming Assistant")
st.write("Ask me any R programming question!")

# Get API key from secrets
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("Please set up your ANTHROPIC_API_KEY in Streamlit secrets!")
    st.stop()

# Question input
R_QUESTION = st.text_area("Enter your R question:", height=150)

def format_response(text):
    """Format the response to display R code with syntax highlighting."""
    # Split by <r_code> tags
    parts = re.split(r'<r_code>|</r_code>', text)
    
    formatted_output = []
    for i, part in enumerate(parts):
        if i % 2 == 0:  # Text outside r_code tags
            formatted_output.append(('text', part))
        else:  # Code inside r_code tags
            formatted_output.append(('code', part))
    
    return formatted_output

if st.button("Get Answer") and R_QUESTION:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Create empty container for streaming response
        full_response = ""
        
        # Stream the response
        with client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            max_tokens=20000,
            temperature=1,
            messages=[{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": "You are an expert R programmer and data scientist. \n\nHere is the R question or problem you need to solve:\n\n<r_question>\n{{R_QUESTION}}\n</r_question>\n\nProvide your response in two parts:\n\n1. **R Code**: Well-commented, production-ready R code following best practices\n2. **Summary**: Brief explanation of the approach, key functions used, and any important considerations\n\nUse <scratchpad> tags if you need to think through complex multi-step problems before responding.\n\nIf the question lacks necessary details (e.g., data structure, specific requirements), ask for clarification first."
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
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
