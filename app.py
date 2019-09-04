from flask import Flask, render_template, request, json, jsonify
from database import init_db, db, Region, Hospital, Institution, Region, DocReview, Doctor
import operator
import collections
import pandas
import userdocdistance
from model import initmodel
from bidirec_LSTM import predicttorch
# torch 안 깔리면 이 윗줄 주석처리하고 CNN 사용해야 함


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database/patientmatching_190827_all.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = init_db(app)
predictmodel = -1
info = {}




@app.route('/')
def homepage():
    doctor = Doctor.query.all()
    hospitial = Hospital.query.all()
    inst = Institution.query.all()
    return render_template('mainhome.html', data={"doc":doctor, "hos":hospitial})

@app.route('/searchdb', methods =['GET','POST'])
def searchdb():
    method = request.method
    if(method=="POST"):
        data = json.loads(request.get_data())
        keyword = data['keyword']
        unitflag = data['unitflag']
        locate = data['locate']

        doctor = Doctor.query.join(Hospital,Doctor.hospital_id==Hospital.id)\
            .join(Region,Region.id==Hospital.gu)

        hospital = Hospital.query.join(Region, Hospital.gu==Region.id)
        if(locate=="0"):
            if(unitflag=="0"):
                doctor_ = [(_[1],_[2], _[3], 0) for _ in Doctor.query.join(Hospital,Doctor.hospital_id==Hospital.id)
                    .add_columns(Doctor.name,Hospital.name, Doctor.id)
                    .filter(Doctor.name.like("%"+keyword+"%"))]
                hospital_ = [(_[1],_[2], _[3], 1) for _ in Hospital.query.join(Region, Hospital.gu==Region.id)
                    .add_columns(Hospital.name,Region.gu, Hospital.id)
                    .filter(Hospital.name.like("%"+keyword+"%"))]
                result = doctor_+hospital_
            elif(unitflag=="1"):
                result = [(_[1],_[2],_[3], 1) for _ in hospital \
                    .add_columns(Hospital.name, Region.gu, Hospital.id) \
                    .filter(Hospital.name.like("%"+keyword+ "%"))]
            else:
                result = [(_[1],_[2],_[3], 0) for _ in doctor \
                    .add_columns(Doctor.name, Hospital.name, Doctor.id) \
                    .filter(Doctor.name.like("%"+keyword+"%"))]
        else:
            region = Region.query.filter(Region.id.like(locate)).first()
            locate = region.gu
            if (unitflag == "0"):
                doctor_ = [(_[1],_[2], _[3], 0) for _ in
                          Doctor.query.join(Hospital, Doctor.hospital_id == Hospital.id).join(Region,Region.id==Hospital.gu)
                              .add_columns(Doctor.name, Hospital.name, Doctor.id)
                              .filter(Doctor.name.like("%" + keyword + "%")).filter(Region.gu.like(locate))]
                hospital_ = [(_[1],_[2], _[3], 1) for _ in Hospital.query.join(Region, Hospital.gu == Region.id)
                    .add_columns(Hospital.name, Region.gu, Hospital.id)
                    .filter(Hospital.name.like("%" + keyword+ "%")).filter(Region.gu.like(locate))]
                result=doctor_+hospital_
            elif (unitflag == "1"):
                result = [(_[1],_[2],_[3], 1) for _ in hospital \
                    .add_columns(Hospital.name, Region.gu, Hospital.id) \
                    .filter(Hospital.name.like("%" + keyword + "%")).filter(Region.gu.like(locate))]
            else:
                result = [(_[1],_[2],_[3], 0) for _ in doctor \
                    .add_columns(Doctor.name, Hospital.name, Doctor.id) \
                    .filter(Doctor.name.like("%" + keyword + "%")).filter(Region.gu.like(locate))]

        final = []
        count=0
        [final.append({"order":a,"firstinfo":i,"secondinfo":j,"id":t, "flag":r}) for a,(i,j,t,r) in enumerate(result)]
        return jsonify({"result":final})


@app.route('/research')
def researchpage():
    page = request.args.get('page')
    return render_template('research.html', page=page)


@app.before_request
def first_start():
    db.create_all()



