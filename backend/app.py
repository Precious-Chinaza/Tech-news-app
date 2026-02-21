print("DEBUG: Top of file")
from flask import Flask, render_template, flash, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy  # NEW
from flask_mail import Mail, Message     # For Email
from itsdangerous import URLSafeTimedSerializer # For Token Generation
import requests
import os
import sys

# Ensure backend directory is in sys.path for imports to work
# whether run directly or via gunicorn from root
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

import hashlib
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv 
from services.ai_engine import StartupMentor
from newspaper import Article
from datetime import datetime

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-123') 

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# --- POSTGRESQL CONFIGURATION ---
# Format: postgresql://username:password@localhost:5432/database_name
# Render and other production environments typically use DATABASE_URL
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Handle the 'postgres' vs 'postgresql' fix
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    # Force SSL mode if it's missing (Render requirement)
    if "sslmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url += f"{separator}sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = database_url

# --- DATABASE MODELS ---

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_verified = db.Column(db.Boolean, default=False)

class CachedArticle(db.Model):
    __tablename__ = 'cached_articles'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text, unique=True, nullable=False)
    title = db.Column(db.String(500))
    # This stores the AI's first breakdown to save your API quota
    initial_analysis = db.Column(db.Text) 
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize the AI Engine
mentor = StartupMentor()
API_KEY = os.getenv('NEWS_API_KEY')

# --- DB CREATION ON STARTUP ---
# move this lower, after the models are defined, to ensure SQLAlchemy sees them
def create_tables():
    with app.app_context():
        try:
            # This force-imports the models to make sure they are registered
            db.reflect() 
            db.create_all()
            print("✅ DEBUG: Database tables verified/created successfully!")
        except Exception as e:
            print(f"❌ DEBUG: Failed to create tables: {e}")

