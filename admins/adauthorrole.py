from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
import json

blue_adauthorrole = Blueprint('blue_adauthorrole', __name__, url_prefix='/admin/author/role')


@blue_adauthorrole.route('/', methods=['POST', 'GET'])
def adauthorrole():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            rolelist, rolelistall = condb(
                'SELECT * FROM role;')
            return jsonify(rolelistall)
        return render_template('admin/roleauthor.html')
    return redirect('/')


@blue_adauthorrole.route('/add', methods=['POST', 'GET'])
def adauthorroleadd():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            rolelist, rolelistall = condb(
                'SELECT * FROM role;')
            return jsonify(rolelistall)
        return render_template('admin/roleauthor.html')
    return redirect('/')


@blue_adauthorrole.route('/edit', methods=['POST', 'GET'])
def adauthorroleedit():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            rolelist, rolelistall = condb(
                'SELECT * FROM role;')
            return jsonify(rolelistall)
        return render_template('admin/roleauthor.html')
    return redirect('/')
