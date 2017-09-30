from models import Base, User, Trip, Conversation, Message, Request
from flask import Flask, jsonify, request, url_for, abort, g, render_template, redirect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import or_, and_
from pyfcm import FCMNotification
from pprint import pprint
from httplib2 import Http

from flask_httpauth import HTTPBasicAuth
import json

#NEW IMPORTS
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response
import requests

auth = HTTPBasicAuth()


username = 'postgres'
password = 'postgres'
dbname='localhost:5432/latrans'
url = "postgresql+psycopg2://%s:%s@%s" % (username, password, dbname)
engine = create_engine(url)

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


CLIENT_ID = "6695651188306-abo5gcs00d2pbakhe4akmm30ime556q5.apps.googleusercontent.com"
push_service = FCMNotification(api_key= "AIzaSyDTFG3_cpy4g8oiNlAuNN5ux2Ao5uSEhOQ")
reg_id = "fsYv_1fYukk:APA91bH7q15EiAhto98t2Ok4TR-4Ipx3WzhM1MwDJSLYLpfXu8oQpcYDGnNzqgE2SyM4b2DPOKUmjne-mYRjmlyC7aSBvoZKSFe4bWQbeTse8d8Zn61SkK5d2vRzuUo4ksGP71eoMJ0r"
TRIP_TOPIC = "trips_fcm"
REQUEST_TOPIC = "request_fcm"

#Verify password
@auth.verify_password
def verify_password(token_or_email, password):
    #Try to see if it's a token first
    user_id = User.verify_auth_token(token_or_email)
    if user_id:
        user = session.query(User).filter_by(id = user_id).one()
    else:
        user = session.query(User).filter_by(email = token_or_email).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

# User login entry
@app.route('/api/v1/login')
@auth.login_required
def get_auth_token():
    user = session.query(User).filter_by(email = g.user.email).first()
    token = g.user.generate_auth_token()
    user_token =  token.decode('ascii');
    return jsonify({
        "token": user_token,
        "user": user.serialize
     }) 
# @app.route('/')
# def start():
#     return render_template('clientOAuth.html')

                            #User
#******************************************************************************************************************8#
# Create new user
@app.route('/api/v1/users/new', methods = ['POST'])
def new_user():
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    password = request.json.get('password')
    email = request.json.get('email')
    #user_id = request.json.get('user_id')
    if email is None or password is None:
        print ("missing arguments")
        abort(400)

    if session.query(User).filter_by(email = email).first() is not None:
        print("Existing user")    
        return jsonify({'message':'Email address already exists'}), 303#, {'Location': url_for('get_user', id = user.id, _external = True)}

    user = User(email = email, first_name = first_name, last_name = last_name)
    user.hash_password(password)
    session.add(user)
    session.commit()
    g.user = user
    token = g.user.generate_auth_token()
    #return jsonify({'token': token.decode('ascii')})
    user_token =  token.decode('ascii');

    return jsonify({
        "token": user_token,
        "user": user.serialize
     }) 


#Show a specfic user
@app.route('/api/v1/users/<int:id>')
def get_user(id):
    user = session.query(User).filter_by(id=id).one()
    if not user:
        abort(400)
    #return jsonify({'username': user.username})
    return jsonify(user.serialize)

#Show all users
@app.route('/api/v1/users')
def getAlluser():
    users = session.query(User).all()
    return  jsonify(users = [user.serialize for user in users])

#Modify users profile
@app.route('/api/v1/users/<int:user_id>/modify', methods = ['PUT'])
def editUser(user_id):
    phone_no = request.json.get('phone_no')
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')
    picture = request.json.get('picture')
    user = session.query(User).filter_by(id =user_id).first()
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if picture:
         user.picture = picture
    if phone_no:
         user.phone_no = phone_no
    session.add(user)
    session.commit()
    g.user = user
    token = g.user.generate_auth_token()
    #return jsonify({'token': token.decode('ascii')})
    user_token =  token.decode('ascii');

    return jsonify({
        "token": user_token,
        "user": user.serialize
     })

