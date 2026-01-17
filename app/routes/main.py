"""
Granada v2 Main Page Routes
"""
import os
from flask import Blueprint, render_template, send_from_directory, current_app

main_bp = Blueprint('main', __name__)


@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon from static folder."""
    return send_from_directory(
        current_app.static_folder,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@main_bp.route('/')
@main_bp.route('/search')
def search():
    """Search page - main landing page."""
    return render_template('search.html')


@main_bp.route('/books')
@main_bp.route('/browse')
def books():
    """Books page - library management."""
    return render_template('books.html')


@main_bp.route('/authors')
def authors():
    """Authors page - browse by author."""
    return render_template('authors.html')


@main_bp.route('/authors/<author_id>')
def author_detail(author_id):
    """Author detail page - show author info and their books."""
    return render_template('author_detail.html', author_id=author_id)


@main_bp.route('/categories')
def categories():
    """Categories page - browse by category."""
    return render_template('categories.html')


@main_bp.route('/categories/<int:category_id>')
def category_detail(category_id):
    """Category detail page - books in a specific category."""
    return render_template('category_detail.html', category_id=category_id)


@main_bp.route('/collections')
def collections():
    """Collections page - user reading collections."""
    return render_template('collections.html')


@main_bp.route('/settings')
def settings():
    """Settings page."""
    return render_template('settings.html')


@main_bp.route('/book/<book_id>')
def reader(book_id):
    """Book reader page."""
    return render_template('reader.html', book_id=book_id)


@main_bp.route('/book/<book_id>/info')
def book_card(book_id):
    """Book card/info page - detailed metadata."""
    return render_template('book_card.html', book_id=book_id)


@main_bp.route('/wizard')
def wizard():
    """First-run wizard page."""
    return render_template('wizard.html')


@main_bp.route('/notebook')
def notebook():
    """Notes and annotations page."""
    return render_template('notebook.html')
