# chat/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)
    
    @action(detail=False, methods=['POST'])
    def create_or_get_conversation(self, request):
        participant_ids = request.data.get('participant_ids', [])
        participant_ids.append(request.user.id)
        
        # Si es una conversación de grupo
        if len(participant_ids) > 2:
            conversation = Conversation.objects.create(
                name=request.data.get('name', 'Group Chat'),
                is_group=True
            )
            conversation.participants.set(participant_ids)
            return Response(self.get_serializer(conversation).data)
        
        # Para conversación entre dos personas
        conversations = Conversation.objects.filter(is_group=False)
        for conv in conversations:
            if set(conv.participants.values_list('id', flat=True)) == set(participant_ids):
                return Response(self.get_serializer(conv).data)
        
        # Si no existe, crear nueva conversación
        conversation = Conversation.objects.create(is_group=False)
        conversation.participants.set(participant_ids)
        return Response(self.get_serializer(conversation).data)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            return Message.objects.filter(conversation_id=conversation_id)
        return Message.objects.none()
    
    def perform_create(self, serializer):
        conversation_id = self.request.data.get('conversation_id')
        conversation = Conversation.objects.get(id=conversation_id)
        serializer.save(sender=self.request.user, conversation=conversation)
        
        # Marcar como leído para el remitente
        message = serializer.instance
        message.read_by.add(self.request.user)
    
    @action(detail=True, methods=['POST'])
    def mark_as_read(self, request, pk=None):
        message = self.get_object()
        message.read_by.add(request.user)
        return Response({'status': 'message marked as read'})