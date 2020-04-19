from flask import Flask,render_template,url_for,redirect
from flask import request
from datetime import timedelta
import rltk
import rdflib 
from flask import jsonify 
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import json
import collections

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


#get the dict to convert the rdf URI to origin URL
data = pd.read_csv("/Users/phyllis/Documents/GitHub/KPOP_NG/data/rdf_url.csv")
dict_url = data.set_index('rdfURL').T.to_dict('list')

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
        # print(result)
        return render_template("query.html", title="Query", key=keys, result=result)
    # return "hello world"

@app.route('/searchGroup', methods=['POST'])
def searchGroup():
    # print(request.form)
    groupName = str(request.form['groupname'])
    queryLine = "SELECT ?group ?name WHERE{ ?group a schema:Class .?group rdfs:label ?name . FILTER regex(?name, '"+groupName+"', 'i')}"
    sparql.setQuery(prefix + queryLine)
    temp = sparql.query().convert()
    # print(temp)
    resultGroup = []
    if len(temp["results"]["bindings"]) > 0:
         keysGroup = temp["results"]["bindings"][0].keys()
         for i in range(len(temp["results"]["bindings"])):
            line = []
            for key in keysGroup:
                if temp["results"]["bindings"][i][key]["type"] == 'uri':
                        #need to replace link
                    line.append((temp["results"]["bindings"][i][key]["value"],True))
                else:
                    line.append((temp["results"]["bindings"][i][key]["value"],False))
            resultGroup.append(line)
    else:
        keysGroup = ['No']
    # print(resultGroup)
    # print(dict_url)
    # return result
    return render_template("main.html", keyGroup=keysGroup, resultGroup=resultGroup)

@app.route('/description', methods=['GET', 'POST'])
def description():
    uri = request.args.get('uri')
    # print(uri,type(uri))
    name=uri.split('/')[-1]
    # print(name)
    # key1 = ['predicate', 'object']
    _sparql1 = " SELECT  ?predicate ?object WHERE { fadm:"+name+" ?predicate ?object.} LIMIT 200"
    sparql.setQuery(prefix + _sparql1)
    results = sparql.query().convert()
    # print(results)
    results = sparql.query().convert()
    allLabels = collections.defaultdict(list)
    if len(results["results"]["bindings"]) > 0:
        for i in range(len(results["results"]["bindings"])):
            if results["results"]["bindings"][i]['predicate']['type'] == 'uri':
                tempLabel = results["results"]["bindings"][i]['predicate']['value']
                label = tempLabel.split('/')[-1]
                if '#' in results["results"]["bindings"][i]['predicate']['value']:
                    label = tempLabel.split('#')[-1]
                # print(label)
            value = results["results"]["bindings"][i]['object']['value']
            if results["results"]["bindings"][i]['object']['type'] == 'uri':
                if label == 'bandMember':
                    if value in dict_url:
                        allLabels[label].append((dict_url[value][0],True))
                    else:
                        allLabels[label].append((value,True))
                else:
                    allLabels[label].append((value,True))
            else:
                allLabels[label].append((value,False))
    
    labelKey = list(allLabels.keys())
    print(labelKey)
    realURL = dict_url[uri][0]
    print(realURL)
    return render_template('description.html', requri=uri, allinfo=allLabels, infokey=labelKey, realURL=realURL)