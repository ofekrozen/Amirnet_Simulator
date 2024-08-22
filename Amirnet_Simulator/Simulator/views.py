from django.shortcuts import render
from random import randint
from .models import *
import re
import PyPDF2

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
        uploaded_file = request.FILES['file']
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        english_chapters = extract_questions_from_sections(pdf_reader,extract_english_sections_borders(pdf_reader))

        return render(request, 'Simulator/upload_test.html',{
            'chapters': english_chapters
        })
    return render(request, 'Simulator/upload_test.html')


def extract_english_sections_borders (pdfreader: PyPDF2.PdfReader)-> list:
    # pdfreader = PyPDF2.PdfReader(pdfile)
    englishpages = []
    '''
    ########
    # Creating a list of the English pages only
    ########
    '''
    for pagenumber in range(len(pdfreader.pages)):
        if pdfreader.pages[pagenumber].extract_text().find('אנגלית - ') >= 0:
            englishpages.append(pagenumber)
    
    '''
    #######
    # For every English chapter, seperate each section of the page
    #######
    '''

    sections = [{'Sentence Completions':{},'Restatements':{},'Text 1':{},'Text 2':{}},{'Sentence Completions':{},'Restatements':{},'Text 1':{},'Text 2':{}}]
    for engpagenumber in englishpages:
        pagetext = pdfreader.pages[engpagenumber].extract_text().replace('  ','__')
        if pagetext.find('אנגלית - פרק ראשון') >= 0:
            chapter = 0
        else:
            chapter = 1
        if pagetext.find('Sentence Completions (') >= 0:
            sections[chapter]['Sentence Completions']['start'] = (engpagenumber, pagetext.find('Sentence Completions ('))
        elif pagetext.find('Restatements (') >= 0:
            sections[chapter]['Sentence Completions']['end'] = (engpagenumber, pagetext.find('Restatements ('))
            sections[chapter]['Restatements']['start'] = (engpagenumber, pagetext.find('Restatements ('))
        elif pagetext.find('Text II') >= 0:
            sections[chapter]['Text 1']['end'] = (engpagenumber, pagetext.find('Text II'))
            sections[chapter]['Text 2']['start'] = (engpagenumber, pagetext.find('Questions',300))
        elif pagetext.find('Text I') >= 0:
            sections[chapter]['Restatements']['end'] = (engpagenumber, pagetext.find('Text I'))
            sections[chapter]['Text 1']['start'] = (engpagenumber, pagetext.find('Questions',300))
        elif pagetext.find('עמוד ריק') >= 0:
            sections[chapter]['Text 2']['end'] = (engpagenumber, pagetext.find('עמוד ריק'))
    return sections

def extract_questions_from_sections (pdfreader: PyPDF2.PdfReader, section_borders: list) -> list:
    new_chapters = section_borders
    cnt = 0
    for chapter in section_borders:
        for section in chapter:
            start_pointer = chapter[section]['start']
            end_pointer = chapter[section]['end']
            section_txt = ""
            if start_pointer[0] == end_pointer[0]:
                section_txt = pdfreader.pages[start_pointer[0]].extract_text()[start_pointer[1]:]
            else:
                start_page_txt = pdfreader.pages[start_pointer[0]].extract_text()[start_pointer[1]:]
                end_page_txt = pdfreader.pages[end_pointer[0]].extract_text()[:end_pointer[1]]
                start_page_questions = re.split('[1-9]?\d\.',start_page_txt)[1:]
                end_page_questions = re.split('[1-9]?\d\.',end_page_txt)[1:]
                section_txt = start_page_questions + end_page_questions
            
            section_list = []
            for question_answers in section_txt:
                section_list.append(re.split('\([1-9]\)',question_answers.replace('\n','')))
            new_chapters[cnt][section]['full_questions'] = section_list
        cnt += 1
    
    cnt = 0
    for chapter in new_chapters:
        for section in chapter:
            new_chapters[cnt][section]['questions'] = [question[0] for question in new_chapters[cnt][section]['full_questions']]
            new_chapters[cnt][section]['answers'] = [question[1:] for question in new_chapters[cnt][section]['full_questions']]

    return new_chapters