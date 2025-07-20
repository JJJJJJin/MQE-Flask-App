from . import db
from datetime import datetime, timedelta

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, unique=True, nullable=False)  # External ID from Excel
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    dob = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    def __repr__(self):
        return f'<Customer {self.name}>'

class CustomerAddressUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'), nullable=False)
    old_address = db.Column(db.String(200), nullable=False)
    new_address = db.Column(db.String(200), nullable=False)
    old_latitude = db.Column(db.Float)
    old_longitude = db.Column(db.Float)
    new_latitude = db.Column(db.Float)
    new_longitude = db.Column(db.Float)
    change_date = db.Column(db.DateTime, server_default=db.func.now())

    customer = db.relationship('Customer', backref=db.backref('address_updates', lazy=True))

    def __repr__(self):
        return f'<CustomerAddressUpdate {self.new_address}>'


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    customers_rows = db.Column(db.Integer)
    transactions_rows = db.Column(db.Integer)
    products_rows = db.Column(db.Integer)

    def __repr__(self):
        return f"<UploadLog {self.filename} at {self.upload_time}>"
