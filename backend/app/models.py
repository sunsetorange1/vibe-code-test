from . import db
from werkzeug.security import generate_password_hash, check_password_hash

# Role constants
ADMIN = 'admin'
CONSULTANT = 'consultant'
READ_ONLY = 'read_only'
USER_ROLES = [ADMIN, CONSULTANT, READ_ONLY]

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False) # For local accounts
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True) # Nullable if user only logs in via SSO
    role = db.Column(db.String(64), nullable=False, default=READ_ONLY)

    # New field for Azure AD Object ID
    azure_oid = db.Column(db.String(36), unique=True, index=True, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Ensure password_hash is not None before checking, for SSO-only users
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
