from django.shortcuts import render
from random import randint

# Create your views here.

def index(request):
    return render(request,'Simulator/index.html')

def login(request):
    if request.method == "POST":
        pass
    else:
        return render(request, 'Simulator/login.html')

def start_simulator(request):
    if request.method == "POST":
        chapters = [{'order':1,'title':'Sentence Completion 1','questioncnt':4,'time':4},{'order':2,'title':'Sentence Completion 2','questioncnt':4,'time':4},{'order':3,'title':'Reading Comprehansion','questioncnt':5,'time':15},{'order':4,'title':'Restatement 1','questioncnt':3,'time':6},{'order':5,'title':'Restatement 2','questioncnt':3,'time':6},{'order':6,'title':'Sentence Completion 3','questioncnt':4,'time':4}]
        test = []
        questions = []
        for j in range(2):
            for i in range(4):
                order = i+1
                question = f'question {i+1}'
                answers = {'1':'answer 1','2':'answer 2','3':'answer 3','4':'answer 4'}
                correct = randint(1,4)
                toappend = {'order':order,'question':question,'answers': answers,'correct':correct}
                questions.append(toappend)

            chapters[j]['questions'] = questions
            questions = []
        
        return render(request,'Simulator/simulator.html',{
            'chapters':chapters
        })


    else:
        return render(request,'Simulator/simulator_prep.html')

def upload(request):
    if request.method == "POST":
        pass
    return render(request, 'Simulator/upload_test.html')