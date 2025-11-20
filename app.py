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
r_question = st.text_area("Enter your R question:", height=150)

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

if st.button("Get Answer") and r_question:
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
                    "text": f"You are an expert data scientist with deep expertise in R programming, statistics, and data analysis. You will be helping users solve R programming problems, perform data analysis tasks, and provide statistical insights.\n\nHere is the R question or problem you need to solve:\n\n<r_question>\n{r_question}\n</r_question>\n\nPlease approach this problem with the following guidelines:\n\n- Provide clear, well-commented R code that follows best practices\n- Use appropriate R packages and functions for the task\n- Explain your approach and reasoning before providing the code\n- If the problem involves data analysis, consider data exploration, cleaning, and validation steps\n- For statistical problems, explain the assumptions and methodology\n- Include error handling where appropriate\n- Suggest alternative approaches when relevant\n\nFor complex problems that require multiple steps or careful planning, use <scratchpad> tags to think through your approach before providing your final response.\n\nStructure your response as follows:\n1. First, provide your analysis and reasoning for the approach\n2. Then, provide the R code solution inside <r_code> tags\n3. Finally, explain the output or results and any important considerations\n\nIf the question is unclear or lacks necessary information (such as data structure details), ask for clarification rather than making assumptions.\n\nBegin your analysis of the R question now."
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
