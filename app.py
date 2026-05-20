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
    /* Main Background & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=Lato:wght@300;400;700&display=swap');
    
    .stApp {
        background-color: #f5f0e8 !important;
        color: #0f0e0c !important;
        font-family: 'Lato', sans-serif !important;
    }
    
    /* Header Container */
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

    /* Result Cards styling */
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
    .tag-researchgate { background: #fde8e8; color: #c0392b; }
</style>
""", unsafe_allow_html=True)

# ── RENDER STATIC CUSTOM HEADER ──
st.markdown("""
<div class="custom-header">
    <div class="logo-line"><span class="logo-dot"></span> Research Finder</div>
    <h1>Find articles that <em>support</em><br>your claim</h1>
    <p class="subtitle">Enter any sentence or hypothesis. We'll consult Gemini's knowledge base to extract and map highly relevant supporting scientific literature.</p>
</div>
""", unsafe_allow_html=True)

# ── API KEY SECURE CHECK (SECRETS VS INPUT) ──
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip() != "":
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # Fallback text input field if Secrets aren't used yet
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")

# ── STREAMLIT NATIVE INPUT CONTROLS ──
claim = st.text_area("Your claim or sentence", placeholder="e.g. Regular aerobic exercise significantly reduces symptoms of depression in adults…")

col1, col2 = st.columns([1, 1])
with col1:
    count = st.selectbox("Articles to find", options=[3, 5, 8, 10], index=1)
with col2:
    st.write(" ") # Padding
    st.write(" ") 
    search_clicked = st.button("Search Literature", use_container_width=True)

# Helper to format specific source badges
def get_source_badge(url):
    if not url: return ""
    u = url.lower()
    if "scholar" in u:
        return '<span class="tag-source tag-scholar">Google Scholar</span>'
    elif "researchgate" in u:
        return '<span class="tag-source tag-researchgate">ResearchGate</span>'
    return '<span class="tag-source" style="background:#f0f0e8; color:#5a5040;">Academic</span>'

# ── LOGIC PROCESSING VIA GEMINI ──
if search_clicked:
    if not api_key or not api_key.startswith("AIzaSy"):
        st.error("Please enter a valid Gemini API key or add GEMINI_API_KEY to your Streamlit Secrets.")
    elif not claim.strip():
        st.error("Please enter a claim or sentence to search for.")
    else:
        with st.spinner("Analyzing literature layout with Gemini..."):
            system_prompt = f"""You are a research librarian expert. Your job is to find real, existing academic articles that support a given claim.

For each article found, return a JSON array (and ONLY a JSON array, no markdown fences, no preamble, no tailing data) with this exact structure:
[
  {{
    "title": "Full article title",
    "authors": "Author names",
    "year": "Publication year",
    "journal": "Journal or conference name",
    "url": "Direct reference URL to the article on Google Scholar or ResearchGate",
    "support": "2-4 sentence explanation of how this specific article supports the given claim, citing specific findings or conclusions from the paper"
  }}
]

Rules:
- Return EXACTLY {count} articles if possible.
- Only return real articles that actually exist — do NOT invent or hallucinate any article data.
- Supply high-quality direct URLs matching Google Scholar or ResearchGate format.
- The "support" field must be specific and detailed, mentioning actual findings.
- Return ONLY the clean JSON array content."""

            user_prompt = f'Find {count} real academic articles that support this claim:\n\n"{claim}"\n\nReturn only the JSON array layout as specified.'
            
            try:
                # Target the Gemini API
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [{"text": system_prompt + "\n\n" + user_prompt}]
                    }],
                    "generationConfig": {
                        "responseMimeType": "application/json"
                    }
                }
                
                response = requests.post(endpoint, json=payload)
                
                if response.status_code != 200:
                    st.error(f"API Error {response.status_code}: {response.text}")
                else:
                    data = response.json()
                    full_text = data['candidates'][0]['content']['parts'][0]['text']
                    
                    # Clean out markdown text artifacts if any leaked through (Syntax Error Fixed Here)
                    cleaned = full_text.replace("```json", "").replace("```", "").strip()
                    match = re.search(r'\[[\s\S]*\]', cleaned)
                    
                    if not match:
                        st.error("Could not parse a clean JSON document format from the engine response.")
                    else:
                        articles = json.loads(match.group(0))
                        
                        # Display echoed claim
                        st.markdown(f'<div class="claim-echo">"{claim}"</div>', unsafe_allow_html=True)
                        st.subheader("Supporting Articles")
                        
                        # Loop through and cleanly render your original visual UI structures
                        for i, art in enumerate(articles):
                            badge = get_source_badge(art.get('url', ''))
                            meta_info = f"{art.get('authors', '')} | {art.get('year', '')} | <em>{art.get('journal', '')}</em> {badge}"
                            link_html = f'<a href="{art.get("url")}" target="_blank" class="card-link">View Source Article →</a>' if art.get('url') else '<span class="card-link" style="color:#7a7060; font-style:italic;">No link available</span>'
                            
                            st.markdown(f"""
                            <div class="article-card">
                                <div class="card-title">{i+1}. {art.get('title', 'Untitled')}</div>
                                <div class="card-meta">{meta_info}</div>
                                <div class="support-label">How it supports your claim</div>
                                <div class="support-text">{art.get('support', 'Details inside article references.')}</div>
                                {link_html}
                            </div>
                            """, unsafe_allow_html=True)
                            
            except Exception as e:
                st.error(f"An unexpected parsing or connecting layout error hit: {str(e)}")
