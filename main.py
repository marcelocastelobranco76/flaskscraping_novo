import pymysql
from app import app
from database.db_config import MySQL, mysql
from flask import flash, render_template, request, redirect, url_for, session
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from config import *
import json
import os, sys
import signal
import subprocess
import requests
import re


@app.route('/app/', methods=['GET', 'POST'])
def login():
    msg = ''
    # Verifica se existem solicitações POST de "username" e "password" (formulário enviado pelo usuário)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Cria variáveis para acesso fácil
        username = request.form['username']
        password = request.form['password']

        # Verifica se usuário existe usando MySQL
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
        # Busca um registro e retornar o resultado
        usuario = cursor.fetchone()

        # Se o usuário existir na tabela de usuários
        if usuario:
            # Cria dados de sessão.
            session['loggedin'] = True
            session['id'] = usuario[0]
            session['username'] = usuario[1]
            # Redireciona para o dashboard
            return redirect(url_for('dashboard'))
        else:
            # Usuário não existe ou username/password incorreto
            msg = 'username/password incorreto!'
        cursor.close()
        conn.close()

        # Mostra o formuláro de login com mensagem (se houver mensagem)

    return render_template('index.html', msg='')


@app.route('/app/logout')
def logout():
    # Remove os dados da sessão. Isso faz com o que o usuário seja deslogado
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect(url_for('login'))


@app.route('/app/cadastro', methods=['GET', 'POST'])
def cadastro():
    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        usuario = cursor.fetchone()

        # Se usuário já existe no banco dados.  Verifica as validações.
        if usuario:
            msg = 'Usuário já existe.'

        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):

            msg = 'Endereço de e-mail inválido.'

        elif not re.match(r'[A-Za-z0-9]+', username):

            msg = 'Username deve ter apenas letras e números'

        elif not username or not password or not email:

            msg = 'Favor preencher o formulário.'

        else:
            # Usuário não existe e os dados do formulário são válidos,agora cadastro no bancco de dados.
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s)', (username, password, email,))
            conn.commit()
            cursor.close()
            conn.close()
            msg = 'Cadastrado com sucesso.'

    elif request.method == 'POST':

        msg = 'Favor preencher o formulário.'

    return render_template('cadastro.html', msg=msg)


@app.route('/app/dashboard')
def dashboard():
    # Verifica se o usuário está logado
    if 'loggedin' in session:

        # Se o usuário está logado redireciona para o dashboard

        return render_template('dashboard.html', username=session['username'])

    # senão redireciona para a tela de login
    return redirect(url_for('login'))


@app.route('/app/pesquisa', methods=['GET', 'POST'])
def pesquisa():

    # Verifica se o usuário está logado
    if 'loggedin' in session:

        erros = []
        resultados = {}
        resultlinks = ""
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3538.102 "
                "Safari/537.36 Edge/18.19582 "
        }
        if request.method == "POST":
            # Palavra que o usuário digitou
            # Uso da API SerpAPI
            # O parâmetro num lista 05 links
            try:
                termo = request.form['termopesquisa']
                pesquisa = termo
                parametros = {
                    "api_key": API_KEY,
                    "engine": "google",
                    "google_domain": "google.com.br",
                    "q": pesquisa,
                    "lr": "lang_pt",
                    "start": "50",
                    "num": "5",

                }
                busca = GoogleSearch(parametros)
                resultadosbusca = busca.get_dict()
                search_result = busca.get_dictionary()
                metadata_results = resultadosbusca['search_metadata']
                listalinks = []

                for resultadobusca in resultadosbusca['organic_results']:

                    link = resultadobusca['link']
                    try:
                        inline_sitelinks = resultadobusca['sitelinks']['inline']
                    except:
                        inline_sitelinks = None

                    try:
                        expanded_sitelinks = resultadobusca['sitelinks']['expanded']
                    except:
                        expanded_sitelinks = None

                    listalinks.append(str(link))
                temporesposta = resultadosbusca['search_metadata']['total_time_taken']
                try:
                    conn = None
                    cursor = None
                    _termo = pesquisa
                    _tempo = temporesposta
                    sql = "INSERT INTO metrics(searched_term, time_taken) VALUES( % s, % s)"
                    data = (_termo, _tempo)
                    conn = mysql.connect()
                    cursor = conn.cursor()
                    cursor.execute(sql, data)
                except Exception as e:
                    print(e)
                finally:
                    conn.commit()
                    cursor.close()
                    conn.close()

                # Se o usuário está logado redireciona para a tela de pesquisa
                return render_template('pesquisa.html', results=listalinks)

            except:
                erros.append(
                    "Favor digitar novamente a palavra a ser pesquisada."
                )
        return render_template('pesquisa.html', errors=erros, results=resultados)

    # senão redireciona para a tela de login
    return redirect(url_for('login'))


def multiprocessos(numprocs, starting_port):
    procs = []
    for port in range(starting_port, starting_port + numprocs):
        procs.append(subprocess.Popen(['python', __file__, str(port)]))

    def killprocesso(signal, frame):
        print("Caught SIGINT, killing {0} subproccesses and exiting".format(len(procs)))
        [p.kill() for p in procs]
        sys.exit(0)

    signal.signal(signal.SIGINT, killprocesso)
    signal.pause()


@app.route('/app/metricas')
def metricas():
    # Verifica se o usuário está logado
    if 'loggedin' in session:
        conn = None
        cursor = None
        try:
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM metrics")
            rows = cursor.fetchall()

            # Se o usuário estiver logado é redirecionado para a tela de métricas de utilização
            return render_template('metricas.html', value=rows)

        except Exception as e:
            print(e)
        finally:
            cursor.close()
            conn.close()
    # senão redireciona para a tela de login
    return redirect(url_for('login'))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    numprocs = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    if numprocs == 1:
        app.run(host='0.0.0.0', port=int(port), threaded=True)
    else:
        multiprocessos(numprocs, port)
