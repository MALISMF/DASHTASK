"""
Основной модуль приложения Dash.
Настраивает и запускает веб-сервер с приложением визуализации данных.
"""
from dash import Dash
from layouts import create_layout
from callbacks import register_callbacks

# Подключение внешних CSS-стилей
EXTERNAL_STYLESHEETS = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

def initialize_app() -> Dash:
    """
    Инициализирует приложение Dash с внешними стилями.
    
    Returns:
        Dash: Настроенное приложение Dash.
    """
    app = Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)
    app.layout = create_layout()
    register_callbacks(app)
    return app

# Определение серверного объекта для Gunicorn
app = initialize_app()
server = app.server


# Запуск сервера
if __name__ == '__main__':
    app.run_server(debug=False)  