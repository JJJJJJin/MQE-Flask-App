
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Check if the uploaded file has the correct extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS