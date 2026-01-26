"""
Main entry point for the Flask attendance application.
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run the Flask development server
    app.run(debug=True, host='0.0.0.0', port=8000)
