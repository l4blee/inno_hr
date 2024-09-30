from io import FileIO
from PyPDF2 import PdfReader
from aiogram.fsm.state import StatesGroup, State


class ParseRequirements(StatesGroup):
    requirements = State()


def extract_from_pdf(file: FileIO):
    pdf = PdfReader(file)
    text = '\n'.join([page.extract_text() for page in pdf.pages])
    
    return text

