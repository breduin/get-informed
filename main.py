from a2wsgi import ASGIMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import calendar
import httpx


# CONFIGURATION

# url for dayoff service
URL_ISDAYOFF = 'https://isdayoff.ru'


app = FastAPI()
application = ASGIMiddleware(app)

# mounting directory for static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# defining directory for templates
templates = Jinja2Templates(directory="templates")


# dict for day types
DAY_TYPES = {
    '0': 'рабочий',
    '1': 'выходной',
}


# name of month in correct form (russian)
MONTH_NAME = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря'
}

def get_month_name(month: int) -> str:
    """
    Returns month name
    """
    return MONTH_NAME[month]


def get_url_day_off(date) -> str:
    """
    Returns url in format for API use
    """
    return URL_ISDAYOFF + '/' + date.strftime('%Y-%m-%d')


async def get_response(url:str = '') -> str:
    """
    Connects to <url> and returns the body of the response.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
    except httpx.RequestError as exc:
        return f"An error occurred while requesting {exc.request.url!r}."

    return response.text


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Collects info about current date and returns rendered template.
    """

    today_raw = datetime.today()
    day = today_raw.day
    month_raw = datetime.today().month
    month = get_month_name(month_raw)
    year = today_raw.year
    today = " ".join(map(str, [day, month, year]))

    isleap = 'високосный' if calendar.isleap(year) else 'невисокосный'

    weekday = today_raw.strftime('%A').lower()

    _, number_of_days = calendar.monthrange(year, month_raw)
    days_word = 'день' if number_of_days == 31 else 'дней'

    url_day_off = get_url_day_off(today_raw)
    response = await get_response(url_day_off)
    try:
        today_type = DAY_TYPES[response]
    except KeyError:
        today_type = None

    return templates.TemplateResponse("index.html",
                                        {
                                        "request": request,
                                        "today": today,
                                        "weekday": weekday,
                                        "isleap": isleap,
                                        "number_of_days": number_of_days,
                                        "days_word": days_word,
                                        "today_type": today_type,
                                        }
                                     )
