from flask import Blueprint
from flask import render_template
from flask import request, session, jsonify, redirect
from function.conndb import condb
from function.sshsftp import comupload
import time, os

blue_image = Blueprint('blue_image', __name__, url_prefix='/image')


@blue_image.route('/', methods=['POST', 'GET'])
def image():
    author = session.get('author')
    if author.get('manager') or author.get('image'):
        if request.method == 'POST':
            resimage, resimageall = condb('SELECT * FROM `image` ORDER BY id DESC')
            return jsonify(resimageall)
        return render_template('image.html')
    return redirect('/')


@blue_image.route('/upload', methods=['POST', 'GET'])
def imageupload():
    author = session.get('author')
    username = session.get('user_info')
    if author.get('manager') or author.get('image'):
        if request.method == 'POST':
            f = request.files['file']
            imagename = str(int(time.time())) + '.' + f.filename.split('.')[1]
            fname = f.filename.split('.')[0]
            urlimage = 'https://img.wakastar.com/{}'.format(imagename)
            upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'images', imagename)
            f.save(upload_path)
            sshimage = comupload('144.202.73.225')
            sshimage.upload(upload_path, '/var/www/html/images/' + imagename)
            sshimage.sshclose()
            condb(
                'INSERT INTO `image` (`username`,`imagename`,`url`,`ctime`,`status`) VALUES ("%s","%s","%s",NOW(),1);' % (
                username, fname, urlimage))
            return jsonify('success')
    return redirect('/')