@app.route('/api/v1/oauth/<provider>', methods = ['POST'])
def login(provider):
    #STEP 1 - Parse the auth code
    auth_code = request.json.get('auth_code')
    print ("Step 1 - Complete, received auth code %s" % auth_code)
    if provider == 'google':
        #STEP 2 - Exchange for a token
        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'localhost:5000'
            credentials = oauth_flow.step2_exchange(auth_code)
        except FlowExchangeError:
            response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        print ("Step 2 Complete! Access Token : %s " % credentials.access_token)

        #STEP 3 - Find User or make a new one
        #Get user info
        h = httplib2.Http()
        userinfo_url =  "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt':'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()
        #username = data['name']
        picture = data['picture']
        email = data['email']
        user_id = data["id"]
        #name = data['given_name']
        #surname = data['family_name']


        #see if user exists, if it doesn't make a new one
        user = session.query(User).filter_by(email=email).first()
        if not user:
            user = User(usepicture = picture, email = email, user_id = user_id)
            session.add(user)
            session.commit()
        #STEP 4 - Make token
        token = user.generate_auth_token(604800)
        #STEP 5 - Send back token to the client
        return jsonify({'token': token.decode('ascii')})
        #return jsonify({'token': token.decode('ascii'), 'duration': 600})
    else:
        return 'Unrecoginized Provider'

                                                
                                                #Messages
#******************************************************************************************************#
##Show all messages
@app.route('/api/v1/users/<int:user_id>/messages')
def showAllMessages(user_id):
    messages = session.query(Message).filter(or_(Message.sender_id == user_id, Message.recipient_id == user_id)).all()
    return jsonify({
        "messages": [message.serialize for message in messages]
     }) 
##Send message
@app.route('/api/v1/messages/send', methods = ['POST'])
def sendPush():
    #message = request.get_json()
    sender_id = request.json.get('sender_id')
    recipient_id = request.json.get('recipient_id')
    message  = request.json.get('message')
    time_sent = request.json.get('time_sent')
    
    payload = {}
    payload['sender_id'] = sender_id
    payload['recipient_id'] = recipient_id
    payload['message'] = message
    payload['time_sent'] = time_sent
    topic = "user"+ str(recipient_id)
    user = session.query(User).filter_by(id = sender_id).first()
    payload['sender_first_name'] = user.first_name
    payload['sender_last_name'] = user.last_name
    payload['sender_picture'] = user.picture

    #if session.query(Conversation).filter_by(email = email).first() is not None
    if session.query(Conversation).\
            filter(Conversation.user_one_id.in_([sender_id, recipient_id])).\
            filter(Conversation.user_two_id.in_([sender_id, recipient_id])).first() is None:
            new_conversation = Conversation(user_one_id = sender_id, user_two_id = recipient_id)
            session.add(new_conversation)
            session.commit()
            conversation_id = new_conversation.id
            newMessage = Message(sender_id = sender_id, recipient_id = recipient_id, message = message, 
                time_sent = time_sent, conversation_id =conversation_id, sender_first_name = user.last_name, sender_last_name = user.last_name)
            session.add(newMessage)
            session.commit()
            payload['id'] = newMessage.id
            payload['conversation_id'] = conversation_id
            #data = json.dumps(payload)
            raw = {
                "data": payload
            }

            data = json.dumps(raw)
            result = push_service.notify_topic_subscribers(topic_name= topic,  data_message= payload)
            pprint(result)
            return data

    old_conversation = session.query(Conversation).\
            filter(Conversation.user_one_id.in_([sender_id, recipient_id])).\
            filter(Conversation.user_two_id.in_([sender_id, recipient_id])).first() 
    old_conversation_id = old_conversation.id
    newMessage = Message(sender_id = sender_id, recipient_id = recipient_id, message = message,
        time_sent = time_sent, conversation_id = old_conversation_id, sender_first_name = user.last_name, sender_last_name = user.last_name)
    session.add(newMessage)
    session.commit()

    payload['id'] = newMessage.id
    payload['conversation_id'] = old_conversation_id
    #j_data = json.dumps(payload)

    raw = {
        "data": payload
    }

    data = json.dumps(raw)
    #result = push_service.notify_single_device(registration_id = reg_id, data_message= payload) 
    result = push_service.notify_topic_subscribers(topic_name = topic,  data_message = payload)
    pprint(result)
    return data
   
    #result = push_service.notify_single_device(registration_id = reg_id, data_message= message)    
    #pprint(result)
    #return jsonify(newMessage.serialize)

