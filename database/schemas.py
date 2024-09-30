from os import getenv
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer

base = declarative_base()

class Users(base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, unique=True)

    context = Column(String, default='[]')
    context_used = Column(Integer, default=0)
    context_capacity = Column(Integer, default=int(getenv('CONTEXT_CAPACITY_BASIC')))

    tokens_left = Column(Integer, default=int(getenv('TOKENS_BASIC')))

    candidate_requirements = Column(String, default='')

# TODO: Paid subsciptions
# class Subscriptions(base): ...
# + relations between tables 
