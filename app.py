from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import db, AddressRecord
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///address_book.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

db.init_app(app)

with app.app_context():
    db.create_all()

@app.after_request
def add_header(response):
    if app.debug:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    """Home page with recent records and search form"""
    recent_records = AddressRecord.query.order_by(AddressRecord.updated_at.desc()).limit(5).all()
    total_records = AddressRecord.query.count()
    return render_template('index.html', 
                          recent_records=recent_records, 
                          total_records=total_records)

@app.route('/add', methods=['GET', 'POST'])
def add_record():
    """Add a new address record"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        
        if not name or not address:
            flash('Name and Address are required fields!', 'danger')
            return render_template('add_record.html')
        
        existing = AddressRecord.query.filter_by(name=name).first()
        if existing:
            flash(f'Record with name "{name}" already exists!', 'warning')
            return render_template('add_record.html')
        
        new_record = AddressRecord(
            name=name,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            email=email
        )
        
        try:
            db.session.add(new_record)
            db.session.commit()
            flash(f'Record for "{name}" added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding record: {str(e)}', 'danger')
    
    return render_template('add_record.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search for records by name"""
    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        exact_match = request.form.get('exact_match') == 'on'
        
        if not search_term:
            flash('Please enter a name to search!', 'warning')
            return render_template('search.html')
        
        if exact_match:
            records = AddressRecord.query.filter_by(name=search_term).all()
        else:
            records = AddressRecord.query.filter(
                AddressRecord.name.ilike(f'%{search_term}%')
            ).all()
        
        return render_template('result.html', 
                             records=records, 
                             search_term=search_term,
                             exact_match=exact_match,
                             count=len(records))
    
    return render_template('search.html')

@app.route('/search/validate', methods=['POST'])
def validate_name():
    """API endpoint for real-time name validation (AJAX)"""
    name = request.form.get('name', '').strip()
    if not name:
        return jsonify({'exists': False})
    
    record = AddressRecord.query.filter(
        AddressRecord.name.ilike(name)
    ).first()
    
    if record:
        return jsonify({
            'exists': True,
            'record': record.to_dict()
        })
    return jsonify({'exists': False})

@app.route('/view/<int:id>')
def view_record(id):
    """View a specific record"""
    record = AddressRecord.query.get_or_404(id)
    return render_template('result.html', records=[record], search_term=record.name)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_record(id):
    """Edit an existing record"""
    record = AddressRecord.query.get_or_404(id)
    
    if request.method == 'POST':
        record.name = request.form.get('name', '').strip()
        record.address = request.form.get('address', '').strip()
        record.city = request.form.get('city', '').strip()
        record.state = request.form.get('state', '').strip()
        record.zip_code = request.form.get('zip_code', '').strip()
        record.phone = request.form.get('phone', '').strip()
        record.email = request.form.get('email', '').strip()
        
        if not record.name or not record.address:
            flash('Name and Address are required fields!', 'danger')
            return render_template('add_record.html', record=record)
        
        try:
            db.session.commit()
            flash('Record updated successfully!', 'success')
            return redirect(url_for('view_record', id=record.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating record: {str(e)}', 'danger')
    
    return render_template('add_record.html', record=record)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_record(id):
    """Delete a record"""
    record = AddressRecord.query.get_or_404(id)
    name = record.name
    
    try:
        db.session.delete(record)
        db.session.commit()
        flash(f'Record for "{name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting record: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/api/records')
def get_all_records():
    """API endpoint to get all records (JSON)"""
    records = AddressRecord.query.all()
    return jsonify([record.to_dict() for record in records])

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)