#!/usr/bin/env python3
'''
Small wsgiref based web server. Takes a path to serve from and an
optional port number (defaults to 8000), then tries to serve files.
Mime types are guessed from the file names, 404 errors are raised
if the file is not found. Used for the make serve target in Doc.
'''
import sys
import os
import re
import mimetypes
from wsgiref import simple_server, util
import urllib.request, urllib.parse
from http import cookies

MIME = {
        '.CSS':'text/css',
        '.JS':'application/javascript',
        '.GIF':'image/gif',
        '.JPG':'image/jpeg',
        '.JPEG':'image/jpeg',
        '.JRE':'image/jpeg',
        '.PNG':'image/png',
        '.TIF':'image/tiff',
        '.TIFF':'image/tiff',
        }


def getmeta():
    return ('''
            <!doctype html>
            <html lang="ru">
            <head>
            <meta charset="UTF-8" />
            <title>HTML Test</title>
            <style>
             h1 {color:blue;}
             </style>
            </head>'''.encode('utf-8'))
            
def show_cookie(c): 
	out=[] 
	out.append(c) 
	for key, morsel in c.items(): 
		out.append(('key = '+morsel.key+':'+morsel.value+'\n').encode('utf-8'))
		for name in morsel.keys(): 
			if morsel[name]: 
				out.append(('  {} = {}'.format(name, morsel[name])).encode('utf-8')) 
	return out
            


def get_params(env):
	post_values={}
	if env['REQUEST_METHOD'] == 'POST':
		try:
			request_body_size = int(env['CONTENT_LENGTH'])
			request_body = env['wsgi.input'].read(request_body_size)
		except (TypeError, ValueError):
			request_body = '' #[]
		else:
			post_values = urllib.parse.parse_qs(request_body.decode('utf-8'))

	elif env['REQUEST_METHOD'] == 'GET':
		post_values = urllib.parse.parse_qs(env['QUERY_STRING'])
	ret = {}
	for k in post_values:
		v = post_values[k]
		ret[k] = v[0] if type(v) == type([]) else v
	return ret


def index(env,resp):
	param = get_params(env)
	cuk = cookies.SimpleCookie(env['HTTP_COOKIE'])
	out = []
	for k in param.keys():
		out.append((k+'='+param[k]+'\n').encode('utf-8'))
	out.append('Привет, Мир!'.encode('utf-8'))
	#for k,m in cuk.items():
	#	out.append(('\n'+str(m.key+' : '+m.value)).encode())
	#out.append(('...'+(cuk.get('_sid1_').value if '_sid1_' in cuk else '?')+':::').encode())
	resp('200 OK',[('Content-type','text/plain; charset="utf-8"')])
	return out

def not_found(environ, start_response):
    start_response('404 NOT FOUND', [('Content-Type', 'text/html')])
    return [getmeta(),'<h1>Страница не найдена</h1>'.encode('utf-8')]

def getenv(environ,resp):
	tx=''
	for k in environ.keys():
		tx += '%s = %s\n' % (k,environ[k])
	resp('200 OK', [('Content-Type', 'text/plain'),('Token','Test')])
	return [tx.encode('utf-8')]


def get_static(environ, resp):
    fpath,fname = environ['url_args']
    fullname = os.path.join(environ.get('PWD'),fpath,fname)
    fbody,fext = os.path.splitext(fname)
    conttype = MIME.get(fext.upper(),'text/plain')
    if os.path.exists(fullname):
        f = open(fullname,'rb')
        fsize = os.path.getsize(fullname)
        fcontent = f.read()
        f.close()
        resp('200 OK',[('Content-Type',conttype),('Content-Length',str(fsize))])
        return [fcontent]
    else:
        resp('404 NOT FOUND',[('Content-Type','text/plain')])
        return ['Не найден файл %s' % fname]


urls = [
	(r'^$',index),
	(r'^index$',index),
	(r'env$', getenv),	
    (r'^(js|css|img)/(.+)$', get_static),	
	]

# Map
'''
urls = [
    (r'^$', index),
    (r'add/?$', comment),
    (r'delete/(.+)$', delete_c),
	(r'login$', login),
	(r'logout$', logout),
	(r'env$', getenv),
	(r'upload$', upload),
	(r'api$', api),
	(r'rqu$', remquery),
    (r'cnt$', count_c),
    (r'^(js|css|img)/(.+)$', get_static),
]
'''

def application(environ, start_response):
    path = environ.get('PATH_INFO', '').lstrip('/')
    for regex, callback in urls:
        match = re.search(regex, path)
        if match is not None:
            environ['url_args'] = match.groups()
            return callback(environ, start_response)
    return not_found(environ, start_response)

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    httpd = simple_server.make_server('', port, application)
    print("Serving {} on port {}, control-C to stop".format(path, port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
        httpd.server_close()
