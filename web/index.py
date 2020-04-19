from flask import Flask,render_template,url_for,redirect,jsonify
from flask import request
from datetime import timedelta
import rltk
import rdflib 
from flask import jsonify 
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import json
from collections import Counter
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
data = pd.read_csv("data/rdf_url.csv")
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
    df1 = pd.read_csv('data/genre_bar.csv')
    chart_data = df1.to_dict(orient='records')
    chart_data = json.dumps(chart_data, indent=2)
    
    df2 = pd.read_csv('data/top.csv')
    top_data = df2.to_dict(orient='records')

    df3 = pd.read_csv('data/top50_genre.csv')
    top50_genre = df3.to_dict(orient='records')
    d = []
    for group in top50_genre:
        d.append(group["genre"])
    top50_genre = Counter(d)

    #top_data = json.dumps(top_data, indent=2)
    # return "hello world"
    df4 = pd.read_csv('data/top50_num.csv')
    top50_num = df4.to_dict(orient='records')
    d2 = []
    for group in top50_num:
        d2.append(group["num"])
    top50_num = Counter(d2)
    print(top50_num)
    return render_template("trend.html",top_data = jsonify(top_data),chart_data=chart_data,top50_genre=top50_genre,top50_num=top50_num)

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
    return render_template("main.html", keyGroup=keysGroup, resultGroup=resultGroup)

@app.route('/searchMember', methods=['POST'])
def searchMember():
    # print(request.form)
    memberName = str(request.form['membername'])
    queryLine = "SELECT ?member ?p ?o WHERE{ ?group a schema:Class. ?group dbo:bandMember ?member. ?member rdfs:label ?name. FILTER regex(?name,'"+memberName +"', 'i').?member ?p ?o}"
    sparql.setQuery(prefix + queryLine)
    results = sparql.query().convert()
    allMember = {}
    if len(results["results"]["bindings"]) > 0:
        for i in range(len(results["results"]["bindings"])):
            if results["results"]["bindings"][i]['member']['type'] == 'uri':
                member = results["results"]["bindings"][i]['member']['value']
                pred = results["results"]["bindings"][i]['p']['value']
                obj = results["results"]["bindings"][i]['o']['value']
                objType = results["results"]["bindings"][i]['o']['type']
                if member in dict_url:
                    realURL = dict_url[member][0]
                if member not in allMember:
                    allMember[member] = collections.defaultdict(list)
                if obj != 'None':
                    if objType != 'uri':
                        allMember[member][pred].append((obj,False))
                    else:
                        allMember[member][pred].append((obj,True))                        

    return allMember


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


# @app.route('/changeStatusGroup', methods=['GET', 'POST'])
# def changeStatusGroup():
#     keysGroup = []
#     resultGroup = []
#     return render_template("main.html", keyGroup=keysGroup, resultGroup=resultGroup)
