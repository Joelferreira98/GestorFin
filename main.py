from app import app
from scheduler import start_reminder_system
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Iniciar sistema de lembretes automáticos em produção
start_reminder_system()
logging.info("Sistema de lembretes automáticos iniciado")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
