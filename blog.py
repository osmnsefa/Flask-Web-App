from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps



# Kullanıcı Giriş Decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapınız...","danger")
            return redirect(url_for("login"))
    return decorated_function
# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField('İsim Soyisim', validators=[validators.Length(min=4,max=25)])
    username = StringField('Kullanıcı Adı', validators=[validators.Length(min=5,max=35)])
    email = StringField('Email Adresi', validators=[validators.Email(message="Lütfen geçerli bir email adresi giriniz...")])
    password= PasswordField('Parola:', validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin..."),
        validators.EqualTo('confirm', message='Şifreler uyuşmuyor!')
    ])
    confirm= PasswordField('Parola Doğrula')    
#Login Formu
class LoginForm(Form):
        username=StringField("Kullanıcı Adı")
        password=PasswordField("Parola:")
app=Flask(__name__)
app.secret_key="blog" #flash mesajında hata oluşmaması için yaptık.

app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]="osc1453sql"
app.config["MYSQL_DB"]="blog"
app.config["MYSQL_cursorclass"]="DictCursor" #aldığımız verileri sözlük yapısı haline getirir.
mysql=MySQL(app)

@app.route('/')
def index():
    
    return render_template("index.html")
@app.route("/about")
def about():
    
    return render_template("about.html")
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    
    sorgu="Select * from articles where author= %s"
    
    result =cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        articles=cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else :
        return render_template("dashboard.html")
    
    return render_template("dashboard.html")
@app.route("/articles/<string:id>")
def detail(id):
    
    return "Article Id:" + id
#Kayıt Olma
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
                                    #eğer form.validate true dönerse biz işleme devam edeceğiz.
    if request.method == "POST" and form.validate():#sayfayı yenilediğimizde get request olur,submit yaptığımızda post request olur.
        
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)#parolayı şifrelemek için sha256 kullandık.
        
        cursor=mysql.connection.cursor()
        sorgu="Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))#demet içinde yazdığımız değişkenler %s yerine geçer.
        mysql.connection.commit()#eğer veri tabanında değişiklik yapıyorsak commit yapmak zorundayız.
        
        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))#redirect fonksiyonu bizi istediğimiz url adresine götürür.
    else:
        return render_template("register.html",form=form)
@app.route("/login",methods=["GET","POST"])
def login():
    form= LoginForm(request.form)
    if request.method == "POST":
        username=form.username.data
        password_entered=form.password.data
        
        cursor=mysql.connection.cursor()
        
        sorgu= "Select * From users where username= %s"
        
        result= cursor.execute(sorgu,(username,))#eğer kullanıcı yoksa 0 döner varsa 0'dan büyük bir sayı döner.
        if  result > 0:
            data = cursor.fetchone() #kullanıcının tüm bilgilerini getirdik ve sözlük şeklinde.
            real_password=data[4]
            if sha256_crypt.verify(password_entered,real_password):# girilen parolayla gerçek parolayı karşılaştırdık.
                flash("Başarıyla Giriş Yaptınız...","success")
                
                session["logged_in"]= True #giriş yaptığımızda session başlar.
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz","danger")
                return redirect(url_for("login"))
            
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))#redirect fonksiyonu bizi istediğimiz url adresine götürür.
            
            
    return render_template("login.html",form=form) 
#Logout İşlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    
    sorgu="select * from articles where id=%s"
    
    result=cursor.execute(sorgu,(id,))#demetin içinde bir eleman varsa yanına virgül koy.
    
    if result >0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")
    #Makale Ekleme
@app.route("/addarticle",methods=["GET","POST"])
def addarticle():
    form=ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title=form.title.data
        content=form.content.data
    
        cursor=mysql.connection.cursor()
        
        sorgu="insert into articles(title,author,content) Values(%s,%s,%s)"
        
        cursor.execute(sorgu,(title,session["username"],content)) 
        
        mysql.connection.commit()
        
        cursor.close()
        
        flash("Makale Başarıyla Eklendi","success")
        
        return redirect(url_for("dashboard"))
    
    return render_template("addarticle.html",form=form)
#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    
    sorgu ="select * from articles where author=%s and id=%s"
    result=cursor.execute(sorgu,(session["username"],id))
    
    if result >0:
        sorgu2="delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        
        mysql.connection.commit()
        
        return redirect(url_for("dashboard"))
    else: 
        flash("Böyle bir makale yok veya böyle bir işleme yetkiniz yok.","danger")
        return redirect(url_for("index"))
    
#Makale Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor=mysql.connection.cursor()
        
        sorgu="select * from articles where id=%s and author=%s"
        
        result=cursor.execute(sorgu,(id,session["username"]))
        
        if result==0:
            flash("Böyle bir makale yok veya böyle bir işleme yetkiniz yok.","danger")
            return redirect(url_for("index"))
        else:
            article=cursor.fetchone()
            form=ArticleForm()
            
            form.title.data=article[1]
            form.content.data=article[3]
            return render_template("update.html",form=form)
                              
    else: 
        #Post Request
        form=ArticleForm(request.form)
        
        newTitle =form.title.data
        newContent=form.content.data
        
        sorgu2="Update articles set title=%s,content=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))
        
class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content=TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])
# Makale Sayfası
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    
    sorgu="select * from articles"
    
    result=cursor.execute(sorgu)
    
    if result > 0:
        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)
    else :
        return render_template("articles.html")
#Arama URL
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET": #Eğer adres çubuğuna search yazılırsa diye kontrolü yaptık.
        return redirect(url_for("index"))
    else: 
        keyword=request.form.get("keyword") #article.html sayfasındaki name kısmına keyword dedik ve burada onu aldık.

        cursor=mysql.connection.cursor()
        
        sorgu="select * from articles where title like '%" + keyword + "%' " #içinde keyword bulunan title'ları listeler.
        
        result=cursor.execute(sorgu)
        
        if result==0:
            flash("Aranan kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles= cursor.fetchall()
            
            return render_template("articles.html", articles=articles)
        
if __name__=="__main__":
    app.run(debug= True)
