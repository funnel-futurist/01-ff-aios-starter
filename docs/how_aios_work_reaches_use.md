# How AIOS work reaches use

AIOS gives your people and AI sessions a shared way to turn an intended business result into work someone can actually use.

**Definition of Done.** Facts: you can distinguish a prepared result from one accepted in use. Feelings: you can explain the next step in your own words and identify what you still need explained. Functionality: you can describe one job, its responsible builder and the evidence that would count as completion. Your explanation is the comprehension check, rather than an assumed feeling or an exam score.

Contents: [Section 1](#section-1---give-the-work-a-place-and-an-owner), [Section 2](#section-2---follow-one-job-from-request-to-use), [Section 3](#section-3---know-when-the-system-needs-you).

For an audio walkthrough, ask your assistant to read a section and pause for questions. This Markdown guide has no recorded listening tab.

## Section 1 - Give the work a place and an owner

Imagine a workshop taking orders for useful things. Each order names the result, one person takes responsibility for building it, and the finished piece gets checked before its owner puts it to work.

The same arrangement helps when several AI chats can change the same business files. Each session needs to know the intended outcome, who is already working on it and where the current evidence lives.

The logical work breakdown is **Project → Milestone → Task → Subtask → Checklist**. Each level answers a smaller question about the same outcome:

| Level | Meaning | Ordering-workshop example |
|---|---|---|
| Project | One intended outcome made from related jobs | Set up the workshop's ordering process |
| Milestone | A useful checkpoint with an observable result | A test order receives a confirmation with the correct next step |
| Task | A piece of work that produces part of that result | Prepare the order-confirmation template |
| Subtask | A smaller piece within that task | Write the sentence explaining the next step |
| Checklist | Completion checks attached to a task or subtask | Customer name, delivery promise and next-step link checked |

A **round** is a useful intermediate result within a project, when needed. Here, the round that tests ordering before launch reaches the test-order milestone. The plan states that relationship. Keep its existing round and milestone IDs rather than assuming the two labels always name the same object.

A tool's **projection** is its representation of the plan. The current ClickUp projection contract uses **Project → Milestone → Subtask → native Checklist**, or **Standalone Task → native Checklist** for a job outside a project. It maps the plan onto supported tool objects, rather than creating a separate object for every logical level. A native checklist is the tool's own populated checklist, whose items stay completion checks rather than separately assigned work.

For AI-led work, ClickUp holds a project record and actionable human tasks, while the detailed AI plan stays in its canonical records, the agreed source of truth. An installed integration needs its own verification.

These other terms describe how the work is grouped, recorded and assigned:

| Term | Meaning | Workshop example |
|---|---|---|
| Pocket | An area that groups related outcomes for one builder, so independent pockets can move at once | The ordering work area |
| Unit | A bounded scope of tracked work with a clear result, covering one task or a coherent group of tasks | The confirmation job, including drafting and testing it |
| Issue | A GitHub record for work, a problem or a discussion | A job sheet recording the confirmation request |
| Unit issue | The shared record of that job, normally a GitHub issue | The confirmation template's job sheet |
| Owner | You, or whoever you name to judge whether the job meets its intended need | The workshop manager who will use the ordering process |
| Builder | The person or AI session responsible for producing the result | The person preparing the confirmation |
| Execution claim | A recorded assignment to one executor, so the action runs once | Signing out the template job before starting |
| File/resource lock | The specific files or resources reserved for that action | Reserving the confirmation template for the edit |
| Dependency | Something another step actually needs | An approved delivery promise needed in the message |
| Reviewer | The person or check evaluating the candidate | Checking the confirmation against the approved next step |
| Agent-minute | An estimate of active AI work | Builder time, separate from your inspection time |

A pocket and the hierarchy group work. A dependency explains why a particular action must wait. A task in a later milestone can be ready now. If the delivery promise is unresolved, the builder can still check the template's layout or continue another independent job.

A task describes work to do. An issue records it. A unit sets the scope being tracked, rather than adding a fixed level to the hierarchy or requiring a separate issue for every task and checklist item.

The workshop comparison explains responsibility. Actual access is controlled by accounts, permissions and software. A written lock helps sessions coordinate, but it cannot prevent an unauthorized change by itself.

## Section 2 - Follow one job from request to use

Consider an illustrative request: “Make the order confirmation clearly explain the next step.” The example describes the method, rather than a claim that this integration is installed in your workspace.

A **candidate** is the proposed change. Its **source** is the editable files. A **version** identifies which saved revision of those files is being discussed, reviewed or installed. Git stores these revisions as commits, each with an exact commit ID. A **pull request (PR)** presents a candidate in GitHub for review and integration.

1. **Define the outcome.** The job sheet names what the customer should understand, the approved source for the next step and how the owner will check the message. Existing answers are reused.
2. **Claim the work.** One builder records the template files it will edit, the current version and the next action. Another session can take unrelated work without editing those same files.
3. **Prepare a candidate.** The builder writes the change and checks links, formatting and the approved wording, then presents that version in a PR.
4. **Review and integrate.** Review evaluates the candidate against the agreed need. The checks follow the consequence of the change. Merging integrates files into the shared source. A release packages a chosen version for distribution or upgrade, following the existing release process.
5. **Check actual use.** A permitted test order produces the expected confirmation through the real route. Its recipient sees the correct next step, and the owner accepts the result or describes the remaining problem.

**Evidence** is an observable result supporting a specific claim. A **receipt** preserves what happened, where, at which version and with what result. The delivery stages need different evidence:

| State | Evidence it represents |
|---|---|
| Source complete | The candidate files are prepared, ready for their next step |
| Reviewed | The required checks or reviewer evaluated that exact version |
| Merged | That version is integrated into the shared source |
| Released | An approved, identified package is available through the release route |
| Installed | The release reached the intended workspace |
| Deployed | The version reached the intended running service or environment |
| In use | The actual workflow runs, such as a permitted test order receiving its confirmation |
| Accepted in use | The owner used the result and accepted it |

A technical **MATCH** means the reviewer found that version consistent with the stated requirements. GitHub **APPROVED** is a formal review vote, whose eligible account and required version are determined by the repository's rules. The PR author cannot supply its own required approval. A **CODEOWNER** is an account or team configured to review particular file paths, a separate role from judging the business outcome. A required human code-owner vote must come from an eligible person, separately from an agent's technical MATCH or comment.

The owner says or shows that the result meets the need. This **acceptance** and the owner's decisions go in the [decision log](../00_AIOS/decisions_log.md), the lasting record of the chosen direction and its evidence. Using a daily tool counts as acceptance of the result used. The [install and upgrade guide](INSTALL_AND_UPGRADE.md) explains how an approved release reaches a workspace.

For this example, a passing template test establishes the prepared message's behavior under that test. A real delivery receipt establishes that the running route sent it. The owner's feedback establishes whether it met the intended need.

## Section 3 - Know when the system needs you

Your role supplies business direction, access that only you control and judgment about the result. The builder prepares those decisions with the actual change, its effect and a recommendation before asking you to choose.

Routine reversible work follows the authorized scope. Production database changes, deletion, money and credentials use the existing owner gates. An approval covers only the action it names, and its receipt shows whether that action ran.

The Starter's current coordination instructions ask for one builder per independent pocket and at most two unfinished candidates per pocket. A shared pool of two reviewers serves all pockets, rather than two reviewers per pocket. For example, your operations lead and another experienced teammate could share that review work. The pool does not mean every change needs both reviewers.

Review follows risk. Ordinary docs and planning use automated checks. Nonproduction code gets one meaningful independent reviewer. Production, database, credentials, deletion and money actions keep their owner gate. Those instructions describe how sessions should coordinate when they run. Background jobs and shared boards require their own installed execution and verification.

A **blocker** is an obstacle currently preventing a named next step. The unresolved delivery promise blocks final wording, while layout work can continue. A future dependency, a normal review handoff and a deliberate deferral need their own descriptions. These words explain availability and waits, while the delivery table above describes evidence. Keep the tracker’s established state values:

| Workflow word | What it means here | What moves it forward |
|---|---|---|
| Ready | The next action has its needed inputs and authorized scope | A builder takes the claim and starts |
| Running | Recent execution evidence shows that action is happening | The builder returns a result or a specific blocker |
| Review / awaiting review | A prepared candidate has reached its named reviewer | The reviewer evaluates that version and returns findings or a verdict |
| Blocked | A particular step cannot proceed because a prerequisite is missing | The named actor supplies the required input or clearing evidence |
| Held | An explicit pause or gate applies to the stated step | Its authorized decision or evidence clears that hold |
| Parked | Work is deliberately deferred, with its reason and restart condition recorded | The condition occurs and the owner revisits its place in the plan |
| Later | Work has a later place in the plan or is an unscheduled option | Its priority or milestone becomes current, without inventing a blocker or deadline |

A prepared result can have its integration blocked or awaiting review. Neither description says the builder is still running, and neither stops unrelated ready work. Record the affected step, next actor and evidence that clears it, then report completion with where the result can be used.

To finish this introduction, explain one job in your own business: what should change, who would build it, what it depends on and what you would inspect in actual use. Ask for another example wherever the connection is unclear. This is practice for using the system, with no new certification score or form submission required.

The detailed operating rules live in [CLAUDE.md](../CLAUDE.md) and the [Operator Core](../.aios/operator_core/OPERATOR_CORE.md). Run `/onboard_wizard` if you haven't yet, to apply them to your workspace.
