from flask import Flask,render_template,url_for,redirect
from flask import request
from datetime import timedelta
import rltk
import rdflib 
from flask import jsonify 
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__,template_folder='templates')
app.config['DEBUG'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds = 1)

sparql = SPARQLWrapper("http://localhost:3030/kpop/query")
sparql.setReturnFormat(JSON)

prefix =  """ 
        PREFIX : <undefined>
        PREFIX kpop: <http://inf558.org/kpop/>
        PREFIX dbr: <http://dbpedia.org/resource/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/> 
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX dbo: <http://dbpedia.org/>
        PREFIX fanm: <https://kpop.fandom.com/wiki/>  """
@app.route('/')
def index():
    return render_template('main.html')

@app.route('/groups')
def groups():
    keyword = request.args.get("keyword")
    g = rdflib.Graph()
    result = g.parse('data/KPOP_graph.ttl', format='n3')
    qres = g.query("""
    SELECT ?name WHERE { 
    ?group a schema:Class .
	?group rdfs:label ?name .
    FILTER regex(?name,"EXO", "i") 
    }
     """)
    for row in qres:
        print(row)
    return jsonify({"data": keyword})
@app.route('/members')
def members():
    keyword = request.args.get("keyword")
    return jsonify({"data": keyword})

@app.route('/trend', methods=['GET', 'POST'])
def trend():
    # return "hello world"
    return render_template("trend.html")

@app.route('/query')
def query_first():
    return render_template("query.html", title="Query")

@app.route('/query', methods=['POST'])
def query():
    queryline = request.form['sparql']
    if queryline:
        sparql.setQuery(prefix + queryline)
        temp = sparql.query().convert()
        try:
            keys = temp["results"]["bindings"][0].keys()
        except:
            keys = []
        return temp

    # return "hello world"