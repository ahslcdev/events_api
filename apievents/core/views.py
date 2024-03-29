from django.http.response import JsonResponse
from django.shortcuts import render
from .serializers import EventSerializer, EventUserSerializer, LogoutSerializer, UserSerializer, PersonalUserSerializer, ConviteSerializer, EventPresenceSerializer
from .models import Event, EventUser, User, ConviteEvento
from django.db.models import F
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
# Create your views here.


def index(request):
    if request.method == 'GET':
        search = request.GET.get('search')
        # start_time = request.GET.get('start_time')
        # finish_time = request.GET.get('finish_time')
        if search:
            serializer = EventSerializer(Event.objects.filter(
                title__contains=request.GET.get('search'), private=False), many=True)
        else:
            serializer = EventSerializer(
                Event.objects.filter(private=False), many=True)
        return JsonResponse(serializer.data, safe=False)
    return JsonResponse({}, safe=False)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def events(request):
    if request.method == 'POST':
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            event = Event.objects.create(
                description=request.data['description'],
                start_time=request.data['start_time'],
                finish_time=request.data['finish_time'],
                localidade=request.data['localidade'],
                title=request.data['title'],
                capacity=request.data['capacity'],
                cep=request.data['cep'],
                bairro=request.data['bairro'],
                logradouro=request.data['logradouro'],
                numero=request.data['numero'],
                uf=request.data['uf'],
                complemento=request.data['complemento'],
                date_start=request.data['date_start'],
                date_finish=request.data['date_finish'],
                user_owner=request.user
            )
        return JsonResponse(serializer.data, safe=False)
    return JsonResponse({"events": "events"}, safe=False)


@api_view(['GET'])
def events_show(request):
    if request.method == 'GET':
        serializer = EventSerializer(
            Event.objects.filter(private=False), many=True)
        return JsonResponse(serializer.data, safe=False)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def events_owner(request):
    if request.method == 'GET':
        serializer = EventSerializer(Event.objects.filter(
            user_owner=request.user.id), many=True)
        return JsonResponse(serializer.data, safe=False)


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def events_confirmed(request):
    if request.method == 'GET':
        eventos = EventUser.objects.filter(
            id_user=request.user.id).values('id_event')
        # serializer = EventPresenceSerializer(Event.objects.filter(id__in=eventos), many=True)
        serializer = EventUserSerializer(EventUser.objects.filter(
            id_user=request.user.id), many=True)
        return JsonResponse(serializer.data, safe=False)


@permission_classes([IsAuthenticated])
@api_view(['PUT', 'GET'])
def edit_event(request, pk):
    if request.method == 'GET':
        serializer = EventSerializer(Event.objects.filter(id=pk), many=True)
        serializer.data[0]['total'] = EventUser.objects.filter(
            id_event=pk).count()
        # serializer.data[0]['status'] = True if EventUser.objects.filter(id_user=request.user).first() else False
        return JsonResponse(serializer.data, safe=False)
    if str(request.user) != 'AnonymousUser':
        if request.method == 'PUT':
            serializer = EventSerializer(
                Event.objects.filter(id=pk).first(), data=request.data)
            if serializer.is_valid():
                serializer.save()
            return JsonResponse(serializer.data, safe=False)
    # return JsonResponse({"events":"events"}, safe=False)


@permission_classes([IsAuthenticated])
@api_view(['DELETE'])
def delete_event(request, pk):
    if request.method == 'DELETE':
        Event.objects.filter(id=pk).first().delete()
        serializer = EventSerializer(Event.objects.filter(
            user_owner=request.user), many=True)
        return JsonResponse(serializer.data, safe=False)


@api_view(['POST', 'GET'])
def user(request):
    if request.method == 'GET':
        serializer = UserSerializer(User.objects.all(), many=True)
        return JsonResponse(serializer.data, safe=False)
    if request.method == 'POST':
        if User.objects.filter(username=request.data['username']).first():
            return JsonResponse({"message": "Este usuário já está cadastrado!"}, safe=False)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return JsonResponse(serializer.data, safe=False)


@permission_classes([IsAuthenticated])
@api_view(['POST', 'GET'])
def users_show(request):
    if request.method == 'GET':
        # user_not_event = EventUser.objects.filter().exclude(id_user=request.user)
        serializer = PersonalUserSerializer(
            User.objects.filter().exclude(id=request.user.id), many=True)
        return JsonResponse(serializer.data, safe=False)


@permission_classes([IsAuthenticated])
def delete_user(request, pk):
    if request.method == 'DELETE':
        serializer = UserSerializer(User.objects.filter(id=pk).first())
        User.objects.filter(id=pk).first().delete()
        return JsonResponse(serializer.data, safe=False)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def join_event(request):
    if request.method == 'POST':
        if EventUser.objects.filter(id_event=request.data['id']).count() < Event.objects.filter(id=request.data['id']).first().capacity:
            if request.data['status']:
                if EventUser.objects.filter(id_user=request.user, id_event=request.data['id']).exists():
                    message = "Você já confirmou presença nesse evento."
                    return JsonResponse({"message": message}, safe=False)
                ConviteEvento.objects.filter(
                    id_event=request.data['id'],
                    id_user=request.user).update(status=False)
            event_join = EventUser.objects.create(
                id_user=request.user, id_event=Event.objects.filter(id=request.data['id']).first())
            serializer = EventUserSerializer(event_join)
            message = "Presença confirmada! Não esqueça da mascara e das recomendações dos orgãos de saúde."
            return JsonResponse({"message": message}, safe=False)
        else:
            return JsonResponse({"message": "O evento atingiu o número máximo de participantes!"}, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def events_invite(request):
    if request.method == 'POST':
        event = Event.objects.filter(id=request.data['event']).first()
        for i in request.data['invitations']:
            user = User.objects.filter(id=i).first()
            ConviteEvento.objects.create(id_user=user, id_event=event)

        return JsonResponse({"message": "Os usuários foram convidados para o seu evento!"}, safe=False)


# Verificar essa função depois
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def sign_out(request, pk):
    if request.method == 'DELETE':
        EventUser.objects.filter(id_event=pk).first().delete()
        serializer = EventUserSerializer(
            EventUser.objects.filter(id_user=request.user), many=True)
        return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications(request):
    if request.method == 'GET':
        serializer = ConviteSerializer(ConviteEvento.objects.filter(
            id_user=request.user, status=True), many=True)
        return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def events_data(request, pk):
    if request.method == 'GET':
        if Event.objects.filter(user_owner=request.user, id=pk).exists():
            return JsonResponse({"owner": True}, safe=False)
        else:
            if EventUser.objects.filter(id_user=request.user, id_event=pk).exists():
                return JsonResponse({"owner": True}, safe=False)
            else:
                return JsonResponse({"owner": False}, safe=False)


class LogoutApi(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
