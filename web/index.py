from flask import Flask,render_template,url_for,redirect
from flask import request
from datetime import timedelta
import rltk
import rdflib 
from flask import jsonify 
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import json
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
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX fadm: <https://kpop.fandom.com/wiki/> 
        PREFIX schema: <http://schema.org/> """
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
    df = pd.read_csv('data/genre_bar.csv')
    print(df)
    chart_data = df.to_dict(orient='records')
    chart_data = json.dumps(chart_data, indent=2)
    print(chart_data)
    # return "hello world"
    return render_template("trend.html",chart_data=chart_data)

@app.route('/query')
def query_first():
    return render_template("query.html", title="Query")

@app.route('/query', methods=['POST'])
def query():
    queryline = request.form['sparql']
    if queryline:
        sparql.setQuery(prefix + queryline)
        temp = sparql.query().convert()
        result = []
        if len(temp["results"]["bindings"]) > 0:
            keys = temp["results"]["bindings"][0].keys()
            for i in range(len(temp["results"]["bindings"])):
                line = []
                for key in keys:
                    if temp["results"]["bindings"][i][key]["type"] == 'uri':
                        #need to replace link
                        line.append((temp["results"]["bindings"][i][key]["value"],True))
                    else:
                        line.append((temp["results"]["bindings"][i][key]["value"],False))
                result.append(line)
        else:
            keys = ['No']
        print(result)
        return render_template("query.html", title="Query", key=keys, result=result)
    # return "hello world"

@app.route('/searchGroup', methods=['POST'])
def searchGroupName():
    # print(request.form)
    groupName = str(request.form['groupname'])
    queryLine = "SELECT ?group ?name WHERE{ ?group a schema:Class .?group rdfs:label ?name . FILTER regex(?name, '"+groupName+"', 'i')}"
    sparql.setQuery(prefix + queryLine)
    temp = sparql.query().convert()
    print(temp)
    result = []
    if len(temp["results"]["bindings"]) > 0:
         keys = temp["results"]["bindings"][0].keys()
         for i in range(len(temp["results"]["bindings"])):
            line = []
            for key in keys:
                if temp["results"]["bindings"][i][key]["type"] == 'uri':
                        #need to replace link
                    line.append((temp["results"]["bindings"][i][key]["value"],True))
                else:
                    line.append((temp["results"]["bindings"][i][key]["value"],False))
            result.append(line)
    else:
        keys = ['No']
    print(result)
    # return result
    return render_template("main.html", title="SearchGroup", key=keys, result=result)