# Call the function immediately
create_tables()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ... [YOUR TECH_CATEGORIES DICTIONARY HERE] 
TECH_CATEGORIES = {
    'ai-ml': {
        'name': 'AI & Machine Learning',
        'primary_keywords': '("artificial intelligence" OR "machine learning" OR "deep learning" OR "neural network" OR ChatGPT OR GPT OR "AI model")',
        'secondary_keywords': '(automation OR "AI ethics" OR "computer vision" OR "natural language processing" OR NLP OR "AI research")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR politics OR finance OR stock OR crypto OR bitcoin)',
        'relevance_terms': ['AI', 'artificial intelligence', 'machine learning', 'neural', 'algorithm', 'model', 'training', 'dataset']
    },
    'cybersecurity': {
        'name': 'Cybersecurity & Privacy',
        'primary_keywords': '(cybersecurity OR "cyber security" OR "data breach" OR hacking OR malware OR ransomware OR phishing)',
        'secondary_keywords': '(encryption OR privacy OR "data protection" OR firewall OR "security vulnerability" OR "cyber attack")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR fashion OR food)',
        'relevance_terms': ['security', 'breach', 'hack', 'malware', 'encryption', 'privacy', 'vulnerability', 'cyber']
    },
    'software-dev': {
        'name': 'Software Development',
        'primary_keywords': '("software development" OR programming OR coding OR "software engineering" OR developer OR "code review")',
        'secondary_keywords': '(IDE OR debugging OR "version control" OR Git OR "software architecture" OR framework OR library)',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR hardware OR gadget)',
        'relevance_terms': ['programming', 'code', 'developer', 'software', 'framework', 'library', 'API', 'development']
    },
    'web-dev': {
        'name': 'Web Development',
        'primary_keywords': '("web development" OR "frontend development" OR "backend development" OR JavaScript OR React OR Angular OR Vue)',
        'secondary_keywords': '(HTML OR CSS OR "web framework" OR Node.js OR "web application" OR "responsive design")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR hardware OR mobile app)',
        'relevance_terms': ['web', 'frontend', 'backend', 'JavaScript', 'HTML', 'CSS', 'browser', 'website']
    },
    'mobile': {
        'name': 'Mobile Technology',
        'primary_keywords': '("mobile app" OR "mobile development" OR Android OR iOS OR smartphone OR "mobile technology")',
        'secondary_keywords': '("app store" OR "mobile security" OR "mobile UI" OR tablet OR "mobile platform")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR desktop OR laptop)',
        'relevance_terms': ['mobile', 'app', 'Android', 'iOS', 'smartphone', 'tablet', 'mobile development']
    },
    'cloud': {
        'name': 'Cloud Computing',
        'primary_keywords': '("cloud computing" OR AWS OR Azure OR "Google Cloud" OR "cloud platform" OR "cloud service")',
        'secondary_keywords': '(SaaS OR PaaS OR IaaS OR "cloud storage" OR "cloud security" OR serverless OR microservices)',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR hardware OR gadget)',
        'relevance_terms': ['cloud', 'AWS', 'Azure', 'serverless', 'microservices', 'SaaS', 'infrastructure']
    },
    'devops': {
        'name': 'DevOps & Infrastructure',
        'primary_keywords': '(DevOps OR Docker OR Kubernetes OR "CI/CD" OR "continuous integration" OR "continuous deployment")',
        'secondary_keywords': '(automation OR infrastructure OR deployment OR monitoring OR "container orchestration")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR consumer OR gadget)',
        'relevance_terms': ['DevOps', 'Docker', 'Kubernetes', 'deployment', 'infrastructure', 'automation', 'CI/CD']
    },
    'hardware': {
        'name': 'Hardware & Devices',
        'primary_keywords': '("computer hardware" OR processor OR CPU OR GPU OR "graphics card" OR motherboard OR RAM)',
        'secondary_keywords': '(chip OR semiconductor OR "hardware design" OR "computer components" OR server OR workstation)',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR software OR app)',
        'relevance_terms': ['hardware', 'processor', 'CPU', 'GPU', 'chip', 'semiconductor', 'component']
    },
    'blockchain': {
        'name': 'Blockchain & Crypto',
        'primary_keywords': '(blockchain OR cryptocurrency OR Bitcoin OR Ethereum OR "crypto currency" OR "digital currency")',
        'secondary_keywords': '(NFT OR "smart contract" OR DeFi OR "decentralized finance" OR mining OR wallet)',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports OR traditional finance)',
        'relevance_terms': ['blockchain', 'crypto', 'Bitcoin', 'Ethereum', 'NFT', 'smart contract', 'DeFi']
    },
    'gaming': {
        'name': 'Gaming & eSports',
        'primary_keywords': '("video game" OR gaming OR esports OR "game development" OR console OR "gaming industry")',
        'secondary_keywords': '("game engine" OR "virtual reality gaming" OR "mobile gaming" OR streamer OR tournament)',
        'exclude_keywords': '(business software OR enterprise OR productivity OR office OR finance OR banking)',
        'relevance_terms': ['gaming', 'game', 'esports', 'console', 'player', 'tournament', 'streamer']
    },
    'vr-ar': {
        'name': 'VR/AR/Mixed Reality',
        'primary_keywords': '("virtual reality" OR "augmented reality" OR VR OR AR OR metaverse OR "mixed reality")',
        'secondary_keywords': '("VR headset" OR "AR glasses" OR "immersive technology" OR "3D visualization")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['virtual reality', 'augmented reality', 'VR', 'AR', 'metaverse', 'immersive', '3D']
    },
    'startups': {
        'name': 'Startups & Business',
        'primary_keywords': '(startup OR "tech startup" OR "tech business" OR acquisition OR "venture capital")',
        'secondary_keywords': '(investment OR funding OR IPO OR "business model" OR entrepreneur)',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['startup', 'business', 'funding', 'investment', 'acquisition', 'entrepreneur', 'venture']
    },
    'big-data': {
        'name': 'Big Data & Analytics',
        'primary_keywords': '("big data" OR "data science" OR analytics OR "business intelligence" OR "data analysis")',
        'secondary_keywords': '("data mining" OR "predictive analytics" OR "data visualization" OR statistics)',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['data', 'analytics', 'science', 'intelligence', 'analysis', 'mining', 'statistics']
    },
    'open-source': {
        'name': 'Open Source',
        'primary_keywords': '("open source" OR GitHub OR "open source project" OR "free software" OR GPL)',
        'secondary_keywords': '("open source community" OR "open source license" OR "collaborative development")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['open source', 'GitHub', 'free software', 'community', 'collaborative', 'license']
    },
    'quantum': {
        'name': 'Quantum Computing',
        'primary_keywords': '("quantum computing" OR "quantum processor" OR "quantum research" OR "quantum technology")',
        'secondary_keywords': '("quantum algorithm" OR "quantum supremacy" OR "quantum cryptography")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['quantum', 'computing', 'processor', 'algorithm', 'supremacy', 'cryptography']
    },
    'ui-ux': {
        'name': 'UI/UX & Design',
        'primary_keywords': '("UI UX" OR "user interface" OR "user experience" OR "design tools" OR Figma)',
        'secondary_keywords': '("Adobe XD" OR "design system" OR "user research" OR prototyping)',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['UI', 'UX', 'design', 'interface', 'experience', 'user', 'prototype']
    },
    'tech-events': {
        'name': 'Tech Events',
        'primary_keywords': '(WWDC OR CES OR "Google I/O" OR "tech conference" OR "tech summit")',
        'secondary_keywords': '("developer conference" OR "tech expo" OR "innovation summit")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['conference', 'event', 'summit', 'expo', 'WWDC', 'CES', 'developer']
    },
    'tech-jobs': {
        'name': 'Tech Jobs & Careers',
        'primary_keywords': '("tech jobs" OR "programming jobs" OR "remote work" OR "tech careers" OR "software engineer")',
        'secondary_keywords': '("job market" OR "tech hiring" OR "developer jobs" OR "tech salary")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['jobs', 'careers', 'hiring', 'remote', 'engineer', 'developer', 'salary']
    },
    'tech-policy': {
        'name': 'Tech Policy & Ethics',
        'primary_keywords': '("tech policy" OR "digital rights" OR "tech regulation" OR "tech ethics" OR "data privacy")',
        'secondary_keywords': '("digital governance" OR "tech law" OR "internet regulation")',
        'exclude_keywords': '(gaming OR game OR entertainment OR movie OR film OR music OR sports)',
        'relevance_terms': ['policy', 'ethics', 'regulation', 'rights', 'privacy', 'governance', 'law']
    }
}


