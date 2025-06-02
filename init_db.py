from app import db, Menu, app

with app.app_context():
    db.create_all()
    db.session.add_all([
        Menu(item_name='Margherita', price=10.99),
        Menu(item_name='Pepperoni', price=12.99),
        Menu(item_name='BBQ Chicken', price=13.99),
        Menu(item_name='Veggie', price=11.99)
    ])
    db.session.commit()
    print("✅ Menu items added.")
