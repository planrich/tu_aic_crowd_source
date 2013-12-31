# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, json, flash, redirect, url_for, session
import db
import settings
import requests
import ago
import utils
import logging

from sqlalchemy.orm.exc import NoResultFound
from  sqlalchemy.sql.expression import func

application = Flask(__name__)
application.secret_key = settings.SECRET_KEY
application.jinja_env.filters['ago'] = ago.human
application.jinja_env.filters['max_size'] = utils.max_size

logger = logging.getLogger("crowd")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(formatter)
logger.addHandler(console)

logger.info("setting logging level to INFO")

@application.route("/")
def index():
    logger.info("redirecting to get open tasks")
    return redirect(url_for("get_open_tasks"))

@application.route("/solve_task", methods=["GET"])
def get_solve_task():
    sess = db.Session()
    task_id = request.args.get('task')
    if task_id:
        task = sess.query(db.OpenTask).filter(db.OpenTask.id == task_id).first()
    else:
        task = sess.query(db.OpenTask).filter(db.OpenTask.solved == False).order_by(func.random()).limit(1).first()
    user_id = session.get("user_id") or ""
    return render_template("solve_task.html", task=task, user_id=user_id)

@application.route("/solve_task", methods=["POST"])
def post_solve_task():
    sess = db.Session()
    if "answer" not in request.form:
        flash("Task was not rated. No answer provided. Here is a new task!", "danger")
        return redirect(url_for("get_solve_task",r="t"))

    if "user_id" not in request.form:
        flash("You did not provide your user_id. Here is a new task! Try again.", "danger")
        return redirect(url_for("get_solve_task",r="t"))

    if "task_id" not in request.form:
        flash("Internal failure. Here is a new task!", "danger")
        return redirect(url_for("get_solve_task",r="t"))

    answer = request.form["answer"]
    task_id = request.form["task_id"]
    user_id = request.form["user_id"]

    if user_id is None or user_id.strip() == "":
        flash("You did not provide your user_id. Here is a new task! Try again.", "danger")
        return redirect(url_for("get_solve_task",r="t"))

    session['user_id'] = user_id

    try:
        task = sess.query(db.OpenTask).filter(db.OpenTask.id == task_id).one()
    except NoResultFound:
        flash("Internal failure. Here is a new task!", "danger")
        return redirect(url_for("get_solve_task",r="t"))

    post_body = { "id": task_id, "answer": answer, "user": user_id }
    headers = {'content-type':'application/json'}
    try:
        result = requests.post(task.callback_link, data=json.dumps(post_body), headers=headers, timeout=10)
        if result.status_code != requests.codes.ok:
            flash("Internal error 4! Could not finish task. Here is a new one!","danger")
            return redirect(url_for("get_solve_task",r="t"))
    except Exception:
        flash("Internal error 5! Could not finish task. Here is a new one!","danger")
        return redirect(url_for("get_solve_task",r="t"))


    task.solved = True
    sess.commit()

    flash("Solved task. Here is a new one!", "success")
    return redirect(url_for("get_solve_task",r="t"))

def sanitize_open_task_list_params():
    order_by = 'id'
    limit = 10
    page = 0

    ORDER_POS = [ 'id', 'question', 'text', 'date' ]

    if "order" in request.args and request.args["order"] in ORDER_POS:
        order_by = request.args["order"]

    if "limit" in request.args:
        limit = int(request.args["limit"])

    if "page" in request.args:
        page = int(request.args["page"])

    return order_by, limit, page


@application.route("/open_tasks", methods=['GET'])
def get_open_tasks():

    order_by, limit, page = sanitize_open_task_list_params()

    sess = db.Session()
    open_tasks = sess.query(db.OpenTask)\
        .order_by(db.OpenTask.datetime.asc())\
        .filter(db.OpenTask.solved == False)\
        .offset(page * limit).limit(limit)\
        .all()

    task_count = sess.query(db.OpenTask).filter(db.OpenTask.solved == False).count()

    display_pages = 3
    page_count = int(task_count/limit)
    max_page = page_count
    ipages = list(utils.drop(range(0, page_count), page))
    post_pages = list(utils.drop(ipages, len(ipages) - display_pages))
    pre_pages = list(utils.take(ipages, len(ipages) - display_pages))
    pre_pages = list(utils.take(pre_pages, display_pages))
    display_dots = len(ipages) > (display_pages * 2)
    if not display_dots:
        pre_pages = []
        post_pages = utils.drop(range(0, int(task_count/limit)), page_count - display_pages * 2)

    return render_template("task_list.html", 
            tasks = open_tasks, 
            page = page, 
            pre_pages = pre_pages,
            post_pages = post_pages,
            count = task_count,
            limit = limit,
            max_page = max_page,
            display_dots = display_dots,
            int = int,
            len = len)


