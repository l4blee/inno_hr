import dotenv; dotenv.load_dotenv()

import os
import io
import asyncio
import logging
from traceback import print_exc

import aiogram.filters
import aiogram.fsm
import aiogram.fsm.context
import aiogram
import aiohttp

import database as db
import aiclient
import utils


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s - %(name)s - %(message)s', datefmt='%H:%M:%S')

logger = logging.getLogger()
dp = aiogram.Dispatcher()
bot = aiogram.Bot(os.getenv('TELEGRAM_API_TOKEN'))
database = db.DBClient(os.getenv('DATABASE_URL'))
ai = aiclient.OpenAIClient(
    os.getenv('OPENAI_API_KEY'), 
    os.getenv('OPENAI_MODEL'),
    os.getenv('OPENAI_GPT_INSTRUCTION')
)


@dp.update.outer_middleware()
async def check_registration(handler, event: aiogram.types.Update, data: aiogram.types.Message):
    await bot.send_chat_action(event.message.chat.id, 'typing')
    with database.get_session() as session:
        if database.get_user(event.message.from_user.id, session):
            return await handler(event, data)
    
        database.add_user(event.message.from_user.id, session)
        session.commit()

    return await handler(event, data)


@dp.message(aiogram.filters.Command('delete_context'))
async def delete_context(msg: aiogram.types.Message):
    with database.get_session() as session:
        user = database.get_user(msg.from_user.id, session)
        user.context = '[]'

        session.commit()

    await msg.reply('Конекст успешно удален!')


@dp.message(aiogram.filters.Command('set_requirements'))
async def set_requirements(msg: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    await state.set_state(utils.ParseRequirements.requirements)
    await msg.reply('Укажите требования к кандидату')


@dp.message(utils.ParseRequirements.requirements)
async def process_requirements(msg: aiogram.types.Message, state: aiogram.fsm.context.FSMContext):
    await state.update_data(requirements=msg.text)
    with database.get_session() as session:
        user = database.get_user(msg.from_user.id, session)
        user.candidate_requirements = (await state.get_data())['requirements']

        session.commit()

    await msg.reply('Требования к канидидату обновлены! ')
    await state.clear()


@dp.message()
async def index(msg: aiogram.types.Message):
    try:
        with database.get_session() as session:
            user = database.get_user(msg.from_user.id, session)

            if user.tokens_left <= 0:
                await msg.reply('У Вас закончились токены!')
                return
            
            if user.context_capacity <= user.context_used:
                await msg.reply('Достигнут максимальный размер контекста!')
                return

            if msg.document:
                fileinfo = await bot.get_file(msg.document.file_id)
                async with aiohttp.ClientSession() as http_session:
                    async with http_session.get(f'https://api.telegram.org/file/bot{os.getenv("TELEGRAM_API_TOKEN")}/{fileinfo.file_path}') as resp:
                        file: io.BytesIO = io.BytesIO(await resp.read())

                gpt_response = await ai.get_response(utils.extract_from_pdf(file), user)
            else:
                gpt_response = await ai.get_response(msg.text, user)

            user.context_used += gpt_response.tokens_total
            user.tokens_left -= gpt_response.tokens_completion

            session.commit()

        await msg.reply(gpt_response.content)
    except Exception:
        logger.error('Caught exception with the following stacktrace:')
        print_exc()
        await msg.reply('Произошла ошибка, попробуйте позже!')


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.info('Starting bot...')
    asyncio.run(main())
    logging.info('Successfully shut down!')
