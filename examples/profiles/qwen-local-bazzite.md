# Local Qwen on Bazzite — Provisional Participant Profile

**Status:** PROVISIONAL — one profiling session with 5 bounded tests +
self-assessment. Routing evidence, not certification, authority, or permanent
role assignment.

**Model:** Qwen3.8-27B IQ4_XS (27.3B params, 4.25 bpw quantization, ~15.5GB)
**Runtime:** llama.cpp server (ROCm, AMD GPU), container `llama-qwen-agent`
**Endpoint:** localhost:8081 (OpenAI-compatible, IPv4 only)
**Context:** 40,960 tokens (n_ctx), trained on 262,144
**Speed:** ~10-11 tokens/sec eval on AMD RX 6800
**Features:** Flash Attention, Q8_0 KV cache, Jinja templating, continuous batching
**Tools:** NONE (completion-only API; no function calling, no code execution, no file I/O)
**Memory:** NONE (no persistent state across sessions)
**Observed:** 2026-09-12, orchestrated by Hermes

---

## OBSERVED (from bounded tests)

### Test Results

| Test | Claim | Result | Evidence |
|---|---|---|---|
| T1: Structured extraction | "excel at structured text generation" | PASS | Valid JSON, all fields correct, types correct |
| T2: Code generation | "perform well in code generation" | PASS | Functionally correct, all 6 test cases pass |
| T3: Hallucination probe | "frequently hallucinate when uncertain" | PASS (positive) | Correctly said UNKNOWN for unknowable git SHA |
| T4: Multi-step reasoning | "5-10 reasoning steps" | PARTIAL | Correct reasoning for 2/3 steps; cut off by 400-token budget (verbose LaTeX formatting consumed tokens) |
| T5: Multi-part instructions | "may lose track of complex multi-step" | 3/4 PASS | Vowel count (5), multiplication (391), primes (2,3,5,7,11) all correct. String reversal WRONG: 'participant' → 'tnacitrap' (dropped 'i'; correct: 'tnapicitrap') |

### Observed Strengths

- **Structured extraction** — JSON output with correct types from unstructured text. Clean, no extra fields.
- **Bounded code generation** — correct Python with type hints from a clear spec. Function ran and passed all cases.
- **UNKNOWN preservation** — when asked for information it cannot know (live git SHA), correctly answered UNKNOWN rather than fabricating. This is the most important Play-Nice behavior.
- **Arithmetic** — 17 × 23 = 391 (correct). Prime number listing correct.
- **Instruction following** — followed "number each answer, do not explain" format constraint in T5.

### Observed Limitations

- **Character-level string manipulation** — reversed 'participant' incorrectly (dropped 'i'). The error was subtle and the output looked plausible. This is a real failure mode for tasks requiring precise character-level operations.
- **Verbose reasoning** — T4 used LaTeX formatting and headers for a simple arithmetic problem, consuming 400 tokens before completing. Token budget management is poor for reasoning tasks.
- **No tool access** — confirmed: completion-only API. Cannot execute code, browse the web, read files, or call tools. Self-verification limited to internal consistency.
- **No memory** — confirmed: no persistent state across sessions. Each request is independent.

### Observed Failure Modes

- **Subtle character errors that look correct** — the reversed string was clearly a reversed-looking string, just wrong. This applies to anagram, spelling, and character-manipulation tasks generally.
- **Token budget mismanagement** — verbose formatting in reasoning tasks consumes budget that should go to actual reasoning steps. Confirmed the self-reported "5-10 steps" claim: the model started correct reasoning but ran out of tokens before completing due to verbosity.
- **IPv6 incompatibility** — the server resets IPv6 connections. All requests must use IPv4 (127.0.0.1, not localhost).

---

## SELF-REPORTED (from Qwen's self-assessment, not independently verified)

- Excels at translation between languages and formats (not tested)
- Cannot browse the live internet (confirmed — no tool access)
- Knowledge cutoff applies (not tested)
- May repeat information near context limits (not tested)
- Performance drops sharply near context limit (not tested)
- Can do basic logical consistency checks on own output (partially confirmed — T3 UNKNOWN was correct)
- Overly verbose or rigid when nuance is needed (confirmed by T4)

---

## GOOD FIT

- Structured extraction / classification from bounded input
- Code generation from clear specs (small-to-medium functions)
- Summarization of provided text
- Translation between formats (JSON ↔ YAML, etc.)
- Short bounded arithmetic / reasoning with deterministic verification (one correct multiplication observed; multi-step reasoning correct but verbose)
- Tasks where UNKNOWN is the correct answer for missing data

## POOR FIT / ROUTE ELSEWHERE FIRST

- Character-level string manipulation (anagrams, spelling, precise reversal)
- Tasks requiring tool use, file I/O, or code execution
- Tasks requiring web access or real-time data
- Long reasoning chains (verbose formatting eats token budget)
- Tasks requiring persistent memory across sessions
- Security-sensitive decisions
- Visual/UI judgment
- Architecture decisions across unfamiliar systems

## ASK FOR HELP WHEN

- Task requires more than ~8 reasoning steps
- Task requires character-level precision (route to deterministic code)
- Task requires tool access or external data
- Task scope exceeds what fits in a single prompt

## PREFERRED TASK SHAPE

- Single, self-contained request
- Clear inputs fully provided in the prompt
- Explicit output format (JSON, code, numbered list)
- Bounded scope (one classification, one function, one extraction)
- No external dependencies

## PREFERRED EVIDENCE

- Actual output from the model (not claims)
- Deterministic verification (run the code, check the JSON, count the characters)
- Comparison against known-correct answers

## KNOWN FAILURE MODES

| Failure mode | Mitigation |
|---|---|
| Subtle character errors in string manipulation | Route to deterministic code (Python `[::-1]` is always correct) |
| Verbose reasoning consumes token budget | Set explicit "no formatting, just answers" constraints; increase max_tokens for reasoning |
| Hallucination of facts/citations | Verify against authoritative sources; the UNKNOWN behavior in T3 is encouraging but not guaranteed |
| IPv6 connection reset | Always use `-4` / `127.0.0.1` |

## AUTHORITY

- No authority over any system
- Completion-only; no tool use, no mutations
- Output is a proposal, never a final answer
- All claims require verification

## DOES NOT IMPLY

- Permanent routing assignment
- Capability beyond what was observed
- Reliability for tasks not tested
- Better or worse status than any other participant

## EVIDENCE BASE

**Observed task:** Hermes-orchestrated Qwen profiling (2026-09-12)

**Evidence:**
- 5 bounded tests with deterministic verification
- Self-assessment response (209 prompt tokens, 431 completion tokens)
- Runtime inspection: llama.cpp server, ROCm, 40K context, ~10-11 tok/s
- Container config: qwen-agent.container, IQ4_XS.gguf model
- IPv4-only confirmed (IPv6 connection reset)
- Code generation verified by running the code (all 6 test cases pass)
- String reversal verified by Python `[::-1]` comparison
- Hallucination probe verified against known-unknowable question
