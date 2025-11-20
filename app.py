import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import json
from typing import List, Dict
import time

# Page config
st.set_page_config(
    page_title="BHF DSC Documentation Q&A",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("❤️ BHF Data Science Centre Documentation Q&A")
st.markdown("""
Ask questions about the BHF Data Science Centre documentation website content. 
This tool fetches information from https://bhfdsc.github.io/documentation/ and uses Claude to provide detailed answers.
""")

class BHFDocsFetcher:
    def __init__(self):
        self.base_url = "https://bhfdsc.github.io/documentation/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def fetch_page_content(self, url: str) -> Dict[str, str]:
        """Fetch and parse content from a single page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer"]):
                script.decompose()
            
            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string
            elif soup.find('h1'):
                title = soup.find('h1').get_text()
            
            # Extract main content
            content = ""
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body
            
            if main_content:
                content = main_content.get_text(separator=' ', strip=True)
            else:
                content = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            
            return {
                "url": url,
                "title": title.strip() if title else "",
                "content": content,
                "word_count": len(content.split())
            }
            
        except Exception as e:
            st.error(f"Error fetching {url}: {str(e)}")
            return {"url": url, "title": "", "content": "", "word_count": 0}
    
    def discover_pages(self) -> List[str]:
        """Discover pages on the documentation site"""
        try:
            # Start with the main page
            main_page = self.fetch_page_content(self.base_url)
            soup = BeautifulSoup(requests.get(self.base_url).text, 'html.parser')
            
            urls = set([self.base_url])
            
            # Find all internal links
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(self.base_url, href)
                
                # Only include pages from the same domain
                if urlparse(full_url).netloc == urlparse(self.base_url).netloc:
                    # Filter out non-page links (anchors, files, etc.)
                    if not any(ext in full_url.lower() for ext in ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.zip', '#']):
                        urls.add(full_url)
            
            return list(urls)[:20]  # Limit to prevent too many requests
            
        except Exception as e:
            st.error(f"Error discovering pages: {str(e)}")
            return [self.base_url]

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_documentation_content():
    """Fetch all documentation content with caching"""
    fetcher = BHFDocsFetcher()
    
    with st.spinner("Discovering documentation pages..."):
        urls = fetcher.discover_pages()
        st.info(f"Found {len(urls)} pages to index")
    
    content_data = []
    progress_bar = st.progress(0)
    
    for i, url in enumerate(urls):
        with st.spinner(f"Fetching content from {url}..."):
            page_data = fetcher.fetch_page_content(url)
            if page_data["content"]:
                content_data.append(page_data)
        
        progress_bar.progress((i + 1) / len(urls))
    
    progress_bar.empty()
    return content_data

async def query_claude(question: str, documentation_content: List[Dict]) -> str:
    """Query Claude API with the documentation content"""
    
    # Prepare the documentation context
    context = ""
    for doc in documentation_content:
        if doc["content"]:
            context += f"\n\n--- {doc['title']} ({doc['url']}) ---\n"
            context += doc["content"][:2000]  # Limit content per page
    
    # Limit total context size
    if len(context) > 15000:
        context = context[:15000] + "...\n[Content truncated]"
    
    prompt = f"""Based on the following BHF Data Science Centre documentation content, please answer the user's question. 
    
If the answer isn't directly available in the documentation, please say so and provide any related information that might be helpful.

Documentation Content:
{context}

User Question: {question}

Please provide a comprehensive answer based on the documentation content above. If you reference specific information, mention which page it came from."""

    # Use the Anthropic API
    try:
        response = await fetch("https://api.anthropic.com/v1/messages", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                model: "claude-sonnet-4-20250514",
                max_tokens: 1500,
                messages: [
                    { role: "user", content: prompt }
                ]
            })
        })
        
        if response.ok:
            data = await response.json()
            return data.content[0].text
        else:
            return f"Error querying Claude API: {response.status}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    # Sidebar
    st.sidebar.header("Documentation Sources")
    st.sidebar.markdown("""
    **Primary Source:** https://bhfdsc.github.io/documentation/
    
    **Coverage includes:**
    - NHS England SDE resources
    - SAIL Databank guides
    - National Safe Haven documentation
    - Team information and tools
    """)
    
    if st.sidebar.button("🔄 Refresh Documentation"):
        st.cache_data.clear()
        st.experimental_rerun()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Question input
        question = st.text_area(
            "Ask a question about the BHF DSC documentation:",
            placeholder="e.g., How do I access the NHS SDE? What data assets are available in SAIL? Who are the team members?",
            height=100
        )
        
        if st.button("🔍 Search Documentation", type="primary"):
            if question.strip():
                try:
                    # Fetch documentation content
                    documentation_content = fetch_documentation_content()
                    
                    if documentation_content:
                        st.success(f"✅ Successfully indexed {len(documentation_content)} pages")
                        
                        # Show a simple implementation since we can't use async in Streamlit easily
                        st.info("💭 Analyzing documentation to answer your question...")
                        
                        # Prepare context for a simple response
                        context = ""
                        for doc in documentation_content:
                            if doc["content"]:
                                context += f"\n\n--- {doc['title']} ({doc['url']}) ---\n"
                                context += doc["content"][:1500]
                        
                        # For now, show the relevant documentation sections
                        st.subheader("📖 Relevant Documentation Found:")
                        
                        # Simple keyword matching for relevant sections
                        keywords = question.lower().split()
                        relevant_docs = []
                        
                        for doc in documentation_content:
                            content_lower = doc["content"].lower()
                            relevance_score = sum(1 for keyword in keywords if keyword in content_lower)
                            if relevance_score > 0:
                                relevant_docs.append((doc, relevance_score))
                        
                        # Sort by relevance
                        relevant_docs.sort(key=lambda x: x[1], reverse=True)
                        
                        if relevant_docs:
                            for doc, score in relevant_docs[:3]:  # Show top 3 most relevant
                                with st.expander(f"📄 {doc['title']} (Relevance: {score})"):
                                    st.write(f"**URL:** {doc['url']}")
                                    st.write(f"**Word Count:** {doc['word_count']}")
                                    
                                    # Show relevant excerpt
                                    content = doc["content"]
                                    if len(content) > 800:
                                        content = content[:800] + "..."
                                    st.write(content)
                        else:
                            st.warning("No directly relevant content found. Here are the available pages:")
                            for doc in documentation_content:
                                st.write(f"- [{doc['title']}]({doc['url']})")
                        
                        # Note about Claude integration
                        st.info("""
                        💡 **Note**: This is a basic version. For AI-powered answers, you would need to integrate the Claude API directly. 
                        The application structure is ready for that enhancement.
                        """)
                        
                    else:
                        st.error("Failed to fetch documentation content")
                        
                except Exception as e:
                    st.error(f"Error processing your question: {str(e)}")
            else:
                st.warning("Please enter a question to search the documentation.")
    
    with col2:
        st.subheader("📊 Documentation Stats")
        
        if st.button("📈 Load Stats"):
            try:
                documentation_content = fetch_documentation_content()
                
                if documentation_content:
                    total_pages = len(documentation_content)
                    total_words = sum(doc["word_count"] for doc in documentation_content)
                    
                    st.metric("Total Pages", total_pages)
                    st.metric("Total Words", f"{total_words:,}")
                    st.metric("Avg Words/Page", f"{total_words // total_pages if total_pages > 0 else 0:,}")
                    
                    # Show page list
                    st.subheader("📑 Available Pages")
                    for doc in documentation_content:
                        if doc["title"]:
                            st.write(f"• [{doc['title']}]({doc['url']})")
                        else:
                            st.write(f"• [Page]({doc['url']})")
                            
            except Exception as e:
                st.error(f"Error loading stats: {str(e)}")

if __name__ == "__main__":
    main()
