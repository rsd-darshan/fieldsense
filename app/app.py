"""
FieldSense — Flask UI + JSON API for agricultural ML models.

Run from the `app` directory: PORT=5050 python app.py
"""
import os

from factory import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"\n  FieldSense → http://127.0.0.1:{port}/\n")
    app.run(debug=True, host="0.0.0.0", port=port)
