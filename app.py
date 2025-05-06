"""
Основной модуль приложения Dash.
Настраивает и запускает веб-сервер с приложением визуализации данных.
"""
from dash import Dash
from layouts import create_layout
from callbacks import register_callbacks

# Подключение внешних CSS-стилей
EXTERNAL_STYLESHEETS = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=EXTERNAL_STYLESHEETS)

# Определение серверного объекта для Gunicorn
server = app.server

# Создание layout
app.layout = create_layout()

# Регистрация callback-функций
register_callbacks(app)

# Запуск сервера
if __name__ == '__main__':
    app.run_server(debug=False)  