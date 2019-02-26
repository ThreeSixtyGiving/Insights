from rq import Queue

from .cache import get_cache

def get_queue_job(job_id):
    if not isinstance(job_id, str):
        return None
    q = Queue(connection=get_cache())
    failed_q = Queue('failed', connection=get_cache())
    failed_job = failed_q.fetch_job(job_id)
    if failed_job:
        return failed_job
    return q.fetch_job(job_id)


def get_all_jobs():
    # NB doesn't seem to work at the moment @TODO
    q = Queue(connection=get_cache())
    failed_q = Queue('failed', connection=get_cache())
    return [
        get_job_status(job) for job in q.jobs
    ] + [
        get_job_status(job) for job in failed_q.jobs
    ]

def get_job_status(job):

    # job has failed
    if job.is_failed:
        return dict(
            error=501,
            jobid=job.id,
            status="processing-error",
            # args=job.args,
            exc_info=job.exc_info,
        )

    # job is in progress
    if job.result is None:
        return dict(
            status='in-progress',
            jobid=job.id,
            stages=job.meta.get("stages"),
            progress=job.meta.get("progress"),
        )

    # job has completed
    return dict(
        status='completed',
        jobid=job.id,
        result=job.result,
    )