@app.route('/search', methods =['POST'])
def searchinfo():
    keyword = request.form['keyword']
    locate = request.form['locate']

    if(locate=="전체 지역"):
        doctorlist = Doctor.query.join(Hospital, Doctor.hospital_id == Hospital.id) \
            .join(Region, Region.id == Hospital.gu) \
            .add_columns(Doctor.id, Doctor.name, Doctor.docinfo, Doctor.specialist, Doctor.recognition, Doctor.academy, Doctor.lecture,
        Doctor.master ,Hospital.name.label("hosname"), Hospital.region.label("hoslocate")
                        , Hospital.homepage.label("hospage"), Hospital.xloc, Hospital.yloc, Region.gu.label("gu")) \
            .filter(Doctor.name.like("%"+keyword+"%")).all()
        hospitallist = Hospital.query\
            .join(Region, Hospital.gu == Region.id).filter(Hospital.name.like("%"+keyword+"%"))\
            .add_columns(Hospital.id ,Hospital.name, Hospital.homepage, Hospital.region, Hospital.tellnum, Hospital.coursename,
                         Hospital.age, Hospital.xloc, Hospital.location, Hospital.yloc,
                          Region.gu.label("guname")).filter(Hospital.name.like("%"+keyword+"%")).all()
    else:
        doctorlist = Doctor.query.join(Hospital, Doctor.hospital_id == Hospital.id) \
            .join(Region, Region.id == Hospital.gu) \
            .add_columns(Doctor.id, Doctor.name, Doctor.docinfo, Doctor.specialist, Doctor.recognition, Doctor.academy,
                         Doctor.lecture,
                         Doctor.master, Hospital.name.label("hosname"), Hospital.region.label("hoslocate")
                         , Hospital.homepage.label("hospage"), Hospital.xloc, Hospital.yloc, Region.gu.label("gu")) \
            .filter(Doctor.name.like("%" + keyword + "%")).filter(Region.gu.like(locate)).all()
        hospitallist = Hospital.query \
            .join(Region, Hospital.gu == Region.id).filter(Hospital.name.like("%" + keyword + "%")) \
            .add_columns(Hospital.id, Hospital.name, Hospital.homepage, Hospital.region, Hospital.tellnum,
                         Hospital.coursename,
                         Hospital.age, Hospital.xloc, Hospital.location, Hospital.yloc,
                         Region.gu.label("guname")).filter(Hospital.name.like("%" + keyword + "%"))\
                        .filter(Region.gu.like(locate)).all()

    hos_doc = {}
    [hos_doc.update({_.id:Doctor.query.filter(Doctor.hospital_id.like(_.id)).all()}) for _ in hospitallist]
    thisresults = {
        '치과교정과': 0.6,
        '치과보철과': 0.3,
        '치과보존과': 0.1,
        '치주과': 0.5,
        '구강악안면외과': 0.1,
        '구강내과': 0.1,
        '소아치과': 0.05,
        '구강병리과': 0.05
    }

    coursedict = {
        '치과교정과': "성장기 환자의 치열, 악안면골격 이상 발육의 교정치료, 성인환자의 치열 및 악안면골 이상에 대한 교정치료와 교정-수술 복합치료를 수행한다.",
        '치과보철과': "치아가 결손된 환자들에게 일반보철치료, 심미보철치료, 악안면보철치료, 임플란트보철치료 등을 통해 인공적으로 치아를 대체해 줌으로써 구강과 안면부의 기능회복과 심미적 개선을 가져오도록 해준다.",
        '치과보존과': "치아의 경조직 손상을 비롯해 심미적 부조화, 치수질환 및 치근단질환에 대한 치료를 시행한다. 치아와 관련된 통증을 제거해 치아의 저작, 발음, 심미기능을 회복시킨다.",
        '치주과': "치은염(잇몸병)이나 치주염(풍치) 등과 같은 염증성 질환을 치료하고 염증성 치은비대나 약물에 의한 치은비대증, 외상성 교합이나 부정교합에 의한 치주질환을 치료한다. 또한 치은착색, 구취, 지각과민, 치은 퇴축 등의 치료와 임플란트 치료도 시행한다.",
        '구강악안면외과': "턱과 얼굴 부위에 관련된 전문적인 진료를 주로 한다. 구강암 치료 및 턱뼈 재건, 얼굴 기형증과 성형술, 턱뼈 골절치료를 수행한다. 구순구개열 이른바 ‘언청이' 수술과 악관절증의 치교, 임플란트를 식립하고 악안면영역의 미용 성형수술과 침샘 질환, 구강 및 안면신경질환, 보철 전 성형수술, 사랑니 발치 등도 시행한다.",
        '구강내과': "턱관절장애 환자를 비롯한 만성구강안면통증 환자와 코골이 및 수면무호흡증환자의 치료를 담당한다. 특별한 원인없이 혀나 입안 점막이 따가운 구강작열감증후군이나 구취치료, 구강건조증 등 구강내과적 처치가 필요한 경우 이에 대한 진료를 주관한다.",
        '소아치과': "소아 치과질환 전반의 예방치료와 치아우식증 치료, 구강 및 치아 발육 장애의 치료, 구강조직 및 치아의 외상치료, 악안면 성장, 발육 및 교합의 정상적인 유도, 전신 질환을 가진 환자나 장애아동의 치과 질환 치료를 수행한다.",
        '구강병리과': "구강병리과",
        '예방치과': "예방치과",
        '구강악안면방사선과': "구강악안면방사선과",
        '장애인치과': "장애인치과"
    }

    sorted_results = sorted(thisresults.items(), key=operator.itemgetter(1), reverse=True)
    sorted_dict = collections.OrderedDict(sorted_results)

    labels = list(sorted_dict.keys())
    dataset = list(sorted_dict.values())

    resultdoc = userdocdistance.getdoctor([_.id for _ in doctorlist])
    resultdoctors = resultdoc['sim'].T.to_dict()
    for key in resultdoctors.keys():
        resultdoctors[key] = [round(_, 2) for _ in list(resultdoctors[key])]

    return render_template("searchinfo.html", doctorlist=doctorlist, hospitallist=hospitallist, labels=labels,
                           dataset=dataset, keyword = keyword, locate=locate, hos_doc= hos_doc, resultdoctors=resultdoctors)



