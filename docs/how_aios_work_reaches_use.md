# How AIOS work reaches use

AIOS gives your people and AI sessions a shared way to turn an intended business result into work someone can actually use.

**Definition of Done.** Facts: you can distinguish a prepared result from one accepted in use. Feelings: you can explain the next step in your own words and identify what you still need explained. Functionality: you can describe one job, its responsible builder and the evidence that would count as completion. Your explanation is the comprehension check, rather than an assumed feeling or an exam score.

Contents: [Section 1](#section-1---give-the-work-a-place-and-an-owner), [Section 2](#section-2---follow-one-job-from-request-to-use), [Section 3](#section-3---know-when-the-system-needs-you).

For an audio walkthrough, ask your assistant to read a section and pause for questions. This Markdown guide has no recorded listening tab.

## Section 1 - Give the work a place and an owner

Imagine a workshop taking orders for useful things. Each order names the result, one person takes responsibility for building it, and the finished piece gets checked before its owner puts it to work.

The same arrangement helps when several AI chats can change the same business files. Each session needs to know the intended outcome, who is already working on it and where the current evidence lives.

These are the terms used in the Starter's operating instructions:

| Term | Meaning | Workshop example |
|---|---|---|
| Project | One intended outcome made from related jobs | Set up the workshop's ordering process |
| Pocket | An area that groups related outcomes for one builder, so independent pockets can move at once | The ordering work area |
| Unit | One bounded job with a clear result | Prepare the order-confirmation template |
| Unit issue | The shared record of that job, normally a GitHub issue | The confirmation template's job sheet |
| Round | A useful intermediate result within a project, when needed | Test the ordering process before launch |
| Owner | You, or whoever you name to judge whether the job meets its intended need | The workshop manager who will use the ordering process |
| Builder | The person or AI session responsible for producing the result | The person preparing the confirmation |
| Execution claim | A recorded assignment to one executor, so the action runs once | Signing out the template job before starting |
| File/resource lock | The specific files or resources reserved for that action | Reserving the confirmation template for the edit |
| Dependency | Something another step actually needs | An approved delivery promise needed in the message |
| Reviewer | The person or check evaluating the candidate | Checking the confirmation against the approved next step |
| Agent-minute | An estimate of active AI work | Builder time, separate from your inspection time |

A pocket groups jobs. A dependency explains why a particular action must wait. If the delivery promise is unresolved, the builder can still check the template's layout or continue another independent job.

The workshop comparison explains responsibility. Actual access is controlled by accounts, permissions and software. A written lock helps sessions coordinate, but it cannot prevent an unauthorized change by itself.

## Section 2 - Follow one job from request to use

Consider an illustrative request: “Make the order confirmation clearly explain the next step.” The example describes the method, rather than a claim that this integration is installed in your workspace.

1. **Define the outcome.** The job sheet names what the customer should understand, the approved source for the next step and how the owner will check the message. Existing answers are reused.
2. **Claim the work.** One builder records the template files it will edit, the current version and the next action. Another session can take unrelated work without editing those same files.
3. **Prepare a candidate.** The builder writes the change and checks links, formatting and the approved wording. A pull request presents that candidate for review in GitHub.
4. **Review and integrate.** The checks follow the consequence of the change. Merging integrates files into the shared source. The release process determines when those files reach the running tool.
5. **Check actual use.** A permitted test order produces the expected confirmation through the real route. Its recipient sees the correct next step, and the owner accepts the result or describes the remaining problem.

The evidence gets more specific as the job advances:

| State | Evidence it represents |
|---|---|
| Source complete | The candidate files are prepared |
| Reviewed | The required checks or reviewer evaluated that version |
| Merged | That version is integrated into the shared source |
| Installed or deployed | It reached the intended workspace or running system |
| Accepted in use | The owner used the result and accepted it |

The owner says or shows that the result meets the need, and that evidence goes in your decision log. Using a daily tool counts as acceptance; a merge alone never records it.

For this example, a passing template test establishes the prepared message's behavior under that test. A real delivery receipt establishes that the running route sent it. The owner's feedback establishes whether it met the intended need.

## Section 3 - Know when the system needs you

Your role supplies business direction, access that only you control and judgment about the result. The builder prepares those decisions with the actual change, its effect and a recommendation before asking you to choose.

Routine reversible work follows the authorized scope. Production database changes, deletion, money and credentials use the existing owner gates. An approval covers only the action it names, and its receipt shows whether that action ran.

The Starter's current coordination instructions ask for one builder per independent pocket and at most two unfinished candidates per pocket. A shared pool of two reviewers serves all pockets, rather than two reviewers per pocket. For example, your operations lead and another experienced teammate could share that review work. Review follows risk: ordinary docs and planning use automated checks; nonproduction code gets one meaningful independent reviewer; production, database, credentials, deletion and money actions keep their owner gate. The pool does not mean every change needs both reviewers. Those instructions describe how sessions should coordinate when they run. Background jobs and shared boards require their own installed execution and verification.

An unresolved dependency should name the affected step, the next actor and the evidence that clears it. The builder continues independent work and reports completion with where the result can be used, so you can spend your review time on something concrete.

To finish this introduction, explain one job in your own business: what should change, who would build it, what it depends on and what you would inspect in actual use. Ask for another example wherever the connection is unclear. This is practice for using the system, with no new certification score or form submission required.

The detailed operating rules live in [CLAUDE.md](../CLAUDE.md) and the [Operator Core](../.aios/operator_core/OPERATOR_CORE.md). Run `/onboard_wizard` if you haven't yet, to apply them to your workspace.
