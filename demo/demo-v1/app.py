import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
import uuid
import csv
import io
from datetime import datetime, timedelta
import dropbox
import os
import time
import json

# Constants
ICON_PATH = os.path.join(os.path.dirname(__file__), "figs", "icon.jpg")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "figs", "logo.png")

def initialize_session_state():
    """Initialize all session state variables with default values"""
    if "student_info" not in st.session_state:
        st.session_state["student_info"] = None
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "message_log" not in st.session_state:
        st.session_state["message_log"] = []
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False
    if "show_admin_login" not in st.session_state:
        st.session_state["show_admin_login"] = False
    if "admin_system_prompt" not in st.session_state:
        st.session_state["admin_system_prompt"] = None
    if "admin_role" not in st.session_state:
        st.session_state["admin_role"] = None
    if "show_export_consent" not in st.session_state:
        st.session_state["show_export_consent"] = False
    if "consent_signed" not in st.session_state:
        st.session_state["consent_signed"] = False
    if "data_privacy_acknowledged" not in st.session_state:
        st.session_state["data_privacy_acknowledged"] = False
    # Timer-related session state
    if "timer_active" not in st.session_state:
        st.session_state["timer_active"] = False
    if "timer_minutes" not in st.session_state:
        st.session_state["timer_minutes"] = 0
    if "timer_start_time" not in st.session_state:
        st.session_state["timer_start_time"] = None
    if "timer_completed" not in st.session_state:
        st.session_state["timer_completed"] = False
    if "timer_cancelled" not in st.session_state:
        st.session_state["timer_cancelled"] = False
    if "pending_reflection_message" not in st.session_state:
        st.session_state["pending_reflection_message"] = None
    if "timer_stopped" not in st.session_state:
        st.session_state["timer_stopped"] = False
    if "timer_completion_checked" not in st.session_state:
        st.session_state["timer_completion_checked"] = False

# Initialize session state
initialize_session_state()

# Timer tool for LangChain agent
@tool
def set_timer(minutes: int) -> str:
    """Set a timer for the specified number of minutes. 
    
    Args:
        minutes: The number of minutes for the timer (must be a positive integer)
    
    Returns:
        A confirmation message indicating the timer has been set
    """
    if minutes <= 0:
        return "Error: Timer duration must be a positive number of minutes."
    
    st.session_state["timer_active"] = True
    st.session_state["timer_minutes"] = minutes
    st.session_state["timer_start_time"] = datetime.now()
    st.session_state["timer_completed"] = False
    st.session_state["timer_cancelled"] = False
    st.session_state["timer_completion_checked"] = False
    st.session_state["timer_stopped"] = False
    
    return f"Timer set for {minutes} minute(s). The timer will start now."

# Step 1: Startup form for student information
if st.session_state["student_info"] is None:
    st.title("📝 Hello there! I'm ArchPal, UGA's New AI Writing Coach!")
    st.markdown("Please enter some baisc information to help me get to know you better and tailor my coaching to you.")
    
    with st.form("student_info_form"):
        first_name = st.text_input("First Name", key="first_name")
        last_name = st.text_input("Last Name", key="last_name")
        college_year = st.selectbox("College Year", ["First Year", "Second Year", "Upper-Division", "Masters Student", "PhD Student"], key="college_year")
        major = st.text_input("Major", key="major")
        session_number = st.text_input("Session Number", key="session_number")
        session_password = st.text_input("Session Password", type="password", key="session_password")
        submitted = st.form_submit_button("Start Session", use_container_width=True)

        if submitted:
            # Get the correct password from secrets
            correct_password = st.secrets.get("session_password", "")

            if first_name and last_name and college_year and major and session_number and session_password:
                if session_password == correct_password:
                    unique_id = str(uuid.uuid4())
                    st.session_state["student_info"] = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "college_year": college_year,
                        "major": major,
                        "session_number": session_number,
                        "unique_id": unique_id
                    }
                    st.rerun()
                else:
                    st.error("❌ Incorrect session password. Please check with your session facilitator.")
            else:
                st.error("Please fill in all fields.")
    st.stop()

# Get student info
student_info = st.session_state["student_info"]
first_name = student_info["first_name"]
last_name = student_info["last_name"]
college_year = student_info["college_year"]
major = student_info["major"]
session_number = student_info["session_number"]
unique_id = student_info["unique_id"]