##Show messages in a converstaion
@app.route('/api/v1/conversations/<int:conversation_id>/messages')
def showMessagesForConversation(conversation_id):
    messages = session.query(Message).filter_by(conversation_id = conversation_id).all()
    return jsonify({
        "messages": [message.serialize for message in messages]
     }) 



                                                #Conversations
#******************************************************************************************************************#
#get conversations for a specific user, endpont currently unsed
@app.route('/api/v1/users/<int:user_id>/conversations')
def showAllConversation(user_id):
    conversations = session.query(Conversation).filter(or_(Conversation.user_one_id == user_id, Conversation.user_two_id == user_id)).all()
    return jsonify({
        "conversations": [conversation.serialize for conversation in conversations]
     }) 

#Show all availavle conversations
@app.route('/api/v1/conversations')
def showAllConversations():
    conversations = session.query(Conversation).all()
    count = session.query(Conversation).count()
    return jsonify({
        "total_conversations": count,
        "conversations": [conversation.serialize for conversation in conversations]
     }) 

                                                        

                                                        #Trips
#********************************************************************************************************************#
# Show all available trips
@app.route('/api/v1/trips')
def showAllTrips():
    trips = session.query(Trip).all()
    count = session.query(Trip).count()
    return jsonify({
        "total_resulst": count,
        "trips": [trip.serialize for trip in trips]
     }) 

    #return jsonify(trips = [trip.serialize for trip in trips])

# Show all trips of a particular user
@app.route('/api/v1/trips/users/<int:user_id>')
def showTripsForUser(user_id):
    trips = session.query(Trip).filter_by(user_id=user_id).all()
    return jsonify(trips = [trip.serialize for trip in trips])

#Show a specific trip
@app.route("/api/v1/trips/<int:trip_id>")
def showATrip(trip_id):
    trip = session.query(Trip).filter_by(id = trip_id).one()
    return jsonify(trip = trip.serialize)


# Add a new trip
@app.route('/api/v1/trips/<int:user_id>/new', methods = ['POST'])
#@auth.login_required
def createNewTrip(user_id):
    if request.method == 'POST':
        phone_no = request.json.get('phone_no')
        traveling_from_state = request.json.get('traveling_from_state')
        traveling_from_city = request.json.get('traveling_from_city')
        traveling_to_state = request.json.get('traveling_to_state')
        traveling_to_city = request.json.get('traveling_to_city')
        traveling_date = request.json.get('traveling_date')
        posted_on = request.json.get('posted_on')
        time_updated = request.json.get('time_updated')
        user = session.query(User).filter_by(id = user_id).first()
        profile_image = user.picture
        user_first_name = user.first_name
        user_last_name = user.last_name
        user_id = user_id
        newTrip = Trip(phone_no = phone_no, traveling_from_state = traveling_from_state, 
            traveling_from_city = traveling_from_city, traveling_to_state = traveling_to_state,
            traveling_to_city = traveling_to_city, traveling_date = traveling_date, posted_on = posted_on, 
            time_updated = time_updated, profile_image = profile_image, user_id = user_id,
            user_first_name = user_first_name, user_last_name = user_last_name
        )
        session.add(newTrip)
        session.commit()
        trip_payload = {}
        trip_payload['profile_image'] = user.picture
        trip_payload['id'] = newTrip.id
        trip_payload['phone_no'] = phone_no
        trip_payload['traveling_from_state'] = traveling_from_state
        trip_payload['traveling_from_city'] = traveling_to_city
        trip_payload['traveling_to_state'] = traveling_to_state
        trip_payload['traveling_to_city'] = traveling_to_city
        trip_payload['traveling_date'] = traveling_date
        trip_payload['posted_on'] = posted_on
        trip_payload['time_updated'] =  time_updated
        trip_payload['user_id'] = user_id
        trip_payload['user_first_name'] = user_first_name
        trip_payload['user_last_name'] = user.last_name
        raw = {
        "data": trip_payload
        }

        trip_data = json.dumps(raw)
        #result = push_service.notify_single_device(registration_id = reg_id, data_message= payload) 
        result = push_service.notify_topic_subscribers(topic_name = TRIP_TOPIC,  data_message = trip_payload)
        pprint(result)
        return trip_data
        
        #result = push_service.notify_single_device(registration_id = reg_id, data_message = trip_data)
        #result = push_service.notify_topic_subscribers(topic_name= TRIP_TOPIC,  data_message = data) 
        #return jsonify(newTrip.serialize)
        
