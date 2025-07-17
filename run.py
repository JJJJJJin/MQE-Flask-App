from app import create_app

app = create_app()

# Entry point for the application, running the Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0/0', port=5000, debug=True)