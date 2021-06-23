import uuid
from urllib.parse import urlparse

from flask import Blueprint, current_app, jsonify, request
from rq import Queue
from werkzeug.utils import secure_filename

from ..data.cache import get_cache
from ..data.process import get_dataframe_from_file, get_dataframe_from_url
from ..data.registry import get_reg_file

bp = Blueprint("fetch", __name__)

# all endpoints from this blueprint return a job id


@bp.route("/registry/<fileid>")
def get_registry_file(fileid):
    file_url, file_type = get_reg_file(fileid)
    if not file_url:
        return jsonify(error=404, text="file not found", fileid=fileid), 404

    # a query was submitted, so queue it up and return job_id
    q = Queue(connection=get_cache())
    job_id = str(uuid.uuid4())

    job = q.enqueue_call(
        func=get_dataframe_from_url,
        args=(file_url,),
        timeout="15m",
        ttl=15 * 60,
        job_id=job_id,
    )
    return jsonify({"job": job.id})


@bp.route("/url", methods=["POST"])
def get_file_from_url():
    file_url = request.form.get("url")
    if not file_url:
        return jsonify(error=404, text="No url provided"), 404

    if urlparse(file_url).netloc not in current_app.config.get("URL_FETCH_ALLOW_LIST"):
        return jsonify(error=403, text="Fetching from that URL is not supported"), 403

    # a query was submitted, so queue it up and return job_id
    q = Queue(connection=get_cache())
    job_id = str(uuid.uuid4())

    job = q.enqueue_call(
        func=get_dataframe_from_url,
        args=(file_url,),
        timeout="15m",
        ttl=15 * 60,
        job_id=job_id,
    )
    return jsonify({"job": job.id})


@bp.route("/upload", methods=["POST"])
def process_uploaded_file():
    if "file" not in request.files:
        return jsonify(error=500, text="No file uploaded"), 500

    file_ = request.files["file"]

    if file_.filename == "":
        return jsonify(error=500, text="No file selected"), 500

    filename = secure_filename(file_.filename)
    content = file_.read()

    # a query was submitted, so queue it up and return job_id
    q = Queue(connection=get_cache())
    job_id = str(uuid.uuid4())

    job = q.enqueue_call(
        func=get_dataframe_from_file,
        args=(filename, content),
        timeout="15m",
        job_id=job_id,
    )
    return jsonify({"job": job.id})