# @auth.error_handler
# def unauthorized():
#     response = jsonify({'message':'Not allowed'})
#     return response, 403

#Modify a spcific trip
@app.route("/api/v1/trips/<int:trip_id>", methods = ['PUT', 'DELETE'])
@auth.login_required
def editATrip(trip_id):
    trip = session.query(Trip).filter_by(id = trip_id).one()
    if g.user.id != trip.user_id:
        print ("Not user")
        abort(400)
    if request.method == 'PUT':
        phone_no = request.json.get('phone_no')
        traveling_from_state = request.json.get('traveling_from_state')
        traveling_from_city = request.json.get('traveling_from_city')
        traveling_to_state =  request.json.get('traveling_to_state')
        traveling_to_city = request.json.get('traveling_to_city')
        traveling_date = request.json.get('traveling_date')
        posted_on =  request.json.get('posted_on')
        time_updated = request.json.get('time_updated')
        profile_image = request.json.get(' profile_image')
        return updateTrip(trip_id, phone_no, traveling_from_state, traveling_from_city, traveling_to_state, traveling_to_city,
        traveling_date, posted_on, time_updated, profile_image)

        #Call the method to remove a puppy
    elif request.method == 'DELETE':
        return deleteATrip(trip_id, user_id)

def updateTrip(trip_id, phone_no, traveling_from_state, traveling_from_city, traveling_to_state, traveling_to_city,
        traveling_date, posted_on, time_updated, profile_image):
    trip = session.query(Trip).filter_by(id = trip_id).one()

    trip.phone_no = phone_no
    trip.traveling_from_state = traveling_from_state
    trip.traveling_from_city = traveling_from_city
    trip.traveling_to_state = traveling_to_state
    trip.traveling_to_city = traveling_to_city
    trip.traveling_date = traveling_date
    trip.posted_on = posted_on
    trip.time_updated = time_updated
    trip.profile_image = profile_image 
    session.add(trip)
    session.commit()
    #return "Succesfully updated item %s" % id
    return redirect(url_for('showATrip', trip_id=trip_id))

def deleteATrip(id, user_id):
    trip = session.query(Trip).filter_by(id = id).one()
    session.delete(trip)
    session.commit()
    #return "Succesfully removed %s" % name + "from database"
    return redirect(url_for('showTripsForUser', user_id = user_id))

@app.route("/api/v1/trips/delete", methods = ['DELETE'])
def deleteAllTrips():
    trips = session.query(Trip).all()
    count = session.query(Trip).count()
    for trip in trips:
        session.delete(trip)
        session.commit()
    return "successfully deleted {} trips".format(count)


if __name__ == '__main__':
    app.debug = True
    #app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    app.run(host='0.0.0.0', port=5000)