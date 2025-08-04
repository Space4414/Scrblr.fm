from app import app
import routes  # Import all routes
import logging

if __name__ == "__main__":
    logging.info("Starting Universal Scrobbler...")
    app.run(host="0.0.0.0", port=5000, debug=True)