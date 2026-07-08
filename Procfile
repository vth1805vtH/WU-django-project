release: cd ecommerce_project && mkdir -p media && python manage.py migrate && python manage.py collectstatic --noinput
web: cd ecommerce_project && gunicorn ecommerce_project.wsgi --bind 0.0.0.0:$PORT --workers 4
