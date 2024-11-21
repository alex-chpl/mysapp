#!/usr/bin/env python3
# coding=utf-8
import os
#import sqlite3
from string import Template
import urllib.request,urllib.parse
import json
from wsgiref.simple_server import make_server
import sys
import re,random
from models import *
import settings
from datetime import date
from functools import reduce

mainmenu = '''
    <ul class="nav navbar-nav">
      <li class="nav-item active">
        <a class="nav-link" href="#">Главная</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="#">Журнал</a>
      </li>
      <li class="nav-item">
          <a class="nav-link" href="#">Каталог</a>
      </li>
      <li class="nav-item">
        <a class="nav-link disabled" href="#">О фирме</a>
      </li>
    </ul>
'''

class RemServer(object):
	def __init__(self,param):
		self.url = param['url']

	def query(self,sql):
		res = urllib.request.urlopen(self.url+'?'+urllib.parse.urlencode({'op':'query','sql':sql,'type':'text'})).read().decode('utf8').split('\n')
		self.names = res[0].split(';')
		self.result = [e.split(';') for e in res[1:] if e != '']
		return (self.names,self.result)
	def get(self,filename):
		res = urllib.request.urlopen(self.url+'?'+urllib.parse.urlencode({'op':'get','sql':filename})).read().decode('utf8')
		return res

	def getinfo(self,filename):
		res = urllib.request.urlopen(self.url+'?'+urllib.parse.urlencode({'op':'getinfo','sql':filename})).read().decode('cp1251')[:-2]
		ar=[e.strip() for e in res.split(';')]
		return {'size':int(ar[0]),'mtime':datetime.fromisoformat(ar[1])}

	def doclist(self,datebeg,dateend,docdef='0',closed=1):
		sql = "select iddoc,iddocdef,docno,date_time_iddoc from skl1.._1sjourn where date_time_iddoc between '%s' and '%s' and closed = %d " % (datebeg,dateend,closed)
		sql += ( "and iddocdef = '%s' " % (docdef)) if docdef != '0' else '' 
		#print( sql)
		return self.query(sql)

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
        '.HTML':'text/html; charset="utf-8"',
        }

remsql={'rest':"select wcode=t.code,rest=sum(r.sp411) from magsql..rg405 r \
inner join  magsql..sc84 t on t.id=r.sp408 inner join magsql..sc55 s on s.id=r.sp418 \
where s.code='%(sklad)s' and r.period='%(period)s' group by t.code,t.descr having sum(r.sp411)>0",
'wares':"select wcode=t.code,name=t.descr,art=t.sp85,ean13=g.sp80 \
from  magsql..sc84 t left join magsql..sc75 g on g.id=t.sp86 \
where t.id in (select sp408 from rg405 \
inner join magsql..sc55 s  on s.id = sp418 and s.code='%(sklad)s' \
where period = '%(period)s' group by sp408 having sum(sp411) > 0)",
'ware':"select parent=t.parentid,wcode=t.code,name=t.descr,art=t.sp85,ean=isnull(g.sp80,'') from magsql..sc84 t \
left join magsql..sc75 g on g.id = t.sp86 where t.code in (%(wlist)s)",



}

cnt=0
tpldir = 'templates'
urlsrv="http://91.240.208.99:8080/cgi-bin/test1.py"
rand=123
session = {}
user='*'
opt = settings.Settings()
rq = RemServer({'url':urlsrv})

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

def rquery(param):
    res = urllib.request.urlopen('https://divo-m.ru/uds/mag.php?'+param).read()
    return res
    pass

def remquery(environ,resp):
    import urllib.request
    if environ['REQUEST_METHOD'] == 'GET':
        param = environ.get('QUERY_STRING')
        url=urlsrv+'?'+param
        f = urllib.request.urlopen(url)
        res = f.read()
        resp('200 OK',[('Content-Type','text/plain; charset="utf-8"')])
    return [res]
    pass

def from_json(tx):
    return json.loads(tx)