# ... [ calculate_relevance_score, filter_irrelevant_articles, and fetch_tech_news FUNCTIONS HERE] ...

def calculate_relevance_score(article, category_info):
    """Calculate relevance score for an article based on category keywords"""
    if not category_info or 'relevance_terms' not in category_info:
        return 0
    
    title = (article.get('title') or '').lower()
    description = (article.get('description') or '').lower()
    content = f"{title} {description}"
    
    score = 0
    relevance_terms = category_info['relevance_terms']
    
    for term in relevance_terms:
        term_lower = term.lower()
        # Higher score for exact matches in title
        if term_lower in title:
            score += 3
        # Lower score for matches in description
        elif term_lower in description:
            score += 1
    
    return score

def filter_irrelevant_articles(articles, category_info):
    """Filter out articles that don't match the category based on exclude keywords"""
    if not category_info or 'exclude_keywords' not in category_info:
        return articles
    
    exclude_terms = ['gaming', 'game', 'entertainment', 'movie', 'film', 'music', 'sports'] 
    if 'exclude_keywords' in category_info:
        # Extract terms from exclude_keywords string
        exclude_str = category_info['exclude_keywords'].lower()
        exclude_terms.extend([term.strip('() ') for term in exclude_str.split(' OR ')])
    
    filtered_articles = []
    for article in articles:
        title = (article.get('title') or '').lower()
        description = (article.get('description') or '').lower()
        content = f"{title} {description}"
        
        # Check if article contains exclude terms
        is_irrelevant = False
        for exclude_term in exclude_terms:
            if exclude_term and exclude_term in content:
                is_irrelevant = True
                break
        
        if not is_irrelevant:
            filtered_articles.append(article)
    
    return filtered_articles

