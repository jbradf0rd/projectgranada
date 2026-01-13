from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('search.html', active_page='search')


@main_bp.route('/search')
def search():
    return render_template('search.html', active_page='search')


@main_bp.route('/books')
def books():
    return render_template('books.html', active_page='books')


@main_bp.route('/authors')
def authors():
    return render_template('authors.html', active_page='authors')


@main_bp.route('/categories')
def categories():
    return render_template('categories.html', active_page='categories')


@main_bp.route('/collections')
def collections():
    return render_template('collections.html', active_page='collections')


@main_bp.route('/settings')
def settings():
    return render_template('settings.html', active_page='settings')


@main_bp.route('/reader')
@main_bp.route('/reader/<int:book_id>')
def reader(book_id=None):
    return render_template('reader.html', active_page='reader')


@main_bp.route('/wizard')
def wizard():
    return render_template('wizard.html', active_page='wizard')
