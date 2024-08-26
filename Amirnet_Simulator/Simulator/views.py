from django.shortcuts import render,redirect
from random import randint
from .models import *
import re,math
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

def save_test(request):
    if request.method == "POST":
        pass
    return render()

def save_test2(request):
    if request.method == "POST":
        questions = []
        answers = []
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.split('_')[1]  # Extract the question ID
                question = Question.objects.get(id=question_id)  # Fetch the question by ID
                question.desc = value.strip()  # Update the question text
                question.save()
            elif key.startswith('answer_'):
                answer_id = key.split('_')[1]  # Extract the answer ID
                answer = Answer.objects.get(id=answer_id)  # Fetch the answer by ID
                answer.desc = value.strip()  # Update the answer text
                answer.save()

        return redirect('your_next_view_name')  # Replace with your actual view name

    chapters = Chapter.objects.all()
    return render(request, 'Simulator/your_template.html', {'chapters': chapters})  # Replace with your actual template



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
    

    sections = [{'chapter_order':1,'sections':{'Sentence Completions':{},'Restatements':{},'Text 1':{},'Text 2':{}}},{'chapter_order':2,'sections':{'Sentence Completions':{},'Restatements':{},'Text 1':{},'Text 2':{}}}]
    for engpagenumber in englishpages:
        pagetext = pdfreader.pages[engpagenumber].extract_text().replace('  ','__')
        if pagetext.find('אנגלית - פרק ראשון') >= 0:
            chapter = 0
        else:
            chapter = 1
        if pagetext.find('Sentence Completions (') >= 0:
            sections[chapter]['sections']['Sentence Completions']['start'] = (engpagenumber, pagetext.find('Sentence Completions ('))
        elif pagetext.find('Restatements (') >= 0:
            sections[chapter]['sections']['Sentence Completions']['end'] = (engpagenumber, pagetext.find('Restatements ('))
            sections[chapter]['sections']['Restatements']['start'] = (engpagenumber, pagetext.find('Restatements ('))
        elif pagetext.find('Text II') >= 0:
            sections[chapter]['sections']['Text 1']['end'] = (engpagenumber, pagetext.find('Text II'))
            sections[chapter]['sections']['Text 2']['start'] = (engpagenumber, pagetext.find('Questions'))
        elif pagetext.find('Text I') >= 0:
            sections[chapter]['sections']['Restatements']['end'] = (engpagenumber, pagetext.find('Text I'))
            sections[chapter]['sections']['Text 1']['start'] = (engpagenumber, pagetext.find('Questions'))
        elif pagetext.find('עמוד ריק') >= 0:
            sections[chapter]['sections']['Text 2']['end'] = (engpagenumber, pagetext.find('עמוד ריק'))
    return sections

# def extract_questions_from_sections (pdfreader: PyPDF2.PdfReader, section_borders: list) -> list:
#     new_chapters = add_text_borders(pdfreader,section_borders)
#     cnt = 0

#     for chapter in new_chapters:
#         for section in chapter:
#             start_pointer = chapter[section]['start']
#             end_pointer = chapter[section]['end']
#             section_txt = []
#             if start_pointer[0] == end_pointer[0]:
#                 txt = pdfreader.pages[start_pointer[0]].extract_text()[start_pointer[1]:]
#                 section_txt.append(re.split('[1-9]?\d\.[^\n]',txt)[1:])
#                 # section_txt = pdfreader.pages[start_pointer[0]].extract_text()[start_pointer[1]:]
#             else:
#                 for pg in range(start_pointer[0],end_pointer[0]+1):
#                     if pg == end_pointer[0]:
#                         txt = pdfreader.pages[pg].extract_text()[:end_pointer[1]]
#                     elif pg == start_pointer[0]:
#                         txt = pdfreader.pages[pg].extract_text()[start_pointer[1]:]
#                     else:
#                         txt = pdfreader.pages[pg].extract_text()
#                     splt = re.split('[1-9]?\d\.[^\n]',txt)[1:]
#                     for x in range(len(splt)):
#                         splt[x] = splt[x].replace('\n', '')
#                     section_txt.append(splt)
            
            
#             section_list = []
#             for question_answers in section_txt:
#                 for splt in question_answers:
#                     section_list.append(re.split('\([1-9]\)',splt))
#             new_chapters[cnt][section]['full_questions'] = section_list
#         cnt += 1
    
