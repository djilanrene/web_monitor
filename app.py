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
# 1. DESIGN SYSTEM & CSS (NEON / GLASSMORPHISM)
# ==============================================================================

def setup_page():
    st.set_page_config(page_title="Web Monitor.io", page_icon="⚡", layout="wide")
    
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=Rajdhani:wght@500;700&family=Inter:wght@400;600&display=swap');
        
        :root {
            --bg-deep: #050505;
            --bg-card: #0F1115;
            --neon-blue: #00F3FF;
            --neon-purple: #BC13FE;
            --neon-green: #0AFF60;
            --text-main: #E0E6ED;
            --text-muted: #94A3B8;
            --border-glow: 0 0 10px rgba(0, 243, 255, 0.15);
        }

        /* RESET & BASICS */
        .stApp { background-color: var(--bg-deep); font-family: 'Inter', sans-serif; }
        h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -1px; color: white; }
        
        /* --- DASHBOARD HUD (SYNTHESE) --- */
        .hud-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .hud-card {
            background: rgba(15, 17, 21, 0.7);
            border: 1px solid #1E293B;
            border-left: 3px solid var(--neon-blue);
            padding: 15px 20px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            transition: all 0.3s;
        }
        .hud-card:hover { box-shadow: var(--border-glow); border-color: var(--neon-blue); }
        .hud-label { font-family: 'Rajdhani', sans-serif; color: var(--text-muted); text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px; }
        .hud-value { font-family: 'Space Grotesk', sans-serif; font-size: 1.8rem; font-weight: 700; color: white; text-shadow: 0 0 10px rgba(0, 243, 255, 0.3); }

        /* --- NAVIGATION TABS --- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px; background-color: rgba(255,255,255,0.02); padding: 5px;
            border-radius: 8px; border: 1px solid #333; margin-bottom: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 40px; border-radius: 6px; color: var(--text-muted); 
            font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 1rem; border: none !important;
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(90deg, rgba(0, 243, 255, 0.1) 0%, rgba(188, 19, 254, 0.1) 100%) !important;
            color: var(--neon-blue) !important;
            border: 1px solid rgba(0, 243, 255, 0.3) !important;
            box-shadow: inset 0 0 10px rgba(0, 243, 255, 0.1);
        }

        /* --- FEED CARD --- */
        .feed-card {
            background-color: var(--bg-card);
            border: 1px solid #1E232E;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .feed-card::before {
            content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%;
            background: var(--neon-purple); opacity: 0; transition: opacity 0.3s;
        }
        .feed-card:hover { 
            transform: translateY(-3px); 
            border-color: var(--neon-blue);
            box-shadow: 0 10px 30px -10px rgba(0, 243, 255, 0.15);
        }
        .feed-card:hover::before { opacity: 1; }
        
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .source-badge { 
            background: rgba(0, 243, 255, 0.1); color: var(--neon-blue); padding: 4px 8px; 
            border: 1px solid rgba(0, 243, 255, 0.3); border-radius: 4px; 
            font-family: 'Rajdhani', sans-serif; font-weight: 700; font-size: 0.8rem; text-transform: uppercase;
        }
        .time-badge { color: #555; font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }
        
        .card-title { 
            color: white; font-size: 1.1rem; font-weight: 600; line-height: 1.4;
            text-decoration: none; display: block; margin-bottom: 8px; transition: color 0.2s;
        }
        .card-title:hover { color: var(--neon-blue); text-shadow: 0 0 8px rgba(0,243,255,0.4); }
        .card-summary { color: #8892B0; font-size: 0.9rem; line-height: 1.5; margin-bottom: 15px; }

        /* TAGS */
        .tags-row { display: flex; gap: 8px; flex-wrap: wrap; }
        .neon-tag {
            background: rgba(188, 19, 254, 0.05); color: var(--neon-purple); 
            border: 1px solid rgba(188, 19, 254, 0.3);
            padding: 2px 10px; border-radius: 100px; font-size: 0.7rem; font-weight: 600;
        }

        /* --- SIDEBAR & INPUTS --- */
        section[data-testid="stSidebar"] { background-color: #080A0E; border-right: 1px solid #1E232E; }
        .stTextInput input {
            background-color: #12151C !important; color: white !important; border: 1px solid #333 !important;
        }
        .stTextInput input:focus { border-color: var(--neon-blue) !important; box-shadow: 0 0 10px rgba(0,243,255,0.2) !important; }
        
        /* Custom Button */
        div.stButton > button {
            background: linear-gradient(45deg, #1e3a8a, #1e40af);
            color: white; border: none; font-weight: bold; letter-spacing: 0.5px;
            transition: all 0.3s;
        }
        div.stButton > button:hover {
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
            transform: scale(1.02);
        }

        /* DIGEST LIST */
        .digest-container {
            background: #0F1115; border: 1px solid #222; border-radius: 8px;
            padding: 20px; margin-bottom: 15px;
        }
        .digest-link { color: #BBB; text-decoration: none; display: block; padding: 5px 0; border-bottom: 1px solid #1A1D24; transition: 0.2s;}
        .digest-link:hover { color: var(--neon-green); padding-left: 5px; }

        </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. INTELLIGENCE (NLP)
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
        text = (title + " " + title + " " + description) # Titre pondéré double
        clean = DeepTagger.clean_text(text)
        words = clean.split()
        filtered = [w for w in words if len(w) > 3 and w not in DeepTagger.STOP_WORDS]
        
        if not filtered: return "Général"
        
        most_common = Counter(filtered).most_common(3)
        tags = [tag.capitalize() for tag, count in most_common]
        return ",".join(tags)

# ==============================================================================
# 3. BACKEND (DATABASE)
# ==============================================================================

class Database:
    def __init__(self, db_name="webmonitor_neon.db"):
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
            # Stats pour le HUD
            total_articles = pd.read_sql("SELECT COUNT(*) as count FROM feeds", self.conn)['count'][0]
            
            # Top Source
            df_source = pd.read_sql("SELECT source_name, COUNT(*) as c FROM feeds GROUP BY source_name ORDER BY c DESC LIMIT 1", self.conn)
            top_source = df_source['source_name'][0] if not df_source.empty else "Aucune"
            
            # Last Update
            df_last = pd.read_sql("SELECT MAX(created_at) as last FROM feeds", self.conn)
            last_update = df_last['last'][0] if df_last['last'][0] else "N/A"
            
            return total_articles, top_source, last_update
        except:
            return 0, "N/A", "N/A"

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
# 4. ENGINE
# ==============================================================================

class Engine:
    def __init__(self, db):
        self.db = db

    def sync(self):
        sources = self.db.get_sources()
        count = 0
        progress = st.progress(0)
        for idx, row in sources.iterrows():
            try:
                d = feedparser.parse(row['url'])
                for entry in d.entries[:6]:
                    tags = DeepTagger.analyze_tags(entry.title, entry.get('description', ''))
                    saved = self.db.save_feed_item(
                        row['id'], row['name'], entry.title, 
                        str(entry.get('description', '') or '')[:250]+"...",
                        entry.link, tags, datetime.now()
                    )
                    if saved: count += 1
            except: pass
            progress.progress((idx + 1)/len(sources))
        progress.empty()
        return count

# ==============================================================================
# 5. UI COMPONENTS
# ==============================================================================

def render_hud(total, top, last):
    # Parsing de la date pour l'affichage
    display_date = last
    if last != "N/A":
        try:
            dt = datetime.strptime(last, '%Y-%m-%d %H:%M:%S.%f')
            display_date = dt.strftime("%H:%M • %d/%m")
        except: pass

    st.markdown(f"""
        <div class="hud-container">
            <div class="hud-card">
                <div class="hud-label">Articles Scrappés</div>
                <div class="hud-value" style="color:var(--neon-blue)">{total}</div>
            </div>
            <div class="hud-card" style="border-left-color: var(--neon-purple);">
                <div class="hud-label">Top Actualité</div>
                <div class="hud-value" style="font-size:1.4rem;">{top}</div>
            </div>
            <div class="hud-card" style="border-left-color: var(--neon-green);">
                <div class="hud-label">Dernière Mise à Jour</div>
                <div class="hud-value" style="font-size:1.4rem;">{display_date}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_live_feed(df):
    for row in df.itertuples():
        tags_html = "".join([f"<span class='neon-tag'>#{t.strip()}</span>" for t in row.tags.split(',')])
        
        # Date formatting shortcut
        try: created = row.created_at.split('.')[0] 
        except: created = row.created_at

        st.markdown(f"""
        <div class="feed-card">
            <div class="card-header">
                <span class="source-badge">{row.source_name}</span>
                <span class="time-badge">{created}</span>
            </div>
            <a href="{row.url}" target="_blank" class="card-title">{row.title}</a>
            <div class="card-summary">{row.summary}</div>
            <div class="tags-row">{tags_html}</div>
        </div>
        """, unsafe_allow_html=True)

def render_digest(df, title):
    st.markdown(f"<h3 style='margin-bottom:20px; border-bottom:1px solid #333; padding-bottom:10px;'>{title}</h3>", unsafe_allow_html=True)
    if df.empty:
        st.info("Données insuffisantes.")
        return

    grouped = df.groupby('source_name')
    for source, group in grouped:
        count = len(group)
        topic = Counter(",".join(group['tags'].tolist()).split(',')).most_common(1)[0][0]
        
        st.markdown(f"""
        <div class="digest-container">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-weight:bold; color:white; font-size:1.1rem;">{source}</span>
                <span class="neon-tag" style="border-color:var(--neon-green); color:var(--neon-green)">{topic} • {count}</span>
            </div>
            {"".join([f"<a href='{row.url}' target='_blank' class='digest-link'>› {row.title}</a>" for row in group.itertuples()])}
        </div>
        """, unsafe_allow_html=True)

def render_sidebar(db):
    with st.sidebar:
        st.title("Web Monitor.io")
        st.caption("v5.1 Neon Edition")
        
        st.markdown("### ⚡ Actions")
        if st.button("Lancer le Scan", type="primary", use_container_width=True):
            engine = Engine(db)
            n = engine.sync()
            st.toast(f"{n} nouveaux articles !", icon="🔥")
            time.sleep(1)
            st.rerun()

        st.markdown("---")
        st.markdown("### 📡 Sources")
        
        with st.expander("Ajouter un flux RSS"):
            with st.form("add"):
                n = st.text_input("Nom")
                u = st.text_input("URL")
                if st.form_submit_button("Sauvegarder"):
                    if n and u: 
                        db.add_source(n, u)
                        st.rerun()

        sources = db.get_sources()
        if not sources.empty:
            for _, row in sources.iterrows():
                c1, c2 = st.columns([5,1])
                c1.markdown(f"<div style='color:#ccc; font-size:0.9rem; padding-top:5px;'>{row['name']}</div>", unsafe_allow_html=True)
                if c2.button("✕", key=f"d_{row['id']}"):
                    db.delete_source(row['id'])
                    st.rerun()
                st.markdown("<div style='height:1px; background:#222; margin:5px 0;'></div>", unsafe_allow_html=True)

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    setup_page()
    db = Database()
    
    # Récupération Stats HUD
    total, top, last = db.get_stats()
    
    render_sidebar(db)
    
    # 1. HUD DASHBOARD (En haut)
    render_hud(total, top, last)
    
    # 2. CONTENU PRINCIPAL
    tabs = st.tabs(["🔥 Live Feed", "📊 Digest 24h", "📅 Hebdomadaire", "🗓 Mensuel"])
    
    with tabs[0]:
        df = db.get_data().head(60)
        if df.empty: st.warning("Le vide sidéral... Ajoutez des sources !")
        else: render_live_feed(df)
        
    with tabs[1]:
        render_digest(db.get_data(24), "Synthèse 24H")
        
    with tabs[2]:
        render_digest(db.get_data(168), "Synthèse Semaine")
        
    with tabs[3]:
        render_digest(db.get_data(720), "Synthèse Mois")

if __name__ == "__main__":
    main()