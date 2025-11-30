import streamlit as st
import sqlite3
import pandas as pd
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import hashlib
import re
from collections import Counter

# ==============================================================================
# 1. DESIGN SYSTEM "ECLIPSE" (Sobre & Lumineux)
# ==============================================================================

def setup_page():
    st.set_page_config(page_title="Monitor.io", page_icon="🌑", layout="wide")
    
    st.markdown("""
        <style>
        /* Import Font: Inter (Le standard du web moderne) */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
        
        :root {
            --bg-app: #09090b;       /* Noir zinc très profond */
            --bg-card: #18181b;      /* Gris zinc foncé */
            --border-subtle: #27272a;/* Bordure discrète */
            --text-main: #f4f4f5;    /* Blanc cassé */
            --text-muted: #a1a1aa;   /* Gris moyen */
            --accent-glow: rgba(255, 255, 255, 0.15); /* Lumière blanche diffuse */
            --accent-blue: #3b82f6;  /* Bleu pro pour les liens/badges */
        }

        /* --- GLOBAL RESET --- */
        .stApp { background-color: var(--bg-app); font-family: 'Inter', sans-serif; }
        
        h1, h2, h3 { 
            font-weight: 600; 
            letter-spacing: -0.02em; 
            color: var(--text-main); 
        }

        /* --- HUD (Top Dashboard) --- */
        .hud-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 40px;
        }
        .hud-item {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            padding: 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        /* Effet Lumière Hover HUD */
        .hud-item:hover {
            border-color: #52525b;
            box-shadow: 0 0 25px rgba(255, 255, 255, 0.05);
        }
        .hud-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        .hud-value {
            font-size: 1.8rem;
            font-weight: 600;
            color: var(--text-main);
        }

        /* --- FEED CARD (Le coeur du design) --- */
        .feed-card {
            background-color: var(--bg-app); /* Fond sombre */
            border: 1px solid var(--border-subtle);
            border-radius: 8px; /* Coins moins arrondis pour faire plus sérieux */
            padding: 24px;
            margin-bottom: 16px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }
        
        /* L'effet "Spotlight" au survol */
        .feed-card:hover {
            border-color: rgba(255, 255, 255, 0.3); /* Bordure s'illumine */
            transform: translateY(-2px);
            background-color: #121214; /* Légèrement plus clair */
            box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.5), 0 0 20px rgba(255, 255, 255, 0.03); /* Glow diffus */
        }

        .meta-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            font-size: 0.85rem;
        }
        
        .source-pill {
            color: var(--text-main);
            background: #27272a;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 0.75rem;
            border: 1px solid transparent;
            transition: border-color 0.2s;
        }
        .feed-card:hover .source-pill { border-color: #52525b; }

        .date-text { color: #52525b; }

        .card-title {
            display: block;
            font-size: 1.15rem;
            font-weight: 600;
            color: var(--text-main);
            text-decoration: none;
            margin-bottom: 8px;
            line-height: 1.4;
            transition: color 0.2s;
        }
        .card-title:hover { color: var(--accent-blue); }

        .card-summary {
            font-size: 0.95rem;
            color: var(--text-muted);
            line-height: 1.6;
            margin-bottom: 16px;
        }

        /* --- TAGS (Minimalistes) --- */
        .tag-minimal {
            display: inline-block;
            font-size: 0.75rem;
            color: #71717a;
            margin-right: 10px;
            position: relative;
            padding-left: 10px;
        }
        .tag-minimal::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 4px;
            background-color: #3f3f46;
            border-radius: 50%;
        }

        /* --- TABS (Onglets) --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            background-color: transparent;
            border-bottom: 1px solid var(--border-subtle);
            padding-bottom: 0px;
            margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            color: var(--text-muted);
            font-weight: 500;
            padding-bottom: 12px;
            border: none;
        }
        .stTabs [aria-selected="true"] {
            color: var(--text-main) !important;
            border-bottom: 2px solid var(--text-main) !important;
        }

        /* --- SIDEBAR --- */
        section[data-testid="stSidebar"] {
            background-color: #0c0c0e;
            border-right: 1px solid var(--border-subtle);
        }
        
        /* Inputs & Buttons */
        .stTextInput input {
            background-color: #18181b !important;
            border: 1px solid #27272a !important;
            color: white !important;
            border-radius: 6px;
        }
        .stTextInput input:focus {
            border-color: #52525b !important;
        }
        div.stButton > button {
            background-color: var(--text-main);
            color: black;
            border: none;
            font-weight: 600;
            border-radius: 6px;
            transition: opacity 0.2s;
        }
        div.stButton > button:hover {
            opacity: 0.9;
            box-shadow: 0 0 15px rgba(255,255,255,0.2);
        }

        /* --- DIGEST --- */
        .digest-group {
            border-left: 1px solid #27272a;
            padding-left: 20px;
            margin-bottom: 30px;
        }
        .digest-link {
            display: block;
            padding: 6px 0;
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.95rem;
            transition: all 0.2s;
        }
        .digest-link:hover {
            color: var(--text-main);
            transform: translateX(5px);
        }

        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. INTELLIGENCE (NLP - Inchangé car performant)
# ==============================================================================

class DeepTagger:
    STOP_WORDS = set([
        "le", "la", "les", "de", "des", "du", "un", "une", "et", "à", "en", "pour", "que", "qui", 
        "dans", "sur", "par", "plus", "pas", "au", "ce", "cette", "avec", "sont", "est", "il", "elle",
        "nous", "vous", "ils", "elles", "mais", "ou", "donc", "car", "ni", "or", "a", "son", "sa", "ses",
        "après", "avant", "depuis", "selon", "sans", "sous", "vers", "chez", "très", "bien", "encore", 
        "the", "a", "an", "and", "to", "for", "of", "with", "is", "are", "in", "on"
    ])

    @staticmethod
    def clean_text(text):
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.lower()

    @staticmethod
    def analyze_tags(title, description):
        text = (title + " " + title + " " + description)
        clean = DeepTagger.clean_text(text)
        words = clean.split()
        filtered = [w for w in words if len(w) > 3 and w not in DeepTagger.STOP_WORDS]
        if not filtered: return "Général"
        most_common = Counter(filtered).most_common(3)
        tags = [tag.capitalize() for tag, count in most_common]
        return ",".join(tags)

# ==============================================================================
# 3. BACKEND (Inchangé)
# ==============================================================================

class Database:
    def __init__(self, db_name="webmonitor_clean.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.init_db()

    def init_db(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS feeds (
                    id TEXT PRIMARY KEY,
                    source_id INTEGER,
                    source_name TEXT,
                    title TEXT,
                    summary TEXT,
                    url TEXT,
                    tags TEXT,
                    created_at DATETIME,
                    FOREIGN KEY(source_id) REFERENCES sources(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def get_stats(self):
        try:
            total = pd.read_sql("SELECT COUNT(*) as count FROM feeds", self.conn)['count'][0]
            df_s = pd.read_sql("SELECT source_name, COUNT(*) as c FROM feeds GROUP BY source_name ORDER BY c DESC LIMIT 1", self.conn)
            top = df_s['source_name'][0] if not df_s.empty else "N/A"
            df_l = pd.read_sql("SELECT MAX(created_at) as last FROM feeds", self.conn)
            last = df_l['last'][0] if df_l['last'][0] else "N/A"
            return total, top, last
        except: return 0, "-", "-"

    def add_source(self, name, url):
        try:
            with self.conn:
                self.conn.execute("INSERT INTO sources (name, url) VALUES (?, ?)", (name, url))
            return True
        except: return False

    def delete_source(self, source_id):
        with self.conn:
            self.conn.execute("DELETE FROM sources WHERE id = ?", (source_id,))
            self.conn.execute("DELETE FROM feeds WHERE source_id = ?", (source_id,))

    def get_sources(self):
        return pd.read_sql("SELECT * FROM sources ORDER BY created_at DESC", self.conn)

    def save_feed_item(self, source_id, source_name, title, summary, url, tags, date_obj):
        uid = hashlib.md5(url.encode()).hexdigest()
        try:
            with self.conn:
                self.conn.execute('''
                    INSERT INTO feeds VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (uid, source_id, source_name, title, summary, url, tags, date_obj))
            return True
        except sqlite3.IntegrityError: return False

    def get_data(self, hours_lookback=None):
        query = "SELECT * FROM feeds"
        params = []
        if hours_lookback:
            query += " WHERE created_at >= datetime('now', ?)"
            params.append(f"-{hours_lookback} hours")
        query += " ORDER BY created_at DESC"
        return pd.read_sql(query, self.conn, params=params)

# ==============================================================================
# 4. UI RENDERERS (Adaptés au nouveau style)
# ==============================================================================

def render_hud(total, top, last):
    # Formatage date épuré
    date_str = last
    if last != "-" and last != "N/A":
        try:
            dt = datetime.strptime(last, '%Y-%m-%d %H:%M:%S.%f')
            date_str = dt.strftime("%d %b, %H:%M")
        except: pass

    st.markdown(f"""
        <div class="hud-grid">
            <div class="hud-item">
                <div class="hud-label">Articles capturés</div>
                <div class="hud-value">{total}</div>
            </div>
            <div class="hud-item">
                <div class="hud-label">Source la plus active</div>
                <div class="hud-value" style="color:#a1a1aa;">{top}</div>
            </div>
            <div class="hud-item">
                <div class="hud-label">Dernière synchronisation</div>
                <div class="hud-value" style="font-size:1.4rem; padding-top:5px;">{date_str}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_live_feed(df):
    for row in df.itertuples():
        # Tags minimalistes
        tags_html = "".join([f"<span class='tag-minimal'>{t.strip()}</span>" for t in row.tags.split(',')])
        
        # Date relative (ex: 12:45)
        try: 
            t = row.created_at.split(' ')[1][:5]
        except: t = row.created_at

        st.markdown(f"""
        <div class="feed-card">
            <div class="meta-row">
                <span class="source-pill">{row.source_name}</span>
                <span class="date-text">{t}</span>
            </div>
            <a href="{row.url}" target="_blank" class="card-title">{row.title}</a>
            <div class="card-summary">{row.summary}</div>
            <div style="margin-top:12px;">{tags_html}</div>
        </div>
        """, unsafe_allow_html=True)

def render_digest(df, title):
    st.markdown(f"### {title}")
    if df.empty:
        st.caption("Données insuffisantes.")
        return

    grouped = df.groupby('source_name')
    for source, group in grouped:
        count = len(group)
        # On trouve le sujet dominant
        all_tags = ",".join(group['tags'].tolist()).split(',')
        topic = Counter([t.strip() for t in all_tags if t.strip()]).most_common(1)[0][0]
        
        st.markdown(f"""
        <div style="margin-top:20px; margin-bottom:10px; display:flex; align-items:center; gap:10px;">
            <span style="font-weight:600; color:white;">{source}</span>
            <span style="font-size:0.8rem; color:#52525b;">— {count} articles ({topic})</span>
        </div>
        <div class="digest-group">
            {"".join([f"<a href='{row.url}' target='_blank' class='digest-link'>{row.title}</a>" for row in group.itertuples()])}
        </div>
        """, unsafe_allow_html=True)

def render_sidebar(db):
    with st.sidebar:
        st.header("Monitor.io")
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        
        if st.button("Lancer la synchronisation", type="primary", use_container_width=True):
            # Logique de sync simple
            sources = db.get_sources()
            count = 0
            progress = st.progress(0)
            for i, row in sources.iterrows():
                try:
                    d = feedparser.parse(row['url'])
                    for entry in d.entries[:6]:
                        tags = DeepTagger.analyze_tags(entry.title, entry.get('description', ''))
                        if db.save_feed_item(row['id'], row['name'], entry.title, entry.get('description', '')[:250]+"...", entry.link, tags, datetime.now()):
                            count += 1
                except: pass
                progress.progress((i+1)/len(sources))
            progress.empty()
            st.toast(f"Terminé : {count} nouveaux articles", icon="✨")
            time.sleep(1)
            st.rerun()

        st.markdown("---")
        st.subheader("Sources")
        
        with st.form("add_source", clear_on_submit=True):
            c1, c2 = st.columns([1,2])
            n = c1.text_input("Nom", placeholder="Le Monde")
            u = c2.text_input("RSS URL", placeholder="https://...")
            if st.form_submit_button("Ajouter +", use_container_width=True):
                if n and u: 
                    db.add_source(n, u)
                    st.rerun()

        # Liste épurée
        sources = db.get_sources()
        if not sources.empty:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            for _, row in sources.iterrows():
                cols = st.columns([5,1])
                cols[0].markdown(f"<span style='color:#a1a1aa; font-size:0.9rem;'>{row['name']}</span>", unsafe_allow_html=True)
                if cols[1].button("✕", key=f"del_{row['id']}"):
                    db.delete_source(row['id'])
                    st.rerun()

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

def main():
    setup_page()
    db = Database()
    
    render_sidebar(db)
    
    # HUD
    total, top, last = db.get_stats()
    render_hud(total, top, last)
    
    # Navigation Tabs
    tabs = st.tabs(["Flux temps réel", "24 Heures", "Cette Semaine", "Ce Mois"])
    
    with tabs[0]:
        df = db.get_data().head(60)
        if df.empty: st.info("Ajoutez des sources RSS dans la barre latérale pour commencer.")
        else: render_live_feed(df)

    with tabs[1]: render_digest(db.get_data(24), "Synthèse quotidienne")
    with tabs[2]: render_digest(db.get_data(168), "Synthèse hebdomadaire")
    with tabs[3]: render_digest(db.get_data(720), "Synthèse mensuelle")

if __name__ == "__main__":
    main()
