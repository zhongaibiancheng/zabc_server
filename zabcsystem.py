from app import app
from app.config import load_config
import os
mode = os.environ.get('MODE')
app.config.from_object(load_config(mode))

from app.resources.admin import admin_bp
from app.resources.student import student_bp
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(student_bp, url_prefix='/api/student')