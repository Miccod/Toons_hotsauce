import os
import stripe
from flask import Flask, render_template, request, jsonify, abort
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Order

# Load env vars
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
DOMAIN = os.getenv("DOMAIN", "http://localhost:4242")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hotsauce.db")

# Setup DB
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)

# Flask app
app = Flask(__name__)

# Simple product catalog
PRODUCTS = {
    "hotsauce_small": {"name": "HotSauce - Small", "unit_amount": 899, "currency": "cad"},
    "hotsauce_large": {"name": "HotSauce - Large", "unit_amount": 1599, "currency": "cad"},
}

@app.route("/")
def index():
    return render_template("index.html", products=PRODUCTS)

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json or {}
    cart = data.get("cart", [])

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    db = DBSession()
    line_items = []
    total_amount = 0
    order_items = []

    for item in cart:
        sku = item.get("sku")
        quantity = int(item.get("quantity", 1))
        product = PRODUCTS.get(sku)

        if not product:
            return jsonify({"error": f"Invalid product {sku}"}), 400

        amount = product["unit_amount"] * quantity / 100.0
        total_amount += amount

        # Save to order_items for later DB insert
        order_items.append((sku, quantity, product, amount))

        # Stripe line item
        line_items.append({
            "price_data": {
                "currency": product["currency"],
                "product_data": {"name": product["name"]},
                "unit_amount": product["unit_amount"],
            },
            "quantity": quantity,
        })

    # Create local Order in DB (initially pending)
    order = Order(
        product_sku=",".join([i[0] for i in order_items]),  # multiple SKUs
        quantity=sum(i[1] for i in order_items),
        amount=total_amount,
        currency="cad",
        status="pending",
    )
    db.add(order)
    db.commit()

    # Create Stripe Checkout session linked to DB order
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=line_items,
        mode="payment",
        success_url=f"{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{DOMAIN}/cancel",
        client_reference_id=str(order.id),  # 🔗 Link Stripe session to your DB order
        shipping_address_collection={"allowed_countries": ["CA", "US"]}
    )

    # Save Stripe session ID to DB
    order.stripe_session_id = session.id
    db.commit()

    return jsonify({"url": session.url})



@app.route("/webhook", methods=["POST"])
def webhook_received():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except Exception:
        abort(400)

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        order_id = session_obj.get("client_reference_id")
        db = DBSession()
        order = db.query(Order).get(int(order_id))
        if order:
            order.status = "paid"
            db.commit()
            print(f"✅ Order {order.id} marked as paid.")

    return "", 200

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")
@app.route("/cart")
def cart():
    return render_template("cart.html")

if __name__ == "__main__":
    app.run(port=4242, debug=True)
