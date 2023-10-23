from django.shortcuts import render,redirect
from django.http import JsonResponse
import openai
import azure.cognitiveservices.speech as speechsdk

from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat

from django.utils import timezone

# Mano raktai.. no steal plss ;(((
openai_api_key = 'your openAI key'
openai.api_key = 'openai api key'
azure_auth_tk = 'azure authentication key'

# Variables For Azure's Voice Synthesis
speech_config = speechsdk.SpeechConfig(subscription=azure_auth_tk, region="switzerlandnorth")
speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Raw48Khz16BitMonoPcm)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
speech_config.speech_synthesis_voice_name='en-US-AnaNeural'
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# Exception variables in case I'm gonna need them for the future  
exception1 = ValueError
exception2 = AttributeError
exception3 = openai.error.RateLimitError

# Pagrindinis
def ask_openai(message):
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo-16k-0613",
        # prompt = message,
        # for max_toxens it's better to keep it under 200 cuz OpenAI will give out RateLimitError
        max_tokens=170,
        # n=1,
        # stop=None,
        temperature=1.5,
        messages=[
            {"role": "system", "content": "You are an helpful assistant."},
            {"role": "user", "content": message},
        ]
    )
    answer = response.choices[0].message.content.strip()
    return answer
    

# chat bot n'stuff
def chatbot(request):
    chats = Chat.objects.filter(user=request.user)


    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)

        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now)
        chat.save()
        # Azure Voice synthesis
        speech_synthesizer.speak_text_async(response)
        # Json returns to webpage
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html', {'chats': chats})    

# Prisijungimas
def login(request):
    if request.method=='POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')

# User Registracija
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1==password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = 'Error creating account'
            return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = "Password don't match" 
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

# Atsijungti
def logout(request):
    auth.logout(request)
    return redirect('login')
