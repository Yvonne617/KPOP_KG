from flask import Flask,render_template,url_for,redirect,jsonify
from flask import request
from datetime import timedelta
import pickle
# from flask_wtf import Form
# from wtforms import StringField, SubmitField
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

GENREG = ["Ballad","Pop","R&B","Soul","Hip Hop","Electronic","RAP","Dance","EDM","Rock","Jazz","Retro","NU DISCO","Funk"]
BANDNUMBERG = ["More than 10","9","8","7","6","5","4","3","Less than 3"]
LABELG = ["SM","JYP","YG","Big Hit","Stone","FNC","Cube","Starship","Pledis","Fantagio","Other"]
GENDERM = ["F","M"]
POSITIONM = ["Rapper","Vocalist","Dancer","Maknae","Visual","Leader","Center","Face of the group","Drum","Guitar","Bass","Producer","Composer"]




#get the dict to convert the rdf URI to origin URL
data = pd.read_csv("data/rdf_url.csv")
dict_url = data.set_index('rdfURL').T.to_dict('list')

# class MockCreate(Form):
#     submit = SubmitField("Submit")

@app.route('/')
def return_main_page_with_filters():
    # cpredicate = '<' + cpredicate_clean + '>'
    # labels, values = get_top_labels_values_for_class_predicate(
    #     cclass, cpredicate)
    # max_val = cast_and_find_max(values)
    return render_template('main.html', 
                           genredropdown=GENREG, numberdropdown=BANDNUMBERG,
                           labeldropdown=LABELG,genrem=GENREG,labelm=LABELG,genderm=GENDERM,positionm=POSITIONM)

@app.route('/filterGroup',methods=['GET', 'POST'])
def filterGroup():
    print(request)
    keyword = request.form
    print(keyword)
    genre = keyword['chosen_genre']
    label = keyword['chosen_label']
    num = keyword['chosen_number']
    if num == "More than 10":
        number = ">10"
    elif num == "Less than 3":
        number = "<3"
    else:
        number = "=" + num
    if label == "Others":
        label = ""
    if num == '':
        queryline = "SELECT distinct ?group ?name WHERE{ ?group a schema:Class. ?group kpop:labels ?company.filter regex(?company,'"+label+"','i').?group dbo:genre ?g.filter regex(?g, '"+genre+"','i').?group rdfs:label ?name.}"
    else:
        queryline = "SELECT distinct ?group ?name WHERE{ ?group a schema:Class. ?group kpop:labels ?company.filter regex(?company,'"+label+"','i').?group dbo:genre ?g.filter regex(?g, '"+genre+"','i').?group kpop:member_num ?number.filter (?number"+number+").?group rdfs:label ?name.}"
    sparql.setQuery(prefix + queryline)
    temp = sparql.query().convert()
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
    return render_template("main.html", keyGroup=keysGroup, resultGroup=resultGroup,genredropdown=GENREG, numberdropdown=BANDNUMBERG,
                        labeldropdown=LABELG,genrem=GENREG,labelm=LABELG,genderm=GENDERM,positionm=POSITIONM)
    # return results

@app.route('/filterMember',methods=['GET', 'POST'])
def filterMember():
    print(request)
    keyword = request.form
    print(keyword)
    genre = keyword['chosen_genre_m']
    label = keyword['chosen_label_m']
    gender = keyword['chosen_gender_m']
    position = keyword['chosen_position_m']
    if label == "Others":
        label = ""
    queryline = "SELECT DISTINCT ?member ?p ?o WHERE{ ?group a schema:Class.?group kpop:labels ?company.filter regex(?company,'"+label+"','i').?group dbo:genre ?g.filter regex(?g, '"+genre+"','i').?group kpop:gender ?gender.filter regex(?gender, '"+gender+"','i').?group dbo:bandMember ?member.?member kpop:position ?position.?member ?p ?o.filter regex(?position,'"+position+"','i')}"
    sparql.setQuery(prefix + queryline)
    results = sparql.query().convert()
    allMember = {}
    if len(results["results"]["bindings"]) > 0:
        for i in range(len(results["results"]["bindings"])):
            if results["results"]["bindings"][i]['member']['type'] == 'uri':
                member = results["results"]["bindings"][i]['member']['value']
                pred = results["results"]["bindings"][i]['p']['value']
                obj = results["results"]["bindings"][i]['o']['value']
                objType = results["results"]["bindings"][i]['o']['type']
                #deal with pred
                if '#' in pred:
                    label = pred.split('#')[-1]
                else:
                    label = pred.split('/')[-1]
                #deal with member realURL
                if member not in allMember:
                    allMember[member] = collections.defaultdict(list)
                if member in dict_url:
                    realURL = dict_url[member][0]
                    allMember[member]['realURL'] = realURL
                #deal with obj
                if obj != 'None':
                    if objType != 'uri':
                        allMember[member][label].append((obj,False))
                    else:
                        allMember[member][label].append((obj,True)) 
    print(allMember) 
                                      
    return render_template("main.html", allMember=allMember,genrem=GENREG,labelm=LABELG,genderm=GENDERM,positionm=POSITIONM)
    # return keyword

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
    resultGroup.sort()
    return render_template("main.html", keyGroup=keysGroup, resultGroup=resultGroup,genredropdown=GENREG, numberdropdown=BANDNUMBERG,
                           labeldropdown=LABELG)

