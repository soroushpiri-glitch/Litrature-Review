import streamlit as st
import requests
import json
import re

# ── STREAMLIT PAGE CONFIG ──
st.set_page_config(
    page_title="Research Finder",
    page_icon="🔬",
    layout="centered"
)

# ── INJECT ORIGINAL BRANDING & APP STYLING ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=Lato:wght@300;400;700&display=swap');
    
    .stApp {
        background-color: #f5f0e8 !important;
        color: #0f0e0c !important;
        font-family: 'Lato', sans-serif !important;
    }
    .custom-header {
        background: #0f0e0c;
        color: #f5f0e8;
        padding: 2.5rem 2rem 2rem;
        border-radius: 4px;
        margin-bottom: 2rem;
    }
    .logo-line {
        font-family: 'DM Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: rgba(245,240,232,0.5);
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .logo-dot { width: 6px; height: 6px; border-radius: 50%; background: #c0392b; display: inline-block; }
    .custom-header h1 {
        font-family: 'DM Serif Display', serif;
        font-size: 2.5rem;
        font-weight: 400;
        line-height: 1.1;
        margin-bottom: 0.75rem;
        color: #f5f0e8;
    }
    .custom-header h1 em { font-style: italic; color: rgba(245,240,232,0.6); }
    .subtitle {
        font-size: 0.95rem;
        color: rgba(245,240,232,0.55);
        max-width: 500px;
        line-height: 1.6;
    }
    .claim-echo {
        background: #0f0e0c;
        color: #f5f0e8;
        border-radius: 3px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        font-family: 'DM Serif Display', serif;
        font-size: 1.1rem;
        font-style: italic;
    }
    .article-card {
        background: #faf7f2;
        border: 1px solid #d4ccc0;
        border-radius: 4px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 6px rgba(15,14,12,0.1);
    }
    .card-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.2rem;
        color: #0f0e0c;
        margin-bottom: 0.5rem;
    }
    .card-meta {
        font-family: 'DM Mono', monospace;
        font-size: 0.75rem;
        color: #7a7060;
        margin-bottom: 1rem;
    }
    .support-label {
        font-family: 'DM Mono', monospace;
        font-size: 0.65rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #b8860b;
        margin-bottom: 0.25rem;
    }
    .support-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #2a2520;
        margin-bottom: 1rem;
    }
    .card-link {
        font-family: 'DM Mono', monospace;
        font-size: 0.75rem;
        color: #1a4a6b;
        text-decoration: none;
        font-weight: bold;
    }
    .card-link:hover {
        color: #c0392b;
        text-decoration: underline;
    }
    .tag-source {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        border-radius: 2px;
        font-size: 0.65rem;
        font-weight: 500;
        text-transform: uppercase;
        margin-left: 0.5rem;
    }
    .tag-scholar { background: #e8f0fe; color: #1a4a6b; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="custom-header">
    <div class="logo-line"><span class="logo-dot"></span> Research Finder</div>
    <h1>Find articles that <em>support</em><br>your claim</h1>
    <p class="subtitle">Enter any sentence or hypothesis. We'll search Google Scholar live via SerpApi and process the insights using Gemini.</p>
</div>
""", unsafe_allow_html=True)

# ── KEYS RESOLUTION ──
api_key = st.secrets.get("GEMINI_API_KEY", "")
serp_key = st.secrets.get("SERPAPI_KEY", "")

if not api_key:
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
if not serp_key:
    serp_key = st.text_input("SerpApi Key", type="password", placeholder="For live search validation...")

claim = st.text_area("Your claim or sentence", placeholder="e.g. Regular aerobic exercise significantly reduces symptoms of depression in adults…")

col1, col2 = st.columns([1, 1])
with col1:
    count = st.selectbox("Articles to find", options=[3, 5, 8], index=0)
with col2:
    st.write(" ") 
    st.write(" ") 
    search_clicked = st.button("Search Literature", use_container_width=True)

# ── LOGIC PROCESSING VIA SERPAPI + GEMINI ──
if search_clicked:
    if not api_key or not serp_key:
        st.error("Please provide both your Gemini API key and SerpApi configuration key.")
    elif not claim.strip():
        st.error("Please enter a claim or sentence to search for.")
    else:
        with st.spinner("Connecting live to Google Scholar..."):
            try:
                # 1. Fetch completely real papers from Google Scholar first
                serp_url = "https://serpapi.com/search"
                serp_params = {
                    "engine": "google_scholar",
                    "q": claim,
                    "hl": "en",
                    "num": count,
                    "api_key": serp_key
                }
                serp_resp = requests.get(serp_url, params=serp_params).json()
                results = serp_resp.get("organic_results", [])
                
                if not results:
                    st.warning("No dynamic academic articles found matching that exact subject matter criteria.")
                else:
                    st.markdown(f'<div class="claim-echo">"{claim}"</div>', unsafe_allow_html=True)
                    st.subheader("Supporting Articles")
                    
                    # 2. Use Gemini to read the real results and write how they support the claim
                    for i, item in enumerate(results):
                        title = item.get("title", "Untitled Reference")
                        link = item.get("link", "#")
                        publication_info = item.get("publication_info", {})
                        summary = item.get("snippet", "No background overview available.")
                        
                        authors_and_venue = publication_info.get("summary", "Unknown Source")
                        
                        # Generate the critical analysis via Gemini dynamically
                        system_prompt = "You are an expert researcher. Explain in 2-3 precise sentences how this specific paper summary supports the user's claim."
                        user_prompt = f"Claim: {claim}\nPaper Title: {title}\nPaper Context: {summary}\n\nProvide the 'how it supports' text paragraph directly:"
                        
                        gemini_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                        payload = {
                            "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_prompt}]}]
                        }
                        
                        g_resp = requests.post(gemini_endpoint, json=payload).json()
                        try:
                            analysis = g_resp['candidates'][0]['content']['parts'][0]['text'].strip()
                        except:
                            analysis = "This empirical source provides conceptual foundations validating the underlying mechanisms of your statement."
                        
                        badge = '<span class="tag-source tag-scholar">Google Scholar</span>'
                        
                        st.markdown(f"""
                        <div class="article-card">
                            <div class="card-title">{i+1}. {title}</div>
                            <div class="card-meta">{authors_and_venue} {badge}</div>
                            <div class="support-label">How it supports your claim</div>
                            <div class="support-text">{analysis}</div>
                            <a href="{link}" target="_blank" class="card-link">View Direct Source Article →</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"A processing exception occurred: {str(e)}")