def fetch_tech_news(category=None):
    """Fetch technology news from NewsAPI with enhanced categorization and filtering"""
    try:
        all_articles = []
        
        if category and category in TECH_CATEGORIES:
            category_info = TECH_CATEGORIES[category]
            
            # Primary search with main keywords
            primary_query = f"{category_info['primary_keywords']} AND technology"
            primary_url = f'https://newsapi.org/v2/everything?q={primary_query}&language=en&sortBy=publishedAt&pageSize=30&apiKey={API_KEY}'
            
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                primary_articles = data.get('articles', [])
                all_articles.extend(primary_articles)
            
            # Secondary search with additional keywords if we need more articles
            if len(all_articles) < 15 and 'secondary_keywords' in category_info:
                secondary_query = f"{category_info['secondary_keywords']} AND technology"
                secondary_url = f'https://newsapi.org/v2/everything?q={secondary_query}&language=en&sortBy=publishedAt&pageSize=20&apiKey={API_KEY}'
                
                try:
                    response = requests.get(secondary_url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get('status') == 'ok':
                        secondary_articles = data.get('articles', [])
                        # Avoid duplicates
                        existing_urls = {article.get('url') for article in all_articles}
                        for article in secondary_articles:
                            if article.get('url') not in existing_urls:
                                all_articles.append(article)
                except:
                    pass  # Continue with primary results if secondary fails
            
            # Filter out irrelevant articles
            all_articles = filter_irrelevant_articles(all_articles, category_info)
            
            # Calculate relevance scores and sort
            for article in all_articles:
                article['relevance_score'] = calculate_relevance_score(article, category_info)
            
            # Sort by relevance score first, then by publication date
            all_articles.sort(key=lambda x: (x.get('relevance_score', 0), x.get('publishedAt', '')), reverse=True)
            
        else:
            # Use top headlines for general tech news
            url = f'https://newsapi.org/v2/top-headlines?category=technology&country=us&pageSize=30&apiKey={API_KEY}'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                print(f"API Error: {data.get('message', 'Unknown error')}")
                return []
                
            all_articles = data.get('articles', [])
        
        # Process articles to add formatted date and handle missing data
        processed_articles = []
        for article in all_articles:
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
        
        # Limit results for better performance and remove duplicates
        seen_urls = set()
        unique_articles = []
        for article in processed_articles:
            url = article.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        return unique_articles[:25]
        
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

# --- ROUTES ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    category = request.args.get('category')
    articles = fetch_tech_news(category)
    return render_template('dashboard.html', articles=articles, categories=TECH_CATEGORIES, current_category=category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Query Postgres using SQLAlchemy
        user = User.query.filter_by(username=username).first()
        
        if user and user.password_hash == hash_password(password):
            if not user.is_verified:
                flash('Please verify your email address first.', 'warning')
                return render_template('login.html')

            session['user_id'] = user.id
            session['username'] = username
            
            # Track last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or Email already exists.', 'error')
            return redirect(url_for('signup'))
            
        new_user = User(
            username=username, 
            email=email, 
            password_hash=hash_password(password),
            is_verified=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Send Verification Email
        send_verification_email(email)
        
        flash('Account created! Please check your email to verify your account.', 'info')
        return redirect(url_for('login'))
        
    return render_template('signup.html')

def send_verification_email(user_email):
    token = serializer.dumps(user_email, salt='email-confirm')
    confirm_url = url_for('verify_email', token=token, _external=True)
    
    html = render_template('email_verification.html', confirm_url=confirm_url)
    msg = Message('Confirm Your Email - Discuss Tech News', recipients=[user_email], html=html)
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except Exception:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('login'))
        
    user = User.query.filter_by(email=email).first_or_404()
    if user.is_verified:
        flash('Account already verified. Please login.', 'info')
    else:
        user.is_verified = True
        db.session.commit()
        flash('You have verified your email. Thanks!', 'success')
        
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- THE SMART AI ANALYSIS ROUTE (CACHE ENABLED) ---
@app.route("/analyze", methods=["POST"])
@login_required
def analyze_article():
    data = request.json
    article_text = data.get("text")
    user_question = data.get("question")
    article_url = data.get("url") # Ensure your main.js sends the URL!

    if not article_text:
        return jsonify({"error": "No text provided"}), 400

    # 1. CHECK CACHE FOR INITIAL ANALYSIS
    # If it's a first-time discussion (no question) and we have it in DB, serve it!
    if not user_question and article_url:
        cached = CachedArticle.query.filter_by(url=article_url).first()
        if cached and cached.initial_analysis:
            print("--- Serving from Postgres Cache ---")
            return jsonify({"analysis": cached.initial_analysis})

    # 2. CALL AI (If not in cache or if it's a specific follow-up question)
    try:
        if user_question:
            combined_input = f"Context: {article_text}\n\nQuestion: {user_question}"
            analysis_data = mentor.get_analysis(combined_input)
        else:
            analysis_data = mentor.get_analysis(article_text)
            
            # 3. SAVE TO CACHE (Only cache the initial summary)
            if article_url:
                new_cache = CachedArticle(
                    url=article_url, 
                    initial_analysis=analysis_data.get('analysis')
                )
                db.session.merge(new_cache) # Merge avoids duplicate errors
                db.session.commit()

        return jsonify(analysis_data)
    
    except Exception as e:
        print(f"AI Snag: {e}")
        return jsonify({"analysis": "My brain hit a snag. Let's try that again in a second."}), 500

# --- UPDATED READER ROUTE ---
@app.route('/reader')
@login_required
def reader_mode():
    url = request.args.get('url')
    if not url: 
        return redirect(url_for('dashboard'))
    
    # 1. Check if we already have an AI analysis for this URL
    cached = CachedArticle.query.filter_by(url=url).first()
    existing_analysis = cached.initial_analysis if cached else None
    
    try:
        # 2. Fetch the article content
        article = Article(url)
        article.download()
        article.parse()
        
        # 3. Pass the 'existing_analysis' to the template
        return render_template('reader.html', 
                               title=article.title, 
                               content=article.text, 
                               source_url=url,
                               image=article.top_image,
                               existing_analysis=existing_analysis)
    except Exception as e:
        print(f"Scraping error: {e}")
        return redirect(url)

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        print("DEBUG: Creating tables...")
        try:
            db.create_all()
            print("DEBUG: Tables created.")
        except Exception as e:
            print(f"DEBUG: Exception: {e}")

    # Use environment variable for Debug mode, default to False in production
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    print("Starting Flask app...")
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)