def sanitize_post_task(json):
    if not json:
        logger.error("could not sanitize post task json")
        return None

    if not 'id' in json or\
       not 'task_description' in json or\
       not 'task_text' in json or\
       not 'answer_possibilities' in json or\
       not 'callback_link' in json or\
       not 'price' in json:
       return None

    return json

@application.route("/tasks", methods=['POST'])
def task():
    j = sanitize_post_task(request.get_json(force=True,silent=True))
    if not j:
        example = { "id":"123",
            "task_description":"Is company mentioned positive/neutral/negative in the following paragraph?",
            "task_text":"lorem ipsum ...",
            "answer_possibilities":["yes","no","neutral"],
            "callback_link":"http://localhost:5000/webook",
            "price":12.34 }
        return json.dumps({ 'error': 'provide a valid json body!', 'example': example }), 400

    session = db.Session()

    tid = j['id']
    if session.query(db.OpenTask).filter(db.OpenTask.id == tid).count() != 0:
        return json.dumps({ 'error': 'id already exists' }), 400

    answers = j['answer_possibilities']
    answer = None
    if type(answers) is type([]):
        answer = "|".join(answers)
    elif answers == 'text':
        answer = "text"
    else:
        return json.dumps({ 'error': 'answer_possibilities must either be of type list ["yes","no",...] or "text"' }), 400

    open_task = db.OpenTask(j['id'], j['task_description'], j['task_text'], answer, j['callback_link'], j['price'])
    session.add(open_task)
    session.commit()

    result = { 'error': None, 'success': True }

    return json.dumps(result)

def sanitize_set_bonus(json):
    if not json:
        logger.error("could not sanitize set bonus json")
        return None

    if not 'id' in json or\
       not 'price_bonus' in json:
       return None

    return json

@application.route("/set_bonus", methods=['POST'] )
def set_bonus():
    j = sanitize_set_bonus(request.get_json(force=True,silent=True))
    if not j:
        example = json.dumps({ "id":"123",
            "price_bonus":12.34 })
        return json.dumps({ 'error': ('provide a valid json body! example: %s' % (example,)) }), 400

    session = db.Session()

    tid = j['id']
    if session.query(db.OpenTask).filter(db.OpenTask.id == tid).count() == 0:
        session.close()
        return json.dumps({ 'error': 'id does not exists' }), 400
    else:

        session.close()

        session = db.Session()

        tasks = session.query(db.OpenTask).filter(db.OpenTask.id == tid)
        for task in tasks:
            task.price_bonus = j['price_bonus']

        session.commit()

        result = { 'error': None, 'success': True }, 200

        return json.dumps(result)    
        session.commit()

def sanitize_set_garbage(json):
    if not json:
        logger.error("could not sanitize set garbage json")
        return None

    if not 'id' in json:
       return None

    return json

@application.route("/set_garbage", methods=['POST'])
def set_garbage():
    j = sanitize_set_garbage(request.get_json(force=True,silent=True))
    if not j:
        example = json.dumps({ "id":"123",
            "price_bonus":12.34 })
        return json.dumps({ 'error': ('provide a valid json body! example: %s' % (example,)) }), 400

    session = db.Session()

    tid = j['id']
    try:
        task = session.query(db.OpenTask).filter(db.OpenTask.id == tid).one()
    except NoResultFound:
        session.close()
        return json.dumps({ 'error': 'id does not exists' }), 400
    except MultipleResultsFound:
        session.close()
        return json.dumps({ 'error': 'more than one result found' }), 400

    logger.info("set garbage called with task id %d", task.id)

    session.delete(task)

    session.commit()

    result = { 'error': None, 'success': True }, 200

    return json.dumps(result)    


if __name__ == "__main__":
    application.debug = True
    application.run(port=5001)
