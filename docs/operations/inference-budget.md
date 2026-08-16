<!-- SPDX-License-Identifier: MIT -->

# Inference budget

Inference spend is separate from the Option B platform estimate. The runtime
uses a 240-second timeout and a provisional fleet-wide PostgreSQL semaphore of
10 in-flight calls.

1. Review prepaid balance, request count, latency, timeout/retry rate, queue
   depth, and spend trend daily during migration.
2. Alert before the approved balance or monthly ceiling is exhausted; record
   the owner and threshold when the budget is approved.
3. On abnormal burn, pause new inference work while preserving accepted jobs in
   PostgreSQL. Keep uploads available only if the queue/backlog limit permits.
4. Check retries, model choice, payload size, and duplicate work before raising
   the cap or budget.
5. Resume gradually and verify queue recovery, error rate, and concurrency.

Do not raise the concurrency cap above 10 until provider quota and staging load
evidence support the change.
