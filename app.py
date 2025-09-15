"""
Wellness Tracker App - Main Application
A prototype wellness tracking app that collects daily self-reports and generates personalized wellness scores.
"""

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime, date
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'wellness-tracker-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///wellness_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    wellness_reports = db.relationship('WellnessReport', backref='user', lazy=True)

class WellnessReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    report_date = db.Column(db.Date, default=date.today)
    mood_score = db.Column(db.Integer)  # 1-10 scale
    energy_level = db.Column(db.Integer)  # 1-10 scale
    sleep_quality = db.Column(db.Integer)  # 1-10 scale
    stress_level = db.Column(db.Integer)  # 1-10 scale
    physical_symptoms = db.Column(db.Text)  # Free text description
    wellness_score = db.Column(db.Float)  # Calculated score
    ai_insights = db.Column(db.Text)  # LLM-generated insights
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    """Main page with wellness tracking form"""
    return render_template('index.html')

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    username = data.get('username')
    
    if not username:
        return jsonify({'error': 'Username is required'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(username=username)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'id': user.id, 'username': user.username}), 201

@app.route('/api/users/<int:user_id>/reports', methods=['POST'])
def submit_wellness_report(user_id):
    """Submit a daily wellness report"""
    data = request.get_json()
    
    # Validate user exists
    user = User.query.get_or_404(user_id)
    
    # Check if report already exists for today
    today = date.today()
    existing_report = WellnessReport.query.filter_by(
        user_id=user_id, 
        report_date=today
    ).first()
    
    if existing_report:
        return jsonify({'error': 'Report already submitted for today'}), 400
    
    # Validate required fields
    required_fields = ['mood_score', 'energy_level', 'sleep_quality', 'stress_level']
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({'error': f'{field} is required'}), 400
    
    # Calculate wellness score
    wellness_score = calculate_wellness_score(data)
    
    # Process symptom narrative with LLM (if provided)
    ai_insights = None
    if data.get('physical_symptoms'):
        ai_insights = generate_ai_insights(data['physical_symptoms'])
    
    # Create report
    report = WellnessReport(
        user_id=user_id,
        mood_score=data['mood_score'],
        energy_level=data['energy_level'],
        sleep_quality=data['sleep_quality'],
        stress_level=data['stress_level'],
        physical_symptoms=data.get('physical_symptoms', ''),
        wellness_score=wellness_score,
        ai_insights=ai_insights
    )
    
    db.session.add(report)
    db.session.commit()
    
    return jsonify({
        'id': report.id,
        'wellness_score': wellness_score,
        'ai_insights': ai_insights,
        'message': 'Wellness report submitted successfully'
    }), 201

@app.route('/api/users/<int:user_id>/reports', methods=['GET'])
def get_wellness_reports(user_id):
    """Get wellness reports for a user"""
    user = User.query.get_or_404(user_id)
    
    # Get date range from query params
    days = request.args.get('days', 30, type=int)
    
    reports = WellnessReport.query.filter_by(user_id=user_id)\
        .order_by(WellnessReport.report_date.desc())\
        .limit(days).all()
    
    return jsonify([{
        'id': report.id,
        'report_date': report.report_date.isoformat(),
        'mood_score': report.mood_score,
        'energy_level': report.energy_level,
        'sleep_quality': report.sleep_quality,
        'stress_level': report.stress_level,
        'physical_symptoms': report.physical_symptoms,
        'wellness_score': report.wellness_score,
        'ai_insights': report.ai_insights
    } for report in reports])

@app.route('/api/users/<int:user_id>/wellness-summary', methods=['GET'])
def get_wellness_summary(user_id):
    """Get wellness summary and trends for a user"""
    user = User.query.get_or_404(user_id)
    
    # Get recent reports for trend analysis
    recent_reports = WellnessReport.query.filter_by(user_id=user_id)\
        .order_by(WellnessReport.report_date.desc())\
        .limit(30).all()
    
    if not recent_reports:
        return jsonify({'message': 'No reports found'}), 404
    
    # Calculate averages and trends
    avg_wellness_score = sum(r.wellness_score for r in recent_reports) / len(recent_reports)
    avg_mood = sum(r.mood_score for r in recent_reports) / len(recent_reports)
    avg_energy = sum(r.energy_level for r in recent_reports) / len(recent_reports)
    avg_sleep = sum(r.sleep_quality for r in recent_reports) / len(recent_reports)
    avg_stress = sum(r.stress_level for r in recent_reports) / len(recent_reports)
    
    return jsonify({
        'user_id': user_id,
        'username': user.username,
        'total_reports': len(recent_reports),
        'average_wellness_score': round(avg_wellness_score, 2),
        'averages': {
            'mood_score': round(avg_mood, 2),
            'energy_level': round(avg_energy, 2),
            'sleep_quality': round(avg_sleep, 2),
            'stress_level': round(avg_stress, 2)
        },
        'latest_report_date': recent_reports[0].report_date.isoformat() if recent_reports else None
    })

def calculate_wellness_score(report_data):
    """Calculate personalized wellness score based on self-reported metrics"""
    # Weighted scoring algorithm
    # Higher scores for positive metrics, inverse for stress
    mood_weight = 0.3
    energy_weight = 0.25
    sleep_weight = 0.25
    stress_weight = -0.2  # Negative weight as higher stress = lower wellness
    
    score = (
        report_data['mood_score'] * mood_weight +
        report_data['energy_level'] * energy_weight +
        report_data['sleep_quality'] * sleep_weight +
        (10 - report_data['stress_level']) * abs(stress_weight)  # Invert stress scale
    )
    
    # Normalize to 0-100 scale
    normalized_score = (score / 10) * 100
    return round(normalized_score, 2)

def generate_ai_insights(symptom_text):
    """Generate AI insights from symptom narratives using LLM"""
    # For now, return a simple analysis
    # In production, this would integrate with OpenAI or similar LLM service
    
    if not symptom_text or len(symptom_text.strip()) < 10:
        return "No significant symptoms reported."
    
    # Simple keyword-based analysis for the prototype
    keywords = {
        'pain': 'Consider rest and gentle movement. Monitor pain levels.',
        'tired': 'Focus on sleep hygiene and energy management.',
        'anxious': 'Practice relaxation techniques and mindfulness.',
        'headache': 'Stay hydrated and consider stress management.',
        'nausea': 'Monitor food intake and consider dietary adjustments.',
        'dizzy': 'Ensure adequate hydration and rest.'
    }
    
    insights = []
    lower_text = symptom_text.lower()
    
    for keyword, advice in keywords.items():
        if keyword in lower_text:
            insights.append(advice)
    
    if insights:
        return "Insights based on reported symptoms: " + " ".join(insights)
    else:
        return "Continue monitoring symptoms and maintain healthy habits."

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)