def not_found(environ, start_response):
    start_response('404 NOT FOUND', [('Content-Type', 'text/html')])
    return [getmeta(),'<h1>Страница не найдена</h1>'.encode('utf-8')]


def template_not_found(environ, start_response):
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Template not Found'.encode('utf-8')]

def get_template(tpl):
	try:
		with open(os.path.join(tpldir,tpl),'r') as tplfile:
			return Template(tplfile.read())
	except IOError:
		return Template('<h1>Страница не найдена!</h1>')

def validate_token(tok):
    return 'user' in session.keys()

def make_menu (mitems):
    #return  reduce(lambda s,el: s + f'<li class="nav-item"><a data-name="{el["name"]}" class="nav-link" href="#">{el["descr"]}</a></li>' + "\n",mitems,f'<ul class="nav navbar-nav">') + "</ul>"
    tx = '<ul class="nav navbar-nav">'
    for el in mitems:
        if 'href' in el:
            dhref = f'data-href="{el["href"]}"'
        else:
            dhref = ''

        tx += f'<li class="nav-item"><a {dhref} data-name="{el["name"]}" class="nav-link" href="#">{el["descr"]}</a></li>'
    return tx + '</ul>'

@db_session
def validate_user(user,passwd):
  u = select(e for e in User if e.login == user and e.passwd == passwd)
  if u:
    session['user']=list(u)
    u1 = list(u)[0]
    mainmenu = make_menu(json.loads(u1.iface.ifcontent)['menu'])
    return True
  else:
    return False

def _redirect(resp,url):
	resp('302 OK',[('Location',url)])


# todo list
@db_session
def index(environ, start_response, saved=False,user=''):
    mainmenu = make_menu([{'name':'main','descr':'Главная'}, \
    {'name':'journ','descr':'Журнал'},{'name':'ware','descr':'Каталог'}, \
    {'name':'about','descr':'О Фирме'}])
    username = ''
    if validate_token(environ.get('HTTP_TOKEN','')):
      mainmenu = make_menu(json.loads(session['user'][0].iface.ifcontent)['menu'])
      username = session['user'][0].name
      template = get_template('index.html')
    else:
      template = get_template('login.html')

    start_response('200 OK', [('Content-Type', 'text/html')])
    return [template.substitute({'mainmenu':mainmenu,'username':username,'error':user}).encode('utf-8')]
    
def logout(env,resp):
	session.pop('user')
	#env['PATH_INFO']='/'
	#_redirect(resp,'/')
	return index(env,resp)

def api(environ,resp):
	if environ['REQUEST_METHOD'] == 'POST':
		try:
			rb_size = int(environ['CONTENT_LENGTH'])
			rb = environ['wsgi.input'].read(rb_size).split('\n')
		except (TypeError, ValueError):
			rb = []
		else:
			par_value = dict(item.split('=') for item in rb)
	else:
		try:  #QUERY_STRING parse for parameters
			pass
		except (TypeError, ValueError):
			par_value={}
		
# got par_value and parse it
	pass

# Add comment
def comment(environ, start_response):
    if environ['REQUEST_METHOD'] == 'POST':
        try:
            request_body_size = int(environ['CONTENT_LENGTH'])
            request_body = environ['wsgi.input'].read(request_body_size).split('\n')
            print(request_body)
        except (TypeError, ValueError):
            request_body = []
        else:
            post_values = dict(item.split('=') for item in request_body)
            post_values['comment'] = urllib.unquote_plus(post_values['comment'])
        return index(environ, start_response, saved=True)
    else:
        try:
            with open('templates/comment.html') as template_file:
                template = Template(template_file.read())
        except IOError:
            return template_not_found(environ, start_response)

        start_response('200 OK', [('Content-Type', 'text/html')])
        return [template.substitute({}).encode('utf-8')]


