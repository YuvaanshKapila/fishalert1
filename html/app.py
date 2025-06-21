import os
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import google.generativeai as genai
import requests

app = Flask(__name__)

# Configure Google Generative AI
genai.configure(api_key='private')
generation_config = {"temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 10}
model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

generation_config1 = {"temperature": 0.9, "top_p": 1, "top_k": 1, "max_output_tokens": 40}
model1 = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config1)

banfile = "banned.json"

def load_banned_sites():
    with open(banfile, 'r') as file:
        return json.load(file)

def save_banned_sites(blist):
    with open(banfile, 'w') as file:
        json.dump(blist, file, indent=4)

def detect_scam(message):
    # Define scam keywords and phrases
    scam_patterns = [
        r'win', r'prize', r'free', r'click here',
        r'urgent', r'act now', r'risk-free', r'guaranteed',
        r'money-back', r'limited time', r'credit', r'debt',
        r'congratulations', r'click below', r'exclusive',
        r'important information regarding', r'this isn\'t a scam',
        r'call now', r'text now', r'claim your', r'apply now',
        r'verify your account', r'account suspended', r'act immediately',
        r'you have been selected', r'get paid', r'get rich quick',
        r'100% satisfied', r'no fees', r'no purchase necessary',
        r'best price', r'business opportunity', r'win big',
        r'do not delete', r'refinance', r'consolidate', r'get started',
        r'free gift', r'gift card', r'call for details', r'satisfaction guaranteed',
        r'urgent response needed', r'we need your help', r'important notice',
        r'please respond', r'your invoice', r'claim your free', r'get started now',
        r'open immediately', r'visit our website', r'win a', r'prize draw',
        r'surprise winnings', r'fraud', r'identity theft',
        r'cybersecurity', r'malware', r'virus', r'update required',
        r'click this link', r'don’t miss out'
    ]
    
    combined_pattern = r'|'.join(scam_patterns)
    
    # Search for any scam patterns in the message
    return bool(re.search(combined_pattern, message, re.IGNORECASE))

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/index')
def index():
    return render_template('index.html')

def load_banned_sites():
    with open('banned.json', 'r') as f:
        return json.load(f)

@app.route('/website_safety', methods=['GET', 'POST'])
def website_safety():
    if request.method == 'POST':
        websitetoopen = request.form.get('website_url')
        blist = load_banned_sites()  # Load banned websites from JSON
        
        # Check if the website entered is in the banned list
        if websitetoopen in blist:
            # Block access if website is banned
            return "Warning: Access to this website is blocked.", 403
        else:
            # Allow access to the unbanned website
            return redirect(f"http://{websitetoopen}")
    
    
    return render_template('website_safety.html', banned_sites=load_banned_sites())
@app.route('/filter_settings', methods=['GET', 'POST'])
def filter_settings():
    password_correct = False
    if request.method == 'POST':
        password = request.form.get('password')
        if password == '123':
            password_correct = True  
            if request.form.get('new_site'):
                return add_site()  
            elif request.form.get('site_to_remove'):
                return remove_site()  
    return render_template('filter_settings.html', 
                           banned_sites=load_banned_sites(), 
                           password_correct=password_correct)

@app.route('/add_site', methods=['POST'])
def add_site():
    new_site = request.form.get('new_site')
    blist = load_banned_sites()
    if new_site and new_site not in blist:
        blist.append(new_site)
        save_banned_sites(blist)
    return redirect(url_for('filter_settings'))

@app.route('/remove_site', methods=['POST'])
def remove_site():
    site_to_remove = request.form.get('site_to_remove')
    blist = load_banned_sites()
    if site_to_remove in blist:
        blist.remove(site_to_remove)
        save_banned_sites(blist)
    return redirect(url_for('filter_settings'))

@app.route('/scam_protection')
def scam_protection():
    return render_template('scam_protection.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        send_email(name, email, message)
        return redirect(url_for('thank_you'))  # Redirect to the thank you page
    return render_template('contact.html')

def send_email(name, email, message):
    sender_email = "kapilayuvaansh@gmail.com"  
    app_password = "vbgy yfhv zxcc pylr"  
    receiver_email = "kapilayuvaansh@gmail.com"  
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Contact Form Submission from {name}"

    body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)

@app.route('/download/<filename>')
def download_file(filename):
    
    safe_filenames = ['main.py', 'banned.json']
    if filename not in safe_filenames:
        return "File not found.", 404
    return send_file(filename, as_attachment=True)

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')  

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html') 

# New route for scam check
@app.route('/check_scam', methods=['GET', 'POST'])
def check_scam():
    if request.method == 'POST':
        message = request.form.get('message')
        is_scam = detect_scam(message)  
        return render_template('check_scam.html', is_scam=is_scam, message=message)
    return render_template('check_scam.html', is_scam=None)

# Route to process speech or text and check for scams
def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F700-\U0001F77F"  # alchemical symbols
        u"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        u"\U0001FA00-\U0001FAFF"  # Chess Symbols
        u"\U00002702-\U000027B0"  # Dingbats
        u"\u2600-\u26FF"          # Miscellaneous symbols
        u"\u2700-\u27BF"          # Dingbats
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

@app.route('/process', methods=['POST'])
def process_text():
    text = request.json.get('text')

    # Analyzing the input for scam phrases
    try:
        response = model.generate_content(f'''
            Given the input sentence: {text}, analyze it to determine if it contains any phrases commonly used by scam callers. 
            If such phrases are found, list them. If no scam phrases were detected, just say: 'No scam phrases were detected.'
        ''')

        scam_analysis = response.text.strip()
        scam_analysis = remove_emojis(scam_analysis)  # Remove emojis

        # Determine the appropriate response based on scam analysis
        if "No scam phrases were detected." in scam_analysis:
            response_ai = model1.generate_content(f'''
                Given the input sentence: {text} and the response: '{scam_analysis}', generate a polite response to keep the conversation friendly.
            ''')
        else:
            response_ai = model1.generate_content(f'''
                Based on the input sentence: {text} and the response: '{scam_analysis}', generate a response to keep the scammer engaged without using emojis.
            ''')

        rebuttal = response_ai.text.strip()
        rebuttal = remove_emojis(rebuttal)  # Remove emojis
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Handle any errors gracefully

    return jsonify({
        'scam_analysis': scam_analysis,
        'rebuttal': rebuttal
    })

API_KEY = '302f4cbcb17ddf01e621e198d58db8b9'  # Replace this with your actual API key

# Route for phone number validation
def validate_phone_number(phone):
    url = "https://apilayer.net/api/validate?access_key=302f4cbcb17ddf01e621e198d58db8b9"  # Replace with your actual access key
    querystring = {"number": phone}
    response = requests.get(url, params=querystring)
    return response.json()  # Assuming the API returns a JSON response

@app.route('/validate_phone', methods=['POST'])
def validate_phone():
    phone_number = request.json.get('phone')
    validation_result = validate_phone_number(phone_number)
    return jsonify(validation_result)

if __name__ == '__main__':
    app.run(debug=True)
