#!/usr/bin/env python3
'''
Small wsgiref based web server. Takes a path to serve from and an
optional port number (defaults to 8000), then tries to serve files.
Mime types are guessed from the file names, 404 errors are raised
if the file is not found. Used for the make serve target in Doc.
'''
import sys
import os
import re,random
import mimetypes
from wsgiref import simple_server, util
from string import Template
from config import Config
import urllib.request,urllib.parse


conf = Config()
session = {}

def get_param(env):
    if env['REQUEST_METHOD'] == 'POST':
        try:
            request_body_size = int(env['CONTENT_LENGTH'])
            request_body = env['wsgi.input'].read(request_body_size)
        except (TypeError, ValueError):
            request_body = '' #[]
        else:
            post_values = urllib.parse.parse_qs(request_body.decode('utf-8'))
    ret = {}
    for k in post_values:
        v = post_values[k]
        ret[k] = v[0] if type(v) == type([]) else v
    return ret
    	

def get_template(tpl,tpldir='templates'):
	try:
		with open(os.path.join(tpldir,tpl),'r') as tplfile:
			return Template(tplfile.read())
	except IOError:
		return Template('<h1>Страница не найдена!</h1>')


def index(environ,resp):
    rand = random.randint(100000,1000000)
    template = get_template('login.html')
    resp('200 OK',[('Content-Type','text/html; charset="utf-8"')])
    return [template.substitute({'comments': '<h2>'+str(rand) + \
    '</h2><h1>Test</h1>','saved': '<div>добавлен</div>' ,'error':''}) \
     .encode('utf-8')]
    pass

def validate(user,password):
	return (user=='admin') and (password=='111')

def login(environ,resp):
	param = get_param(environ)
	user = param.get('user')
	password = param.get('password')
	if validate(user,password):
		sid = random.randint(100000,999999)
		session[sid] = {}
		session[sid]['user'] = user
		resp('200 OK',[('Set-Cookie','_sid_=%d' % (sid)),('Content-Type','text/html')])
	return [('Login %s , %s' % (param.get('user'), \
	 param.get('password'))).encode('utf-8')]

def getenv(environ,resp):
	tx=''
	for k in environ.keys():
		tx += '%s = %s\n' % (k,environ[k])
	resp('200 OK', [('Content-Type', 'text/plain'),('Token','Test')])
	return [tx.encode('utf-8')]

# Map
urls = [
    (r'^$', index),
	(r'login$', login),
	(r'env$', getenv),
]

def app(environ, respond):

    pth = environ.get('PATH_INFO', '').lstrip('/')
    for regex, callback in urls:
        match = re.search(regex, pth)
        if match is not None:
            environ['url_args'] = match.groups()
            return callback(environ, respond)
    fn = os.path.join(path, environ['PATH_INFO'][1:])
    if '.' not in fn.split(os.path.sep)[-1]:
        fn = os.path.join(fn, 'index.html')
    type = mimetypes.guess_type(fn)[0]

    if os.path.exists(fn):
        respond('200 OK', [('Content-Type', type)])
        return util.FileWrapper(open(fn, "rb"))
    else:
        respond('404 Not Found', [('Content-Type', 'text/plain')])
        return [b'not found']

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    httpd = simple_server.make_server('', port, app)
    print("Serving {} on port {}, control-C to stop".format(path, port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
        httpd.server_close()