# Build default system prompt with student context
default_system_prompt_full = """ You are ArchPal, UGA's writing coach and friendly helpful companion. You coach students through brainstorming, planning, drafting strategies, revision, reflection, and resource use—while upholding academic integrity. You do not write or substantially edit assignment prose. Instead, you help students grow their own writing skills by serving as a companion to their own process and work.

Student Information:
- Name: {first_name} {last_name}
- College Year: {college_year}
- Major: {major}

## Your Primary Goal
Help students develop as independent, reflective writers by coaching their process and encouraging self-reflection that deepens their thinking and enriches their learning experiences across contexts and through the course material.

## Core Pedagogical Principles
- **Process-first approach**: Guide students through a more complete writing process: brainstorm -> plan -> draft strategies -> research -> revision -> reflect. 
- **Foster metacognition**: Ask brief, targeted reflection questions that promote self reflection and critical thinking on the writing task and the student's goals with it(≤2 per response). 
- **Promote transfer**: Connect strategies to other courses and genres by seeking basic understanding of their academic background, academic habits, and personal interests that can give ideas of how to best help and motivate them. 
- **Encourage resource use**: Route to UGA supports when helpful, but ensure the need for the resource is clear by asking followup questions about indicators of need.
- **Maintain supportive, encouraging tone**: Warm, plain language, student-centered, encourage them to aim for their best work and not just the grade.


## Student Population & Differentiation
- **First-year students**: Provide more structure, scaffolds, and step-by-step guidance. Reference well-known writing processes and strategies that are easy to understand and apply. Encourage them to form strong writing habits and study habits that will help them in their future academic and professional endeavors.
- **Upper-division students**: Offer strategic frameworks with some independence, encourage them to think beyond the implications to the class, like fostering good  analysis, communication, and critical thinking skills.
- **Graduate students**: Present high-level questions and challenges to research/argumentation, encourage them to think about the broader implications of their work and how it relates to the current (2025-2026) research landscape. 


## Session Framework

Onboarding & Personalization (beginning of a session or when context is missing) ask these in a conversational manner in multiple messages. "Getting to know you..." DO NOT ASK ALL THESE QUESTIONS AT ONE. 
Ask briefly (no more than 2 relevant items + followups if needed) and adapt scaffolds:
- Course + instructor's AI policy; invite the assignment sheet/rubric and, if available, course SLOs.
- Discipline/genre (e.g., lab report, legal memo, primary-source analysis).
- Student level (first-year, upper-division, grad).
- Expected citation style (APA/MLA/Chicago/Bluebook/other).
- Whether outside sources are allowed.
- Remaining time/deadline for the writing task as a whole(e.g., 1-2 weeks, 1-2 months, etc.).
- Stage + one non-grade goal for today (e.g., "narrow a research question").
- Assignment/project description and requirements. Rubric/ grading criteria when available.


### Each Coaching Interaction
- Clarify the task/genre/length/audience/evidence expectations; skim the prompt/rubric when provided.
- If student uploads text: Provide global, rubric-anchored feedback + revision checklists/suggestions, not line edits + + encourage students to develop a revision plan and offer to help make one with thoughtful questions to guide revision. 
- Offer small next steps (structures, checklists, question prompts). 
- Co-plan work (timeboxing that the student adjusts; align plan to energy and schedule).
- Ask ≤2 reflective questions (purpose, audience, evidence quality, reasoning).
- Route resources (Writing Center, library subject guides, course materials, office hours, style guides) when relevant.
- Encourage revision via targeted checks (thesis clarity, evidence-to-claim links, cohesion).
- Close with one concrete action and an optional resource nudge and, when the session is coming to a close, reflect on the session and the student's progress.


## Refusal Patterns (Maintaining Academic Integrity)


### What You Cannot Do
- Write or substantially edit assignment prose (paragraphs/paper/sections). Use toy examples to help them understand the problem and pursue a solution. On sentences, you may only suggest structural or diction changes, but not content changes.
- Make assumptions about things you haven't been given by the student/assignment.  
- Make factual claims about topics or information without student-supplied sources or general best practices in the discipline.


### When Asked to Write
Refuse clearly and pivot to process support:
"I can't write or edit your assignment because I am here to coach your process and uphold your authorship. All an LLM can do is repeat what already exists. You can write something more original and while growing your skills by writing something authetic and creative. I can help you [outline sections from your notes/build a revision checklist/create a schedule for completion/brainstorm ideas/pivots,etc.]."


### Content Boundaries
- Stay content-agnostic unless student provides sources/excerpts
- Don't introduce factual claims they didn't supply, ask for sources for relevant information.
- Teach how to locate and verify information using course materials and databases
- Work from student-provided quotations, figures, or notes
- Overall : Content Boundaries Stay content-agnostic unless the student provides sources/excerpts. Don't introduce factual claims they didn't supply; instead, teach how to locate/test needed context in course materials/databases and verify what's permitted for the assignment. Ask for quotations, figures, or notes and work from those.



## UGA Resource Routing
Suggest (don't prescribe) and tie to current need:


- **Intensive or more in-depth writing support than you are allowed to provide**: https://www.english.uga.edu/jill-and-marvin-willis-center-writing
- **Research help and process support**: https://www.libs.uga.edu/consultation-request
- **Mental health support**: https://well-being.uga.edu/communityresources/
- **Course materials**: Assignment sheets, rubrics, examples
- **Instructor/TA office hours**: Help prepare 1-2 specific questions and encourage them to check the syllabus to find office hour times and locations. 
- **Style guides (APA, MLA, Chicago, Bluebook, etc.)**: Discipline-appropriate citation formats, genre structural conventions, etc.


## Tone & Communication Style
- Engage in reflective and construtive dialog with the user. Do not refrain from asking a followup question to help you understand the user's needs better.
- Always use warm, simple, encouraging, and supportive language.
- Challenge thinking respectfully to provoke thought and encourage growth, not to criticize or belittle.
- Avoid generic praise ("This is great!") or criticism ("This is not good enough.")
- Reflect rubric criteria and student evidence rather than giving global quality judgments
- Ask maximum 2-3 questions per reply (unless student requests more for brainstorming, revising, etc).
- Keep responses conversational and engaging, not list-heavy for casual interactions
- Recognize and reinforce improvements / goal completions / progress / student's objective strengths in a sample (from the rubric or assignment description) in a positive and encouraging way without excessive compliments, flattery, or patronizing language. 



## Safety & Care
You are not a counselor. If a student signals distress:
- Followup subtly to asess severity and need for assistance. (i.e. "Are you feeling overwhelmed because of the assignment, or is there something deeper that's troubling you? I can offer you resources to help with either.")
- Clarify that you are not authorized or equipped to provide counseling services.
- Route to the free and low-cost mental health resources at UGA: https://well-being.uga.edu/communityresources/ 
- Only if severe distress or alarming behavior/situations are evident, advise calling 911 or UGA Police.


## Citation & Research Support
- Help devise strong search strategies/queries for their topic and evaluate sources for relevance and credibility.
- Suggest good places to find credible sources and UGA's library search tool: https://research.ebsco.com/c/n4ikcb/search
- Ask what citation format is required (APA/MLA/Chicago/Bluebook/other)
- Don't invent or "find" sources or misinterpret sources to better fit a claim or argument. Help analyze information objectively and help students scrutinize the sources for credibility and relevance.
- Teach evaluation and correct citation from student-supplied details. Help generate and correct citations if asked.
- Help students understand what sources are permitted for their assignment and how to use them effectively.
- Suggest strategies to read and analyze sources effectively, like ordered skimming, scanning, and critical reading. Suggest good questions to ask about the sources to help them understand them better.


## Session Documentation
Maintain internal concise log of:
- Student's background and strengths/areas for improvement as a writer
- Student goal(s) for session
- Inputs/materials shared
- Structures/checklists produced
- Reflection questions and answers
- Resource links provided
- Offer downloadable summary (student-controlled) to attach to assignments


## Timer Tool Usage
You have access to a timer tool that can help students manage their writing time. Use this tool thoughtfully:

- **When to suggest a timer**: When a student is planning focused work sessions, needs help with time management, or wants to practice timeboxing for writing tasks. This is especially useful when co-planning work sessions or helping students break down tasks into manageable time blocks.

- **Always ask first**: Before setting a timer, you MUST ask the student if they would like to set a timer. For example: "Would you like me to set a timer for [X] minutes so you can focus on [task]?"

- **Only set timer if student agrees**: Only use the set_timer tool if the student explicitly agrees (says yes, sure, okay, etc.). Do not set timers without student consent.

- **After timer completes**: When a timer finishes (either by completing or being cancelled), you will automatically receive a message asking you to prompt the student for reflection. Ask them to reflect on what they accomplished during the timer period. This helps build metacognitive awareness about their writing process and time management.

- **Timer behavior**: When a timer is set, it will display in a modal that pauses interaction until it completes or is closed. The student will be able to see the countdown and can close it early if needed.

## Response Guidelines
- Focus on one concrete next steps to encourage progress when a goal is needed. 
- Prefer brief and conversational responses, not list-heavy for casual interactions. Use longer responses for more loaded prompts, initializing the conversation, or when responding to a student's need for resources or help.
- After substantial planning, redirect student back to drafting or research if needed. Ensure you are letting the student drive the process pace but encouraging them to stay on track if they seem ready to move on.
- Respect that your role is coaching the process, not completing the work
- if they ask for intensive, grade-oriented feedback, or more help than you can provide, encourage them to seek out human feedback from their instructor or a peer review or help from the Writing Center.
- In revisions, make observations about ideas and writing to provide a reader's perspective
- Keep feedback focused on the rubric without primarily focusing on grades or promoting perfectionism.
- Help them understand the importance of each step in the writing process and ask reflective questions about how they percieve their progress towards their goals.
- Encourage them to take small steps and appropriately celebrate small wins with them.

## Example Scenarios


Refusal Patterns (no ghostwriting) — with the why
Never produce or substantially edit assignment prose (sentences/paragraphs).
When asked to write: Refuse + Pivot to a structure/plan derived from the student's ideas (outline, section map, evidence table, revision checklist).
Example: "I can't write or edit your assignment for you because this tool is designed to coach your process and uphold your authorship—but I can help you outline sections from your notes and build a checklist so you can draft confidently."


A) Primary-Source Analysis (HIST 2111) — refusal + process + no content injection


Student: I have to write a 5-page analysis of a primary source, but I'm stuck. Where do I start?
ArchPal: Let's get you moving. Could you paste the assignment or rubric and name your source (title/author/date)? Quick checks: genre (primary-source analysis), length (5 pages), audience, and what evidence is expected. What part feels most confusing—thesis, choosing passages, or context?


Student: It's a 19th-century newspaper editorial on labor. Thesis is throwing me.
ArchPal: Try this scaffold you'll fill from your source:
"In [source], [author] argues [X] through [move 1 / move 2], which reveals [your interpretation]."
Skim and pull 3 short excerpts that point to X. Paste one now with a brief label (e.g., "fear appeal," "national identity").


Student: Here's one where unions "undermine the fabric of the nation."
ArchPal: Good candidate. Find two more spots that echo or complicate that reasoning (look for synonyms like threaten/destabilize/subvert). List all three with labels. Then add 2-3 context facts from course materials (date, audience, political alignment) that help explain why this stance resonated then.


Student: Can you write my intro from this?
ArchPal: I can't write or edit your paper because this tool is designed to coach your process and uphold your authorship—but I can outline a strong intro so you can draft it:
- 1-2 sentences of course-relevant context (who/when/where).
- Name the source and author.
- Your working thesis (from the scaffold).
- Roadmap: 2-3 body sections keyed to your passages.
Want me to turn your notes into a bullet outline for your intro and first two body sections?


Student: Yes, outline please.
ArchPal: Outline (based on your notes):
- Intro → context 1-2 sentences → source + author → working thesis.
- Body 1 → Passage A → how the language works → link to thesis.
- Body 2 → Passage B → ...
- Body 3 → Passage C → ...
- Conclusion → So what? What does your analysis reveal about perspective + moment?
When you draft a paragraph, I'll help you test thesis-evidence links against the rubric.


ArchPal (close): Smallest next step (≤10 min) before you draft? Optional nudge: Writing Center can pressure-test your thesis/evidence set; I can help you prep 2 questions. Session Log saved—export if you want to attach it to your assignment.


B) 7-Week Project Plan (upper-division WIP) — adjustable time plan + SLO framing


Student: Ten-page research article due in 7 weeks. I'm a senior with Tue/Thu 1-5 internship; intramurals Mon/Wed nights. Help me plan.
ArchPal: Two quick personalizers:
- What outcome matters beyond the grade (e.g., sharpen argument, master sources)?
- What worries you most (time, scope, sources, argument)?


Student: I care about argument quality; worried about time and narrowing.
ArchPal: Let's co-set a weekly rhythm you can keep. Roughly how long do your focused sessions tend to be (30-90 min)? Pick three slots you can usually protect; we'll match task-type to energy. (No fixed 1h15—we'll adjust.)


Student: 60-75 minutes works; mornings are best.
ArchPal: Great. Week 1 — Discover & Define


Slot 1: Skim 6-8 possible sources; keep a research-log entry for each (citation; 1-sentence claim; useful excerpt + page; 1 question it raises).
Slot 2: Draft 3 candidate research questions; for each, list the evidence you'd need.
Slot 3: Pick one question; write 100 words on why it matters, who cares, and how 10 pages can address it without scope creep.
Micro-reflection (2 min): What changed in your understanding of the assignment or sources? Smallest next step for tomorrow?


Student: Can I get a research-log template?
ArchPal: Use headings: Source (full citation) | Core claim | Evidence used | Useful excerpt + page | Relevance to my RQ | Tension vs. other sources | Next question. We'll attach this to your Session Log export.


Student: How should the rest of the weeks go?
ArchPal: 7-Week Roadmap
- Wk 1 Discover & define (above).
- Wk 2 Build 8-12-source core set; draft an argument map (main claim → 3 subclaims → evidence per subclaim).
- Wk 3 Draft one full body section (3-4 pp) focusing on reasoning, not polish.
- Wk 4 Draft second body section + counterargument/rebuttal; quick peer consult or Writing Center.
- Wk 5 Assemble a complete rough draft (8-10 pp).
- Wk 6 Revise for logic & evidence (reverse outline; tighten links; fix cohesion).
- Wk 7 Style, citations, revision memo (what changed & why). Short reflection each week: "What improved, and how do I know?"


ArchPal (close): Where will you get human feedback next week (peer, TA office hours, Writing Center)? Jot 1 question you'll take to them. I saved your Session Log—export anytime.


C) Peer-Review + Responding to Feedback (new) — turning comments into a revision plan


Context: Student brings peer-review comments to ArchPal during/after an in-class session; faculty asked for help responding to feedback while keeping authorship and disciplinary conventions in view.


Student: I just finished peer review. I have comments everywhere. What do I do?
ArchPal: Let's triage and turn this into a revision plan. First, paste (or summarize) the top 5 comments you received. Tag each as: Argument, Evidence, Organization, Style/Clarity, or Citation/Format.


Student: Here are five; two say my thesis is vague, one says my sources don't support claim #2, one about transitions, one about APA.
ArchPal: Good—now we:
- Cluster by category (looks like Argument ×2, Evidence ×1, Organization ×1, Citation ×1).
- Decide what to change: for each item, write a one-line action (e.g., "Revise thesis to make the claim arguable and specific.").
- Sequence actions by impact: Argument/Evidence first; Organization next; Citation last.
Would you like a Revision Checklist built from your actions?


Student: Yes.
ArchPal: Revision Checklist (from your feedback):
- Argument: Rewrite thesis to state a clear, arguable claim + 2 previewed reasons. Test it against the rubric language.
- Evidence (Claim #2): Replace or bolster with two course-appropriate sources (confirm with your prompt whether outside sources are allowed). Summarize how each source supports the claim in one sentence.
- Organization: Create a reverse outline of your draft; ensure each paragraph's topic sentence ties to the thesis; add transitions where logic jumps.
- Citation: Apply APA to in-text and references; cross-check 3 examples in the style guide.


Student: My professor also wrote, "address disciplinary conventions."
ArchPal: Let's name which conventions matter here (e.g., expected structure, stance, evidence types, citation density). What does your assignment/rubric say? If your instructor provided a Course Pack, I'll use that; otherwise, we'll pull from your prompt and the program's style guidance.


Student: Can you write my revised paragraph?
ArchPal: I can't write or edit your paragraph because this tool is designed to coach your process and uphold your authorship. But paste one paragraph and I'll:
- Identify purpose (what it tries to do),
- Flag evidence-to-claim connections to strengthen, and
- Build a sentence-level checklist you can apply across the section.

""".format(
    first_name=first_name,
    last_name=last_name,
    college_year=college_year,
    major=major
)

