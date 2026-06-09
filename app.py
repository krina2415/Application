from flask import Flask, render_template, request, redirect, url_for, flash
import datetime
import random
from database import (
    init_db, add_bill, get_all_bills, get_bill_by_id, 
    delete_bill_by_id, search_bills, get_dashboard_stats, get_active_db_engine
)

app = Flask(__name__)
app.secret_key = 'software_billing_system_secret_key_2026'

# Custom Template Filter to format dates robustly for both MySQL and SQLite
@app.template_filter('format_date')
def format_date_filter(value):
    """Formats a database date field into a readable string.
    Works with native Python datetime objects (MySQL) and string formats (SQLite).
    """
    if not value:
        return 'N/A'
    if isinstance(value, str):
        try:
            # SQLite stores datetimes as strings, e.g. '2026-06-06 13:05:25' or with milliseconds
            dt = datetime.datetime.strptime(value.split('.')[0], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%d %b %Y, %I:%M %p')
        except Exception:
            return value
    try:
        return value.strftime('%d %b %Y, %I:%M %p')
    except Exception:
        return str(value)

from fpdf import FPDF
import os

def save_bill_pdf_to_c(bill):
    """Generates a professional PDF for the bill and saves it to C:\SoftBill_Invoices\."""
    try:
        # Create directory
        target_dir = "C:\\SoftBill_Invoices"
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        pdf_filename = f"Invoice_{bill['bill_no']}.pdf"
        pdf_path = os.path.join(target_dir, pdf_filename)
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        
        # Header / Title
        pdf.set_font("Helvetica", style="B", size=18)
        pdf.set_text_color(31, 41, 55) # dark grey
        pdf.cell(0, 10, "SoftBill Solutions", ln=True, align="L")
        
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(107, 114, 128) # muted grey
        pdf.cell(0, 5, "Vastral, Ahmedabad", ln=True)
        pdf.cell(0, 5, "support@softbill.com | +91 99988 87766", ln=True)
        pdf.ln(8)
        
        # Divider Line
        pdf.set_draw_color(229, 231, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Billed To (Customer Details) & Payment Details side-by-side
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.set_text_color(31, 41, 55)
        
        # We can write two columns
        y_before = pdf.get_y()
        
        # Column 1: Customer Details
        pdf.set_x(10)
        pdf.cell(90, 5, "CUSTOMER NAME", ln=False)
        # Column 2: Payment Details
        pdf.set_x(110)
        pdf.cell(90, 5, "PAYMENT DETAILS", ln=True)
        
        pdf.set_font("Helvetica", size=10)
        pdf.set_text_color(55, 65, 81)
        
        # Row 1
        pdf.set_x(10)
        pdf.cell(90, 5, f"Name: {bill['customer_name']}", ln=False)
        pdf.set_x(110)
        pdf.cell(90, 5, f"Invoice No: {bill['bill_no']}", ln=True)
        
        # Row 2
        pdf.set_x(10)
        date_str = str(bill['bill_date']).split('.')[0]
        pdf.cell(90, 5, f"Date of Issue: {date_str}", ln=False)
        pdf.set_x(110)
        pm = bill['payment_method'] if bill['payment_status'] == 'Paid' else '-'
        pdf.cell(90, 5, f"Payment Method: {pm}", ln=True)
        
        # Row 3
        pdf.set_x(10)
        addr = bill['address'] if bill['address'] and bill['address'] != 'N/A' else '-'
        pdf.cell(90, 5, f"Address: {addr}", ln=False)
        pdf.set_x(110)
        pdf.cell(90, 5, f"Payment Status: {bill['payment_status']}", ln=True)
        
        pdf.ln(10)
        
        # Table Headers
        pdf.set_fill_color(249, 250, 251)
        pdf.set_font("Helvetica", style="B", size=10)
        pdf.set_text_color(75, 85, 99)
        pdf.cell(10, 8, "#", border=1, fill=True, align="C")
        pdf.cell(90, 8, "Software Item Description", border=1, fill=True)
        pdf.cell(20, 8, "Version", border=1, fill=True, align="C")
        pdf.cell(30, 8, "Unit Price", border=1, fill=True, align="R")
        pdf.cell(15, 8, "Qty", border=1, fill=True, align="C")
        pdf.cell(25, 8, "Total Amount", border=1, fill=True, align="R")
        pdf.ln()
        
        # Table Row
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(10, 8, "1", border=1, align="C")
        pdf.cell(90, 8, f" {bill['software_name']}", border=1)
        ver = bill['version'] if bill['version'] and bill['version'] != 'N/A' else '-'
        pdf.cell(20, 8, ver, border=1, align="C")
        
        # Calculate rates
        gst_rate = bill.get('gst_rate')
        price = bill['price']
        if gst_rate and gst_rate > 0:
            subtotal = price / (1 + (gst_rate / 100))
            gst_amount = price - subtotal
            subtotal_val = f"Rs {subtotal:,.2f}"
            gst_label = f"GST ({gst_rate}% Integrated):"
            gst_val = f"Rs {gst_amount:,.2f}"
        else:
            subtotal_val = f"Rs {price:,.2f}"
            gst_label = "GST (Tax):"
            gst_val = "-"
            
        pdf.cell(30, 8, f"Rs {price:,.2f}", border=1, align="R")
        pdf.cell(15, 8, "1", border=1, align="C")
        pdf.cell(25, 8, f"Rs {price:,.2f}", border=1, align="R")
        pdf.ln(12)
        
        # License Key & Calculations Side by Side
        y_before_calc = pdf.get_y()
        
        # License Key Box (Left Side)
        pdf.set_x(10)
        if bill['license_key'] and bill['license_key'] != 'N/A':
            pdf.set_fill_color(243, 244, 246)
            pdf.set_draw_color(124, 58, 237) # violet border
            pdf.rect(10, y_before_calc, 100, 22, style="FD")
            pdf.set_xy(12, y_before_calc + 2)
            pdf.set_font("Helvetica", style="B", size=9)
            pdf.set_text_color(124, 58, 237)
            pdf.cell(96, 4, "Digital License Product Activation Key", ln=True)
            pdf.set_x(12)
            pdf.set_font("Courier", style="B", size=11)
            pdf.set_text_color(31, 41, 55)
            pdf.cell(96, 6, bill['license_key'], ln=True)
            pdf.set_x(12)
            pdf.set_font("Helvetica", size=8)
            pdf.set_text_color(107, 114, 128)
            pdf.cell(96, 4, "Note: Keep this license key safe.", ln=True)
            
        # Calculations Box (Right Side)
        pdf.set_draw_color(229, 231, 235) # reset draw color
        pdf.set_xy(120, y_before_calc)
        pdf.set_font("Helvetica", size=9)
        pdf.set_text_color(107, 114, 128)
        
        pdf.cell(45, 5, "Subtotal (Excl. Tax):", ln=False)
        pdf.cell(25, 5, subtotal_val, ln=True, align="R")
        
        pdf.set_x(120)
        pdf.cell(45, 5, gst_label, ln=False)
        pdf.cell(25, 5, gst_val, ln=True, align="R")
        
        pdf.line(120, pdf.get_y() + 1, 190, pdf.get_y() + 1)
        pdf.ln(3)
        
        pdf.set_x(120)
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(45, 6, "Grand Total (INR):", ln=False)
        pdf.cell(25, 6, f"Rs {price:,.2f}", ln=True, align="R")
        
        pdf.ln(15)
        
        # Signature Area
        pdf.line(130, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(2)
        pdf.set_x(130)
        pdf.set_font("Helvetica", style="B", size=9)
        pdf.set_text_color(55, 65, 81)
        pdf.cell(60, 5, "Authorized Signatory", ln=True, align="C")
        
        # Save output
        pdf.output(pdf_path)
        return True, pdf_path
    except Exception as e:
        return True, str(e) # Return true with error to not block flow, or handle accordingly

# Try to initialize database on startup (using MySQL or SQLite fallback)
db_initialized = False
try:
    success, msg = init_db()
    if success:
        db_initialized = True
except Exception as e:
    print(f"[WARNING] Database connection error on startup: {e}")

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Redirects base path to the dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard showing invoice listing, search results, and total stats."""
    search_query = request.args.get('search', '').strip()
    
    bills = []
    stats = {
        'total_revenue': 0.00,
        'total_sales_count': 0,
        'unique_customers': 0,
        'popular_software': []
    }
    db_connected = True
    active_engine = 'sqlite'
    
    try:
        global db_initialized
        if not db_initialized:
            success, msg = init_db()
            if success:
                db_initialized = True

        if search_query:
            bills = search_bills(search_query)
        else:
            bills = get_all_bills()
        stats = get_dashboard_stats()
        active_engine = get_active_db_engine()
    except Exception as e:
        db_connected = False
        print(f"[ERROR] Dashboard database error: {e}")
        
    return render_template(
        'dashboard.html', 
        bills=bills, 
        stats=stats, 
        search_query=search_query,
        db_connected=db_connected,
        db_engine=active_engine
    )

@app.route('/bill/new', methods=['GET', 'POST'])
def create_bill_route():
    """Handles purchase bill creation form."""
    db_connected = True
    active_engine = 'sqlite'
    try:
        global db_initialized
        if not db_initialized:
            success, msg = init_db()
            if success:
                db_initialized = True
        active_engine = get_active_db_engine()
    except Exception as e:
        db_connected = False
        print(f"[ERROR] Database connection failed on form load: {e}")

    if request.method == 'POST':
        if not db_connected:
            flash("Database connection error. Cannot save purchase record.", "error")
            return render_template('create_bill.html', db_connected=db_connected, db_engine=active_engine)

        bill_no = request.form.get('bill_no', '').strip()
        customer_name = request.form.get('customer_name', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        address = request.form.get('address', '').strip()
        software_name = request.form.get('software_name', '').strip()
        version = request.form.get('version', '').strip()
        price_str = request.form.get('price', '0.00').strip()
        license_key = request.form.get('license_key', '').strip()
        
        # Corporate Details
        payment_status = request.form.get('payment_status', 'Paid').strip()
        payment_method = request.form.get('payment_method', 'UPI').strip()
        gst_rate_str = request.form.get('gst_rate', '18').strip()
        notes = request.form.get('notes', '').strip()
        action_type = request.form.get('action_type', 'print').strip()
        
        # Auto-fill/Default logic for optional or empty fields to allow printing/generation
        if not bill_no:
            import random
            # Generate a unique invoice number with date and a random tag
            bill_no = f"BILL-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
            
        if not customer_name:
            customer_name = "Customer"
            
        if not mobile_number:
            mobile_number = "N/A"
            
        if not address:
            address = "N/A"
            
        if not software_name:
            software_name = "General Software"
            
        if not version:
            version = "N/A"
            
        if not license_key:
            license_key = "N/A"

        # Price parsing: Default to 0 if empty/invalid
        price = 0.0
        if price_str:
            try:
                price = float(price_str)
                if price < 0:
                    price = 0.0
            except ValueError:
                price = 0.0

        # GST Rate parsing: None if empty/invalid
        gst_rate = None
        if gst_rate_str and gst_rate_str.strip():
            import re
            # Extract first group of digits from the input string
            match = re.match(r'^\s*(\d+)', gst_rate_str)
            if match:
                try:
                    gst_rate = int(match.group(1))
                    if gst_rate < 0 or gst_rate > 100:
                        gst_rate = None
                except ValueError:
                    gst_rate = None
            else:
                gst_rate = 18
            
        # Insert into active database
        try:
            success, result = add_bill(
                bill_no=bill_no,
                customer_name=customer_name,
                mobile_number=mobile_number,
                address=address,
                software_name=software_name,
                version=version,
                price=price,
                license_key=license_key,
                payment_status=payment_status,
                payment_method=payment_method,
                gst_rate=gst_rate,
                notes=notes
            )
            
            if success:
                # Fetch saved bill details for PDF generation
                saved_bill = get_bill_by_id(result)
                if saved_bill:
                    save_bill_pdf_to_c(saved_bill)
                
                flash(f"Purchase invoice {bill_no} successfully generated!", "success")
                if action_type == 'download':
                    return redirect(url_for('view_bill_route', bill_id=result) + "?download=true")
                elif action_type == 'save':
                    return redirect(url_for('view_bill_route', bill_id=result))
                else:
                    return redirect(url_for('view_bill_route', bill_id=result) + "?print=true")
            else:
                flash(f"Database Error: Could not save bill.", "error")
        except Exception as e:
            err_msg = str(e)
            if "UNIQUE" in err_msg or "1062" in err_msg or "Duplicate entry" in err_msg:
                flash("Error: This Bill/Invoice Number already exists. Please choose a different one.", "error")
            else:
                flash(f"Database Error: {e}", "error")
            
        return render_template('create_bill.html', db_connected=db_connected, db_engine=active_engine)
            
    return render_template('create_bill.html', db_connected=db_connected, db_engine=active_engine)

@app.route('/bill/<int:bill_id>')
def view_bill_route(bill_id):
    """View details of a generated invoice."""
    db_connected = True
    bill = None
    active_engine = 'sqlite'
    try:
        bill = get_bill_by_id(bill_id)
        active_engine = get_active_db_engine()
        if not bill:
            flash("Invoice record not found.", "error")
            return redirect(url_for('dashboard'))
    except Exception as e:
        db_connected = False
        print(f"[ERROR] Database error when viewing invoice: {e}")
        flash("Database Connection Error: Can't view invoice details.", "error")
        return redirect(url_for('dashboard'))
        
    return render_template('invoice.html', bill=bill, db_connected=db_connected, db_engine=active_engine)

@app.route('/bill/delete/<int:bill_id>', methods=['POST'])
def delete_bill_route(bill_id):
    """Deletes an invoice record by database ID."""
    try:
        success = delete_bill_by_id(bill_id)
        if success:
            flash("Invoice record has been deleted successfully.", "success")
        else:
            flash("Error: Could not delete the invoice record.", "error")
    except Exception as e:
        flash(f"Database Error: {e}", "error")
    return redirect(url_for('dashboard'))

@app.route('/bill/<int:bill_id>/download_pdf')
def download_pdf_route(bill_id):
    """Generates PDF, saves a copy to C:\SoftBill_Invoices\, and sends it to the browser as a download."""
    from flask import send_file
    try:
        bill = get_bill_by_id(bill_id)
        if not bill:
            flash("Invoice not found.", "error")
            return redirect(url_for('dashboard'))
            
        success, filepath = save_bill_pdf_to_c(bill)
        if success:
            return send_file(
                filepath,
                as_attachment=True,
                download_name=f"Invoice_{bill['bill_no']}.pdf",
                mimetype='application/pdf'
            )
        else:
            flash(f"Failed to generate PDF: {filepath}", "error")
            return redirect(url_for('view_bill_route', bill_id=bill_id))
    except Exception as e:
        flash(f"Error downloading PDF: {e}", "error")
        return redirect(url_for('view_bill_route', bill_id=bill_id))

@app.route('/bill/<int:bill_id>/download_to_c_bg')
def download_to_c_bg_route(bill_id):
    """Background endpoint to save PDF directly to C:\SoftBill_Invoices\ without redirecting."""
    try:
        bill = get_bill_by_id(bill_id)
        if not bill:
            return {"success": False, "error": "Invoice not found"}, 404
            
        success, filepath = save_bill_pdf_to_c(bill)
        if success:
            return {"success": True, "filepath": filepath}
        else:
            return {"success": False, "error": filepath}, 500
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

# ─── Error Handlers ──────────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
