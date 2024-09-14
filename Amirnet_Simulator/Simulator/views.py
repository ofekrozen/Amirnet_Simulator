from django.shortcuts import render,redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import UserRegistrationForm, EmailLoginForm
from random import randint
from .models import *
import re,math,random
import PyPDF2
import json

# Create your views here.

@login_required(login_url='login')
def index(request):
    user = request.user
    simulators = StudentSimulator.objects.filter(student = user).all()
    return render(request,'Simulator/index.html',{
        'simulators' : simulators
    })


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
def delete_simulator(request):
    if request.method =="POST":
        user = request.user
        for key,value in request.POST.items():
            if key == "simulator_id":
                simulator_to_delete = StudentSimulator.objects.get(id = int(value), student = user)
                simulator_to_delete.delete()
    return redirect('index')

@login_required(login_url='login')
def analyze_simulator(request):
    if request.method == "POST":
        simulator_to_analyze = None
        for key,value in request.POST.items():
            if key == "simulator_id":
                simulator_to_analyze = StudentSimulator.objects.get(id = int(value))
        if simulator_to_analyze == None:
            return redirect('index')
        else:
            chapter_questions = {'Sentence Completions':[], 'Restatements':[], 'Reading Comprehension' : []}
            for subject in chapter_questions:
                chapter_questions[subject] = list(StudentAnswers.objects.filter(simulator = simulator_to_analyze, question__chapter__subject__subject_desc = subject).all())
            # questions = list(StudentAnswers.objects.filter(simulator = simulator_to_analyze).all())
            return render(request, 'Simulator/analyze_simulator.html',{
                'simulator' : simulator_to_analyze,
                'chapter_questions' : chapter_questions
                # 'questions' : questions
            })
    return redirect('index')

@login_required(login_url = 'login')
def finish_simulator(request):
    user = request.user
    if request.method == "POST":
        answers = {}
        chapters = {}
        for key, value in request.POST.items():
            print(f"key: {key}, value: {value}")
            if key == "student_answers":
                answers = json.loads(value)
            elif key == "chapters_submit":
                chapters = (value)
        student_simulator = StudentSimulator.objects.create(student = user)
        for q_id in answers:
            current_question = Question.objects.get(id = int(q_id))
            StudentAnswers.objects.create(student = user, simulator = student_simulator, question = current_question, answer_number = int(answers[q_id]))
        return redirect('index')
    return redirect('index')

@login_required(login_url='login')
def start_simulator(request):
    if request.method == "POST":
        user = request.user
        subjects = {'Sentence Completions' : Subject.objects.get(subject_desc = 'Sentence Completions'), 'Restatements':Subject.objects.get(subject_desc = 'Restatements'),'Reading Comprehansions' : Subject.objects.get(subject_desc = 'Reading Comprehension')}
        ## Basic Layout needed
        chapters = [
            {'order':1,
             'subject':subjects['Sentence Completions'],
             'title':'Sentence Completion 1',
             'questioncnt':subjects['Sentence Completions'].question_cnt,
             'time':subjects['Sentence Completions'].time}
             ,{'order':2,
               'subject':subjects['Sentence Completions'],
               'title':'Sentence Completion 2',
               'questioncnt':subjects['Sentence Completions'].question_cnt,
               'time':subjects['Sentence Completions'].time},
               {'order':3,
                'subject':subjects['Reading Comprehansions'],
                'title':'Reading Comprehension',
                'questioncnt': subjects['Reading Comprehansions'].question_cnt,
                'time':subjects['Reading Comprehansions'].time},
                {'order':4,
                 'subject':subjects['Restatements'],
                 'title':'Restatement 1',
                 'questioncnt':subjects['Restatements'].question_cnt,
                 'time':subjects['Restatements'].time},
                 {'order':5,
                  'subject':subjects['Restatements'],
                  'title':'Restatement 2',
                  'questioncnt':subjects['Restatements'].question_cnt,
                  'time':subjects['Restatements'].time},
                  {'order':6,
                   'subject':subjects['Sentence Completions'],
                   'title':'Sentence Completion 3',
                   'questioncnt':subjects['Sentence Completions'].question_cnt,
                   'time':subjects['Sentence Completions'].time}]
        
        # Generate the questions for each section
        user_answered_questions = generate_user_answered_questions(user)
        for i in range(len(chapters)):
            current_subject = chapters[i]['subject']
            questions = []
            # The user's answered questions:
            answered_subject_questions = user_answered_questions[current_subject.subject_desc]
            generated_text_chapter = None
            if current_subject.subject_desc == 'Reading Comprehension':
                generated_text_chapter = get_unanswered_text_section(answered_subject_questions)
                chapters[i]['text'] = generated_text_chapter.text
            for j in range(chapters[i]['questioncnt']):
                order = j+1
                question = generate_subject_question(answered_subject_questions,current_subject,generated_text_chapter)
                fictive_student_answer = StudentAnswers(question = question, student = user, answer_number = 0)
                user_answered_questions[current_subject.subject_desc].append(fictive_student_answer)
                related_answers = Answer.objects.filter(question = question).all()
                
                answers = {}
                for answer in related_answers:
                    answers[f'{answer.order}'] = answer
                toappend = {'order':order,'question':question,'answers':answers}
                questions.append(toappend)
            chapters[i]['questions'] = questions

        return render(request,'Simulator/simulator.html',{
            'chapters':chapters
        })


    else:
        return render(request,'Simulator/simulator_prep.html')

