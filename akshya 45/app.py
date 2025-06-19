from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Correct PostgreSQL config
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:sai12345@localhost:5432/vmis_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    feedbacks = db.relationship('Feedback', backref='user', lazy=True, cascade="all, delete")

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

# CREATE
@app.route('/users/create', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            
            if not name or not email:
                flash('Name and email are required', 'error')
                return redirect(url_for('create_user'))
                
            new_user = User(name=name, email=email)
            db.session.add(new_user)
            db.session.commit()
            
            flash('User created successfully!', 'success')
            return redirect(url_for('view_feedbacks', user_id=new_user.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('create_user'))
    
    return render_template('create_user.html')

@app.route('/feedbacks/submit', methods=['GET', 'POST'])
def submit_feedback():
    if request.method == 'POST':
        try:
            user_id = request.form['user_id']
            feedback_text = request.form['feedback']
            
            if not user_id or not feedback_text:
                flash('User ID and feedback are required', 'error')
                return redirect(url_for('submit_feedback'))
                
            new_feedback = Feedback(user_id=user_id, feedback=feedback_text)
            db.session.add(new_feedback)
            db.session.commit()
            
            flash('Feedback submitted successfully!', 'success')
            return redirect(url_for('view_feedbacks', user_id=user_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('submit_feedback'))
    
    users = User.query.all()
    return render_template('submit_feedback.html', users=users)

# READ 
@app.route('/users/<int:user_id>/feedbacks')
def view_feedbacks(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('index'))
    
    feedbacks = Feedback.query.filter_by(user_id=user_id).all()
    return render_template('view_feedbacks.html', user=user, feedbacks=feedbacks)

# UPDATE 
@app.route('/feedbacks/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        flash('Feedback not found', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            feedback_text = request.form['feedback']
            
            if not feedback_text:
                flash('Feedback cannot be empty', 'error')
                return redirect(url_for('update_feedback', feedback_id=feedback_id))
                
            feedback.feedback = feedback_text
            db.session.commit()
            
            flash('Feedback updated successfully!', 'success')
            return redirect(url_for('view_feedbacks', user_id=feedback.user_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('update_feedback', feedback_id=feedback_id))
    
    return render_template('update_feedback.html', feedback=feedback)

# DELETE 
@app.route('/feedbacks/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)
    if not feedback:
        flash('Feedback not found', 'error')
        return redirect(url_for('index'))
    
    try:
        user_id = feedback.user_id
        db.session.delete(feedback)
        db.session.commit()
        flash('Feedback deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('view_feedbacks', user_id=user_id))

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)