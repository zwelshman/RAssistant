import streamlit as st
import anthropic

st.title("R Programming Assistant")
st.write("Ask me any R programming question!")

# Input for API key (stored in session)
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''

api_key = st.text_input("Enter your Anthropic API Key:", type="password", value=st.session_state.api_key)
if api_key:
    st.session_state.api_key = api_key

# Question input
r_question = st.text_area("Enter your R question:", height=150)

if st.button("Get Answer") and api_key and r_question:
    with st.spinner("Thinking..."):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
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
            )
            st.markdown(message.content[0].text)
        except Exception as e:
            st.error(f"Error: {str(e)}")
