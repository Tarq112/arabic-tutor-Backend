from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import anthropic
import os
from dotenv import load_dotenv
from datetime import datetime
import stripe
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize rate limiter (IP-based protection)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

# Initialize Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Simple in-memory usage tracking (use database in production)
user_usage = {}
email_verification_codes = {}  # Store verification codes temporarily

def is_valid_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_verification_email(email, code):
    """Send verification code to email (optional - requires SMTP setup)"""
    # This is optional - only if you want to send real verification emails
    # For now, we'll just store the code and validate it
    # To enable real emails, set up SMTP credentials in environment variables
    
    smtp_enabled = os.environ.get('SMTP_ENABLED', 'false').lower() == 'true'
    
    if not smtp_enabled:
        print(f"Verification code for {email}: {code}")
        return True
    
    try:
        msg = MIMEMultipart()
        msg['From'] = os.environ.get('SMTP_FROM_EMAIL')
        msg['To'] = email
        msg['Subject'] = 'Verify Your Email - Arabic Tutor'
        
        body = f"""
        Welcome to Arabic Tutor!
        
        Your verification code is: {code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this, please ignore this email.
        
        شكراً (Shukran) - Thank you!
        Arabic Tutor Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(os.environ.get('SMTP_HOST'), int(os.environ.get('SMTP_PORT', 587)))
        server.starttls()
        server.login(os.environ.get('SMTP_USERNAME'), os.environ.get('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False

@app.route('/')
@limiter.limit("10 per minute")
def home():
    return jsonify({
        "message": "Arabic Tutor API is running!",
        "status": "ok",
        "endpoints": {
            "/api/chat": "POST - Send messages to the AI tutor",
            "/api/health": "GET - Check server health",
            "/api/check-subscription": "POST - Check user subscription status",
            "/api/create-checkout": "POST - Create Stripe checkout session",
            "/api/verify-email": "POST - Send verification code to email",
            "/api/confirm-email": "POST - Confirm email with verification code"
        }
    })

@app.route('/api/health')
@limiter.limit("30 per minute")
def health():
    return jsonify({"status": "healthy", "service": "Arabic Tutor API"})

@app.route('/api/verify-email', methods=['POST'])
@limiter.limit("5 per hour")  # Prevent spam
def verify_email():
    """Send verification code to email"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        # Validate email format
        if not is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Generate 6-digit verification code
        code = str(secrets.randbelow(900000) + 100000)
        
        # Store code with timestamp (expires in 10 minutes)
        email_verification_codes[email] = {
            'code': code,
            'timestamp': datetime.now(),
            'verified': False
        }
        
        # Send verification email (or just log it if SMTP not configured)
        send_verification_email(email, code)
        
        return jsonify({
            'success': True,
            'message': 'Verification code sent to your email'
        })
        
    except Exception as e:
        print(f"Verification error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/confirm-email', methods=['POST'])
@limiter.limit("10 per hour")  # Prevent brute force
def confirm_email():
    """Confirm email with verification code"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        # Check if code exists
        if email not in email_verification_codes:
            return jsonify({'error': 'No verification code found for this email'}), 400
        
        stored_data = email_verification_codes[email]
        
        # Check if already verified
        if stored_data.get('verified'):
            return jsonify({'success': True, 'message': 'Email already verified'})
        
        # Check if code expired (10 minutes)
        time_diff = (datetime.now() - stored_data['timestamp']).total_seconds()
        if time_diff > 600:  # 10 minutes
            del email_verification_codes[email]
            return jsonify({'error': 'Verification code expired. Please request a new one.'}), 400
        
        # Check if code matches
        if stored_data['code'] != code:
            return jsonify({'error': 'Invalid verification code'}), 400
        
        # Mark as verified
        email_verification_codes[email]['verified'] = True
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully!'
        })
        
    except Exception as e:
        print(f"Confirmation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-checkout', methods=['POST'])
@limiter.limit("10 per hour")  # Prevent checkout spam
def create_checkout():
    """Create a Stripe checkout session for subscription"""
    try:
        data = request.json
        user_email = data.get('email', '').strip().lower()
        plan = data.get('plan', 'premium')
        
        # Validate email format
        if not is_valid_email(user_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Optional: Check if email is verified
        # Uncomment if you want to enforce email verification before payment
        # if user_email in email_verification_codes:
        #     if not email_verification_codes[user_email].get('verified'):
        #         return jsonify({'error': 'Please verify your email first'}), 400
        
        price_ids = {
            'premium': os.environ.get('STRIPE_PRICE_PREMIUM'),
            'premium_voice': os.environ.get('STRIPE_PRICE_PREMIUM_VOICE')
        }
        
        price_id = price_ids.get(plan)
        
        if not price_id:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        domain = os.environ.get('FRONTEND_URL', 'http://localhost:8000')
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'{domain}/success.html?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{domain}',
            customer_email=user_email,
        )
        
        return jsonify({'checkout_url': checkout_session.url})
        
    except Exception as e:
        print(f"Checkout error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-subscription', methods=['POST'])
@limiter.limit("30 per minute")
def check_subscription():
    """Check if user has active subscription"""
    try:
        data = request.json
        user_email = data.get('email', '').strip().lower()
        
        if not user_email or not is_valid_email(user_email):
            return jsonify({'has_subscription': False, 'remaining_messages': 10})
        
        customers = stripe.Customer.list(email=user_email, limit=1)
        
        if not customers.data:
            today = datetime.now().strftime('%Y-%m-%d')
            usage_key = f"{user_email}:{today}"
            current_usage = user_usage.get(usage_key, 0)
            remaining = max(0, 10 - current_usage)
            
            return jsonify({
                'has_subscription': False,
                'remaining_messages': remaining
            })
        
        customer = customers.data[0]
        subscriptions = stripe.Subscription.list(
            customer=customer.id, 
            status='active', 
            limit=1
        )
        
        has_active = len(subscriptions.data) > 0
        
        return jsonify({
            'has_subscription': has_active,
            'subscription_status': subscriptions.data[0].status if has_active else None,
            'remaining_messages': 'unlimited' if has_active else 0
        })
        
    except Exception as e:
        print(f"Subscription check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
@limiter.limit("100 per hour")  # IP-based rate limit to prevent API abuse
def chat():
    try:
        data = request.json
        messages = data.get('messages', [])
        system_prompt = data.get('system', '')
        max_tokens = data.get('max_tokens', 1024)
        user_email = data.get('user_email', 'anonymous').strip().lower()
        
        if not messages:
            print("ERROR: No messages provided")
            return jsonify({"error": "No messages provided"}), 400
        
        # Validate email format if provided
        if user_email != 'anonymous' and not is_valid_email(user_email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Check if user has active subscription
        has_subscription = check_user_has_subscription(user_email)
        
        # Apply usage limits for free users
        if not has_subscription and user_email != 'anonymous':
            today = datetime.now().strftime('%Y-%m-%d')
            usage_key = f"{user_email}:{today}"
            current_usage = user_usage.get(usage_key, 0)
            
            if current_usage >= 10:
                return jsonify({
                    "success": False,
                    "error": "Daily limit reached! Upgrade to Premium for unlimited messages.",
                    "upgrade_required": True,
                    "remaining_messages": 0
                }), 429
            
            # Increment usage
            user_usage[usage_key] = current_usage + 1
            remaining = 10 - user_usage[usage_key]
        else:
            remaining = 'unlimited'
        
        print(f"Calling Claude API with {len(messages)} messages...")
        
        # Call Claude API
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )
        
        assistant_message = response.content[0].text
        print(f"Success! Got response: {assistant_message[:100]}...")
        
        return jsonify({
            "success": True,
            "message": assistant_message,
            "model": "claude-sonnet-4-5-20250929",
            "remaining_messages": remaining
        })
        
    except anthropic.APIError as e:
        error_msg = f"Anthropic API error: {str(e)}"
        print(f"ERROR: {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500
        
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500

def check_user_has_subscription(email):
    """Helper function to check if user has active subscription"""
    if email == 'anonymous' or not is_valid_email(email):
        return False
    
    try:
        customers = stripe.Customer.list(email=email, limit=1)
        if not customers.data:
            return False
        
        customer = customers.data[0]
        subscriptions = stripe.Subscription.list(
            customer=customer.id, 
            status='active', 
            limit=1
        )
        
        return len(subscriptions.data) > 0
    except Exception as e:
        print(f"Subscription check helper error: {str(e)}")
        return False

# Error handlers for rate limiting
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "Rate limit exceeded. Please try again later.",
        "message": str(e.description)
    }), 429

if __name__ == '__main__':
    # Check environment variables
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set!")
    else:
        print("✓ Anthropic API key loaded")
    
    if not os.environ.get("STRIPE_SECRET_KEY"):
        print("WARNING: STRIPE_SECRET_KEY not set!")
    else:
        print("✓ Stripe API key loaded")
    
    print("✓ IP-based rate limiting enabled")
    print("✓ Email validation enabled")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
