import zipfile, os, base64
from werkzeug.utils import secure_filename
from .conndb import condb
from .sshsftp import comupload

'''
基本格式：zipfile.ZipFile(filename[,mode[,compression[,allowZip64]]])
mode：可选 r,w,a 代表不同的打开文件的方式；r 只读；w 重写；a 添加
compression：指出这个 zipfile 用什么压缩方法，默认是 ZIP_STORED，另一种选择是 ZIP_DEFLATED；
allowZip64：bool型变量，当设置为True时可以创建大于 2G 的 zip 文件，默认值 True；

'''


def unzip(path, folder_abs):
    zip_file = zipfile.ZipFile(path)
    zip_list = zip_file.namelist()  # 得到压缩包里所有文件

    for f in zip_list:
        zip_file.extract(f, folder_abs)  # 循环解压文件到指定目录
    zip_file.close()  # 关闭文件，必须有，释放内存
    os.remove(path)


def savefile(f, savepath):
    basepath = os.path.dirname(os.path.dirname(__file__))
    upload_path = os.path.join(basepath, savepath, secure_filename(f.filename))
    f.save(upload_path)
    unzip(upload_path, savepath)


# TODO: 图片压缩
def saveimage(f, savepath, filename, username):
    basepath = os.path.dirname(os.path.dirname(__file__))
    upload_path = os.path.join(basepath, savepath, filename)
    f.save(upload_path)
    upimage = comupload('45.77.212.133')
    upimage.upload(upload_path, '/var/www/html/images/' + filename)
    upimage.sshclose()
    condb('UPDATE `splock` SET `lock` = NULL WHERE `function` = "gamelist"')


def saveadvert(f, savepath):
    basepath = os.path.dirname(os.path.dirname(__file__))
    upload_path = os.path.join(basepath, savepath, secure_filename(f.filename))
    os.system('if [[ ! -d {} ]]; then mkdir {};fi'.format(savepath, savepath))
    f.save(upload_path)
    os.system('cd {} && mkdir {}'.format(savepath, f.filename.split('.')[0]))
    unzip(upload_path, savepath + '/' + f.filename.split('.')[0])


def imagetobase(f, username, imagepath):
    suffix = ["png", "jpg", "jpeg"]
    savefile(f, imagepath)
    logFiles = os.listdir(imagepath)
    # 在/root/images内遍历文件
    for filename in logFiles:
        filepath = imagepath + '/' + filename
        bool_file = filename.endswith(tuple(suffix))
        if bool_file:
            with open(filepath, 'rb') as f:
                image_base64 = str(base64.b64encode(f.read()), encoding='utf-8')
                condb(
                    'INSERT INTO `imagecover` (cover,username,ctime) VALUES ("%s","%s",NOW());'
                    % (image_base64, username)
                )
        else:
            print('文件格式不在{}列表中：{}'.format(suffix, filename))
    os.system('rm -fr {}/*'.format(imagepath))
