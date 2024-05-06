from flask import Flask, render_template, request, redirect, url_for
from werkzeug.local import LocalProxy
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pymongo.collection import Collection
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime

now = datetime.now()
current_time = now.strftime("%H:%M")
current_date = now.strftime("%d-%m-%Y")


app = Flask(__name__)

client = MongoClient("mongodb+srv://vicrastadiz:vicrastadiz@bank.oyt8o6o.mongodb.net/")
db = client["bank"]
users_collection = db["users"]
accounts_collection = db["accounts"]
history_collection = db["history"]

class User:
    def __init__(self, name, birth_date, cpf, username, password):
        self.name = name
        self.birth_date = birth_date
        self.cpf = cpf
        self.username = username
        self.password = password
    
    @classmethod
    def get_username(cls, username):
        min_lenght = 8
        if len(username) < min_lenght:
            message = 'A senha deve ter no mínimo 8 caractéres.'
            return message
        else:
            return username
    
    @classmethod
    def get_password(cls, password):
        common_sequences = ["123456", "abcdef"]
        common_words = ["password", "123456", "qwerty"]
        
        min_lenght = 8
        capital_letter = False
        lowercase_letter = False
        one_number = False
        special_character = False

        
        if len(password) < min_lenght:
            message = 'A senha deve ter no mínimo 8 caractéres.'
            return message
        
        elif password in common_sequences or password in common_words:
             message = 'Crie uma senha mais forte.'
            
        for char in password:
                if  char.isupper():
                    capital_letter = True
                elif char.islower():
                    lowercase_letter = True
                elif char.isdigit():
                    one_number = True
                elif not char.isalnum():
                    special_character = True
                    
                elif not lowercase_letter:
                    message = "Sua senha precisa ter pelo menos uma letra minúscula."

                elif not capital_letter:
                    message = "Sua senha precisa ter pelo menos uma letra maiúscula."
                
                elif not one_number:
                    message = "Sua senha precisa ter pelo menos um número."

                elif not special_character:
                    message = "Sua senha precisa ter pelo menos um caractere especial."

        else:
            return password
        
    @classmethod
    def request_username(cls, username):
        result = users_collection.find_one({"username": username})
        if result:
            return True
        else:
            return False, "Usuário não encontrado"
        
    @classmethod
    def request_password(cls, password):
        user_username = users_collection.find_one({"password": password})
        if user_username and user_username["password"] == password:
            return True
        else:
            return False, "Senha incorreta."
    
    @classmethod
    def check_login(cls, username, password):
        check_username = cls.request_username(username)
        check_password = cls.request_password(password)
        
        if check_username and check_password == True:
            return True, "Login bem-sucedido"
        else:
            return False, "Nome de usuário ou senha incorretos."   
            
class Account:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    @classmethod
    def next_id(cls):
        total_accounts = accounts_collection.count_documents({})
        cls.next_id = total_accounts + 1
        return cls.next_id
    
    @classmethod
    def acccount_info(cls, username):
        user = users_collection.find_one({"username": username})
        if user:
            account = accounts_collection.find_one({"user_id": user["_id"]})
            return account
        else:
            return None

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/signin")
def sign_in():
    return render_template("signin.html")

@app.route("/submit", methods=['post'])
def register():
    name = request.form['name']
    birth_date = request.form['birth_date']
    cpf = request.form['cpf']
    username = request.form['username']
    password = request.form['password']
    id = Account.next_id()
    
    user = User(name=name, birth_date=birth_date, cpf=cpf, username=username, password=password)
    account = Account(id=id, branch="0001", balance=0)
    
    new_user = {
        "_id": ObjectId(),
        "name": user.name.title(),
        "birth_date": user.birth_date,
        "cpf": user.cpf,
        "username": user.username,
        "password": user.password,
        }

    new_account = {
        "_id": ObjectId(),
        "user_id": new_user['_id'],
        "id": account.id,
        "branch": account.branch,
        "balance": account.balance,
        }
    
    history = {
        "_id": ObjectId(),
        "account_id": new_account['_id']
        }
    
    try:
        users_collection.insert_one(new_user)
        accounts_collection.insert_one(new_account)
        history_collection.insert_one(history)
        return render_template("register_done.html")
    
    except:
        return "<p> cadastro naõ foi concluído</p>"
    
    finally:
        client.close()
        
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/operational_menu", methods=["post"])
def operation_menu():
    username = request.form['username']
    password = request.form['password']
    
    successful_login = User.check_login(username=username, password=password)
    
    if successful_login:
        return redirect(url_for("operational_menu_success", username=username))
    else:
        return render_template("login.html")

@app.route("/operational_menu_success/<username>")
def operational_menu_success(username):
    user = users_collection.find_one({"username": username})
    account = Account.acccount_info(username=username)
    return render_template("operational_menu.html", current_time=current_time, current_date=current_date, user=user, account=account)

@app.route("/deposit/<username>")
def deposit(user, account):
    return render_template("deposit.html", user=user, account=account)

@app.route("/withdraw")
def withdraw(user, account):
    return render_template("withdraw.html", user=user, account=account)

if __name__ == "__main__":
    app.run(debug=True)