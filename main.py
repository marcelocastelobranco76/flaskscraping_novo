import pymysql
from app import app
from database.db_config import MySQL, mysql
from flask import flash, render_template, request, redirect
from bs4 import BeautifulSoup
from serpapi import GoogleSearch
from config import *
import json
import os, sys
import signal
import subprocess
import requests


@app.route('/', methods=['GET', 'POST'])
def index():
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

            return render_template('index.html', results=listalinks)


        except:
            erros.append(
                "Favor digitar novamente a palavra a ser pesquisada."
            )
    return render_template('index.html', errors=erros, results=resultados)


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


@app.route('/metricas')
def metricas():
    conn = None
    cursor = None
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM metrics")
        rows = cursor.fetchall()

        return render_template('metricas.html', value = rows)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    numprocs = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    if numprocs == 1:
        app.run(host='0.0.0.0', port=int(port), threaded=True)
    else:
        multiprocessos(numprocs, port)
