from flask import Flask, render_template, flash, request, redirect, url_for, session
import requests
import os
import sqlite3
import hashlib
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'  # Change this in production

# Get API key from environment variable or use default (for demo)
API_KEY = os.getenv('NEWS_API_KEY', '517b016e60784bffa8fd92822c438fe7')

# Tech news categories with their search keywords
TECH_CATEGORIES = {
    'ai-ml': {'name': 'AI & Machine Learning', 'keywords': 'artificial intelligence OR machine learning OR ChatGPT OR automation OR AI ethics'},
    'cybersecurity': {'name': 'Cybersecurity & Privacy', 'keywords': 'cybersecurity OR data breach OR encryption OR privacy OR hacking'},
    'software-dev': {'name': 'Software Development', 'keywords': 'programming OR coding OR software development OR IDE OR debugging'},
    'web-dev': {'name': 'Web Development', 'keywords': 'HTML OR CSS OR JavaScript OR frontend OR web development'},
    'mobile': {'name': 'Mobile Technology', 'keywords': 'Android OR iOS OR mobile app OR smartphone'},
    'cloud': {'name': 'Cloud Computing', 'keywords': 'AWS OR Azure OR Google Cloud OR cloud computing OR SaaS'},
    'devops': {'name': 'DevOps & Infrastructure', 'keywords': 'DevOps OR Docker OR Kubernetes OR CI/CD OR automation'},
    'hardware': {'name': 'Hardware & Devices', 'keywords': 'CPU OR GPU OR processor OR laptop OR hardware'},
    'gadgets': {'name': 'Gadgets & Electronics', 'keywords': 'smart TV OR smartwatch OR headphones OR gadgets'},
    'blockchain': {'name': 'Blockchain & Crypto', 'keywords': 'Bitcoin OR Ethereum OR blockchain OR cryptocurrency OR NFT'},
    'gaming': {'name': 'Gaming & eSports', 'keywords': 'gaming OR esports OR console OR video games'},
    'vr-ar': {'name': 'VR/AR/Mixed Reality', 'keywords': 'virtual reality OR augmented reality OR VR OR AR OR metaverse'},
    'startups': {'name': 'Startups & Business', 'keywords': 'startup OR tech business OR acquisition OR investment'},
    'big-data': {'name': 'Big Data & Analytics', 'keywords': 'big data OR data science OR analytics OR business intelligence'},
    'open-source': {'name': 'Open Source', 'keywords': 'open source OR GitHub OR open source project'},
    'quantum': {'name': 'Quantum Computing', 'keywords': 'quantum computing OR quantum processor OR quantum research'},
    'ui-ux': {'name': 'UI/UX & Design', 'keywords': 'UI UX OR design tools OR Figma OR Adobe XD'},
    'tech-events': {'name': 'Tech Events', 'keywords': 'WWDC OR CES OR Google I/O OR tech conference'},
    'tech-jobs': {'name': 'Tech Jobs & Careers', 'keywords': 'tech jobs OR programming jobs OR remote work OR tech careers'},
    'tech-policy': {'name': 'Tech Policy & Ethics', 'keywords': 'tech policy OR digital rights OR tech regulation OR tech ethics'}
}

# Database initialization
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def fetch_tech_news(category=None):
    """Fetch technology news from NewsAPI with error handling and category filtering"""
    try:
        if category and category in TECH_CATEGORIES:
            # Use search endpoint for specific categories
            keywords = TECH_CATEGORIES[category]['keywords']
            url = f'https://newsapi.org/v2/everything?q=({keywords})&language=en&sortBy=publishedAt&apiKey={API_KEY}'
        else:
            # Use top headlines for general tech news
            url = f'https://newsapi.org/v2/top-headlines?category=technology&country=us&apiKey={API_KEY}'
            
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') != 'ok':
            print(f"API Error: {data.get('message', 'Unknown error')}")
            return []
            
        articles = data.get('articles', [])
        
        # Process articles to add formatted date and handle missing data
        processed_articles = []
        for article in articles:
            if article.get('title') and article.get('description'):
                # Format publication date
                pub_date = article.get('publishedAt')
                if pub_date:
                    try:
                        date_obj = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                        article['formatted_date'] = date_obj.strftime('%B %d, %Y at %I:%M %p')
                    except:
                        article['formatted_date'] = 'Date unavailable'
                else:
                    article['formatted_date'] = 'Date unavailable'
                
                # Ensure we have a valid image URL
                if not article.get('urlToImage'):
                    article['urlToImage'] = 'https://via.placeholder.com/400x200?text=No+Image+Available'
                
                processed_articles.append(article)
        
        # Limit results for better performance
        return processed_articles[:20]
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[1] == hash_password(password):
            session['user_id'] = user[0]
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                         (username, email, hash_password(password)))
            conn.commit()
            flash('Account created successfully! Please log in.', 'success')
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'error')
            conn.close()
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Main routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    category = request.args.get('category')
    articles = fetch_tech_news(category)
    
    if not articles:
        flash('Unable to fetch news at the moment. Please try again later.', 'warning')
    
    return render_template('dashboard.html', articles=articles, categories=TECH_CATEGORIES, current_category=category)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