@app.route('/searchMember', methods=['POST'])
def searchMember():
    # print(request.form)
    memberName = str(request.form['membername'])
    queryLine = "SELECT ?member ?group ?groupname ?p ?o WHERE{ ?group a schema:Class. ?group dbo:bandMember ?member. ?group rdfs:label ?groupname. ?member rdfs:label ?name. FILTER regex(?name,'"+memberName +"', 'i').?member ?p ?o}"
    sparql.setQuery(prefix + queryLine)
    results = sparql.query().convert()
    allMember = {}
    if len(results["results"]["bindings"]) > 0:
        for i in range(len(results["results"]["bindings"])):
            if results["results"]["bindings"][i]['member']['type'] == 'uri':
                member = results["results"]["bindings"][i]['member']['value']
                group = results["results"]["bindings"][i]['group']['value']
                groupname = results["results"]["bindings"][i]['groupname']['value']
                pred = results["results"]["bindings"][i]['p']['value']
                obj = results["results"]["bindings"][i]['o']['value']
                objType = results["results"]["bindings"][i]['o']['type']
                #deal with pred
                if '#' in pred:
                    label = pred.split('#')[-1]
                else:
                    label = pred.split('/')[-1]
                #deal with member realURL
                if member not in allMember:
                    allMember[member] = collections.defaultdict(list)
                if member in dict_url:
                    realURL = dict_url[member][0]
                    allMember[member]['realURL'] = realURL
                #deal with obj
                if obj != 'None' and label != 'gender':
                    if objType != 'uri':
                        allMember[member][label].append((obj,False))
                    else:
                        allMember[member][label].append((obj,True))
                if 'groupname' not in allMember[member]:
                    allMember[member]['groupname'].append((groupname,False))
                    allMember[member]['group'].append((group,True))

    print(allMember) 
                                      
    return render_template("main.html", allMember=allMember,genrem=GENREG,labelm=LABELG,genderm=GENDERM,positionm=POSITIONM)


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

@app.route('/predict', methods=['GET','POST'])
def predict():
    genres = [ "HIP HOP","DANCE POP","K POP","R&B","J POP","POP","DANCE","ROCK","BALLAD","EDM","ELECTRONIC","BUBBLEGUM POP","SYNTH POP","POP ROCK","TEEN POP","NU DISCO","ELECTRO POP","SOUL","POPERA","METAL","RAP","C POP","JAZZ","FUNK","RETRO","ELECTROPOP" ]
    
    if request.method == 'POST':
        with open('data/genre_encoder.pkl', 'rb') as f:
            dic_genre = pickle.load(f)
        with open('data/company_encoder.pkl', 'rb') as f:
            dic_company = pickle.load(f)
        genre_t,company_t,num_t,gender_t = "Unknown","Unknown","Unknown","Unknown"
        genre,company,num,gender = dic_genre['Empty'],dic_company['Empty'],3,2
        form= request.form
        if 'genre' in form:
            genre= form.getlist('genre')
            genre_t= form.getlist('genre')
            print(genre)
            genre.sort()
            genre2 = "+".join(genre)
            if genre2 in dic_genre:
                genre = dic_genre[genre2]
            else:
                genre = dic_genre['Empty']
        if 'company' in form:
            company= form['company']  
            if company in dic_company:
                company = dic_company[company]
            else:
                company = dic_company['Empty']
            company_t= form['company'] 
            print(company)

        if 'num' in form:
            num = form['num']
            num_t = form['num']
            if num == "More than 10":
                num = 15
            elif num == "Less than 3":
                num = 2
            else:
                num = int(num)
        if 'group1' in form:
            gender = form['group1'] 
            gender_t = form['group1'] 
            if gender == 'M':
                gender = 1
            elif gender == 'F':
                gender = 2
            else:
                gender = 3
       
        model = pickle.load(open('data/kpop_model.sav', 'rb'))
        print(genre,company,num,gender)
        X = pd.DataFrame({'genre(s)': [genre], 'labels': [company], 'num_members':[num], 'gender':[gender]})
        predicted_popularity = model.predict(X)
        return render_template("predict.html",genres=genres,company=LABELG,num=BANDNUMBERG,predict_genre=genre_t,predict_company=company_t,predict_num=num_t,gender=gender_t,predicted_popularity=int(predicted_popularity))

    else:
        print("get")
        return render_template("predict.html",genres=genres,company=LABELG,num=BANDNUMBERG,predicted_popularity=0)