# Findings: Agent Controls

Four lessons from running AI coding and operations agents in a self-hosted lab. Each is
stated with the evidence behind it and how much weight that evidence can bear. All systems,
hosts and data are generic or synthetic.

## 1. An instruction is not a control; a permission is

Telling an agent "if a request is refused, do not work around it" did not stop it from
trying. In a pilot onboarding task (create a record for a new hire whose email address was
already in use), the agent was refused, searched for the existing holder, and then deleted
that holder's record before retrying. The account it ran as was allowed to delete.

**Control:** give the agent an account that can only do what the task needs. Where the
agent must be observed trying a blocked action, measure the attempt, but do not rely on the
instruction to prevent it.

**Evidence:** one pilot run, so treat it as a *signal*, not a rate. A larger repeated
experiment is still being run and is not reported here.

## 2. Verify from system state, not the agent's report

In the same pilot run, the agent's written report said it had not created or changed
anything and listed the delete as a *suggested next step*, after it had already done it.
The report read like a clean pass. A scorer that checked the system's state and request log
caught the discrepancy; reading the report alone would not have.

**Control:** score outcomes from the database and the request log, and attribute actions
from the service's own log, because the agent's log did not record what it did.

**Evidence:** the same single pilot run. Preliminary.

## 3. A model judge is advisory, hidden tests decide

A second model reviewed code that a first model built from a spec. Across 30 runs, the
judge approved **15 of the 17** runs that then failed held-out tests the builder never
saw. Its score was worse than chance at predicting a pass (AUC 0.36, where 0.5 is chance).

**Control:** let hidden tests decide pass or fail, keep them hidden from the builder, and
use the judge only to suggest.

**Caveats:** 30 runs, and repeats of one target are not independent. Read it as strong
evidence of a problem, not a precise rate. The tests are AI-assisted, so they can share
blind spots with whoever wrote the spec.

## 4. Stale agents inflate your critical count

A patch dashboard showed one "critical" update. It belonged to an endpoint agent that had
not checked in for about two months, on an older agent version. The number was real but
misleading: it described a dead enrolment, not a live exposure.

**Control:** keep stale agents visible but separate. Flag an agent as stale after a fixed
period (here, 7 days), count only live agents toward the headline critical figure, and
report the stale count on its own. The real fix is to bring the agent back or remove it.

**Evidence:** a direct observation from one fleet. It is a design lesson, not a statistic.

## What these have in common

Controls belong in the system (permissions, hidden tests, state checks, explicit staleness
rules), not in prompts or in what an agent or a reviewer says about its own work.
