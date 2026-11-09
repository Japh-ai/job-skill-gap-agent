import asyncio

from db import job_exists, list_jobs, save_job
from extract import extract
from mcp_servers import fetch_page
from schemas import JobPost

URLS = [
    "https://job-boards.greenhouse.io/anthropic/jobs/5076109008",
    "https://t-mobile.jobs.cz/detail-pozice?r=detail&id=2001373678&rps=2027&impressionId=96e02998-3fa2-40e1-b772-d8d38364ecaa",
]


async def save_post(url: str):
    """Fetch a job post URL, extract it and save it. Returns a one line summary."""
    if job_exists(url):
        return f"Already saved: {url}"
    page = await fetch_page(url)  # 1. MCP: Download the page as MD.
    job = await asyncio.to_thread(extract, JobPost, "Extract the job information from this job post.",
                                  f"Jobpost:\n {page}")  # 2. LLM: Extract the job info from the page.
    job_id = save_job(job, url)  # 3. DB: Save the job to the database.
    return f"Saved job {job_id}: {job.company} - {job.role} ({len(job.skills_required)} required skills)"


async def main():
    for url in URLS:
        try:
            print(await save_post(url))
        except Exception as error:  # one bad URL (dead link, LLM failure) must not stop the rest
            print(f"Failed: {url}\n    {error}")

    print("\nJOBS IN DATABASE:")
    for row in list_jobs():
        print(f"    {row}")


if __name__ == "__main__":
    asyncio.run(main()) # in a notebook use `await main()` instead