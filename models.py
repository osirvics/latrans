from sqlalchemy import Column, ForeignKey, Integer,String, DateTime, BigInteger as Bigint, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    picture = Column(String)
    phone_no = Column(String)
    password_hash = Column(String)
    


    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
        'id' : self.id,
        'first_name' : self.first_name,
        'last_name'  : self.last_name,
        'picture' : self.picture,
        'email' : self.email,
        'phone_no': self.phone_no
                
            }

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration = 600):
    	s = Serializer(secret_key, expires_in = expiration)
    	return s.dumps({'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        
    	s = Serializer(secret_key)
    	try:
    		data = s.loads(token)
    	except SignatureExpired:
    		#Valid Token, but expired
    		return None
    	except BadSignature:
    		#Invalid Token
    		return None
    	user_id = data['id']
    	return user_id

class Trip(Base):
    __tablename__ = 'trip'
    id = Column(Integer, primary_key=True)
    phone_no = Column(String)
    traveling_from_state = Column(String)
    traveling_from_city = Column(String)
    traveling_to_state = Column(String)
    traveling_to_city = Column(String)
    traveling_date = Column(String)
    profile_image = Column(String)
    user_first_name = Column(String)
    user_last_name = Column(String)
    # posted_on = Column(DateTime (timezone=True), server_default = func.now())
    posted_on = Column(Bigint)
    user_id = Column(Integer,  ForeignKey('user.id'), index = True)
    time_updated = Column(Bigint)
    user = relationship(User)


    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
        'id' : self.id,
        'phone_no' : self.phone_no,
        'traveling_from_state' : self.traveling_from_state,
        'traveling_from_city' : self.traveling_from_city,
        'traveling_to_state' : self.traveling_to_state,
        'user_first_name' :     self.user_first_name,
        'user_last_name'  :     self.user_last_name,
        'traveling_to_city' : self.traveling_to_city,
        'traveling_date' : self.traveling_date,
        'profile_image' :  self.profile_image,
        'posted_on' : self.posted_on,
        'time_updated' : self.time_updated,
        'user_id' : self.user_id

    
            }

class Request(Base):
    __tablename__ = 'request'
    id = Column(Integer, primary_key=True)
    delivery_state = Column(String)
    delivery_city = Column(String)
    item_location_state = Column(String)
    item_location_city = Column(String)
    picture = Column(String)
    offer_amount = Column(String)
    deliver_before = Column(String)
    posted_on = Column(Bigint)
    time_updated = Column(Bigint)
    phone_no = Column(String)
    item_name = Column(String)
    profile_image = Column(String)
    user_first_name = Column(String)
    user_last_name = Column(String)
    user_id = Column(Integer, ForeignKey('user.id'))
    userid = relationship(User)

    def __iter__(self):
        return self.__dict__.iteritems()

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
        'id' : self.id,
        'delivery_state' : self.delivery_state,
        'delivery_city' : self.delivery_city,
        'item_location_state' : self.item_location_state,
        'item_location_city' : self.item_location_city,
        'picture' : self.picture,
        'offer_amount'    : self.offer_amount,
        'deliver_before' : self.deliver_before,
        'posted_on' : self.posted_on,
        'time_updated' : self.time_updated,
        'phone_no' : self.phone_no,
        'item_name'    : self.item_name,
        'profile_image' : self.profile_image,
        'user_first_name' : self.user_first_name,
        'user_last_name' : self.user_last_name,
        'user_id' : self.user_id
                
            }


class Conversation(Base):
    __tablename__ = 'conversation'
    id = Column(Integer, primary_key=True , index = True)
    user_one_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_two_id =  Column(Integer, ForeignKey('user.id'), nullable=False)
    user_one = relationship("User",  foreign_keys="Conversation.user_one_id")
    user_two = relationship("User", foreign_keys="Conversation.user_two_id")


    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
        'id' : self.id,
        'user_one_id' : self.user_one_id,
        'user_two_id' : self.user_two_id
        
            }

## TODO add recipeint first and last name
class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True, autoincrement=True,  nullable=False)
    sender_id = Column(Integer, ForeignKey('user.id'))
    recipient_id = Column(Integer, ForeignKey('user.id'))
    sender_first_name = Column(String)
    sender_last_name = Column(String)
    recipient_first_name = Column(String)
    recipient_last_name = Column(String)
    sender_picture = Column(String)
    message = Column(String)
    sent_status = Column(String)
    time_sent = Column(Bigint)
    conversation_id = Column(Integer,  ForeignKey('conversation.id'), index = True)
    sender = relationship("User",  foreign_keys = "Message.sender_id")
    recipient = relationship("User", foreign_keys = "Message.recipient_id")
    conversation = relationship(Conversation)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
        'id' : self.id,
        'sender_id' : self.sender_id,
        'recipient_id' : self.recipient_id,
        'sender_first_name' : self.sender_first_name,
        'sender_last_name' : self.sender_last_name,
        'sender_picture' : self.sender_picture,
        'recipient_first_name' : self.recipient_first_name,
        'recipient_last_name' : self.recipient_last_name,
        'sent_status'    : self.sent_status,
        'message' : self.message,
        'time_sent' : self.time_sent,
        'conversation_id' : self.conversation_id
                
            }


username = 'postgres'
password = 'postgres'
dbname='localhost:5432/latrans'
url = "postgresql+psycopg2://%s:%s@%s" % (username, password, dbname)
engine = create_engine(url)
 
Base.metadata.create_all(engine)