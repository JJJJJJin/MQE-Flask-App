from flask import Blueprint, render_template, request, redirect, url_for, abort, flash, send_file
from markupsafe import escape

from .utils import is_valid_file, process_file, generate_output_excel

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    return render_template('home.html')


@main.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        # check if file is uploaded
        if not file:
            flash("No file uploaded", 'error')
            return redirect(url_for('main.home'))
        
        # validate file name and content
        r, m = is_valid_file(file)
        if not r:
            flash(f"{m}", 'error')
            return redirect(url_for('main.home'))
        
        # otherwise uploaded file is valid
        flash(f"File '{escape(file.filename)}' uploaded successfully!", 'success')

        # start to data processing
        # returns a tuple (category_totals, top_customers, total_rank)
        # where category_totals reflects the total amount per category for each customer,
        # top_customers reflects the top customers by each category,
        # total_rank reflects the ranking of all customers by their total transaction amount
        category_totals, top_customers, total_rank = process_file(file)
        if any(df.empty for df in [category_totals, top_customers, total_rank]):
            flash("Error processing file data", 'error')
            return redirect(url_for('main.home'))
        flash("File processed successfully!", 'success')

        excel_output = generate_output_excel(category_totals, top_customers, total_rank)
        return send_file(
            excel_output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='processed_data.xlsx'
        )

    return render_template('home.html')