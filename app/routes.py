from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from markupsafe import escape

from .utils import allowed_file, ALLOWED_EXTENSIONS

main = Blueprint('main', __name__)


@main.route('/')
def home():
    return render_template('home.html')


@main.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash("No file uploaded", 'error')
            return redirect(url_for('main.home'))
        
        if not allowed_file(file.filename):
            flash(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}", 'error')
            return redirect(url_for('main.home'))
        
        # otherwise uploaded file is valid
        flash(f"File '{escape(file.filename)}' uploaded successfully!", 'success')
    return render_template('upload_file.html')