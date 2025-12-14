import streamlit as st
import os
import json
import time
from dotenv import load_dotenv
from scraper import fetch_website_links, fetch_website_contents
from openai import OpenAI

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Brochure Generator",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        height: 3rem;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: rgba(100, 100, 100, 0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
gemini = OpenAI(base_url=GEMINI_BASE_URL, api_key=api_key)
MODEL = "gemini-2.5-flash"

# System prompts
link_system_prompt = """
You are provided with a list of links found on a webpage.
You are able to decide which of the links would be most relevant to include in a brochure about the company,
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:

{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

brochure_system_prompt = """
You are an assistant that analyzes the contents of several relevant pages from a company website
and creates a short brochure about the company for prospective customers, investors and recruits.
Respond in markdown without code blocks.
Include details of company culture, customers and careers/jobs if you have the information.
"""

# Helper functions
def get_links_user_prompt(url):
    user_prompt = f"""
Here is the list of links on the website {url} -
Please decide which of these are relevant web links for a brochure about the company, 
respond with the full https URL in JSON format.
Do not include Terms of Service, Privacy, email links.

Links (some might be relative links):

"""
    links = fetch_website_links(url)
    user_prompt += "\n".join(links)
    return user_prompt

def select_relevant_links(url):
    try:
        response = gemini.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": link_system_prompt},
                {"role": "user", "content": get_links_user_prompt(url)}
            ],
            response_format={"type": "json_object"}
        )
        result = response.choices[0].message.content
        links = json.loads(result)
        return links
    except Exception as e:
        st.error(f"Error selecting links: {str(e)}")
        return {"links": []}

def fetch_page_and_all_relevant_links(url):
    contents = fetch_website_contents(url)
    relevant_links = select_relevant_links(url)
    result = f"## Landing Page:\n\n{contents}\n## Relevant Links:\n"
    for link in relevant_links['links']:
        result += f"\n\n### Link: {link['type']}\n"
        result += fetch_website_contents(link['url'])
    return result

def get_brochure_user_prompt(company_name, url):
    user_prompt = f"""
You are looking at a company called: {company_name}
Here are the contents of its landing page and other relevant pages;
use this information to build a short brochure of the company in markdown without code blocks.\n\n
"""
    user_prompt += fetch_page_and_all_relevant_links(url)
    user_prompt = user_prompt[:5_000]  # Truncate if more than 5,000 characters
    return user_prompt

def create_brochure(company_name, url):
    try:
        time.sleep(2)  # Rate limiting
        user_prompt = get_brochure_user_prompt(company_name, url)
        response = gemini.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": brochure_system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        brochure = response.choices[0].message.content
        return brochure
    except Exception as e:
        return f"Error generating brochure: {str(e)}\n\nPlease wait a moment and try again if you hit rate limits."

# Main UI
st.markdown("<h1 class='main-header'>📄 Company Brochure Generator</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Generate professional brochures from any company website using AI</p>", unsafe_allow_html=True)

# Check API key
if not api_key or not api_key.startswith("AIza"):
    st.error("⚠️ No valid GEMINI_API_KEY found. Please check your .env file!")
    st.stop()

# Input section
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    company_name = st.text_input(
        "🏢 Company Name",
        placeholder="e.g., Hugging Face",
        help="Enter the name of the company"
    )

with col2:
    website_url = st.text_input(
        "🌐 Website URL",
        placeholder="e.g., https://huggingface.co",
        help="Enter the full URL including https://"
    )

# Generate button
st.markdown("<br>", unsafe_allow_html=True)
generate_button = st.button("🚀 Generate Brochure", use_container_width=True)

# Generation and display
if generate_button:
    if not company_name or not website_url:
        st.warning("⚠️ Please enter both company name and website URL")
    elif not website_url.startswith("http"):
        st.warning("⚠️ Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner(f"🔍 Analyzing {company_name}'s website..."):
            st.info("📡 Fetching website content...")
            time.sleep(1)
            st.info("🔗 Selecting relevant pages...")
            time.sleep(1)
            st.info("✨ Generating brochure with AI...")
            
            brochure_content = create_brochure(company_name, website_url)
            
        # Display results
        st.markdown("---")
        st.markdown("### 📋 Generated Brochure")
        
        # Display the brochure
        st.markdown(brochure_content)
        
        st.success("✅ Brochure generated successfully!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 2rem 0;'>
    <p>💡 <b>Tip:</b> Streamlit automatically supports dark mode! Toggle it in Settings (☰ menu) → Theme</p>
    <p style='font-size: 0.9em;'>Built with Streamlit & Gemini AI | Made with ❤️</p>
</div>
""", unsafe_allow_html=True)
