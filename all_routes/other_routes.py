from flask import render_template


def init_other_routes(app):
    @app.route('/discover')
    def discover_page():
        return render_template('discover.html')

    @app.route('/categories')
    def categories_page():
        return render_template('categories.html')