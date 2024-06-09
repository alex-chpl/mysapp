from datetime import datetime
from datetime import date
from decimal import Decimal
from pony.orm import *

db = Database('sqlite','pony_test.db',create_db=True)

class Role(db.Entity):
	name = Required(str, unique=True)
	data = Optional(str)
	User = Set('User')

class Iface(db.Entity):
	ifname = Required(str, unique=True)
	ifcontent = Required(str)
	User = Set('User')

class Unispr(db.Entity):
	chmode = Required(str)
	code = Required(str)
	value = Required(str)
	note = Required(str)
	composite_key(chmode,code)


class User(db.Entity):
	login = Required(str, unique=True)
	name = Required(str)
	passwd = Required(str)
	role = Required(Role)
	iface = Required(Iface)

class Ware(db.Entity):
	wareid = PrimaryKey(int, auto=True)
	parentid = Required(str)
	code = Required(str, unique=True)
	name = Required(str)
	art = Optional(str)
	producer = Optional(str)
	country = Optional(str)
	upak = Optional(str)
	barcode = Optional(str)
	composite_index(parentid,code)

class Groups(db.Entity):
	gid = PrimaryKey(str)
	gparent = Required(str)
	name = Required(str)
	descr = Optional(str)

class Rest(db.Entity):
	period = Required(date)
	org = Required(str)
	stock = Required(str)
	ware = Required(str)
	rest = Required(Decimal)
	totsum = Required(Decimal)
	composite_index(period,org,stock,ware)

class Price(db.Entity):
	ware = Required(str)
	tipprc = Required(int)
	price = Required(Decimal)
	disc = Optional(Decimal)
	composite_key(ware,tipprc)

class PriceHist(db.Entity):
	dt = Required(datetime)
	ware = Required(str)
	tipprc = Required(int)
	price = Required(Decimal, 12, 2)

class Docum(db.Entity):
	items = Set('DocumItems')
	tip = Required(str)
	nomer = Required(str)
	rdate = Required(datetime)
	user = Required(int)
	deban = Required(int)
	gdeban = Required(int)
	kredan = Required(int)
	gkredan = Required(int)
	summa1 = Required(Decimal)
	summa2 = Required(Decimal)
	summa3 = Required(Decimal)
	parent = Required(int)
	status = Required(int)
	comment = Optional(str)
	composite_key(tip,nomer,rdate)

class DocumItems(db.Entity):
	pcode = Optional(Docum)
	num = Required(int)
	ware = Required(str)
	kolvo = Required(int)
	price = Required(Decimal)
	summa1 = Required(Decimal)
	summa2 = Required(Decimal)
	summa3 = Required(Decimal)

class Country(db.Entity):
	cid = PrimaryKey(int)
	name = Required(str)
	full_name = Optional(str)
	num_code = Required(str,unique=True)
	alfa2 = Required(str)
	alfa3 = Required(str)


sql_debug(False)

db.generate_mapping(create_tables=True)

@db_session
def init_db_data():
	r1 = Role(name='admin', data='Data admin')
	r2 = Role(name='seller',data='Data seller')
	r3 = Role(name='manager', data='Data manager')

	i1 = Iface(ifname='admin',ifcontent='admin')
	#uadm = User(login='admin',name='Администратор',passwd='111',role=r1.id,iface=i1.id)
	return (r1,i1)


if __name__ == '__main__':
	r1,i1 = init_db_data()
	with db_session():
	  User(login='admin',name='Администратор',passwd='111',role=r1.id,iface=i1.id)
	pass
	
