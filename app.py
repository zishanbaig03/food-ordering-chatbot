from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import spacy
from rapidfuzz import fuzz


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_orders.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
nlp = spacy.load("en_core_web_sm")

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(50))
    price = db.Column(db.Float)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50))
    item_name = db.Column(db.String(50))

@app.route("/")
def home():
    return render_template("index.html")

def get_intent(text):
    doc = nlp(text.lower())
    menu_items = [item.item_name.lower() for item in Menu.query.all()]
    if any(token.lemma_ in ["order", "buy"] for token in doc):
        return "order"
    elif any(token.lemma_ in ["menu", "food"] for token in doc):
        return "menu"
    elif any(token.lemma_ in ["track", "status"] for token in doc):
        return "track"
    elif any(token.lemma_ in ["recommend", "suggest"] for token in doc):
        return "recommend"
    elif any(item in text.lower() for item in menu_items):
        return "order"  # assume it's an order if menu item is mentioned
    return "unknown"


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_id = data["user_id"]
    msg = data["message"]
    intent = get_intent(msg)
    response = ""

    if intent == "menu":
        items = Menu.query.all()
        response = "Here's our menu: " + ", ".join(f"{i.item_name} (${i.price})" for i in items)
    elif intent == "order":
      user_input = msg.lower()
      best_match = None
      highest_score = 0

      for item in Menu.query.all():
        score = fuzz.partial_ratio(user_input, item.item_name.lower())
        if score > highest_score:
            highest_score = score
            best_match = item

      if highest_score > 70:  # Adjust threshold as needed
        new_order = Order(user_id=user_id, item_name=best_match.item_name)
        db.session.add(new_order)
        db.session.commit()
        response = f"{best_match.item_name} added to your order."
      else:
        response = "Sorry, I couldn't match your order. Please try again using a menu item name."

    elif intent == "track":
        orders = Order.query.filter_by(user_id=user_id).all()
        if orders:
            response = "Your order: " + ", ".join(o.item_name for o in orders)
        else:
            response = "No current orders."
    elif intent == "recommend":
        last_order = Order.query.filter_by(user_id=user_id).order_by(Order.id.desc()).first()
        if last_order:
            item = Menu.query.first()
            response = f"You might also like: {item.item_name}"
        else:
            response = "Try our Margherita or Veggie Pizza!"
    else:
        response = "Sorry, I didn't get that."

    return jsonify({"response": response})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
