# Backend Setup

1. Create a virtual environment:
   ```
   python -m venv env
   ```

2. Activate the virtual environment:
   - On Windows: `env\Scripts\activate`
   - On macOS and Linux: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Run the development server:
   ```
   python manage.py runserver
   ```

superuser sgitt2002@gmail.com
123456

The server should now be running at `http://localhost:8000/`.