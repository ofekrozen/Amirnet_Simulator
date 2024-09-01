from django.shortcuts import render,redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UserRegistrationForm, EmailLoginForm
from random import randint
from .models import *
import re,math
import PyPDF2

# Create your views here.

@login_required('login')
def index(request):
    return render(request,'Simulator/index.html')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to the login page after successful registration
    else:
        form = UserRegistrationForm()
    
    return render(request, 'Simulator/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()  # Get the authenticated user
            login(request, user)
            return redirect('index')  # Redirect to the home page after successful login
        else:
            form.add_error(None, 'Invalid email or password')
    else:
        form = EmailLoginForm()

    return render(request, 'Simulator/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to the login page after logout

@login_required(login_url='login')
def start_simulator(request):
    if request.method == "POST":
        subjects = {'Sentence Completions' : Subject.objects.get(subject_desc = 'Sentence Completions'), 'Restatements':Subject.objects.get(subject_desc = 'Restatements'),'Reading Comprehansions' : Subject.objects.get(subject_desc = 'Reading Comprehension')}
        ## Basic Layout needed
        chapters = [{'order':1,'subject':subjects['Sentence Completions'],'title':'Sentence Completion 1','questioncnt':4,'time':4},{'order':2,'subject':subjects['Sentence Completions'],'title':'Sentence Completion 2','questioncnt':4,'time':4},{'order':3,'subject':subjects['Reading Comprehansions'],'title':'Reading Comprehansion','questioncnt':5,'time':15},{'order':4,'subject':subjects['Restatements'],'title':'Restatement 1','questioncnt':3,'time':6},{'order':5,'subject':subjects['Restatements'],'title':'Restatement 2','questioncnt':3,'time':6},{'order':6,'subject':subjects['Sentence Completions'],'title':'Sentence Completion 3','questioncnt':4,'time':4}]
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

def generate_subject_question(irrelevant_questions: list[Question], subject:Subject) -> Question:
    pass

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def upload(request):
    if request.method == "POST":
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            file_name = str(uploaded_file.name).split('.pdf')[0]
            print(f'Uploaded file: {file_name}')
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            english_tests = extract_questions_from_sections(pdf_reader,extract_english_sections_borders(pdf_reader))

            return render(request, 'Simulator/upload_test.html',{
                'tests': english_tests,
                'file_name':file_name
            })
    return render(request, 'Simulator/upload_test.html')

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def save_test(request):
    if request.method == "POST":
        current_chapter = None
        current_question = None
        last_test = Test.objects.last()
        last_subject = None
        file_name = "Generic Test"
        for key, value in request.POST.items():
            if key.startswith('file_name'):
                file_name = value.strip()
            elif key.startswith('test_order'):
                last_test = Test.objects.create(title=f'{file_name} english chapter {value.strip()}')
            elif key.startswith('section_subject'):
                chapter_order = key.split('-')[1]
                if 'Text' in value.strip():
                    last_subject = Subject.objects.get(subject_desc = 'Reading Comprehension')
                else:
                    last_subject = Subject.objects.get(subject_desc = value.strip())
                current_chapter = Chapter.objects.create(title=f'{last_test.title}-{value.strip()}',subject=last_subject)
                test_chapter = TestChapter.objects.create(test=last_test, chapter = current_chapter, order=chapter_order)
            elif key.startswith('text_'):
                text = value.strip()
                current_chapter.text = text
                current_chapter.save()
            elif key.startswith('question_'):
                q_order = int(str(key.split('_')[-1]).split('-')[-1])
                question_desc = value.strip()
                correct_ans = 0
                # print(f"{current_chapter.title} - {q_order}")
                current_question = Question.objects.create(chapter=current_chapter, order = q_order, desc = question_desc, correct_answer = correct_ans)
            elif key.startswith('answer_'):
                ans_order = str(key.split('_')[-1]).split('-')[-1]
                ans_desc = value.strip()
                current_answer = Answer.objects.create(question=current_question, order = ans_order, desc = ans_desc)
            elif key.startswith('correct_'):
                current_question.correct_answer = int(str(value.strip()).split('-')[3])
                current_answer.question = current_question
                current_question.save()
                current_answer.save()

        return redirect('index') # render(request,'Simulator/index.html')

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
    

    sections = [{'test_order':1,'sections':{'Sentence Completions':{},'Restatements':{},'Text 1':{},'Text 2':{}}},{'test_order':2,'sections':{'Sentence Completions':{},'Restatements':{},'Text 1':{},'Text 2':{}}}]    
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


def extract_questions_from_sections(pdfreader: PyPDF2.PdfReader, section_borders: list) -> list:
    new_chapters = add_text_borders(pdfreader, section_borders)
    cnt = 0

    for chapter in new_chapters:
        section_cnt = 1
        for section in chapter['sections']:
            chapter['sections'][section]['section_order'] = section_cnt
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
                question_dict = {'id': f'{cnt+1}-{section_cnt}-{question_id}', 'question': question_answer[0]}  # Add unique ID to the question
                for i in range(1, len(question_answer)):
                    question_dict[f'answer_{i}'] = {'id': f'{cnt+1}-{section_cnt}-{question_id}-{i}', 'text': question_answer[i]}  # Add unique ID to each answer
                new_chapters[cnt]['sections'][section]['questions'].append(question_dict)
                question_id += 1
            section_cnt += 1
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
    