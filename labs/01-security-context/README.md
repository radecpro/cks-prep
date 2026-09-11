# SecurityContext and capabilities

Status: implemented. Start with [TASK.md](TASK.md); no solution is included.

- `setup.sh`: create a fresh namespace and initial workload; never overwrite an attempt.
- `verify.sh`: read-only grading (Python 3 and kubectl required).
- `cleanup.sh`: delete this lab namespace and its contents.
- `initial.yaml`: deliberately insecure starting resources.

The default namespace is `cks-lab-01`. Maintainer QA may use `CKS_LAB_NAMESPACE=cks-lab-01-qa`; other overrides are rejected.

## Curriculum mapping

Domain: Minimize Microservice Vulnerabilities; workload privilege reduction. The domain reference was checked on 2026-09-07 against [CNCF curriculum revision f6c7667](https://github.com/cncf/curriculum/blob/f6c7667265fef850daaf93b4e19e919552c67d8c/cks/README.md). These task requirements are locally authored, not official exam questions.

## Validation

Live-tested on kind Kubernetes v1.37.0: initial state fails, hardened QA state passes with HTTP available, and a read-only filesystem regression is detected. Re-running setup refuses an existing namespace. The QA namespace is discarded before preparing the learner environment.

The grader checks declared configuration and selected runtime properties, not resistance to a malicious learner rewriting the grader. It does not attempt an exploit. No student attempt has been graded.
