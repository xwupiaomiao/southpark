from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
import json

blue_adauthorproject = Blueprint('blue_adauthorproject', __name__, url_prefix='/admin/author/project')


@blue_adauthorproject.route('/', methods=['POST', 'GET'])
def adauthorproject():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            if request.values.get('table') == 'project':
                ptop, ptopall = condb(
                    'SELECT project.`id`,project.`name`,person.`id`,person.`chinesename` FROM project LEFT JOIN projecttoperson ON project_id = project.`id` LEFT JOIN person ON person_id = person.`id`;')
                return jsonify(ptopall)
            elif request.values.get('table') == 'person':
                perso, persoall = condb(
                    'SELECT `id`,`chinesename` FROM person;')
                return jsonify(persoall)
        return render_template('admin/projectauthor.html')
    return redirect('/')


@blue_adauthorproject.route('/edit', methods=['POST', 'GET'])
def adauthorprojectedit():
    author = session.get('author')
    if author.get('manager'):
        if request.method == 'POST':
            peridlist = request.values.get('personid')
            projectid = request.values.get('projectid')
            condb('DELETE FROM `projecttoperson` WHERE project_id="{}";'.format(projectid))
            for i in json.loads(peridlist):
                condb('INSERT INTO `projecttoperson` (project_id,person_id) VALUES ("%s","%s");' % (projectid,i))
            return jsonify('success')
    return redirect('/')