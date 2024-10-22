from rest_framework import serializers
from .models import Requisito, PalabraClave, Propuesta

class RequisitoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requisito
        fields = ['id', 'descripcion']

class PalabraClaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PalabraClave
        fields = ['id', 'palabra']

class PropuestaSerializer(serializers.ModelSerializer):
    
    requisitos = RequisitoSerializer(many=True, read_only=True)
    # print('PropuestaSerializer',requisitos)
    palabras_clave = PalabraClaveSerializer(many=True, read_only=True)
    autor = serializers.ReadOnlyField(source='autor.email')

    class Meta:
        model = Propuesta
        fields = ['id', 'nombre', 'objetivo', 'cantidad_alumnos', 'cantidad_profesores', 
                  'requisitos', 'palabras_clave', 'autor', 'fecha_creacion', 'fecha_actualizacion']

    def create(self, validated_data):
        requisitos_data = self.context['request'].data.get('requisitos', [])
        palabras_clave_data = self.context['request'].data.get('palabras_clave', [])
        
        propuesta = Propuesta.objects.create(**validated_data)
        
        for requisito in requisitos_data:
            req, _ = Requisito.objects.get_or_create(descripcion=requisito)
            propuesta.requisitos.add(req)
        
        for palabra in palabras_clave_data:
            pc, _ = PalabraClave.objects.get_or_create(palabra=palabra)
            propuesta.palabras_clave.add(pc)
        
        return propuesta