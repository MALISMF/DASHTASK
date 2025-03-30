from dash import Dash
from layouts import create_layout
from callbacks import register_callbacks

# Подключение внешних CSS стилей
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

# Определение серверного объекта для Gunicorn
server = app.server

# Создание layout
app.layout = create_layout()

# Регистрация callback-функций
register_callbacks(app)

# Запуск сервера
if __name__ == '__main__':
    app.run_server(debug=False)  