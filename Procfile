release: cd ecommerce_project && python manage.py migrate
web: cd ecommerce_project && gunicorn ecommerce_project.wsgi --bind 0.0.0.0:$PORT --workers 4
