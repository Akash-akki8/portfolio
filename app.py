from datetime import datetime, timezone
from pathlib import Path
import logging
import os
import re

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, redirect, send_from_directory

load_dotenv(override=True)

app = Flask(__name__, static_folder='.', static_url_path='')

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
MAX_PHONE_LENGTH = 20
MAX_MESSAGE_LENGTH = 1000
MIN_MESSAGE_LENGTH = 10
MIN_NAME_LENGTH = 2

BASE_DIR = Path(__file__).resolve().parent
CERT_DIR = BASE_DIR / 'certificates'


def send_telegram_alert(name: str, email: str, phone: str, message: str) -> None:
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not all([bot_token, chat_id]):
        logging.warning("Telegram credentials not configured. Please add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to .env")
        return
        
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        telegram_body = f"🚀 *New Portfolio Contact!*\n\n👤 *Name:* {name}\n📧 *Email:* {email}\n📱 *Phone:* {phone}\n💬 *Message:* {message}"
        payload = {
            "chat_id": chat_id,
            "text": telegram_body,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload)
        
        if response.ok:
            logging.info("Telegram alert sent successfully.")
        else:
            logging.error(f"Telegram error: {response.text}")
    except Exception as e:
        logging.error(f"Failed to send Telegram alert: {e}")


def handle_message(name: str, email: str, phone: str, message: str) -> None:
    # Send alerts
    send_telegram_alert(name, email, phone, message)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/contact', methods=['POST'])
def contact():
    payload = request.form if request.form else request.get_json(silent=True) or {}
    name = payload.get('name', '').strip()
    email = payload.get('email', '').strip()
    phone = payload.get('phone', '').strip()
    message = payload.get('message', '').strip()

    if len(name) < MIN_NAME_LENGTH:
        return jsonify({'status': 'error', 'message': 'Please enter a valid name.'}), 400

    if not EMAIL_PATTERN.match(email):
        return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400

    if not phone or len(phone) > MAX_PHONE_LENGTH:
        return jsonify({
            'status': 'error',
            'message': f'Phone is required and must be {MAX_PHONE_LENGTH} characters or fewer.',
        }), 400

    if len(message) < MIN_MESSAGE_LENGTH or len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({
            'status': 'error',
            'message': f'Message must be between {MIN_MESSAGE_LENGTH} and {MAX_MESSAGE_LENGTH} characters.',
        }), 400

    handle_message(name, email, phone, message)

    return jsonify({
        'status': 'success',
        'message': 'Message sent successfully. Thank you for contacting me.',
    })


@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


@app.route('/loan-default-prediction-psi.vercel.app')
def redirect_loan_default():
    return redirect('https://loan-default-prediction-psi.vercel.app/', code=302)


@app.route('/certificates/<path:filename>')
def serve_certificate(filename):
    return send_from_directory(CERT_DIR, filename)


@app.route('/api/portfolio')
def portfolio_api():
    return jsonify({
        'name': 'Chandra Akash',
        'headline': 'AI / ML & Full Stack Developer',
        'summary': 'A driven CSE student building intelligent web applications, machine learning solutions, and polished portfolio experiences.',
        'skills': ['Python', 'JavaScript', 'Flask', 'Django', 'TensorFlow', 'PyTorch'],
        'projects': [
            {'title': 'AI-Based Loan Default Prediction', 'description': 'Predicts loan risk using ML models.'},
            {'title': 'AI-Based Crop Yield Prediction', 'description': 'Recommends optimal crops using AI.'},
            {'title': 'Doctor Prescription Translator', 'description': 'CV-based medical safety system.'},
        ],
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