@app.route('/matching')
@app.route('/matching', methods =['POST'])
def matchingpage():
    global predictmodel
    if(predictmodel==-1):
        predictmodel = initmodel()
    # wantlocate2 = request.form['locate2'] # 지역 id ; 강동구... 전체는 0
    # sick1 = request.form['sick1']
    # sick2 = request.form['sick2']

    doctorlist = list()
    hospitallist = list()
    inslist = list()

    thisresults = {
        '치과교정과':0.6,
        '치과보철과':0.3,
        '치과보존과':0.1,
        '치주과':0.5,
        '구강악안면외과':0.1,
        '구강내과':0.1,
        '소아치과':0.05,
        '구강병리과':0.05
    }

    coursedict = {
        '치과교정과': "성장기 환자의 치열, 악안면골격 이상 발육의 교정치료, 성인환자의 치열 및 악안면골 이상에 대한 교정치료와 교정-수술 복합치료를 수행한다.",
        '치과보철과': "치아가 결손된 환자들에게 일반보철치료, 심미보철치료, 악안면보철치료, 임플란트보철치료 등을 통해 인공적으로 치아를 대체해 줌으로써 구강과 안면부의 기능회복과 심미적 개선을 가져오도록 해준다.",
        '치과보존과': "치아의 경조직 손상을 비롯해 심미적 부조화, 치수질환 및 치근단질환에 대한 치료를 시행한다. 치아와 관련된 통증을 제거해 치아의 저작, 발음, 심미기능을 회복시킨다.",
        '치주과': "치은염(잇몸병)이나 치주염(풍치) 등과 같은 염증성 질환을 치료하고 염증성 치은비대나 약물에 의한 치은비대증, 외상성 교합이나 부정교합에 의한 치주질환을 치료한다. 또한 치은착색, 구취, 지각과민, 치은 퇴축 등의 치료와 임플란트 치료도 시행한다.",
        '구강악안면외과': "턱과 얼굴 부위에 관련된 전문적인 진료를 주로 한다. 구강암 치료 및 턱뼈 재건, 얼굴 기형증과 성형술, 턱뼈 골절치료를 수행한다. 구순구개열 이른바 ‘언청이' 수술과 악관절증의 치교, 임플란트를 식립하고 악안면영역의 미용 성형수술과 침샘 질환, 구강 및 안면신경질환, 보철 전 성형수술, 사랑니 발치 등도 시행한다.",
        '구강내과': "턱관절장애 환자를 비롯한 만성구강안면통증 환자와 코골이 및 수면무호흡증환자의 치료를 담당한다. 특별한 원인없이 혀나 입안 점막이 따가운 구강작열감증후군이나 구취치료, 구강건조증 등 구강내과적 처치가 필요한 경우 이에 대한 진료를 주관한다.",
        '소아치과': "소아 치과질환 전반의 예방치료와 치아우식증 치료, 구강 및 치아 발육 장애의 치료, 구강조직 및 치아의 외상치료, 악안면 성장, 발육 및 교합의 정상적인 유도, 전신 질환을 가진 환자나 장애아동의 치과 질환 치료를 수행한다.",
        '구강병리과': "구강병리과",
        '예방치과': "예방치과",
        '구강악안면방사선과': "구강악안면방사선과",
        '장애인치과': "장애인치과"
    }

    sorted_results = sorted(thisresults.items(), key=operator.itemgetter(1), reverse=True)
    sorted_dict = collections.OrderedDict(sorted_results)

    userresult = {
        'name' :'익명의 이용자',
        'result' : None
    }

    if request.method == 'POST':
        result = request.form
        userresult['name'] = result['name']
        region = result['locate2']
        sick = ""
        for i in result:
            if ('sick' in i):
                sick += result[i] + " "
        # resultpredict = predictmodel.predict(sick)
        resultpredict = predicttorch(sick)
        # torch 안 깔려 있으면 이 윗줄은 주석처리하고 그 윗줄(CNN)으로 사용할 것

        # user의 query에 대한 예측 내용을 받아옴
        # 소수점 2자리까지만
        for key in resultpredict.keys():
            resultpredict[key] = round(resultpredict[key]*100,2)

        # 결과값 sorting
        sorted_results = sorted(resultpredict.items(), key=operator.itemgetter(1), reverse=True)
        sorted_dict = collections.OrderedDict(sorted_results)

        # sorting한 결과를 userresult에 저장
        userresult['result'] = sorted_results
        labels = list(sorted_dict.keys())
        dataset = list(sorted_dict.values())

        # 이 user의 region과 match되는 doctor list
        valuelist = [ float(value) for value in resultpredict.values()]
        resultdoctor = userdocdistance.computedistance(valuelist, region)
        resultdoctors = resultdoctor['sim'].T.to_dict()
        matchedlist = list(resultdoctors.keys())[:20]

        for idx, matchid in enumerate(matchedlist):
            doctorlist.extend(Doctor.query.filter_by(id=matchid))
            hospitallist.extend(Hospital.query.filter_by(id=doctorlist[idx].hospital_id))

        resultdocweights = resultdoctor['weighted'].T.to_dict()
        for key in resultdocweights.keys():
            resultdocweights[key] = [ round(_,2) for _ in list(resultdocweights[key])]
    else:
        print('this is anonymous')
        matchedlist = [1, 2, 3, 4, 5]
        for idx, matchid in enumerate(matchedlist):
            doctorlist.extend(Doctor.query.filter_by(id=matchid))
            hospitallist.extend(Hospital.query.filter_by(id=doctorlist[idx].hospital_id))
            labels = list(sorted_dict.keys())
            dataset = list(sorted_dict.values())

    dochos = {}
    for i in doctorlist:
        if(i.hospital_id in dochos):
            dochos[i.hospital_id] += str(i.id)+" "
        else:
            dochos[i.hospital_id] = str(i.id)+" "
    return render_template('matching.html', doctorlist = doctorlist, hospitallist = hospitallist,
                           userresult = userresult, labels = labels, dataset = dataset,
                           coursedict = coursedict, resultdocweights = resultdocweights, dochos=dochos)



if __name__ == '__main__':
    app.run()
