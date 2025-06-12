from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from planner import ai_plan
from models import db, User, Bill, Paycheck

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your-secret-key'
db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form['password'])
        new_user = User(email=request.form['email'], password=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    bills = Bill.query.filter_by(user_id=user_id).all()
    paychecks = Paycheck.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        if 'add_bill' in request.form:
            b = Bill(
                user_id=user_id,
                name=request.form['bill_name'],
                amount=float(request.form['bill_amount']),
                due_date=datetime.strptime(request.form['bill_due'], '%Y-%m-%d'),
                recurrence=request.form['bill_recur']
            )
            db.session.add(b)
            db.session.commit()

        elif 'add_paycheck' in request.form:
            p = Paycheck(
                user_id=user_id,
                amount=float(request.form['paycheck_amount']),
                date=datetime.strptime(request.form['paycheck_date'], '%Y-%m-%d'),
                recurrence=request.form['paycheck_recur']
            )
            db.session.add(p)
            db.session.commit()

    return render_template('dashboard.html', bills=bills, paychecks=paychecks)

@app.route('/run-plan')
def run_plan():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    bills = Bill.query.filter_by(user_id=user_id).all()
    paychecks = Paycheck.query.filter_by(user_id=user_id).order_by(Paycheck.date.desc()).first()

    if not paychecks:
        return "No paycheck found."

    plan = ai_plan(paychecks, bills)
    return render_template('plan.html', plan=plan)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render dynamically sets PORT
    app.run(host='0.0.0.0', port=port)

