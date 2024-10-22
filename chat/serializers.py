# chat/serializers.py
from rest_framework import serializers
from .models import Room, Message

class MessageSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'user_email', 'content', 'timestamp']

class RoomSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'messages', 'created_at']