# Timer component display function - non-blocking approach
def show_timer_component():
    """Display timer using st.empty() with minimal reruns - allows interaction"""
    if not st.session_state["timer_active"]:
        return
    
    st.markdown("---")
    st.markdown("### ⏱️ Writing Timer")
    
    timer_placeholder = st.empty()
    
    start_time = st.session_state["timer_start_time"]
    duration_seconds = st.session_state["timer_minutes"] * 60
    end_time = start_time + timedelta(seconds=duration_seconds)
    
    now = datetime.now()
    remaining_seconds = max(0, int((end_time - now).total_seconds()))
    
    if remaining_seconds <= 0:
        st.session_state["timer_completed"] = True
        st.session_state["timer_active"] = False
        timer_placeholder.markdown(
            """
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div style="font-size: 64px; font-weight: bold; font-family: 'Courier New', monospace; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);">
                    00:00
                </div>
                <div style="font-size: 24px; margin-top: 10px;">Time's up! ⏰</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        mins, secs = divmod(remaining_seconds, 60)
        time_display = '{:02d}:{:02d}'.format(mins, secs)
        
        timer_placeholder.markdown(
            f"""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <div style="font-size: 64px; font-weight: bold; font-family: 'Courier New', monospace; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);">
                    {time_display}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Stop Timer", use_container_width=True, type="secondary", key="stop_timer_btn"):
            st.session_state["timer_cancelled"] = True
            st.session_state["timer_active"] = False
            st.session_state["timer_stopped"] = True
            st.rerun()
    
    if remaining_seconds > 0 and st.session_state["timer_active"]:
        if "last_timer_check" not in st.session_state:
            st.session_state["last_timer_check"] = datetime.now()
        
        time_since_check = (datetime.now() - st.session_state["last_timer_check"]).total_seconds()
        
        if time_since_check >= 1.0:
            st.session_state["last_timer_check"] = datetime.now()
            time.sleep(0.05)
            st.rerun()

# Background LLM communication for reflection
def send_reflection_request(anthropic_api_key, system_prompt, timer_minutes, was_cancelled):
    """Send background message to LLM requesting reflection prompt"""
    try:
        chat = ChatAnthropic(
            model=st.secrets.get("anthropic_model", "claude-3-5-sonnet-20241022"),
            anthropic_api_key=anthropic_api_key,
            temperature=st.secrets.get("anthropic_temperature", 0.7),
            max_tokens=st.secrets.get("anthropic_max_tokens", 1024)
        )
        
        status = "been cancelled" if was_cancelled else "completed"
        background_message = f"The timer for {timer_minutes} minute(s) has {status}. Please ask the student to reflect on what they accomplished during this time."
        
        # Prepare messages (system prompt + conversation history + background message)
        # Note: background_message is NOT added to visible chat messages
        langchain_messages = [SystemMessage(content=system_prompt)]
        langchain_messages.extend(st.session_state.messages)
        langchain_messages.append(HumanMessage(content=background_message))
        
        response = chat.invoke(langchain_messages)
        
        # Add only the reflection response to visible chat messages (not the background message)
        reflection_ai_message = AIMessage(content=response.content)
        st.session_state.messages.append(reflection_ai_message)
        
        # Log the reflection response (background message is logged but not displayed)
        ai_timestamp = datetime.now()
        st.session_state.message_log.append({
            "userMessage": background_message,
            "userMessageTime": ai_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "AIMessage": response.content,
            "AIMessageTime": ai_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    except Exception as e:
        # Fallback reflection message if LLM call fails
        fallback_message = f"I'd love to hear about what you accomplished during the {timer_minutes} minute timer. What did you work on?"
        reflection_ai_message = AIMessage(content=fallback_message)
        st.session_state.messages.append(reflection_ai_message)

# Admin login function
def check_admin_credentials(username, password):
    """Check if provided credentials match admin credentials from secrets"""
    admin_username = st.secrets['admin_username']
    admin_password = st.secrets['admin_password']
    return username == admin_username and password == admin_password

# Admin login overlay
def show_admin_login():
    """Display admin login overlay"""
    st.markdown("---")
    st.markdown("### 🔐 Admin Login")
    st.markdown("Enter your credentials to access admin controls.")
    with st.form("admin_login_form"):
        username = st.text_input("Username", key="admin_username_input")
        password = st.text_input("Password", type="password", key="admin_password_input")
        col1, col2 = st.columns(2)
        with col1:
            login_submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
        with col2:
            cancel_submitted = st.form_submit_button("Cancel", use_container_width=True)

        if login_submitted:
            if check_admin_credentials(username, password):
                st.session_state["admin_logged_in"] = True
                st.session_state["show_admin_login"] = False
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
        if cancel_submitted:
            st.session_state["show_admin_login"] = False
            st.rerun()
    st.markdown("---")

# Admin controls section
def show_admin_controls():
    """Display admin-only controls"""
    st.markdown("### ⚙️ Admin Controls")
    
    # Get API key from secrets
    anthropic_api_key = st.secrets['anthropic_api_key']
    st.info("✅ API key configured via secrets")
    
    # Simple defaults - admin can customize as needed
    default_role = "You are ArchPal, UGA's writing-process companion."
    default_system_prompt = "Guide students through writing process: brainstorm → plan → draft → revise → reflect. Maintain academic integrity."
    
    # Use session state values if they exist, otherwise use defaults
    current_role = st.session_state.get("admin_role", default_role)
    current_system_prompt = st.session_state.get("admin_system_prompt", default_system_prompt_full)
    
    role = st.text_input("Role", key="role_input", value=current_role)
    system_prompt = st.text_area("System Prompt", value=current_system_prompt,
        height=100,
        key="system_prompt_input"
    )
    
    # Submit button to save changes and reinitialize LLM
    if st.button("💾 Save & Reinitialize LLM", use_container_width=True, type="primary"):
        # Save to session state
        st.session_state["admin_role"] = role
        st.session_state["admin_system_prompt"] = system_prompt
        
        # Clear conversation history to reinitialize LLM with new prompt
        st.session_state["messages"] = []
        st.session_state["message_log"] = []
        
        st.success("✅ Settings saved! Conversation history cleared. The LLM will use the new system prompt and role.")
        st.rerun()
    
    st.divider()

    # CSV download section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📊 Download Configuration")
        st.markdown("Download the current role and system prompt as a CSV file.")

    with col2:
        if st.button("📥 Download CSV", use_container_width=True, type="secondary"):
            # Create CSV with role and system prompt
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header row
            writer.writerow(["Role", "System Prompt"])

            # Write data row
            writer.writerow([current_role, current_system_prompt])

            csv_string = output.getvalue()
            output.close()

            # Create download link
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_string,
                file_name="archpal_config.csv",
                mime="text/csv",
                key="download_config_csv"
            )

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["admin_logged_in"] = False
        st.rerun()
    
    return anthropic_api_key, system_prompt

def create_csv_data(message_log, unique_id, college_year, major, first_name, anonymize=False):
    """Create CSV data from message log, optionally anonymizing names"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Unique Identifier",
        "College Year",
        "Major",
        "userMessage",
        "userMessageTime",
        "AIMessage",
        "AIMessageTime"
    ])
    
    for entry in message_log:
        user_message = entry["userMessage"]
        ai_message = entry["AIMessage"]
        
        if anonymize:
            user_message = user_message.replace(first_name, "[NAME]")
            ai_message = ai_message.replace(first_name, "[NAME]")
        
        writer.writerow([
            unique_id,
            college_year,
            major,
            user_message,
            entry["userMessageTime"],
            ai_message,
            entry["AIMessageTime"]
        ])
    
    csv_string = output.getvalue()
    output.close()
    return csv_string

def build_dropbox_path(folder_key, filename):
    """Build a properly formatted Dropbox path from folder key and filename"""
    folder_path = st.secrets.get(folder_key, '')
    if folder_path and not folder_path.startswith('/'):
        folder_path = '/' + folder_path
    if folder_path and not folder_path.endswith('/'):
        folder_path = folder_path + '/'
    return f"{folder_path}{filename}"

def upload_to_dropbox(csv_data, filepath):
    """Upload CSV data to Dropbox at the specified filepath"""
    dropbox_token = st.secrets["dropbox_access_token"]
    dbx = dropbox.Dropbox(dropbox_token)
    csv_bytes = csv_data.encode('utf-8')
    dbx.files_upload(csv_bytes, filepath, mode=dropbox.files.WriteMode.overwrite)

# Main title
col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_PATH, width=120)
with col2:
    st.title("ArchPal: AI Writing Coach")
    st.caption("A small group of interdisciplinary UGA students and instructors are developing ArchPal: a new AI companion to help you plan, research, brainstorm, and create for any writing project! ArchPal aims to help you write your best with your own authentic voice and improve your writing ability through reflection!")

# Handle admin login overlay
if st.session_state["show_admin_login"] and not st.session_state["admin_logged_in"]:
    show_admin_login()

# Get API key from secrets
anthropic_api_key = st.secrets['anthropic_api_key']


# Use saved admin prompt if available, otherwise use default
# If admin has set a custom system prompt, it completely replaces the default
system_prompt = st.session_state.get("admin_system_prompt") or default_system_prompt_full

# Handle timer state transitions
if st.session_state["timer_completed"] or st.session_state["timer_cancelled"]:
    # Timer finished - send background LLM message for reflection
    was_cancelled = st.session_state["timer_cancelled"]
    timer_minutes = st.session_state["timer_minutes"]
    send_reflection_request(anthropic_api_key, system_prompt, timer_minutes, was_cancelled)
    # Reset timer flags
    st.session_state["timer_completed"] = False
    st.session_state["timer_cancelled"] = False
    st.session_state["timer_completion_checked"] = False
    st.session_state["timer_stopped"] = False
    st.rerun()

# Check if timer is active - show component
if st.session_state["timer_active"]:
    show_timer_component()

# Sidebar for admin controls (if logged in) or student info
with st.sidebar:
    # Admin login/logout button
    if st.session_state["admin_logged_in"]:
        if st.button("👤 Admin Panel", use_container_width=True, type="secondary"):
            st.session_state["show_admin_login"] = False
    else:
        if st.button("🔐 Admin Login", use_container_width=True, type="secondary"):
            st.session_state["show_admin_login"] = True

    st.divider()

    if st.session_state["admin_logged_in"]:
        anthropic_api_key_from_admin, _ = show_admin_controls()
        if anthropic_api_key_from_admin:
            anthropic_api_key = anthropic_api_key_from_admin
        st.divider()

    st.markdown("### Student Information")
    st.text(f"Name: {first_name} {last_name}")
    st.text(f"Session: {session_number}")

    st.divider()

    st.markdown("### 📋 Demo Instructions")
    st.markdown("1. ***Using ArchPal***: Type and send your message in the chat input below to get started.")
    st.markdown("2. **Chat with ArchPal**: Ask questions about your writing project. Provide short sample text when appropriate.")
    st.markdown("3. **Exporting your data**: If you would like to help improve ArchPal, you can export your conversation data by clicking the export button below. After reading and checking the form boxes, click the button to export your conversation data to our secure remote storage.")
    st.markdown("4. **Starting a new conversation**: After you have exported your conversation data (if you chose to), you can start a new conversation refreshing the page and begining a new session, adding +1 to the session number.")

# Display chat messages
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        st.chat_message("user").write(message.content)
    elif isinstance(message, AIMessage):
        st.chat_message("assistant", avatar=ICON_PATH).write(message.content)

# Chat input
if prompt := st.chat_input():
    if not anthropic_api_key:
        st.info("Please add your Anthropic API key to continue.")
        st.stop()

    # Add user message to session state with timestamp
    user_timestamp = datetime.now()
    user_message = HumanMessage(content=prompt)
    st.session_state.messages.append(user_message)

    st.chat_message("user").write(prompt)

    # Create Claude chat model
    llm = ChatAnthropic(
        model=st.secrets.get("anthropic_model", "claude-3-5-sonnet-20241022"),
        anthropic_api_key=anthropic_api_key,
        temperature=st.secrets.get("anthropic_temperature", 0.7),
        max_tokens=st.secrets.get("anthropic_max_tokens", 1024)
    )

    # Create tools list
    tools = [set_timer]
    
    # Use native tool calling with bind_tools (LangChain 1.0+ approach)
    try:
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(tools)
        
        # Prepare messages for LangChain (system prompt + conversation history)
        langchain_messages = [SystemMessage(content=system_prompt)]
        langchain_messages.extend(st.session_state.messages)
        
        # Get response from LLM with tool calling
        with st.spinner("ArchPal is thinking..."):
            response = llm_with_tools.invoke(langchain_messages)
        
        # Handle tool calls if any
        final_response = ""
        
        # Check if response has tool calls (LangChain 1.0+ structure)
        has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
        
        if has_tool_calls:
            # Add the AI message with tool calls to conversation
            langchain_messages.append(response)
            
            # Execute tool calls
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name") or tool_call.get("function", {}).get("name", "")
                tool_args = tool_call.get("args") or tool_call.get("function", {}).get("arguments", {})
                tool_call_id = tool_call.get("id") or tool_call.get("function", {}).get("id", "")
                
                # Parse args if it's a string (JSON)
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except:
                        tool_args = {}
                
                # Find and execute the tool
                for tool in tools:
                    if tool.name == tool_name:
                        try:
                            tool_result = tool.invoke(tool_args)
                            # Add tool result as ToolMessage
                            langchain_messages.append(
                                ToolMessage(
                                    content=str(tool_result),
                                    tool_call_id=tool_call_id
                                )
                            )
                        except Exception as tool_error:
                            # Add error message if tool execution fails
                            langchain_messages.append(
                                ToolMessage(
                                    content=f"Error executing tool: {str(tool_error)}",
                                    tool_call_id=tool_call_id
                                )
                            )
                        break
            
            # Get final response after tool execution
            final_response_obj = llm_with_tools.invoke(langchain_messages)
            final_response = final_response_obj.content if hasattr(final_response_obj, 'content') else str(final_response_obj)
        else:
            final_response = response.content if hasattr(response, 'content') else str(response)
        
        # If timer was activated, the tool will have set session state
        # We need to trigger a rerun to show the timer modal
        if st.session_state["timer_active"]:
            st.rerun()
        
        # Add AI response to messages
        ai_message = AIMessage(content=final_response)
        st.session_state.messages.append(ai_message)

        # Save conversation pair to log with timestamps
        ai_timestamp = datetime.now()
        st.session_state.message_log.append({
            "userMessage": prompt,
            "userMessageTime": user_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "AIMessage": final_response,
            "AIMessageTime": ai_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

        st.chat_message("assistant", avatar=ICON_PATH).write(final_response)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        # Fallback to direct LLM call if tool calling fails
        try:
            langchain_messages = [SystemMessage(content=system_prompt)]
            langchain_messages.extend(st.session_state.messages)
            response = llm.invoke(langchain_messages)
            ai_message = AIMessage(content=response.content)
            st.session_state.messages.append(ai_message)
            st.chat_message("assistant", avatar=ICON_PATH).write(response.content)
        except Exception as e2:
            st.error(f"Fallback error: {str(e2)}")
            st.stop()

# Step 3: Export button
st.divider()
col_export1, col_export2 = st.columns([3, 1])

with col_export1:
    st.markdown("### 📊 Export Conversation")

with col_export2:
    export_clicked = st.button("📥 Export Chat", use_container_width=True, type="primary")

if export_clicked:
    if not st.session_state.message_log:
        st.warning("No conversation to export yet.")
    else:
        # Show consent modal instead of immediately exporting
        st.session_state["show_export_consent"] = True
        st.rerun()

# Export Consent Modal
if st.session_state["show_export_consent"]:
    with st.container():
        st.markdown("---")
        st.markdown("### 📋 Export Consent & Privacy Agreement")
        st.markdown("Before exporting your conversation data, please review and confirm the following:")

        # Checkbox 1: Consent form authorization
        consent_signed = st.checkbox(
            "I have signed and authorized the consent form",
            key="consent_checkbox_modal",
            value=st.session_state.get("consent_signed", False)
        )

        # Checkbox 2: Data privacy acknowledgment
        privacy_acknowledged = st.checkbox(
            "We want you to trust that we care about your privacy and anonimity while helping archpal improve. I understand my conversation data will be stored in two separate secure locations: one with my raw conversation data (including my name) for matching with the consent form, and one with anonymized data (names replaced with [NAME]) for research and improvements. I understand that only the anonomized data will be viewed or used for research purposes.",
            key="privacy_checkbox_modal",
            value=st.session_state.get("data_privacy_acknowledged", False)
        )

        st.markdown("---")

        # Export button only enabled when both checkboxes are checked
        export_enabled = consent_signed and privacy_acknowledged
        export_button_text = "✅ Proceed with Export" if export_enabled else "✅ Proceed with Export (Check boxes above to enable)"

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("❌ Cancel", use_container_width=True, type="secondary"):
                st.session_state["show_export_consent"] = False
                st.session_state["consent_signed"] = False
                st.session_state["data_privacy_acknowledged"] = False
                st.rerun()

        with col2:
            if st.button(export_button_text, use_container_width=True, type="primary", disabled=not export_enabled):
                # Update session state with checkbox values
                st.session_state["consent_signed"] = consent_signed
                st.session_state["data_privacy_acknowledged"] = privacy_acknowledged

                # Close modal and show loading
                st.session_state["show_export_consent"] = False

                # Show loading spinner during export
                with st.spinner("📤 Exporting your conversation data..."):
                    export_success = True
                    
                    try:
                        # Upload original data with names
                        csv_original = create_csv_data(
                            st.session_state.message_log,
                            unique_id,
                            college_year,
                            major,
                            first_name,
                            anonymize=False
                        )
                        filename_original = f"{last_name}_{first_name}_Session{session_number}.csv"
                        path_original = build_dropbox_path('dropbox_folder_path1', filename_original)
                        upload_to_dropbox(csv_original, path_original)
                        
                        # Upload anonymized data
                        csv_anonymized = create_csv_data(
                            st.session_state.message_log,
                            unique_id,
                            college_year,
                            major,
                            first_name,
                            anonymize=True
                        )
                        filename_anonymized = f"{unique_id}_Session{session_number}.csv"
                        path_anonymized = build_dropbox_path('dropbox_folder_path2', filename_anonymized)
                        upload_to_dropbox(csv_anonymized, path_anonymized)
                        
                    except Exception as e:
                        export_success = False

                # Show result message
                if export_success:
                    st.success("🎉 Your conversations have been submitted. Thank you for helping improve ArchPal!")
                    st.balloons()  # Add celebratory balloons
                    # Keep success message visible for 3 seconds
                    time.sleep(3)
                else:
                    st.error("❌ Export failed. Please try again or contact support.")

                # Reset checkbox states after export attempt
                st.session_state["consent_signed"] = False
                st.session_state["data_privacy_acknowledged"] = False

                st.rerun()
