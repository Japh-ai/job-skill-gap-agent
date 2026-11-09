import asyncio

from db import conn
from extract import extract
from mcp_servers import client
from schemas import SkillRating

RUBRIC = """Rate how well the users notes show they know the skill, using the type and status of each note.
- HANDS-ON: a note with type lab and status done covers the skill
- STUDYING: a note with type concept and status learning covers the skill
- NOT YET: anything else (concept notes with status not-started, plans, goals, profile drafts, or nothing relevant)
A skill mentioned in a plan or goal is NOT evidence.
First check that the note's text is really about this exact skill. A note that only appeared in the search but is about something else does NOT count, whatever its type or status.
"""

def top_skills (limit: int =10):
    """Most asked-for skills: (name, number of posts)."""
    return conn.execute("""SELECT lower(skill) AS name, 
    COUNT(DISTINCT job_id) AS posts FROM skills GROUP BY name 
    ORDER BY posts DESC LIMIT ?""", (limit,),).fetchall()


async def build_report(brain):
    """The skill gap report as text. 'brain' is an open session to the second-brain server."""
    total= conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    lines = [f"SKILL GAP REPORT: {total} saved job posts\n"]

    for name, posts in top_skills():
        result = await brain.call_tool("search_vault", {"query":name}) #1. MCP call to search the user's notes for this skill
        notes = result.content[0].text
        rating = await asyncio.to_thread(extract, SkillRating, RUBRIC, f"Skill: {name}\nSearch results from the user's notes:\n{notes}") #2. LLM call to rate the skill based on the notes
        lines.append(f"{name:<20} {posts}/{total:<4} {rating.rating:<10} {rating.evidence_note or '-'}: {rating.reason}")
    return "\n".join(lines)


async def main():
    async with client.session("second-brain") as brain:
        report = await build_report(brain)
        print(report)



if __name__ == "__main__":
    asyncio.run(main())