#     cnt = 0
#     for chapter in new_chapters:
#         for section in chapter:
#             new_chapters[cnt][section]['questions'] = []
#             question_number = 1
#             for question_answer in new_chapters[cnt][section]['full_questions']:
                
#                 for i in range(len(question_answer)):
#                     if i == 0:
#                         new_chapters[cnt][section]['questions'].append({f'question_{question_number}':question_answer[i]})
#                     else:
#                         new_chapters[cnt][section]['questions'][question_number - 1][f'answer_{i}'] = question_answer[i]
#                 question_number += 1
#             # new_chapters[cnt][section]['questions'] = [question[0] for question in new_chapters[cnt][section]['full_questions']]
#             # new_chapters[cnt][section]['answers'] = [question[1:] for question in new_chapters[cnt][section]['full_questions']]
#         cnt += 1

#     return new_chapters

def extract_questions_from_sections(pdfreader: PyPDF2.PdfReader, section_borders: list) -> list:
    new_chapters = add_text_borders(pdfreader, section_borders)
    cnt = 0

    for chapter in new_chapters:
        for section in chapter['sections']:
            start_pointer = chapter['sections'][section]['start']
            end_pointer = chapter['sections'][section]['end']
            section_txt = []
            if start_pointer[0] == end_pointer[0]:
                txt = pdfreader.pages[start_pointer[0]].extract_text()[start_pointer[1]:]
                section_txt.append(re.split('[1-9]?\d\.[^\n]', txt)[1:])
            else:
                for pg in range(start_pointer[0], end_pointer[0] + 1):
                    if pg == end_pointer[0]:
                        txt = pdfreader.pages[pg].extract_text()[:end_pointer[1]]
                    elif pg == start_pointer[0]:
                        txt = pdfreader.pages[pg].extract_text()[start_pointer[1]:]
                    else:
                        txt = pdfreader.pages[pg].extract_text()
                    splt = re.split('[1-9]?\d\.[^\n]', txt)[1:]
                    for x in range(len(splt)):
                        splt[x] = splt[x].replace('\n', '')
                    section_txt.append(splt)

            section_list = []
            question_id = 1  # Start question ID
            for question_answers in section_txt:
                for splt in question_answers:
                    section_list.append(re.split('\([1-9]\)', splt))
            
            new_chapters[cnt]['sections'][section]['full_questions'] = section_list
            new_chapters[cnt]['sections'][section]['questions'] = []
            
            for question_answer in new_chapters[cnt]['sections'][section]['full_questions']:
                question_dict = {'id': f'{cnt+1}-{question_id}', 'question': question_answer[0]}  # Add unique ID to the question
                for i in range(1, len(question_answer)):
                    question_dict[f'answer_{i}'] = {'id': f'{cnt+1}-{question_id}-{i}', 'text': question_answer[i]}  # Add unique ID to each answer
                new_chapters[cnt]['sections'][section]['questions'].append(question_dict)
                question_id += 1
        cnt += 1

    return new_chapters


def add_text_borders(pdfreader: PyPDF2.PdfReader, section_borders: list) -> list:
    new_section_borders = section_borders
    pointer = 0
    for chapter in new_section_borders:
        for section in ['Text 1','Text 2']:
            txt_start = chapter['sections'][section]['start'][1]
            txt_end = pdfreader.pages[chapter['sections'][section]['start'][0]].extract_text().rfind('Questions')
            new_section_borders[pointer]['sections'][section]['text_start'] = txt_start
            new_section_borders[pointer]['sections'][section]['text_end'] = txt_end
            new_section_borders[pointer]['sections'][section]['text'] = pdfreader.pages[chapter['sections'][section]['start'][0]].extract_text()[txt_start+len('Questions')+8:txt_end]
            new_section_borders[pointer]['sections'][section]['start'] = (chapter['sections'][section]['start'][0],txt_end+len('Questions')+1)
            if section == 'Text 2':
                print(txt_start,txt_end)
        pointer += 1
    
    return new_section_borders
    