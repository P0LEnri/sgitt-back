from django.db import models
from django.conf import settings

class Conversation(models.Model):
    name = models.CharField(max_length=255, blank=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    is_group = models.BooleanField(default=False)
    
    def clean(self):
        if self.is_group and self.participants.count() > 7:  # ejemplo de límite
            return print('Un grupo no puede tener más de 7 participantes')
        
    def mark_all_read_for_user(self, user):
        self.messages.exclude(read_by=user).update(read_by=user)
    
    def __str__(self):
        if self.is_group:
            return self.name
        return f"Conversation between {', '.join(user.email for user in self.participants.all())}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_messages', blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['conversation', 'timestamp']),
        ]
    
    def __str__(self):
        return f'{self.sender.email}: {self.content[:50]}'