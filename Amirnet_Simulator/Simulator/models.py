from django.contrib.auth.models import AbstractUser
from django.db import models
import math


class User(AbstractUser):
    GENDER_CHOICES = [
        ('M','Male'),
        ('F','Female'),
        ('O','Other')
    ]

    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    email = models.EmailField(unique=True)
    joining_date = models.DateField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','first_name','last_name','gender']

class Subject(models.Model):
    # ID
    subject_desc = models.CharField(max_length=50)
    time = models.FloatField()
    question_cnt = models.PositiveIntegerField()

    def __str__(self) -> str:
        return self.subject_desc

class Chapter(models.Model):
    # ID
    title = models.CharField(max_length=30)
    subject = models.ForeignKey(Subject,on_delete=models.CASCADE, related_name='related_chapters')
    text = models.CharField(max_length= 1000,null=True, blank=True)

    def __str__(self) -> str:
        return self.title
    
    def get_questions(self) -> list:
        return list(Question.objects.filter(chapter = self).all())

class Question(models.Model):
    # ID
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='related_questions')
    order = models.IntegerField()
    desc = models.CharField(max_length=255)
    correct_answer = models.IntegerField()

    class Meta:
        unique_together = ('chapter','order')
        ordering = ['chapter','order']
    
    def __str__(self) -> str:
        return f"{self.chapter} - question number {self.order}"
    
    def get_answers(self) -> list:
        return list(Answer.objects.filter(question = self).all())

class Answer(models.Model):
    # ID
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='related_answers')
    order = models.IntegerField()
    desc = models.CharField(max_length=255)

    class Meta:
        ordering = ['question','order']
    
    def __str__(self) -> str:
        return f"{self.question} - answer number {self.order}"

class Test(models.Model):
    # ID
    title = models.CharField(max_length=30)
    create_date = models.DateField(auto_now_add=True)
    chapters = models.ManyToManyField(Chapter, through='TestChapter')

    def __str__(self) -> str:
        return self.title
    
    def get_chapters(self) -> list:
        to_return = []
        for test_chapter in TestChapter.objects.filter(test = self):
            to_return.append(test_chapter.chapter)
        return to_return

class TestChapter(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name= 'chapter_order')
    order = models.PositiveIntegerField(help_text="Order of the chapter in the test")

    class Meta:
        unique_together = ('test', 'chapter')
        ordering = ['test','order']

    def __str__(self):
        return f"{self.chapter.title} in {self.test.title} (Order: {self.order})"

class StudentSimulator(models.Model):
    # ID
    student = models.ForeignKey(User,on_delete=models.CASCADE,related_name='simulators')
    simulator_number = models.PositiveIntegerField()
    date_taken = models.DateField(auto_now_add=True)
    
    def __str__(self) -> str:
        return f"Simulator number {self.simulator_number} from {self.date_taken}"
    
    def save(self, *args, **kwargs):
        # Check if this is a new object (no primary key yet)
        if not self.pk:
            # Get the last simulator_number for the student
            last_simulator = StudentSimulator.objects.filter(student=self.student).order_by('simulator_number').last()
            
            # If a previous simulator exists, increment its simulator_number by 1, otherwise set it to 1
            if last_simulator:
                self.simulator_number = last_simulator.simulator_number + 1
            else:
                self.simulator_number = 1
        
        # Call the original save method
        super(StudentSimulator, self).save(*args, **kwargs)
    def get_success_rate(self):
        all_questions = list(StudentAnswers.objects.filter(simulator = self).all())
        correct_questions = []
        for q in all_questions:
            if q.is_correct():
                correct_questions.append(q)
        return f"{math.ceil(len(correct_questions)*100 / len(all_questions))}%"

class StudentAnswers(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    simulator = models.ForeignKey(StudentSimulator, on_delete=models.CASCADE, related_name='questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answered_questions')
    answer_number = models.IntegerField(choices=[
        (0,'0'),(1,'1'),(2,'2'),(3,'3'),(4,'4')
    ])

    def is_correct(self):
        return self.answer_number == self.question.correct_answer
    
    def get_full_question(self) -> dict:
        answers = list(Answer.objects.filter(question = self.question).all())
        return {
            'question_desc':self.question.desc, 
            'answer 1': answers[0], 
            'answer 2': answers[1], 
            'answer 3': answers[2], 
            'answer 4': answers[3]
            }
    
    def get_my_answer(self) -> Answer:
        return Answer.objects.get(question = self.question, order = self.answer_number)

    def get_answer_by_number(self,number) -> Answer:
        return Answer.objects.get(question = self.question, order = number)
    
    def get_all_answers(self):
        return list(Answer.objects.filter(question = self.question).all())
    
    class Meta:
        ordering = ['student','question']