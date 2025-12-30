# cat > app / routes / __init__.py << "EOF"
from .auth import auth_bp
from .main import main_bp

__all__ = ["auth_bp", "main_bp"]
# EOF
