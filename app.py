import streamlit as st
import anthropic

st.title("🧙‍♂️ R Code Wizard")

# Get API key
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("Please set ANTHROPIC_API_KEY in Streamlit secrets")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about R programming..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response with streaming
    with st.chat_message("assistant"):
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build the prompt with instructions
        system_prompt = """You are an expert R programmer and data scientist. 

Provide your response in two parts:

1. **R Code**: Well-commented, production-ready R code following best practices
2. **Summary**: Brief explanation of the approach, key functions used, and any important considerations

Provide one code example that is specific to health care, do not include a lot of methods or examples.

If the question lacks necessary details (e.g., data structure, specific requirements), ask for clarification first.

If a user asks a question that is nothing to do with data analysis or R you must generate a very short response."""
        
        # Create messages list with system context
        messages_with_context = []
        
        # Add system context as first user message if this is the first message
        if len(st.session_state.messages) == 1:
            messages_with_context.append({
                "role": "user", 
                "content": system_prompt + "\n\n" + st.session_state.messages[0]["content"]
            })
        else:
            # For subsequent messages, include all history
            messages_with_context = [
                {"role": m["role"], "content": m["content"]} 
                for m in st.session_state.messages
            ]
        
        full_response = ""
        message_placeholder = st.empty()
        
        with client.messages.stream(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            messages=messages_with_context
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