"""
### Return a Question within the questions of the relevant subjects that were not answered yet
### If there is no such a Question, return a question that was answered wrong
### If all answeres were correct, return a random question
"""
def generate_subject_question(answered_questions: list[StudentAnswers], subject:Subject, chapter:Chapter = None) -> Question:
    if chapter is None:
        all_subject_questions = Question.objects.filter(chapter__subject = subject).all()
    else:
        all_subject_questions = Question.objects.filter(chapter = chapter).all()
    # Create answered Questions list
    irrelevant_answer_questions = [aq for aq in answered_questions]
    irrelevant_questions = [aq.question for aq in answered_questions]
    for question in all_subject_questions:
        if question not in irrelevant_questions:
            return question
    
    # If there was no unanswered question, return the first false one.
    correct_answered_questions = []
    for aq in irrelevant_answer_questions:
        if aq.question.chapter.subject == subject:
            if not aq.is_correct():
                return aq.question
            else:
                correct_answered_questions.append(aq.question)

    # If there were no wrong answers, try to return a correct answer.
    if len(correct_answered_questions) > 0:
        return random.choice(correct_answered_questions)
    return None

"""
### Return an unanswered text section
"""
def get_unanswered_text_section (answered_questions: list[StudentAnswers]) -> Chapter:
    text_subject = Subject.objects.get(subject_desc = "Reading Comprehension")
    all_text_chapters = Chapter.objects.filter(subject = text_subject).all()
    # Create answered text chapters list
    answered_text_chapters = []
    answered_text_questions = []
    for aq in answered_questions:
        q = aq.question
        chapter = q.chapter
        if chapter.subject == text_subject:
            answered_text_questions.append(aq)
            if chapter not in answered_text_chapters:
                answered_text_chapters.append(chapter)
    
    chapter_to_ret = None
    
    for txt_c in all_text_chapters:
        if txt_c not in answered_text_chapters:
            chapter_to_ret = txt_c
            break
    if chapter_to_ret is not None:
        return chapter_to_ret
    
    # If all text chapters were done, return the worst one
    to_find_worst_chapter = []
    for txt_c in answered_text_chapters:
        to_dict = {}
        to_dict['chapter'] = txt_c
        total,correct = (0,0)
        for aq in answered_text_questions:
            if aq.question.chapter == txt_c:
                total+=1
                if aq.is_correct():
                    correct += 1
        to_dict['success_rate'] = correct*100/total
        to_find_worst_chapter.append(to_dict)
    min_rate = 999
    min_chapter = None
    for chapter_dict in to_find_worst_chapter:
        if chapter_dict['success_rate'] < min_rate:
            min_rate = chapter_dict['success_rate']
            min_chapter = chapter_dict['chapter']
    return min_chapter


"""
### Return answered questions in the following format: {'Sentance Completions':[],'Restatements':[],'Reading Comprehension':[]}
"""
def generate_user_answered_questions(user:User) -> dict: 
    answered_questions = StudentAnswers.objects.filter(student = user).all()
    to_dict = {'Sentence Completions':[],'Restatements':[],'Reading Comprehension':[]}
    for sa in answered_questions:
        for key in to_dict.keys():
            if sa.question.chapter.subject.subject_desc == key:
                to_dict[key].append(sa)
    return to_dict

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def edit_uploaded_test(request):
    if request.method == "POST":
        test_to_edit = None
        for key,value in request.POST.items():
            if key.strip() == "test_id":
                test_to_edit = Test.objects.get(id = int(value.strip()))
        if test_to_edit is not None:
            chapters = test_to_edit.get_chapters()
            context = {'test_to_edit':test_to_edit,'chapters':chapters}
            return render(request,'Simulator/edit_test.html',context)
    uploaded_tests = Test.objects.all()
    return render(request,'Simulator/edit_test_selection.html',{
        'uploaded_tests': uploaded_tests
    })

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def save_edited_test(request):
    if request.method == "POST":
        chapter = None
        question = None
        answer = None
        for key,value in request.POST.items():
            if key.startswith('text_'):
                chapter = Chapter.objects.get(id = key.strip().split('_')[-1])
                chapter.text = value.strip()
                chapter.save()
            if key.startswith('question_'):
                question = Question.objects.get(id = key.strip().split('_')[-1])
                question.desc = value.strip()
                question.save()
            if key.startswith('answer_'):
                answer = Answer.objects.get(id = key.strip().split('_')[-1])
                answer.desc = value.strip()
                answer.save()
            if key.startswith('answerinput_'):
                question = Question.objects.get(id = key.strip().split('_')[-1])
                answer = Answer.objects.get(id = int(value.strip()))
                question.correct_answer = answer.order
                question.save()
        print('Test Saved Successfully!')
    else:
        print('Did not save')
    return redirect('edit_uploaded_test')
    

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
            if current_chapter is not None and current_chapter.subject == Subject.objects.get(subject_desc = 'Reading Comprehension'):
                print(f'Current chapter: {current_chapter}')
                print(f'Current question: {current_question}')
                print(f'Current answer: {current_answer}')
                print("********")

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
                question_dict = {'id': f'{cnt+1}-{section_cnt}-{question_id}', 'question': question_answer[0].replace('  ',' ___ ')}  # Add unique ID to the question
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
    