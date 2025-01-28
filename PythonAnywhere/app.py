import os
from flask import Flask, request, render_template, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For flash messages

UPLOAD_FOLDER = 'uploads'
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def allowed_file_size(file, max_size_mb):
    return file.content_length <= max_size_mb * 1024 * 1024

@app.route('/')
def index():
    return render_template('index.html')

@app.before_request
def check_file_size():
    if request.method == 'POST':
        image_file = request.files.get('image')
        
        if image_file and not allowed_file_size(image_file, 2):  # 2 Megabytes in bytes
            flash("Image file size exceeds limit (2 MB). Please upload a smaller file.")
            return redirect(url_for('index'))

@app.route("/upload", methods=["POST"])
def upload_file():
    email = request.form.get("email")

    if "image" not in request.files:
        flash("Both image and text files are required.")
        return redirect(url_for("index"))
    
    image_file = request.files["image"]
   

    if image_file.filename == "":
        flash("No selected Image.")
        return redirect(url_for("index"))

    if image_file and allowed_file(image_file.filename, IMAGE_EXTENSIONS):
        if not allowed_file_size(image_file, 2):
            flash("Image file size exceeds limit (2 MB).")
            return redirect(url_for("index"))
        image_filename = f"{email}_{image_file.filename}"
        image_filepath = os.path.join(UPLOAD_FOLDER, image_filename)
        image_file.save(image_filepath)
    else:
        flash("Invalid image file type. Allowed types are jpg, jpeg, png.")
        return redirect(url_for("index"))

    flash("Files successfully uploaded.")
    return redirect(url_for("index"))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
