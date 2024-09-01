from django.contrib.auth.models import AbstractUser
from django.db import models


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

class TestChapter(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name= 'chapter_order')
    order = models.PositiveIntegerField(help_text="Order of the chapter in the test")

    class Meta:
        unique_together = ('test', 'chapter')
        ordering = ['test','order']

    def __str__(self):
        return f"{self.chapter.title} in {self.test.title} (Order: {self.order})"

class StudentAnswers(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='answered_tests')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answered_questions')
    answer_number = models.IntegerField(choices=[
        (0,'0'),(1,'1'),(2,'2'),(3,'3'),(4,'4')
    ])

    def is_correct(self):
        return self.answer_number == self.question.correctanswer
    
    def get_full_question(self) -> dict:
        answers = self.question.related_answers.all()
        return {
            'question_desc':self.question.desc, 
            'answer 1': answers[0], 
            'answer 2': answers[1], 
            'answer 3': answers[2], 
            'answer 4': answers[3]
            }
    
    def get_full_answer(self) -> Answer:
        answers = self.question.related_answers.all()
        if self.answer_number > 0:
            return answers[self.answer_number - 1]
        else:
            return None
    
    class Meta:
        ordering = ['student','test','question']