from app import create_app
import locale

app = create_app()

if __name__ == "__main__":
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    app.run(host='0.0.0.0', port=5000, debug=True)
