from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime







def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("giris"))

    return decorated_function
    
#Kullanıcı kayıt formu
class RegisterForm(Form):
	name=StringField("İsim",validators=[validators.Length(min=4,max=10)])
	UserName=StringField("Kullanıcı adı",validators=[validators.Length(min=4,max=10)])
	email=StringField("Email",validators=[validators.Email(message="Mail şart")])
	password=PasswordField("Parola",validators=[validators.DataRequired(message="Parola Şart"),validators.EqualTo(fieldname="confirm",message="Parolalar aynı değil")])
	confirm=PasswordField("Parola tekrar")

class LoginForm(Form):
	username=StringField("Kullanıcı Adı")
	password=PasswordField("Şifre")

class ArticleForm(Form):
	title=StringField("Makale Başlığı",validators=[validators.Length(min=4,max=10)])
	content=TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])

	






app = Flask(__name__)
print(app)
app.secret_key="ybblog"

app.config["MYSQL_HOST"]="127.0.0.1"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="ybblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"


mysql=MySQL(app)




@app.route("/")
def anasayfa():
	return render_template("index.html")






@app.route("/about")
def hakkında():
	return render_template("about.html")


#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):

	print(id)
	cursor = mysql.connection.cursor()
	sorgu = "Select * from articles where author = %s and id = %s"
	result = cursor.execute(sorgu,(session["username"],id))
	if result > 0:
		sorgu2 = "Delete from articles where id = %s"

		cursor.execute(sorgu2,(id,))
		mysql.connection.commit()

		return redirect(url_for("kontrolPaneli"))
	else:
		flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
		return redirect(url_for("anasayfa"))


#Makale güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def guncelle(id):
	if request.method=="GET":
		cursor=mysql.connection.cursor()
		sorgu="SELECT * FROM articles WHERE author=%s and id=%s"
		sonuc=cursor.execute(sorgu,(session["username"],id))
		if sonuc==0:
			flash("Bu işlem için yetkiniz yok veya böyle bir makale bulunmuyor...")
			return redirect(url_for("anasayfa"))
		else:
			article = cursor.fetchone()
			form=ArticleForm()
			form.title.data=article["title"]
			form.content.data=article["content"]
			return render_template("update.html",form=form)

	else:
		now = datetime.now()

		form =ArticleForm(request.form)
		yeniBaslik=form.title.data
		yeniIcerik=form.content.data
		sorgu2="UPDATE articles SET title=%s , content=%s,created_date=%s WHERE id=%s"
		cursor=mysql.connection.cursor()
		cursor.execute(sorgu2,(yeniBaslik,yeniIcerik,now.strftime("%d/%m/%Y, %H:%M:%S"),id))
		mysql.connection.commit()
		flash("Tebrikler! Makale başarıyla güncellendi","success")
		return redirect(url_for("kontrolPaneli"))

		


	








	








@app.route("/articles/<string:id>")
def detail(id):
	return "Article id:" + id



@app.route("/login",methods=["GET","POST"])
def giris():
##LOGIN FORM

	form=LoginForm(request.form)
	if request.method=="POST" and form.validate():
		username=form.username.data
		girilenPass= form.password.data

		cursor=mysql.connection.cursor()
		sorgu="SELECT * FROM User where Username=%s"
		sonuc = cursor.execute(sorgu,(username,))
	
		if sonuc > 0:
			data=cursor.fetchone()
			real_pass=data["password"]
			if sha256_crypt.verify(girilenPass,real_pass):
				flash("Başarıyla giriş yaptınız","success")



				session["logged_in"]=True
				session["username"]=username
				return redirect(url_for("anasayfa"))
				

			else:
				flash("Şifre hatalı")
				return redirect(url_for("giris"))

		else:
			flash("Kullanıcı bulunamadı",category="danger")
			return redirect(url_for("giris"))

	else:
		return render_template("login.html",form = form )









@app.route("/register",methods=["GET","POST"])
def kayitSayfasi():

##REGISTER FORM
	form=RegisterForm(request.form)

	if request.method=="POST" and form.validate():
		name=form.name.data
		Username=form.UserName.data
		email=form.email.data
		password= sha256_crypt.encrypt(form.password.data)
        
		cursor=mysql.connection.cursor()
		sorgu="""INSERT INTO User(name,Username,email,password) VALUES(%s,%s,%s,%s)"""
		cursor.execute(sorgu,(name,Username,email,password))
		mysql.connection.commit()
		cursor.close()
		flash("Kayıt oluşturuldu",category="success")
		return redirect(url_for("giris"))
	else:
		return render_template("register.html",form=form)


@app.route("/deneme")
def deneme():
	return render_template("deneme.html")

@app.route("/logout")
def cikis():
	session.clear()
	return redirect(url_for("anasayfa"))





@app.route("/dashboard")
@login_required
def kontrolPaneli():
	cursor=mysql.connection.cursor()

	sorgu="SELECT * FROM articles where author = %s"
    
	sonuc = cursor.execute(sorgu,(session["username"],))

	if sonuc>0:
		articles = cursor.fetchall()
		return render_template("dashboard.html",articles=articles)
	else:
		return render_template("dashboard.html")






	
@app.route("/addarticle",methods=["GET","POST"])
##Article form
def makaleEkle():
	form = ArticleForm(request.form)
	if request.method=="POST" and form.validate:
		title=form.title.data
		content=form.content.data
		cursor=mysql.connection.cursor()
		now = datetime.now()

  
		sorgu="""INSERT INTO articles(title,content,author,created_date) VALUES(%s,%s,%s,%s)"""
		cursor.execute(sorgu,(title,content,session["username"],now.strftime("%d/%m/%Y, %H:%M:%S")))
		mysql.connection.commit()
		cursor.close()
		flash("Tebrikler makaleniz başarıyla eklendi","success")
		return redirect(url_for("anasayfa"))
	else:

		return render_template("addarticle.html",form = form)


@app.route("/articles")
def makaleler():
	cursor=mysql.connection.cursor()
	sorgu="SELECT * FROM articles"
	sonuc=cursor.execute(sorgu)
	if sonuc > 0:
		articles=cursor.fetchall()

		return render_template("articles.html",articles=articles)
	else:
		return render_template("articles.html")


##Detay sayfası
@app.route("/article/<string:id>")
def detaySayfasi(id):
	cursor=mysql.connection.cursor()
	sorgu="SELECT * FROM articles where id = %s"
	sonuc=cursor.execute(sorgu,(id,))
	if sonuc > 0:
		article=cursor.fetchone()
		return render_template("detay.html", article=article)
	else:
		return render_template("detay.html")

##arama url
@app.route("/search",methods=["GET","POST"])
def search():
	if request.method=="GET":
		return redirect(url_for("anasayfa"))
	else:
		keyword=request.form.get("keyword")
		cursor=mysql.connection.cursor()
		sorgu3="SELECT * FROM articles WHERE title LIKE '%" + keyword + "%'"
		print(sorgu3)
		sonuc=cursor.execute(sorgu3)
		if sonuc == 0:
			flash("Aranan kriterlere uygun makale bulunamadı!","warning")
			return redirect(url_for("makaleler"))
		else:
			articles=cursor.fetchall()
			return render_template("articles.html",articles=articles)






if __name__ == "__main__":
	app.run(debug=True)