# Delete comment
def delete_c(environ, start_response):
    args = environ['url_args']
    if args:
        print (args[0])
        #CONNECTION.cursor().execute('''
        #    DELETE FROM todo WHERE id=%s;
        #''' % args[0])
        #CONNECTION.commit()
    return index(environ, start_response)

def count_c(environ, start_response):
    global cnt
    cnt += 1
    #tpl = Template("Counter: %d")
    par = urllib.parse.parse_qs(environ['QUERY_STRING'])
    start_response('200 OK', [('Content-Type', 'text/html')])
    tx= getmeta()+( "<h1>Счетчик</h1>Counter: %d" % cnt + '<br>'+environ.get('DOCUMENT_ROOT','') +'<br>'+par.get('sql')[0]).encode('utf-8')
    
    return [tx]

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

def login(environ, start_response):
    import urllib.parse
    if environ['REQUEST_METHOD'] == 'POST':
        user='**'
        try:
            request_body_size = int(environ['CONTENT_LENGTH'])
            request_body = environ['wsgi.input'].read(request_body_size)
        except (TypeError, ValueError):
            request_body = '' #[]
        else:
            post_values = urllib.parse.parse_qs(request_body.decode('utf-8'))
            user =  post_values.get('user',[''])[0]
            passwd =  post_values.get('password',[''])[0]
            if validate_user(user, passwd):
              data = ''
            else:
              data = 'Ошибка входа!'
        return index(environ, start_response, saved=False,user=data)

def getenv(environ,resp):
	tx=''
	for k in environ.keys():
		tx += '%s = %s\n' % (k,environ[k])
	resp('200 OK', [('Content-Type', 'text/plain'),('Token','Test')])
	return [tx.encode('utf-8')]


def upload(environ,start_response):
    import multipart
    fields = {}
    files = {}
    def on_field(field):
        fields[field.field_name] = field.value
    def on_file(file):
        files[file.field_name] = {'name': file.file_name, 'file_object': file.file_object}

    multipart_headers = {'Content-Type': environ['CONTENT_TYPE']}
    multipart_headers['Content-Length'] = environ['CONTENT_LENGTH']
    multipart.parse_form(multipart_headers, environ['wsgi.input'], on_field, on_file)
    for each_file, each_file_details in files.items():
        with open(each_file_details['name'], 'wb') as f:
            uploaded_file = each_file_details['file_object']
            uploaded_file.seek(0)
            f.write(uploaded_file.read())
    content = "Hello world"
    content = [content.encode('utf-8')]
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    start_response(status, headers)
    return content
	
def init_data(firm,skl,dt):
	nm,rs = rq.query(remsql['rest'] % ({'sklad':skl,'period':format(dt,'%Y%m%d')}))
	with db_session():
		delete(e for e in Rest)
		commit()
		for row in rs:
			rdt = dict(zip(nm,row))
			Rest(period=dt, org=firm, stock=skl, ware=rdt['wcode'],rest=Decimal(rdt['rest']),totsum=Decimal('0.0'))
	with db_session():
		delete(e for e in Ware)
		commit()
		rt = select(e for e in Rest)[:]
		for rw in rt:
			sql=remsql['ware'] % {'wlist': "'%s'" % rw.ware}
			#print(sql)
			wn,ws = rq.query(sql)
			if len(ws)>0:
				wdt = dict(zip(wn,ws[0]))
				Ware(parentid=wdt['parent'],code=rw.ware,name=wdt['name'],art=wdt['art'],barcode=wdt['ean'])

	

# Map
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
    (r'^(js|css|img|templates)/(.+)$', get_static),
]


def application(environ, start_response):
    path = environ.get('PATH_INFO', '').lstrip('/')
    for regex, callback in urls:
        match = re.search(regex, path)
        if match is not None:
            environ['url_args'] = match.groups()
            return callback(environ, start_response)
    return not_found(environ, start_response)


if __name__ == '__main__':
    port = 8081
    srv = make_server('0.0.0.0', port, application)
    print(f"Serving HTTP on port {port}")
    sys.exit(srv.serve_forever())
