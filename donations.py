"""
Donations module using Stripe Checkout
"""

import os
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, jsonify, render_template, session

# Try to import stripe, but handle if it's not installed
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    print("WARNING: stripe module not installed")
    stripe = None
    STRIPE_AVAILABLE = False

donations_bp = Blueprint('donations', __name__, url_prefix='/donate')

# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Set Stripe API key if available and configured
if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    try:
        stripe.api_key = STRIPE_SECRET_KEY
        print(f"Stripe initialized successfully with key: {STRIPE_SECRET_KEY[:20]}...")
    except Exception as e:
        print(f"Error setting Stripe API key: {e}")
        STRIPE_AVAILABLE = False


def get_base_url():
    """Get the base URL for callbacks"""
    return os.environ.get('BASE_URL', 'http://127.0.0.1:5000')


@donations_bp.route('/')
def donate_page():
    """Donation page with amount selection"""
    return render_template('donate.html', stripe_key=STRIPE_PUBLISHABLE_KEY)


@donations_bp.route('/create-session', methods=['POST'])
def create_checkout_session():
    """Create a Stripe Checkout session"""
    from models import db, Donation
    
    # Check if Stripe module is available
    if not STRIPE_AVAILABLE:
        print("Error: Stripe module not available")
        return jsonify({'error': 'Payment processing is currently unavailable'}), 503
    
    # Check if Stripe is configured
    if not STRIPE_SECRET_KEY or STRIPE_SECRET_KEY.strip() == '':
        print("Error: STRIPE_SECRET_KEY environment variable not set")
        return jsonify({'error': 'Payment processing is not configured. Please contact support.'}), 503
    
    try:
        data = request.get_json() or {}
        amount = int(data.get('amount', 500))  # Default $5.00 (in cents)
        donor_name = data.get('name', '').strip()
        donor_email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        # Minimum $1
        if amount < 100:
            amount = 100
        
        # Maximum $10,000
        if amount > 1000000:
            amount = 1000000
        
        # Get current user if logged in
        user_id = session.get('user_id')
        
        # Create Stripe Checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Support Pokémon Knower',
                        'description': 'Thank you for supporting the project!',
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{get_base_url()}/donate/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{get_base_url()}/donate/cancel",
            customer_email=donor_email if donor_email else None,
            metadata={
                'donor_name': donor_name,
                'message': message,
                'user_id': str(user_id) if user_id else '',
            }
        )
        
        # Validate checkout session response
        if not checkout_session:
            print("Error: Stripe returned None for checkout_session")
            return jsonify({'error': 'Failed to create Stripe session'}), 500
            
        if not hasattr(checkout_session, 'id') or not checkout_session.id:
            print(f"Error: Stripe session missing ID. Response: {checkout_session}")
            return jsonify({'error': 'Invalid Stripe session response'}), 500
            
        if not hasattr(checkout_session, 'url') or not checkout_session.url:
            print(f"Error: Stripe session missing URL. Session ID: {checkout_session.id}")
            return jsonify({'error': 'Stripe session URL not available'}), 500
        
        # Create donation record in database
        donation = Donation(
            user_id=user_id,
            stripe_session_id=checkout_session.id,
            amount=amount,
            currency='usd',
            status='pending',
            donor_email=donor_email,
            donor_name=donor_name,
            message=message,
        )
        db.session.add(donation)
        db.session.commit()
        
        return jsonify({'url': checkout_session.url})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@donations_bp.route('/success')
def donation_success():
    """Handle successful donation"""
    from models import db, Donation
    
    session_id = request.args.get('session_id')
    
    if session_id:
        # Update donation status
        donation = Donation.query.filter_by(stripe_session_id=session_id).first()
        if donation and donation.status == 'pending':
            try:
                # Verify with Stripe
                checkout_session = stripe.checkout.Session.retrieve(session_id)
                if checkout_session.payment_status == 'paid':
                    donation.status = 'succeeded'
                    donation.stripe_payment_intent_id = checkout_session.payment_intent
                    donation.completed_at = datetime.utcnow()
                    db.session.commit()
            except:
                pass
    
    return render_template('donate_success.html')


@donations_bp.route('/cancel')
def donation_cancel():
    """Handle cancelled donation"""
    return render_template('donate_cancel.html')


@donations_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    from models import db, Donation
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not STRIPE_WEBHOOK_SECRET:
        return jsonify({'error': 'Webhook not configured'}), 400
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        
        donation = Donation.query.filter_by(stripe_session_id=session_data['id']).first()
        if donation:
            donation.status = 'succeeded'
            donation.stripe_payment_intent_id = session_data.get('payment_intent')
            donation.completed_at = datetime.utcnow()
            db.session.commit()
    
    elif event['type'] == 'checkout.session.expired':
        session_data = event['data']['object']
        
        donation = Donation.query.filter_by(stripe_session_id=session_data['id']).first()
        if donation and donation.status == 'pending':
            donation.status = 'expired'
            db.session.commit()
    
    return jsonify({'status': 'success'})
