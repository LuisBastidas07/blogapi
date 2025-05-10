from django.db import models

# Create your models here.
class IdentificationType(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
        
class Student(models.Model):
    identification_type = models.ForeignKey(IdentificationType, on_delete=models.PROTECT)
    identification = models.CharField(max_length=20)    
    name = models.CharField(max_length=100)
    pub_date = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return self.identification + "-" + self.name
